import requests
import json
import time
import datetime
import os
from pytz import timezone
import sqlite3

os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.getcwd(), "cacert.pem")


# create data base from schema
def create_db():
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.close()


def create_config():
    conn = sqlite3.connect('sigicom2Conf.db', timeout=30)
    with open('confSchema.sql') as f:
        conn.executescript(f.read())
    conn.close()


def get_sensors():
    token=get_token()
    header = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.get('https://soldataus.infralogin.com/api/v1/sensor', headers=header,
                            auth=('user',token))
    data = response.json()
    serials = []
    for row in data:
        if not row['disabled']:
            serials.append(row['serial'])
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    for sn in serials:
        cur.execute('INSERT OR IGNORE INTO instruments (serial) VALUES (?)', (str(sn),))
        cur.execute('INSERT OR IGNORE INTO stats (serial) VALUES (?)', (str(sn),))
    conn.commit()
    conn.close()


def get_sensor_info(sns=None):
    token=get_token()
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    if sns is None:
        sns = cur.execute('SELECT serial from instruments').fetchall()
        sns = [x[0] for x in sns]
    header = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    snDic = {}
    for sn in sns:
        print(sn)
        response = requests.get('https://soldataus.infralogin.com/api/v1/sensor/{}'.format(sn), headers=header,
                                auth=('user', token))
        data = response.json()
        sensorDic = {}
        sensorDic['timestamp_last_read'] = data['timestamp_last_read']
        if data['state'] == 'regon':
            sensorDic['regon'] = True
        else:
            sensorDic['regon'] = False
        snDic[sn] = sensorDic
    for sn in snDic.keys():
        cur.execute('UPDATE instruments SET time_last_read={}, regon={} WHERE serial={}'
                    .format(snDic[sn]['timestamp_last_read'], snDic[sn]['regon'], sn))
        print('UPDATE instruments SET time_last_read={}, regon={} WHERE serial={}')
    conn.commit()
    conn.close()


def update_sensor_parameters():
    token=get_token()
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    header = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.get('https://soldataus.infralogin.com/api/v1/logger',
                            headers=header,
                            auth=('user', token))
    data = response.json()
    for sensor in data:
        last_com, name, humid_time, humid, temp_time, temp, bat_time, bat = (0, 'Sigicom VM', 0, 0, 0, 0, 0, 0)
        serial = sensor['serial']
        try:
            last_com = sensor['last_communication']
            name = sensor['custom_name']
            humid_time, humid = list(sensor['humidity'][0].items())[-1]
            temp_time, temp = list(sensor['temperature_board'][0].items())[-1]
            bat_time, bat = list(sensor['battery_voltage'][0].items())[-1]
        except:
            print('Not all logger parameters available for: ', serial)
            pass
        cur.execute(
            'UPDATE instruments set com_dif=?-last_com, temp=?, temp_time=?, humid=?, humid_time=?, name=?, '
            'last_com=?, bat=?, bat_timestamp=? WHERE serial=?',
            (last_com, temp, temp_time, humid, humid_time, name, last_com, bat, bat_time, serial))
    conn.commit()
    conn.close()


def get_project_info():
    token=get_token()
    header = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.get('https://soldataus.infralogin.com/api/v1/project', headers=header,
                            auth=('user', token))
    data = response.json()
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    for project in data:
        cur.execute('INSERT OR IGNORE INTO projects (projectName) VALUES (?)', (project['name'],))
        response = requests.get(
            'https://soldataus.infralogin.com/api/v1/project/{}/measure_point'.format(project['id']), headers=header,
            auth=('user', token))
        data = response.json()
        ser_list = [dic['sensors'][0]['sensor_serial'] for dic in data]
        ser_string = "('" + "','".join([str(x) for x in ser_list]) + "')"
        print(ser_string)
        projectName = project['name']
        timezone = project['timezone']
        cur.execute(
            "UPDATE instruments set timezone='{}', projectName='{}' WHERE serial in {}".format(timezone, projectName,
                                                                                               ser_string))
    conn.commit()
    conn.close()


def generate_search_url(SN, start_timestamp, end_timestamp):
    token=get_token()
    #basetz = 'America/Los_Angeles'
    basetz=get_base_timezone()
    start_time = datetime.datetime.fromtimestamp(start_timestamp, tz=timezone(basetz))
    end_time = datetime.datetime.fromtimestamp(end_timestamp, tz=timezone(basetz))
    start_string, end_string = (datetime.datetime.strftime(x, '%Y-%m-%d %H:%M') for x in [start_time, end_time])
    header = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    data = {'datetime_from': start_string, 'datetime_to': end_string}
    data = json.dumps(data)
    response = requests.post('https://soldataus.infralogin.com/api/v1/sensor/{}/search'.format(SN),
                             data=data, headers=header,
                             auth=('user', token))
    if not response.status_code == 200:
        raise Exception('Error from API no data or invalid time period')
    # store url in DB
    print(response.json()['self_url'])
    return response.json()['self_url']


def check_search_state(url_post):
    token=get_token()
    header = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.get('https://soldataus.infralogin.com' + url_post, headers=header,
                            auth=('user', token))
    state = response.json()['state']
    return state



def check_for_update(sn):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute('SELECT com_dif from instruments where serial={}'.format(sn)).fetchone()
    last_com = ret[0]
    if last_com is not None and last_com > 0:
        max_dat = cur.execute('SELECT MAX(timestamp) from intervals where serial={}'.format(sn)).fetchone()[0]
        now = datetime.datetime.now().timestamp()
        if max_dat is not None and now - max_dat > 3600:
            start_timestamp = max_dat
        else:
            start_timestamp = now - 3600
        return start_timestamp, now
    conn.close()


def auto_acq(sn_list=None):
    if sn_list is None:
        sn_list = get_auto_record_instrums()
    update_sensor_parameters()
    for sn in sn_list:
        query_dts = check_for_update(sn)
        if query_dts is not None:
            get_data(sn, *query_dts)


def update_com_dif_err(SN):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    cur.execute('UPDATE instruments set last_com=0 WHERE serial={}'.format(SN))
    conn.commit()


def update_stats(sn, q, time, abort):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    cur.execute(
        'UPDATE stats SET queries=queries+{}, total_wait=total_wait+{}, avg_q_time=(total_wait+{})/(queries+{}), '
        'aborted_q=aborted_q+{} where serial={}'.format(
            q, time, time, q, abort, sn))
    conn.commit()


def update_aborted_urls(sn, start_timestamp, end_timestamp, url):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    cur.execute(
        'INSERT OR IGNORE INTO failed_urls (url, state, date_failed, serial, start_time, end_time) VALUES (?,?,?,?,?,?)',
        (url, 'aborted', datetime.datetime.now(), sn, start_timestamp, end_timestamp))
    conn.commit()


def get_data(SN, start_timestamp, end_timestamp, manual=False):
    token=get_token()
    start_timestamp = int(start_timestamp)
    end_timestamp = int(end_timestamp)
    url = generate_search_url(SN, start_timestamp, end_timestamp)
    header = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    print('Serial Number: ', SN)
    print('start_timestamp: ', start_timestamp, ' end_timestamp: ', end_timestamp)
    wait_time = 0
    for i in range(100):
        state = check_search_state(url)
        print(state)
        if state == 'abort':
            print('Data URL has been aborted')
            update_com_dif_err(SN)
            update_aborted_urls(SN, start_timestamp, end_timestamp, url)
            update_stats(SN, 1, wait_time, 1)
            return
        if state == 'finished':
            break
        time.sleep(10)
        wait_time += 10
    update_stats(SN, 1, wait_time, 0)

    for i in range(5):
        response = requests.get('https://soldataus.infralogin.com' + url + '/data', headers=header,
                                auth=('user', token))
        if response.status_code == 200:
            dataInt = json_to_df(response.json(), 'intervals')
            dataTrans = json_to_df(response.json(), 'transients')
            insert_rows(dataInt, 'intervals')
            insert_rows(dataTrans, 'transients')
            if not manual:
                export_data(SN, start_timestamp, end_timestamp)
            return
        else:
            print('Data URL returned incorrect response after finishing data_url')
            update_com_dif_err(SN)
            update_aborted_urls(SN, start_timestamp, end_timestamp, url)
        time.sleep(10)


def insert_rows(rows, table):
    start = time.time()
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    for row in rows:
        cur.execute(
            'INSERT OR REPLACE INTO {} (serial, timestamp, datetime, value, label, frequency) VALUES (?,?,?,?,?,?)'.format(
                table),
            (row['SN'], row['timestamp'], row['datetime'],
             row['value'], row['label'], row['frequency']))
    conn.commit()
    conn.close()
    end = time.time()
    print('time to insert data from query: ', end - start, " sec.")


def json_to_df(js, table):
    rows = []
    SN = js['meta']['devices'][0]['serial']
    sntz = get_timezone(SN)
    for data in js[table]:
        data_row = data[str(SN)][table]
        time = data['timestamp']
        for row in data_row:
            row['timestamp'] = time
            row['datetime'] = datetime.datetime.fromtimestamp(time, tz=timezone(sntz)).replace(tzinfo=None)
            row['SN'] = SN
            rows.append(row)
    return rows
    # df=pd.DataFrame(rows)


def get_base_timezone():
    conn=sqlite3.connect('sigicom2Conf.db', timeout=30)
    cur=conn.cursor()
    ret=cur.execute('SELECT timezone from secret_token').fetchall()
    conn.close()
    return ret[0][0]


def set_base_timezone(newTimezone: str):
    conn = sqlite3.connect('sigicom2Conf.db', timeout=30)
    cur = conn.cursor()
    cur.execute('UPDATE secret_token set timezone=(?)',(newTimezone,))
    conn.close()


def get_timezone(sn):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute('SELECT timezone from instruments WHERE serial={}'.format(sn)).fetchone()[0]
    conn.close()
    return ret


def update_auto_record(sn, state):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    cur.execute('UPDATE instruments set auto_record={} where serial ={}'.format(state, sn))
    conn.commit()
    conn.close()


def get_auto_record_instrums():
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute('SELECT serial from instruments where auto_record is true').fetchall()
    conn.close()
    return [x[0] for x in ret]


def get_project_names():
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute('SELECT projectName from projects').fetchall()
    conn.close()
    return [x[0] for x in ret]


def update_project_path(projectName, path):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    cur.execute("UPDATE projects set export_path='{}' where projectName='{}'".format(path, projectName))
    conn.commit()
    conn.close()


def get_project_path(projectName):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute("SELECT export_path from projects WHERE projectName='{}'".format(projectName)).fetchone()
    conn.close()
    return ret[0]


def get_sensors_by_project(projectName):
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute("SELECT serial, name from instruments where projectName='{}'".format(projectName)).fetchall()
    return [(x[0], x[1]) for x in ret]


def get_all_sensors():
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute('SELECT serial from instruments').fetchall()
    conn.close()
    return [x[0] for x in ret]


def get_token():
    conn = sqlite3.connect('sigicom2Conf.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute('SELECT token from secret_token').fetchall()
    conn.close()
    return ret[0][0]


def set_token(newToken: str):
    conn = sqlite3.connect('sigicom2Conf.db', timeout=30)
    cur = conn.cursor()
    cur.execute('UPDATE secret_token set token=(?)', (newToken,))
    conn.commit()
    conn.close()


def get_sensors_by_project_dict():
    conn = sqlite3.connect('sigicom2.db', timeout=30)
    cur = conn.cursor()
    ret = cur.execute("SELECT serial, name, projectName from instruments").fetchall()
    conn.close()
    output = {}
    for row in ret:
        if not row[2] in output.keys():
            output.update({row[2]: [(row[0], row[1])]})
        else:
            output[row[2]].append((row[0], row[1]))
    return output


def manual_export(sn, start_datetime, end_datetime):
    if type(sn) == list:
        for s in sn:
            sntz = get_timezone(s)
            start_timestamp = timezone(sntz).localize(start_datetime).timestamp()
            end_timestamp = timezone(sntz).localize(end_datetime).timestamp()
            export_data(s, start_timestamp, end_timestamp)
    else:
        sntz = get_timezone(sn)
        start_timestamp = timezone(sntz).localize(start_datetime).timestamp()
        end_timestamp = timezone(sntz).localize(end_datetime).timestamp()
        export_data(sn, start_timestamp, end_timestamp)


def manual_get_data(sn, start_datetime, end_datetime):
    if type(sn) == list:
        for s in sn:
            sntz = get_timezone(s)
            start_timestamp = timezone(sntz).localize(start_datetime).timestamp()
            end_timestamp = timezone(sntz).localize(end_datetime).timestamp()
            get_data(s, start_timestamp, end_timestamp, True)
    else:
        sntz = get_timezone(sn)
        start_timestamp = timezone(sntz).localize(start_datetime).timestamp()
        end_timestamp = timezone(sntz).localize(end_datetime).timestamp()
        get_data(sn, start_timestamp, end_timestamp, True)


def get_all_instrum_stats(sn):
    # SELECT a.*, b.*,c.bat, c.humid, c.temp, c.last_com from stats a join failed_urls b on a.serial=b.serial join instruments c on c.serial=a.serial where a.serial='102813' order by b.date_failed desc limit 1
    conn = sqlite3.connect('sigicom2.db', timeout=30, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    keys = ['serial', 'queries', 'total_wait', 'avg_q_time', 'aborted_q', 'bat', 'humid', 'temp', 'last_com']
    ret = cur.execute('SELECT a.*, c.bat, c.humid, c.temp, c.last_com from stats a join instruments c'
                      ' on c.serial=a.serial where a.serial={}'.format(sn)).fetchall()
    stats = dict(zip(keys, ret[0]))
    conn.close()
    return stats


def export_data(sn, start_time, end_time):
    print('Exporting: ', sn)
    conn = sqlite3.connect('sigicom2.db', timeout=30, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    ret = cur.execute(
        'SELECT a.serial, b.projectName, b.export_path from instruments a JOIN projects b on '
        'a.projectName=b.projectName where serial={}'.format(
            sn)).fetchone()
    path = ret[2]
    dat = cur.execute(
        'SELECT value, label, frequency, datetime as "[timestamp]" from intervals WHERE serial={} and timestamp>{} '
        'and timestamp<={} order by timestamp desc'.format(
            sn, start_time, end_time)).fetchall()
    dat2 = cur.execute(
        'SELECT value, label, frequency, datetime as "[timestamp]" from transients WHERE serial={} and timestamp>{} '
        'and timestamp<={} order by timestamp desc'.format(
            sn, start_time, end_time)).fetchall()
    tables = ['inter_', 'trans_']
    output = []
    row = None
    for idx, set in enumerate((dat, dat2)):
        prefix = tables[idx]
        for row in set:
            dat_name = prefix + row[1]
            date_string = row[3].strftime('%d/%m/%Y %H:%M:%S')
            ln = sn + '_' + dat_name + '\t' + date_string + '\t' + str(row[0]) + '\t0\n'
            output.append(ln)
            if row[2] is not None:
                dat_name = prefix + 'freq_' + row[1]
                ln = sn + '_' + dat_name + '\t' + date_string + '\t' + str(row[2]) + '\t0\n'
                output.append(ln)
    params = cur.execute(
        'SELECT humid, humid_time, temp, temp_time, bat, bat_timestamp, timezone from instruments where serial={}'.format(
            sn)).fetchone()
    humid_time = datetime.datetime.fromtimestamp(params[1], tz=timezone(params[6])).replace(tzinfo=None)
    temp_time = datetime.datetime.fromtimestamp(params[3], tz=timezone(params[6])).replace(tzinfo=None)
    bat_time = datetime.datetime.fromtimestamp(params[5], tz=timezone(params[6])).replace(tzinfo=None)
    output.append(sn + '_bat_V' + '\t' + bat_time.strftime('%d/%m/%Y %H:%M:%S') + '\t' + str(params[4]) + '\t0\n')
    output.append(sn + '_humid' + '\t' + bat_time.strftime('%d/%m/%Y %H:%M:%S') + '\t' + str(params[0]) + '\t0\n')
    output.append(sn + '_boardTemp' + '\t' + bat_time.strftime('%d/%m/%Y %H:%M:%S') + '\t' + str(params[2]) + '\t0\n')
    if row is None:
        row = [None, None, None, datetime.datetime.now()]
    fileName = path + row[3].strftime('%Y-%m-%dT%H_%M_%S') + "_sn_" + sn + '.txt'
    with open(fileName, 'w') as file:
        for ln in output:
            file.write(ln)
    conn.close()


def data_to_plot(sn, start_datetime, end_datetime):
    sntz = get_timezone(sn)
    start_time = timezone(sntz).localize(start_datetime).timestamp()
    end_time = timezone(sntz).localize(end_datetime).timestamp()
    print("sigi start time: ", start_time)
    print("sigi end time: ", end_time)
    conn = sqlite3.connect('sigicom2.db', timeout=30, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    dat = cur.execute(
        'SELECT value, label, frequency, datetime as "[timestamp]" from intervals WHERE serial={} and timestamp>={} '
        'and timestamp<={} order by timestamp desc'.format(
            sn, start_time, end_time)).fetchall()
    dat2 = cur.execute(
        'SELECT value, label, frequency, datetime as "[timestamp]" from transients WHERE serial={} and timestamp>={} '
        'and timestamp<={} order by timestamp desc'.format(
            sn, start_time, end_time)).fetchall()
    conn.close()
    interDic = {'L': [], 'T': [], 'V': [], 'R': []}
    for pt in dat:
        if pt[1] in interDic.keys():
            interDic[pt[1]].append((pt[3], pt[0]))
    transDic = {'L': [], 'T': [], 'V': []}
    for pt in dat2:
        if pt[1] in transDic.keys():
            transDic[pt[1]].append((pt[3], pt[0]))
    return interDic, transDic


def clear_old_data():
    try:
        timestamp_now = datetime.datetime.now().timestamp()
        timestamp_week_ago = timestamp_now - 604800
        conn = sqlite3.connect('sigicom2.db', timeout=30)
        cur = conn.cursor()
        cur.execute('DELETE FROM intervals WHERE timestamp<{}'.format(timestamp_week_ago))
        cur.execute('DELETE FROM transients WHERE timestamp<{}'.format(timestamp_week_ago))

        conn.commit()
        cur.execute('VACUUM')
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)

DROP TABLE IF EXISTS intervals;
DROP TABLE IF EXISTS transients;
DROP TABLE IF EXISTS instruments;
DROP TABLE IF EXISTS pending_urls;
DROP TABLE IF EXISTS failed_urls;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS stats;

CREATE TABLE pending_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    date_created TEXT NOT NULL,
    date_finished TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    serial TEXT NOT NULL,
    state TEXT DEFAULT "NOT CHECKED"
);
CREATE index url_time_index on pending_urls (end_date);

CREATE TABLE failed_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    state TEXT NOT NULL,
    date_failed TEXT NOT NULL,
    serial NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL
);

CREATE TABLE instruments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  serial TEXT UNIQUE NOT NULL,
  auto_record BOOL DEFAULT FALSE,
  projectName TEXT DEFAULT 'DEFAULT',
  regon BOOL DEFAULT FALSE,
  time_last_read INTEGER,
  name TEXT DEFAULT 'Sigicom VM',
  bat FLOAT,
  bat_timestamp INTEGER,
  timezone TEXT NOT NULL DEFAULT 'America/Los_Angeles',
  temp FLOAT,
  temp_time INTEGER,
  humid FLOAT,
  humid_time INTEGER,
  last_com INTEGER,
  com_dif INTEGER
);

CREATE TABLE stats (
    serial TEXT UNIQUE NOT NULL,
    queries INTEGER DEFAULT 0,
    total_wait INTEGER DEFAULT 0,
    avg_q_time FLOAT DEFAULT 0,
    aborted_q INTEGER DEFAULT 0
);



CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projectName TEXT UNIQUE DEFAULT "DEFAULT",
    export_path TEXT DEFAULT "./"
);

INSERT INTO projects (projectName, export_path) VALUES ('DEFAULT','./');

CREATE TABLE intervals (
    serial TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    datetime TEXT NOT NULL,
    value FLOAT NOT NULL,
    label TEXT NOT NULL,
    frequency FLOAT
);

CREATE index inter_time_index on intervals (timestamp);
CREATE UNIQUE INDEX inter_uni_dat ON intervals (timestamp, serial, label);

CREATE TABLE transients (
    serial TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    datetime TEXT NOT NULL,
    value FLOAT NOT NULL,
    label TEXT NOT NULL,
    frequency FLOAT
);

CREATE index trans_time_index on transients (timestamp);
CREATE UNIQUE INDEX trans_uni_dat ON transients (timestamp, serial, label);
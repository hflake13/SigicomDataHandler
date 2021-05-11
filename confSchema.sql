
DROP TABLE IF EXISTS secret_token;


CREATE TABLE secret_token (
    Lock char(1) not null,
    token TEXT DEFAULT "",
    timezone TEXT DEFAULT "America/Los_Angeles",
    constraint PK_T1 PRIMARY KEY (Lock),
    constraint CK_T1_Locked CHECK(Lock='X')
);

INSERT INTO secret_token (Lock, token) VALUES ('X',"");

DROP DATABASE IF EXISTS monitordb;
CREATE DATABASE monitordb;
use monitordb;

DROP TABLE IF EXISTS Reading;
DROP TABLE IF EXISTS Position;

CREATE TABLE Room (
    ID              int NOT NULL,
    roomName    	VARCHAR(15),
    PRIMARY KEY(ID)
);

CREATE TABLE Reading(
    ID              int NOT NULL AUTO_INCREMENT,
    temp            DECIMAL(4,2),
    humidity        SMALLINT,
    roomID      	int,
    date        	TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(ID),
    FOREIGN KEY(roomID)  REFERENCES Room(ID) ON DELETE SET NULL
);


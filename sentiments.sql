CREATE TABLE tweets (id INTEGER PRIMARY KEY, status TEXT, message VARCHAR(150), message_p VARCHAR(150), q VARCHAR(150));
CREATE TABLE sentiments (id VARCHAR(255), username VARCHAR(15), sentiment INTEGER, energy INTEGER, UNIQUE (id, username));

PRAGMA foreign_keys=ON;

BEGIN TRANSACTION;

CREATE TABLE words(
   id INTEGER NOT NULL PRIMARY KEY,
   word TEXT NOT NULL
);

CREATE TABLE solutions(
   parent_word integer NOT NULL,
   child_word integer NOT NULL,
   FOREIGN KEY (parent_word) REFERENCES words(id),
   FOREIGN KEY (child_word) REFERENCES words(id),
   PRIMARY KEY (parent_word, child_word)
);


CREATE TABLE player(
   id integer NOT NULL PRIMARY KEY,
   telegram_id TEXT NOT NULL
);

CREATE TABLE game_session(
   id integer NOT NULL PRIMARY KEY,
   player integer NOT NULL,
   word integer NOT NULL,
   is_over integer DEFAULT 0,
   timestamp integer NOT NULL,
   FOREIGN KEY (player) REFERENCES player(id),
   FOREIGN KEY (word) REFERENCES words(id),
   UNIQUE (id, player, word)
);

CREATE TABLE game_answers(
   id integer NOT NULL PRIMARY KEY,
   session integer NOT NULL,
   word integer NOT NULL,
   FOREIGN KEY (session) REFERENCES game_session(id),
   FOREIGN KEY (word) REFERENCES words(id),
   UNIQUE (id, session, word)
);

-- Test data
--insert into player(telegram_id) values(112233);
--insert into game_session(player, word, timestamp) values(1, 1, 20190209000000);
--insert into game_answers(session, word) values(1, 10);
--insert into game_answers(session, word) values(1, 20);
--insert into game_answers(session, word) values(1, 30);

COMMIT;

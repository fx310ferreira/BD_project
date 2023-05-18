CREATE TABLE publisher (
id	 BIGSERIAL,
name VARCHAR(512) NOT NULL,
PRIMARY KEY(id)
);

CREATE TYPE privilege AS ENUM ('ADMIN', 'ARTIST', 'COSTUMER');
CREATE TABLE login (
id	 BIGSERIAL,
username VARCHAR(512) NOT NULL UNIQUE,
email	 VARCHAR(512) NOT NULL UNIQUE,
password VARCHAR(512) NOT NULL,
user_privilege privilege NOT NULL,
PRIMARY KEY(id)
);


CREATE TABLE person (
cc	 VARCHAR(512) NOT NULL UNIQUE,
name	 VARCHAR(512) NOT NULL,
created_at TIMESTAMP NOT NULL,
phone	 BIGINT NOT NULL,
address	 VARCHAR(512) NOT NULL,
zip_code VARCHAR(512) NOT NULL,
city	 VARCHAR(512) NOT NULL,
login_id	 BIGINT,
PRIMARY KEY(login_id),
CONSTRAINT person_fk1 FOREIGN KEY (login_id) REFERENCES login(id)
);

CREATE TABLE administrator (
login_id BIGINT,
PRIMARY KEY(login_id),
CONSTRAINT administrator_fk1 FOREIGN KEY (login_id) REFERENCES login(id)
);

CREATE TABLE artist (
artistic_name		 VARCHAR(512) NOT NULL UNIQUE,
administrator_id 	BIGINT NOT NULL,
publisher_id		 BIGINT NOT NULL,
login_id	 BIGINT,
PRIMARY KEY(login_id),
CONSTRAINT artist_fk1 FOREIGN KEY (administrator_id) REFERENCES administrator(login_id),
CONSTRAINT artist_fk2 FOREIGN KEY (publisher_id) REFERENCES publisher(id),
CONSTRAINT artist_fk3 FOREIGN KEY (login_id) REFERENCES person(login_id)
);

CREATE TABLE consumer (
expire_date DATE NOT NULL,
login_id	 BIGINT,
PRIMARY KEY(login_id),
CONSTRAINT consumer_fk1 FOREIGN KEY (login_id) REFERENCES person(login_id)
);

CREATE TABLE song (
ismn			 BIGSERIAL,
title			 VARCHAR(512) NOT NULL,
genre			 VARCHAR(512),
release_date		 DATE NOT NULL,
duration		 INT,
artist_id BIGINT NOT NULL,
publisher_id		 BIGINT NOT NULL,
PRIMARY KEY(ismn),
CONSTRAINT song_fk1 FOREIGN KEY (artist_id) REFERENCES artist(login_id),
CONSTRAINT song_fk2 FOREIGN KEY (publisher_id) REFERENCES publisher(id)
);

CREATE TABLE song_feat (
artist_id 		BIGINT,
song_ismn		 BIGINT,
PRIMARY KEY(artist_id, song_ismn),
CONSTRAINT song_fk1 FOREIGN KEY (artist_id) REFERENCES artist(login_id),
CONSTRAINT song_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn)
);

CREATE TABLE comment (
id				 BIGSERIAL NOT NULL,
comment				 VARCHAR(512) NOT NULL,
consumer_id BIGINT NOT NULL,
comment_id			 BIGINT,
song_ismn			 BIGINT NOT NULL,
PRIMARY KEY(id),
CONSTRAINT comment_fk1 FOREIGN KEY (consumer_id) REFERENCES login(id),
CONSTRAINT comment_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn),
CONSTRAINT comment_fk3 FOREIGN KEY (comment_id) REFERENCES comment(id)
);

CREATE TYPE card_price AS ENUM (10, 25, 50);
CREATE TABLE pay_card (
id			 CHAR(16),
limit_date		 DATE NOT NULL,
price		 card_price NOT NULL,
ammount_left     DOUBLE PRECISION NOT NULL,
admin_id BIGINT NOT NULL,
customer_id BIGINT,
PRIMARY KEY(id),
CONSTRAINT pay_card_fk1 FOREIGN KEY (admin_id) REFERENCES administrator(login_id),
CONSTRAINT pay_card_fk2 FOREIGN KEY (customer_id) REFERENCES consumer(login_id)
);

CREATE TYPE plan_duration AS ENUM ('MONTH', 'QUARTER', 'SEMESTER');
CREATE TABLE plan (
id	 BIGSERIAL,
duration plan_duration  NOT NULL,
price	 DOUBLE PRECISION NOT NULL,
active     BOOL NOT NULL,
PRIMARY KEY(id)
);



CREATE TABLE subscription (
id				 BIGSERIAL,
movement_date			 TIMESTAMP NOT NULL,
plan_id			 BIGINT NOT NULL,
consumer_id BIGINT NOT NULL,
PRIMARY KEY(id),
CONSTRAINT subscription_fk1 FOREIGN KEY (plan_id) REFERENCES plan(id),
CONSTRAINT subscription_fk2 FOREIGN KEY (consumer_id) REFERENCES consumer(login_id)
);

CREATE TABLE subscription_activity (
subscription_id 	BIGINT,
pay_card_id			 CHAR(16),
ammount			DOUBLE PRECISION NOT NULL,
PRIMARY KEY(pay_card_id, subscription_id),
CONSTRAINT subscription_activity_fk1 FOREIGN KEY (pay_card_id) REFERENCES pay_card(id),
CONSTRAINT subscription_activity_fk2 FOREIGN KEY (subscription_id) REFERENCES subscription(id)
);

CREATE TABLE playlist (
id				 BIGSERIAL,
name				 VARCHAR(512) NOT NULL,
created_at			 TIMESTAMP NOT NULL,
private			 BOOL NOT NULL,
creator_id BIGINT NOT NULL,
PRIMARY KEY(id),
CONSTRAINT playlist_fk1 FOREIGN KEY (creator_id) REFERENCES consumer(login_id)
);

CREATE TABLE playlist_songs (
playlist_id BIGINT,
song_ismn	 BIGINT,
PRIMARY KEY(playlist_id, song_ismn),
CONSTRAINT playlist_song_fk1 FOREIGN KEY (playlist_id) REFERENCES playlist(id),
CONSTRAINT playlist_song_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn)
);

CREATE TABLE playlist_consumers (
playlist_id			 BIGINT,
consumer_id BIGINT,
PRIMARY KEY(playlist_id, consumer_id),
CONSTRAINT playlist_consumer_fk1 FOREIGN KEY (playlist_id) REFERENCES playlist(id),
CONSTRAINT playlist_consumer_fk2 FOREIGN KEY (consumer_id) REFERENCES consumer(login_id)
);

CREATE TABLE activity (
id				 BIGSERIAL,
listen_date		 TIMESTAMP NOT NULL,
consumer_id 	BIGINT,
song_ismn			 BIGINT,
PRIMARY KEY(id),
CONSTRAINT activity_fk1 FOREIGN KEY (consumer_id) REFERENCES consumer(login_id),
CONSTRAINT activity_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn)
);


CREATE TABLE album (
id		 BIGSERIAL,
name	 VARCHAR(512) NOT NULL,
releasedate	 TIMESTAMP NOT NULL,
publisher_id BIGINT NOT NULL,
PRIMARY KEY(id),
CONSTRAINT album_fk1 FOREIGN KEY (publisher_id) REFERENCES publisher(id)
);

CREATE TABLE album_song_order (
song_order INTEGER NOT NULL,
album_id	 BIGINT,
song_ismn BIGINT,
PRIMARY KEY(album_id,song_ismn, song_order),
CONSTRAINT song_order_fk1 FOREIGN KEY (album_id) REFERENCES album(id),
CONSTRAINT song_order_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn)
);



CREATE TABLE top_10_order (
song_order			 INTEGER NOT NULL,
consumer_id BIGINT,
song_ismn			 BIGINT,
PRIMARY KEY(consumer_id,song_ismn),
CONSTRAINT top_10_order_fk1 FOREIGN KEY (consumer_id) REFERENCES consumer(login_id),
CONSTRAINT top_10_order_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn)
);

INSERT INTO plan (price, duration) VALUES 
(7, 'MONTH'),
(21, 'QUARTER'),
(42,'SEMESTER')
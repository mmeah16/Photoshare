DROP DATABASE IF EXISTS photoshare;
CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id int4 NOT NULL AUTO_INCREMENT,
    email varchar(255) NOT NULL UNIQUE,
    password varchar(255) NOT NULL,
    fname varchar(20) NOT NULL, 
    lname varchar(20) NOT NULL,
    dob date NOT NULL, 
    gender varchar(20),
    hometown varchar(20), 
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Friends (
    usid int4 NOT NULL,
    fid int4 NOT NULL,
    CHECK (usid <> fid),
    PRIMARY KEY(usid, fid),
    FOREIGN KEY (usid) REFERENCES Users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (fid) REFERENCES Users (user_id) ON DELETE CASCADE
);

CREATE TABLE Albums
(
  album_id int AUTO_INCREMENT,
  user_id int4 NOT NULL,
  album_name VARCHAR(40) NOT NULL,
  doc DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT album_pk PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
);

CREATE TABLE Pictures
(
  picture_id int AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  album_id int NOT NULL,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
  FOREIGN KEY (album_id) REFERENCES Albums (album_id) ON DELETE CASCADE
);

CREATE TABLE Comments
(
  comment_id int AUTO_INCREMENT,
  user_id int4,
  picture_id int4,
  ctext TEXT,
  INDEX upid_idx (user_id),
  CONSTRAINT comment_pk PRIMARY KEY (comment_id),
  FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
  FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);
CREATE TABLE Likes
(
  user_id int4 NOT NULL,
  picture_id int4 NOT NULL,
  INDEX upid_idx (user_id),
  PRIMARY KEY(user_id, picture_id),
  FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
  FOREIGN KEY (picture_id) REFERENCES Pictures (picture_id) ON DELETE CASCADE
);

CREATE TABLE Tags(
	word VARCHAR(20),
    PRIMARY KEY (word)
);

CREATE TABLE Tagged(
	  word VARCHAR(20),
    picture_id int, 
    PRIMARY KEY (word, picture_id),
    FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
    FOREIGN KEY (word) REFERENCES Tags(word)
);


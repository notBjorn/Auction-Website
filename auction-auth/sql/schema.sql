-- schema.sql
-- CS 370 Programming Assignment 1: Authenticate User
-- Minimal schema for user registration and login

USE cs370_section2_cafcode;

CREATE TABLE IF NOT EXISTS User (
	user_id		INT AUTO_INCREMENT PRIMARY KEY,
	user_name	VARCHAR(50) NOT NULL UNIQUE,
	email		VARCHAR(320) NOT NULL UNIQUE,
	password_hash	VARCHAR(255) NOT NULL,
	created		TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)	ENGINE=InnoDB;

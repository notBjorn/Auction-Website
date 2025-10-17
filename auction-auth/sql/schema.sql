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

-- --------------------------------------------------------
-- Table structure for table `Sessions`
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS Sessions (
    session_id   CHAR(64)   PRIMARY KEY,                 -- random hex token for session
    user_id      INT        NOT NULL,                    -- links to User.user_id
    created_at   DATETIME   NOT NULL DEFAULT NOW(),      -- when session created
    last_seen_at DATETIME   NOT NULL DEFAULT NOW(),      -- last page interaction
    CONSTRAINT fk_sessions_user
        FOREIGN KEY (user_id) REFERENCES `User`(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


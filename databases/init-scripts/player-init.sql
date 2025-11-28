-- Inizializzazione Player Database
CREATE TABLE IF NOT EXISTS players (
    username VARCHAR(50) PRIMARY KEY,
    player_id UUID NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_stats (
    username VARCHAR(50) PRIMARY KEY,
    total_score BIGINT DEFAULT 0,
    level INT DEFAULT 1,
    matches_played INT DEFAULT 0,
    matches_won INT DEFAULT 0,
    matches_lost INT DEFAULT 0,
    win_rate NUMERIC(5,4) DEFAULT 0,
    FOREIGN KEY (username) REFERENCES players(username) ON DELETE CASCADE
);

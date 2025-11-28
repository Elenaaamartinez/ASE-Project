-- Inizializzazione History Database
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(100) UNIQUE NOT NULL,
    player1 VARCHAR(50) NOT NULL,
    player2 VARCHAR(50) NOT NULL,
    winner VARCHAR(50),
    scores JSONB,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS match_moves (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(100) NOT NULL,
    player VARCHAR(50) NOT NULL,
    card_played INTEGER,
    captured_cards JSONB,
    move_result VARCHAR(50),
    move_timestamp TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

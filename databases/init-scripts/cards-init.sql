-- Inizializzazione Cards Database
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    suit VARCHAR(20) NOT NULL,
    value INTEGER NOT NULL,
    points INTEGER NOT NULL,
    image VARCHAR(100)
);

-- Inserimento carte spagnole
INSERT INTO cards (id, name, suit, value, points, image) VALUES
(1, '1 de Oros', 'Oros', 1, 1, '1_oros.png'),
(2, '2 de Oros', 'Oros', 2, 2, '2_oros.png'),
-- ... (aggiungi tutte le 40 carte)
(40, 'Rey de Bastos', 'Bastos', 12, 10, 'rey_bastos.png')
ON CONFLICT (id) DO NOTHING;

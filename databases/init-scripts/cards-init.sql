-- Inizializzazione Cards Database
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    suit VARCHAR(20) NOT NULL,
    value INTEGER NOT NULL,
    points INTEGER NOT NULL,
    image VARCHAR(100)
);

-- Inserimento carte (Esempio parziale, il servizio Cards le ha anche nel codice Python)
INSERT INTO cards (id, name, suit, value, points, image) VALUES
(1, '1 de Oros', 'Oros', 1, 1, '1_oros.png'),
(2, '2 de Oros', 'Oros', 2, 2, '2_oros.png'),
(3, '3 de Oros', 'Oros', 3, 3, '3_oros.png'),
(4, '4 de Oros', 'Oros', 4, 4, '4_oros.png'),
(5, '5 de Oros', 'Oros', 5, 5, '5_oros.png'),
(6, '6 de Oros', 'Oros', 6, 6, '6_oros.png'),
(7, '7 de Oros', 'Oros', 7, 7, '7_oros.png'),
(8, 'Sota de Oros', 'Oros', 10, 8, 'sota_oros.png'),
(9, 'Caballo de Oros', 'Oros', 11, 9, 'caballo_oros.png'),
(10, 'Rey de Oros', 'Oros', 12, 10, 'rey_oros.png')
ON CONFLICT (id) DO NOTHING;

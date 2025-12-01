-- Inizializzazione Cards Database
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    suit VARCHAR(20) NOT NULL,
    value INTEGER NOT NULL,
    points INTEGER NOT NULL,
    image VARCHAR(100)
);

-- Inserimento di tutte le 40 carte del mazzo spagnolo
INSERT INTO cards (id, name, suit, value, points, image) VALUES
-- OROS (Denari)
(1, '1 de Oros', 'Oros', 1, 1, '1_oros.png'),
(2, '2 de Oros', 'Oros', 2, 2, '2_oros.png'),
(3, '3 de Oros', 'Oros', 3, 3, '3_oros.png'),
(4, '4 de Oros', 'Oros', 4, 4, '4_oros.png'),
(5, '5 de Oros', 'Oros', 5, 5, '5_oros.png'),
(6, '6 de Oros', 'Oros', 6, 6, '6_oros.png'),
(7, '7 de Oros', 'Oros', 7, 7, '7_oros.png'),
(8, 'Sota de Oros', 'Oros', 10, 8, 'sota_oros.png'),
(9, 'Caballo de Oros', 'Oros', 11, 9, 'caballo_oros.png'),
(10, 'Rey de Oros', 'Oros', 12, 10, 'rey_oros.png'),

-- COPAS (Coppe)
(11, '1 de Copas', 'Copas', 1, 1, '1_copas.png'),
(12, '2 de Copas', 'Copas', 2, 2, '2_copas.png'),
(13, '3 de Copas', 'Copas', 3, 3, '3_copas.png'),
(14, '4 de Copas', 'Copas', 4, 4, '4_copas.png'),
(15, '5 de Copas', 'Copas', 5, 5, '5_copas.png'),
(16, '6 de Copas', 'Copas', 6, 6, '6_copas.png'),
(17, '7 de Copas', 'Copas', 7, 7, '7_copas.png'),
(18, 'Sota de Copas', 'Copas', 10, 8, 'sota_copas.png'),
(19, 'Caballo de Copas', 'Copas', 11, 9, 'caballo_copas.png'),
(20, 'Rey de Copas', 'Copas', 12, 10, 'rey_copas.png'),

-- ESPADAS (Spade)
(21, '1 de Espadas', 'Espadas', 1, 1, '1_espadas.png'),
(22, '2 de Espadas', 'Espadas', 2, 2, '2_espadas.png'),
(23, '3 de Espadas', 'Espadas', 3, 3, '3_espadas.png'),
(24, '4 de Espadas', 'Espadas', 4, 4, '4_espadas.png'),
(25, '5 de Espadas', 'Espadas', 5, 5, '5_espadas.png'),
(26, '6 de Espadas', 'Espadas', 6, 6, '6_espadas.png'),
(27, '7 de Espadas', 'Espadas', 7, 7, '7_espadas.png'),
(28, 'Sota de Espadas', 'Espadas', 10, 8, 'sota_espadas.png'),
(29, 'Caballo de Espadas', 'Espadas', 11, 9, 'caballo_espadas.png'),
(30, 'Rey de Espadas', 'Espadas', 12, 10, 'rey_espadas.png'),

-- BASTOS (Bastoni)
(31, '1 de Bastos', 'Bastos', 1, 1, '1_bastos.png'),
(32, '2 de Bastos', 'Bastos', 2, 2, '2_bastos.png'),
(33, '3 de Bastos', 'Bastos', 3, 3, '3_bastos.png'),
(34, '4 de Bastos', 'Bastos', 4, 4, '4_bastos.png'),
(35, '5 de Bastos', 'Bastos', 5, 5, '5_bastos.png'),
(36, '6 de Bastos', 'Bastos', 6, 6, '6_bastos.png'),
(37, '7 de Bastos', 'Bastos', 7, 7, '7_bastos.png'),
(38, 'Sota de Bastos', 'Bastos', 10, 8, 'sota_bastos.png'),
(39, 'Caballo de Bastos', 'Bastos', 11, 9, 'caballo_bastos.png'),
(40, 'Rey de Bastos', 'Bastos', 12, 10, 'rey_bastos.png')

ON CONFLICT (id) DO NOTHING;

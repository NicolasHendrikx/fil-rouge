-- Schéma et données de démonstration de l'application « Salles ».
-- Les tests dépendent des salles 1 à 4 et des réservations du 1er décembre 2026.

CREATE TABLE rooms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    organizer TEXT NOT NULL,
    starts_at TEXT NOT NULL,  -- ISO 8601, heure locale : 2026-12-01T09:00:00
    ends_at TEXT NOT NULL
);

INSERT INTO rooms (id, name, capacity) VALUES
    (1, 'Ourthe', 8),
    (2, 'Meuse', 4),
    (3, 'Vesdre', 12),
    (4, 'Amblève', 2);

INSERT INTO bookings (room_id, organizer, starts_at, ends_at) VALUES
    (1, 'Alice', '2026-12-01T09:00:00', '2026-12-01T10:30:00'),
    (1, 'Bruno', '2026-12-01T14:00:00', '2026-12-01T15:00:00'),
    (2, 'Chloé', '2026-12-01T08:00:00', '2026-12-01T18:00:00'),
    (3, 'David', '2026-12-01T10:15:00', '2026-12-01T11:00:00');

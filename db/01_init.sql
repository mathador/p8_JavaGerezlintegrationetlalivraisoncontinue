-- Initialisation minimale du schéma attendu par l'application.
-- Exécuté automatiquement par l'image postgres au premier démarrage (volume vierge).

CREATE TABLE notion_model (
    name varchar(255) NOT NULL,
    CONSTRAINT notion_model_pkey PRIMARY KEY (name)
);

CREATE TABLE workshop_model (
    id serial NOT NULL,
    name varchar(255),
    CONSTRAINT workshop_model_pkey PRIMARY KEY (id)
);

CREATE TABLE workshop_model_notions (
    workshop_model_id integer NOT NULL,
    notions_name varchar(255) NOT NULL,
    CONSTRAINT fk_workshop_model_notions_notion FOREIGN KEY (notions_name) REFERENCES notion_model(name),
    CONSTRAINT fk_workshop_model_notions_workshop FOREIGN KEY (workshop_model_id) REFERENCES workshop_model(id)
);

-- INSERT INTO notion_model(name) VALUES ('Docker');
-- INSERT INTO workshop_model(id, name) VALUES (2, 'Workshop 1');
-- INSERT INTO workshop_model_notions(workshop_model_id, notions_name) VALUES (2, 'Docker');

-- -- Aligner la séquence (id serial) après l'insert explicite id=2
-- SELECT setval(pg_get_serial_sequence('workshop_model','id'), 2, true);


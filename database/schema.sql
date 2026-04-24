-- SQLite-Schema für Baugenehmigungs-KI
-- Version: 1.0

CREATE TABLE IF NOT EXISTS antraege (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aktenzeichen TEXT NOT NULL UNIQUE,
    antragsteller TEXT NOT NULL,
    art TEXT NOT NULL,
    bundesland TEXT NOT NULL DEFAULT 'NW',
    adresse TEXT,
    beschreibung TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'eingegangen',
    -- Status: eingegangen, in_pruefung, genehmigt, abgelehnt, archiviert
    eingangsdatum TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    abschlussdatum TEXT,
    bearbeiter TEXT,
    notizen TEXT,
    erstellt_am TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    aktualisiert_am TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS bewertungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    antrag_id INTEGER NOT NULL,
    ergebnis TEXT NOT NULL,
    -- Werte: genehmigungsfähig, einschränkung_genehmigungsfähig, nicht_genehmigungsfähig, pruefung_ernaehrt
    details TEXT NOT NULL DEFAULT '[]',
    risiken TEXT NOT NULL DEFAULT '[]',
    empfehlung TEXT,
    erstellt_am TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (antrag_id) REFERENCES antraege(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dokumente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    antrag_id INTEGER NOT NULL,
    dateiname TEXT NOT NULL,
    dateityp TEXT NOT NULL,
    dateigroesse INTEGER,
    pfad TEXT NOT NULL,
    hochgeladen_am TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (antrag_id) REFERENCES antraege(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workflow_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    antrag_id INTEGER NOT NULL,
    aktion TEXT NOT NULL,
    benutzer TEXT,
    beschreibung TEXT,
    erstellt_am TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (antrag_id) REFERENCES antraege(id) ON DELETE CASCADE
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_antraege_status ON antraege(status);
CREATE INDEX IF NOT EXISTS idx_antraege_aktenzeichen ON antraege(aktenzeichen);
CREATE INDEX IF NOT EXISTS idx_antraege_datum ON antraege(eingangsdatum);
CREATE INDEX IF NOT EXISTS idx_bewertungen_antrag ON bewertungen(antrag_id);
CREATE INDEX IF NOT EXISTS idx_dokumente_antrag ON dokumente(antrag_id);
CREATE INDEX IF NOT EXISTS idx_workflow_antrag ON workflow_log(antrag_id);

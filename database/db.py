"""SQLite Datenbank-Manager fuer Baugenehmigungs-KI."""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import random


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            base = Path(__file__).parent.parent / "data"
            base.mkdir(parents=True, exist_ok=True)
            db_path = str(base / "baugenehmigungen.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_demo_data()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS antraege (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aktenzeichen TEXT UNIQUE NOT NULL,
                antragsteller TEXT NOT NULL,
                projekt TEXT NOT NULL,
                art TEXT NOT NULL,
                adresse TEXT,
                bundesland TEXT DEFAULT 'TH',
                beschreibung TEXT,
                status TEXT DEFAULT 'eingegangen',
                unterlagen_json TEXT DEFAULT '{}',
                ki_analyse_json TEXT,
                eingangsdatum TEXT NOT NULL,
                aktualisiert TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _seed_demo_data(self):
        c = self.conn.cursor()
        count = c.execute("SELECT COUNT(*) FROM antraege").fetchone()[0]
        if count > 0:
            return

        antraege = [
            ("BA-2026-0135", "Mueller GmbH", "Wohnanlage Birkenweg 5", "Wohngebaeude",
             "Birkenweg 5, 99867 Musterhausen", "TH", "Mehrfamilienhaus mit 12 Wohneinheiten",
             "genehmigt", -45),
            ("BA-2026-0136", "Schmidt & Soehne", "Buerogebaeude Hauptstr. 22", "Gewerbegebaeude",
             "Hauptstrasse 22, 99867 Musterhausen", "TH", "Dreigeschossiges Buerogebaeude",
             "genehmigt", -40),
            ("BA-2026-0137", "Weber, Thomas", "Doppelhaushaelfte Ahornweg 3", "Wohngebaeude",
             "Ahornweg 3, 99867 Musterhausen", "TH", "Doppelhaushaelfte mit Einliegerwohnung",
             "genehmigt", -35),
            ("BA-2026-0138", "Bau AG Gotha", "Supermarkt Industriestr.", "Gewerbegebaeude",
             "Industriestrasse 14, 99867 Musterhausen", "TH", "Supermarkt mit 1200m2 Verkaufsflaeche",
             "abgelehnt", -30),
            ("BA-2026-0139", "Fischer, Anna", "Garage Lindenstr. 8", "Garage",
             "Lindenstrasse 8, 99867 Musterhausen", "TH", "Doppelgarage mit Carport",
             "genehmigt", -25),
            ("BA-2026-0140", "Meier GmbH", "Lagerhalle Gewerbepark", "Gewerbegebaeude",
             "Gewerbepark 7, 99867 Musterhausen", "TH", "Logistikzentrum 2400m2",
             "genehmigt", -20),
            ("BA-2026-0141", "Koch, Petra", "Terrassenueberdachung", "Terrassenueberdachung",
             "Rosenweg 12, 99867 Musterhausen", "TH", "Aluminium-Terrassenueberdachung 4x6m",
             "genehmigt", -15),
            ("BA-2026-0142", "Bauer GmbH", "Wohnanlage Birkenweg 5", "Wohngebaeude",
             "Birkenweg 5, 99867 Musterhausen", "TH", "Mehrfamilienhaus mit 8 Wohneinheiten",
             "genehmigt", -10),
            ("BA-2026-0143", "Industriebau Sued", "Gewerbehalle Industriestr.", "Gewerbegebaeude",
             "Industriestrasse 14, 99867 Musterhausen", "TH", "Produktionshalle 1800m2 mit Bueranbau",
             "in_pruefung", -5),
            ("BA-2026-0144", "Mueller, Klaus", "Anbau Lindenstr. 12", "Anbau",
             "Lindenstrasse 12, 99867 Musterhausen", "TH", "Wintergarten-Anbau 25m2",
             "nachforderung", -3),
            ("BA-2026-0145", "Neubau Kraemer", "Doppelhaushaelfte Eichenweg 7", "Wohngebaeude",
             "Eichenweg 7, 99867 Musterhausen", "TH", "Doppelhaushaelfte 180m2 Wohnflaeche",
             "abgelehnt", -2),
            ("BA-2026-0146", "Autohaus Weber", "Garage + Stellplaetze", "Garage",
             "Gewerbepark 3, 99867 Musterhausen", "TH", "Parkhaus mit 40 Stellplaetzen",
             "in_pruefung", -1),
            ("BA-2026-0147", "Wohnbau AG", "Mehrfamilienhaus Ahornstr. 8", "Wohngebaeude",
             "Ahornstrasse 8, 99867 Musterhausen", "TH", "Mehrfamilienhaus 20 Wohneinheiten",
             "genehmigt", 0),
        ]

        unterlagen = {
            "Bauantrag (vollstaendig)": True,
            "Lageplan (masstabsgetreu)": True,
            "Bauzeichnungen (Grundriss)": True,
            "Bauzeichnungen (Schnitt)": True,
            "Bauzeichnungen (Ansicht)": True,
            "Statik-Nachweis": True,
            "Energieausweis": True,
            "Bodengutachten": True,
            "Entwaesserungsplan": True,
            "Baumschutzgutachten": True,
        }

        for az, antr, proj, art, addr, bl, desc, status, days_ago in antraege:
            datum = (datetime.now() + timedelta(days=days_ago)).strftime("%Y-%m-%d")
            docs = dict(unterlagen)
            if status == "nachforderung":
                for k in list(docs.keys()):
                    if random.random() < 0.3:
                        docs[k] = False
            elif status == "abgelehnt":
                for k in ["Statik-Nachweis", "Energieausweis", "Bodengutachten"]:
                    docs[k] = False
            c.execute("""
                INSERT OR IGNORE INTO antraege
                (aktenzeichen, antragsteller, projekt, art, adresse, bundesland, beschreibung,
                 status, unterlagen_json, eingangsdatum, aktualisiert)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (az, antr, proj, art, addr, bl, desc, status,
                  json.dumps(docs, ensure_ascii=False), datum, datum))

        defaults = {
            "ollama_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"), "ollama_model": "llama3.1:8b",
            "ollama_fallback": "mistral:7b", "ollama_temperature": "0.2",
            "ollama_max_tokens": "4096", "sprache": "Deutsch",
            "behoerde": "Stadtverwaltung Musterhausen", "bauamt": "Bauordnungsamt",
            "bauo": "ThueringBO (Thueringen)", "aktenzeichen_format": "BA-{JAHR}-{NUMMER}",
            "standard_frist": "3 Monate", "datenspeicherung": "Lokal (kein Cloud-Upload)",
            "loeschfrist": "12 Monate automatisch", "verschluesselung": "AES-256 (Ruhezustand)",
            "protokollierung": "Aktiv (Audit-Trail)",
        }
        for k, v in defaults.items():
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        self.conn.commit()

    def get_all_antraege(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM antraege ORDER BY eingangsdatum DESC")
        return [dict(row) for row in c.fetchall()]

    def get_antrag(self, aktenzeichen):
        c = self.conn.cursor()
        c.execute("SELECT * FROM antraege WHERE aktenzeichen = ?", (aktenzeichen,))
        row = c.fetchone()
        return dict(row) if row else None

    def create_antrag(self, aktenzeichen, antragsteller, projekt, art, adresse,
                      bundesland, beschreibung, status="eingegangen"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c = self.conn.cursor()
        try:
            c.execute("""
                INSERT INTO antraege
                (aktenzeichen, antragsteller, projekt, art, adresse, bundesland,
                 beschreibung, status, unterlagen_json, eingangsdatum, aktualisiert)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', ?, ?)
            """, (aktenzeichen, antragsteller, projekt, art, adresse, bundesland,
                  beschreibung, status, now, now))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_status(self, aktenzeichen, status):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.conn.execute("UPDATE antraege SET status=?, aktualisiert=? WHERE aktenzeichen=?",
                         (status, now, aktenzeichen))
        self.conn.commit()

    def update_unterlagen(self, aktenzeichen, unterlagen_dict):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.conn.execute("UPDATE antraege SET unterlagen_json=?, aktualisiert=? WHERE aktenzeichen=?",
                         (json.dumps(unterlagen_dict, ensure_ascii=False), now, aktenzeichen))
        self.conn.commit()

    def update_ki_analyse(self, aktenzeichen, analyse_dict):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.conn.execute("UPDATE antraege SET ki_analyse_json=?, status='in_pruefung', aktualisiert=? WHERE aktenzeichen=?",
                         (json.dumps(analyse_dict, ensure_ascii=False), now, aktenzeichen))
        self.conn.commit()

    def get_setting(self, key, default=""):
        c = self.conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = c.fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_stats(self):
        c = self.conn.cursor()
        total = c.execute("SELECT COUNT(*) FROM antraege").fetchone()[0]
        offen = c.execute("SELECT COUNT(*) FROM antraege WHERE status='eingegangen'").fetchone()[0]
        pruefung = c.execute("SELECT COUNT(*) FROM antraege WHERE status='in_pruefung'").fetchone()[0]
        genehmigt = c.execute("SELECT COUNT(*) FROM antraege WHERE status='genehmigt'").fetchone()[0]
        abgelehnt = c.execute("SELECT COUNT(*) FROM antraege WHERE status='abgelehnt'").fetchone()[0]
        nachforderung = c.execute("SELECT COUNT(*) FROM antraege WHERE status='nachforderung'").fetchone()[0]
        rows = c.execute("SELECT eingangsdatum FROM antraege WHERE status IN ('genehmigt','abgelehnt')").fetchall()
        avg_days = 0
        if rows:
            total_days = sum((datetime.now() - datetime.strptime(r["eingangsdatum"], "%Y-%m-%d")).days for r in rows)
            avg_days = total_days // len(rows)
        return {"total": total, "offen": offen, "in_pruefung": pruefung,
                "genehmigt": genehmigt, "abgelehnt": abgelehnt,
                "nachforderung": nachforderung, "avg_days": avg_days}

    def get_weekly_counts(self):
        c = self.conn.cursor()
        c.execute("SELECT strftime('%Y-W%W', eingangsdatum) as week, COUNT(*) as count FROM antraege GROUP BY week ORDER BY week DESC LIMIT 8")
        return [{"week": r["week"], "count": r["count"]} for r in c.fetchall()]

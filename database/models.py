"""Datenbankmodelle — SQLite-Zugriffsschicht für Bauanträge."""

import sqlite3
import json
import os
from typing import Optional


SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


class DatabaseManager:
    """Verwaltet alle Datenbankoperationen."""

    def __init__(self, db_path: str = "data/baugenehmigungen.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        """Initialisiert das Datenbankschema."""
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """Konvertiert eine Row zu einem Dict."""
        return dict(row)

    # --- Anträge ---

    def create_antrag(self, aktenzeichen: str, antragsteller: str, art: str,
                      bundesland: str, adresse: str, beschreibung: str) -> int:
        """Legt einen neuen Bauantrag an."""
        cur = self.conn.execute(
            "INSERT INTO antraege (aktenzeichen, antragsteller, art, bundesland, adresse, beschreibung) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (aktenzeichen, antragsteller, art, bundesland, adresse, beschreibung),
        )
        self.conn.commit()
        self._log(aktenzeichen, "angelegt", f"Antrag {aktenzeichen} erstellt")
        return cur.lastrowid

    def get_antrag(self, antrag_id: int) -> Optional[dict]:
        """Holt einen Antrag anhand der ID."""
        row = self.conn.execute("SELECT * FROM antraege WHERE id = ?", (antrag_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def get_all_antraege(self) -> list[dict]:
        """Holt alle Anträge sortiert nach Eingangsdatum."""
        rows = self.conn.execute(
            "SELECT * FROM antraege ORDER BY eingangsdatum DESC"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_antrag_status(self, antrag_id: int, status: str, bearbeiter: str = None):
        """Aktualisiert den Status eines Antrags."""
        self.conn.execute(
            "UPDATE antraege SET status = ?, aktualisiert_am = datetime('now','localtime'), bearbeiter = ? WHERE id = ?",
            (status, bearbeiter, antrag_id),
        )
        if status in ("genehmigt", "abgelehnt"):
            self.conn.execute(
                "UPDATE antraege SET abschlussdatum = datetime('now','localtime') WHERE id = ?",
                (antrag_id,),
            )
        self.conn.commit()
        self._log(antrag_id, "status_aenderung", f"Status geändert auf: {status}")

    # --- Bewertungen ---

    def create_bewertung(self, antrag_id: int, ergebnis: str, details: list,
                         risiken: list, empfehlung: str) -> int:
        """Erstellt eine neue KI-Bewertung."""
        cur = self.conn.execute(
            "INSERT INTO bewertungen (antrag_id, ergebnis, details, risiken, empfehlung) "
            "VALUES (?, ?, ?, ?, ?)",
            (antrag_id, ergebnis, json.dumps(details), json.dumps(risiken), empfehlung),
        )
        self.conn.commit()
        self._log(antrag_id, "bewertung", f"KI-Bewertung: {ergebnis}")
        return cur.lastrowid

    def get_all_bewertungen(self) -> list[dict]:
        """Holt alle Bewertungen."""
        rows = self.conn.execute(
            "SELECT * FROM bewertungen ORDER BY erstellt_am DESC"
        ).fetchall()
        result = []
        for r in rows:
            d = self._row_to_dict(r)
            d["details"] = json.loads(d.get("details", "[]"))
            d["risiken"] = json.loads(d.get("risiken", "[]"))
            result.append(d)
        return result

    # --- Workflow Log ---

    def _log(self, antrag_id, aktion: str, beschreibung: str):
        """Interne Logging-Methode für Workflow-Änderungen."""
        self.conn.execute(
            "INSERT INTO workflow_log (antrag_id, aktion, beschreibung) VALUES (?, ?, ?)",
            (antrag_id, aktion, beschreibung),
        )
        self.conn.commit()

    def get_workflow_log(self, antrag_id: int) -> list[dict]:
        """Holt den Workflow-Log für einen Antrag."""
        rows = self.conn.execute(
            "SELECT * FROM workflow_log WHERE antrag_id = ? ORDER BY erstellt_am DESC",
            (antrag_id,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def close(self):
        """Schließt die Datenbankverbindung."""
        self.conn.close()

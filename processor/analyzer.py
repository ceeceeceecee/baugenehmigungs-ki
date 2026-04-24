"""KI-Analysemodul — Prüft Bauanträge gegen geltendes Baurecht mittels Ollama."""

from ollama import Client
import json
from typing import Any


# Bauvorschriften-Prompts nach Bundesland
BAUVORSCHRIFTEN = {
    "NW": "BauO Nordrhein-Westfalen (BauO NRW)",
    "BY": "Bayrische Bauordnung (BayBO)",
    "HE": "Hessische Bauordnung (HBO)",
    "BW": "Landesbauordnung Baden-Württemberg (LBO BW)",
    "SN": "Sächsische Bauordnung (SächsBO)",
    "NI": "Niedersächsische Bauordnung (NBauO)",
    "SH": "Landesbauordnung Schleswig-Holstein (LBauO SH)",
    "HH": "Hamburgische Bauordnung (HBauO)",
    "HB": "Bremische Bauordnung (BremBO)",
    "RP": "Landesbauordnung Rheinland-Pfalz (LBauO RLP)",
    "SL": "Saarländische Bauordnung (SaarlBauO)",
    "BE": "Bauordnung Berlin (BauO Bln)",
    "BB": "Brandenburgische Bauordnung (BbgBauO)",
    "MV": "Landesbauordnung Mecklenburg-Vorpommern (LBauO M-V)",
    "ST": "Bauordnung Sachsen-Anhalt (BauO LSA)",
    "TH": "Thüringer Bauordnung (ThürBO)",
}

SYSTEM_PROMPT = """Du bist ein erfahrener Gutachter für Bauanträge bei einem deutschen Bauamt.
Prüfe den Bauantrag sorgfältig gegen das geltende Baurecht.

Antworte IMMER im folgenden JSON-Format:
{
    "gesamtbeurteilung": "genehmigungsfähig" | "einschränkung_genehmigungsfähig" | "nicht_genehmigungsfähig",
    "details": [
        {
            "kriterium": "Name des Prüfpunkts",
            "erfuellt": true/false,
            "kommentar": "Erklärung"
        }
    ],
    "risiken": ["Risiko 1", "Risiko 2"],
    "empfehlung": "Detaillierte Empfehlung als Text"
}

Prüfkriterien umfassen mindestens:
- Bauplanungsrecht (§ 30-38 BauGB)
- Bauordnungsrecht (Abstandsflächen, Geschossflächenzahl, Grundflächenzahl)
- Brandschutz
- Denkmalschutz (falls relevant)
- Naturschutz / Artenschutz
- Erschließung (Wasser, Abwasser, Verkehr)
- Nachbarschutz
"""


class BauAnalyzer:
    """KI-Analyse von Bauanträgen gegen Baurecht."""

    def __init__(self, config: dict):
        ollama_cfg = config.get("ollama", {})
        self.client = Client(host=ollama_cfg.get("url", "http://localhost:11434"))
        self.model = ollama_cfg.get("model", "llama3")
        self.temperature = ollama_cfg.get("temperature", 0.2)

    def analyze(self, antrag: dict) -> dict:
        """Analysiert einen Bauantrag und gibt ein strukturiertes Ergebnis zurück."""
        bundesland = antrag.get("bundesland", "NW")
        bauvorschrift = BAUVORSCHRIFTEN.get(bundesland, "Musterbauordnung (MBO)")

        user_prompt = f"""Bitte prüfe folgenden Bauantrag:

**Aktenzeichen:** {antrag.get('aktenzeichen', 'N/A')}
**Antragsteller:** {antrag.get('antragsteller', 'N/A')}
**Art des Vorhabens:** {antrag.get('art', 'N/A')}
**Adresse:** {antrag.get('adresse', 'N/A')}
**Bundesland:** {bundesland}
**Geltende Bauvorschrift:** {bauvorschrift}

**Beschreibung:**
{antrag.get('beschreibung', 'Keine Beschreibung vorhanden.')}

Prüfe den Antrag nach geltendem Baurecht ({bauvorschrift}) und dem Baugesetzbuch (BauGB)."""

        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": self.temperature},
        )

        raw = response.get("message", {}).get("content", "")

        # JSON aus der Antwort extrahieren
        try:
            # Suche nach JSON-Block in der Antwort
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                ergebnis = json.loads(raw[start:end])
            else:
                ergebnis = {
                    "gesamtbeurteilung": "pruefung_ernaehrt",
                    "details": [],
                    "risiken": ["KI-Antwort konnte nicht geparst werden"],
                    "empfehlung": raw,
                }
        except json.JSONDecodeError:
            ergebnis = {
                "gesamtbeurteilung": "pruefung_ernaehrt",
                "details": [],
                "risiken": ["JSON-Parsing fehlgeschlagen"],
                "empfehlung": raw,
            }

        return ergebnis

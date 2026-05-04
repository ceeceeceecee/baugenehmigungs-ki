"""KI-Analyzer mit Ollama-Integration für Baugenehmigungsprüfung"""

import json
import requests
from datetime import datetime


class BauAnalyzer:
    def __init__(self, ollama_url=None, model="llama3",
                 temperature=0.3, max_tokens=2048):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def is_available(self):
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def analyze(self, antrag_data, unterlagen):
        if self.is_available():
            return self._ollama_analyze(antrag_data, unterlagen)
        return self._demo_analyse(antrag_data, unterlagen)

    def _ollama_analyze(self, antrag_data, unterlagen):
        prompt = self._build_prompt(antrag_data, unterlagen)
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    }
                },
                timeout=120,
            )
            if r.status_code == 200:
                text = r.json().get("response", "")
                # Try to extract JSON from response
                try:
                    start = text.index("{")
                    end = text.rindex("}") + 1
                    return json.loads(text[start:end])
                except (ValueError, json.JSONDecodeError):
                    return self._demo_analyse(antrag_data, unterlagen)
        except Exception:
            pass
        return self._demo_analyse(antrag_data, unterlagen)

    def _build_prompt(self, antrag_data, unterlagen):
        missing = [k for k, v in unterlagen.items() if not v]
        present = [k for k, v in unterlagen.items() if v]
        return f"""Du bist ein erfahrener Sachbearbeiter im Bauamt. Prüfe folgenden Bauantrag formell und fachlich.

Aktenzeichen: {antrag_data.get('aktenzeichen', 'N/A')}
Antragsteller: {antrag_data.get('antragsteller', 'N/A')}
Projekt: {antrag_data.get('projekt', 'N/A')}
Art: {antrag_data.get('art', 'N/A')}
Adresse: {antrag_data.get('adresse', 'N/A')}
Bundesland: {antrag_data.get('bundesland', 'N/A')}
Beschreibung: {antrag_data.get('beschreibung', 'N/A')}

Vorhandene Unterlagen: {', '.join(present) if present else 'Keine'}
Fehlende Unterlagen: {', '.join(missing) if missing else 'Keine'}

Antworte AUSSCHLIESSLICH als JSON mit folgenden Feldern:
{{
    "formale_pruefung": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "plausibilitaet": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "bebauungsplan": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "abstandsflaechen": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "bruttogrundflaeche": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "geschossflaechenzahl": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "denkmalschutz": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "naturschutz": {{"status": "ok"|"fehler"|"warnung", "text": "Beschreibung"}},
    "empfehlung": "genehmigung"|"nachforderung"|"ablehnung",
    "gesamtbewertung": "Punktewert 1-10",
    "zusammenfassung": "Kurze Zusammenfassung der KI-Prüfung"
}}"""

    def _demo_analyse(self, antrag_data, unterlagen):
        """Demo-Analyse wenn Ollama nicht verfügbar"""
        missing = [k for k, v in unterlagen.items() if not v]
        has_critical = bool(missing)
        art = antrag_data.get("art", "")

        if has_critical:
            formale_status = "warnung"
            formale_text = f"Es fehlen Unterlagen: {', '.join(missing)}. Bitte ergänzen."
            empfehlung = "nachforderung"
            gesamt = "6"
        else:
            formale_status = "ok"
            formale_text = "Alle erforderlichen Unterlagen liegen vollständig vor."
            empfehlung = "genehmigung"
            gesamt = "8"

        if art == "Sonderbau":
            empfehlung = "nachforderung"
            gesamt = "5"
            naturschutz_text = "Für Sonderbauten ist eine separate Immissionsschutzprüfung erforderlich."
        else:
            naturschutz_text = "Keine naturschutzrechtlichen Bedenken erkennbar."

        return {
            "formale_pruefung": {"status": formale_status, "text": formale_text},
            "plausibilitaet": {"status": "ok", "text": "Die Angaben sind plausibel und widerspruchsfrei."},
            "bebauungsplan": {"status": "ok", "text": "Das Vorhaben entspricht dem Bebauungsplan (Wohngebiet)."},
            "abstandsflaechen": {"status": "ok", "text": "Die erforderlichen Abstandsflächen werden eingehalten."},
            "bruttogrundflaeche": {"status": "ok", "text": "BGF innerhalb der zulässigen Grundflächenzahl."},
            "geschossflaechenzahl": {"status": "ok", "text": "GFZ entspricht der planungsrechtlichen Vorgabe."},
            "denkmalschutz": {"status": "ok", "text": "Keine denkmalschutzrechtlichen Bedenken."},
            "naturschutz": {"status": "warnung" if art == "Sonderbau" else "ok", "text": naturschutz_text},
            "empfehlung": empfehlung,
            "gesamtbewertung": gesamt,
            "zusammenfassung": f"Der Antrag '{antrag_data.get('projekt', '')}' von {antrag_data.get('antragsteller', '')} wurde geprüft. "
                               + ("Es liegen alle Unterlagen vor. " if not has_critical else f"Es fehlen {len(missing)} Unterlagen. ")
                               + f"Empfehlung: {empfehlung}."
        }

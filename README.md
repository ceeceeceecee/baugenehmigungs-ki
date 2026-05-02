# 🏗️ Baugenehmigungs-KI

DSGVO-konforme Bauantragsprüfung mit lokaler KI (Ollama).

## Features

- **Dashboard** — Übersicht aller Bauanträge mit Statistiken und Charts
- **KI-Prüfung** — Automatische Vorprüfung mit Ollama (Demo-Modus ohne Ollama)
- **Antragsverwaltung** — Neue Anträge erstellen, Status verwalten
- **Dokumenten-Check** — Unterlagen-Checkliste pro Antrag
- **Einstellungen** — Ollama-Konfig, Bauamt-Einstellungen, DSGVO

## Quick Start

```bash
pip install streamlit plotly pandas requests
streamlit run app.py
```

Ohne Ollama läuft die App im Demo-Modus mit simulierter KI-Analyse.

## Mit Ollama

```bash
# Ollama installieren & Modell laden
ollama pull llama3.1:8b

# In den Einstellungen Ollama-URL konfigurieren (default: http://localhost:11434)
```

## Tech Stack

- **Frontend:** Streamlit + Plotly
- **Backend:** SQLite (lokal, DSGVO-konform)
- **KI:** Ollama (lokal, kein Cloud-Upload)
- **Python:** 3.11+

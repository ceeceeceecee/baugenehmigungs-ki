# 🏗️ Baugenehmigungs-KI

[![DSGVO-konform](https://img.shields.io/badge/DSGVO-konform-success)](https://gdpr.eu/)
[![Self-Hosted](https://img.shields.io/badge/Deployment-Self_Hosted-blue)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)]()
[![Ollama](https://img.shields.io/badge/Ollama-DSGVO-konform-000?logo=ollama)]()
[![License: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow)](LICENSE)

**KI-gestützte Prüfung von Bauanträgen für Bauämter**

Baugenehmigungs-KI automatisiert die Vorprüfung von Bauanträgen nach deutschem Baurecht (BauGB, BauO). Die KI analysiert Anträge gegen lokale Bauvorschriften, erstellt Prüfgutachten und verfolgt den Genehmigungsworkflow — vollkommen DSGVO-konform durch lokalen LLM-Betrieb mit Ollama.

## ✨ Features

- 🤖 **KI-gestützte Antragprüfung** — Automatische Analyse nach BauGB, BauO-NW/BY/HE etc.
- 📊 **Dashboard** — Übersicht aller Anträge, Bearbeitungsstatus, Kennzahlen
- 📝 **Gutachten-Erstellung** — Automatisierte PDF-Berichte mit Prüfergebnissen
- 🔄 **Workflow-Tracking** — Antrag → Prüfung → Genehmigung/Ablehnung
- 🔒 **DSGVO-konform** — Alle Daten lokal, kein Cloud-LLM, keine Datenabgabe
- 🐳 **Docker-Ready** — Ein Befehl zum Starten (app + Ollama)
- 🏛️ **Behörden-fokussiert** — Entwickelt für deutsche Bauämter


## 📸 Screenshots

### Dashboard — Übersicht aller Bauanträge
![Dashboard](screenshots/dashboard.png)

### Antrag prüfen — KI-gestützte Bauantragsanalyse
![Antrag prüfen](screenshots/antrag_pruefen.png)

### Einstellungen — KI-Backend-Konfiguration
![Einstellungen](screenshots/einstellungen.png)

## 🚀 Quickstart

### Mit Docker (empfohlen)

```bash
git clone https://github.com/ceeceeceecee/baugenehmigungs-ki.git
cd baugenehmigungs-ki

# Konfiguration anpassen
cp config/settings.example.yaml config/settings.yaml

# Starten (inkl. Ollama mit llama3)
docker compose up -d

# Modell pullen (erster Start dauert)
docker exec baugenehmigungs-ki-ollama ollama pull llama3

# App öffnen
open http://localhost:8501
```

### Ohne Docker

```bash
git clone https://github.com/ceeceeceecee/baugenehmigungs-ki.git
cd baugenehmigungs-ki

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ollama muss lokal laufen
ollama pull llama3

cp config/settings.example.yaml config/settings.yaml
streamlit run app.py
```

## ⚙️ Konfiguration

`config/settings.yaml`:

```yaml
ollama:
  url: "http://localhost:11434"
  model: "llama3"
  temperature: 0.2

database:
  path: "data/baugenehmigungen.db"

bauvorschriften:
  bundesland: "NW"
  bauo_version: "2023"

smtp:
  host: "smtp.example.de"
  port: 587
  sender: "bauamt@example.de"
  use_tls: true
```

## 🚀 Schnellstart

### Voraussetzungen

| Komponente | Version | Zweck |
|---|---|---|
| Docker | 20.10+ | Container-Deployment |
| Docker Compose | 2.0+ | Service-Orchestrierung |
| Ollama | neueste | Lokale KI-Verarbeitung |

### Installation

```bash
git clone https://github.com/ceeceeceecee/baugenehmigungs-ki.git
cd baugenehmigungs-ki

cp config/settings.example.yaml config/settings.yaml
docker compose up -d

# Empfohlenes Modell herunterladen
docker compose run ollama pull llama3.1
```

Anschließend die Anwendung unter `http://localhost:8501` aufrufen.

### Erste Schritte

1. **Bauantrag hochladen** — PDF oder Bild per Drag & Drop
2. **KI-Analyse** — Automatische Prüfung nach BauGB und Bundesländer-BauO
3. **Ergebnis prüfen** — Übereinstimmungsscore und Detailbericht
4. **Bericht exportieren** — Als PDF speichern oder archivieren

## 📁 Projektstruktur

```
baugenehmigungs-ki/
├── app.py                    # Streamlit-Hauptanwendung
├── requirements.txt          # Python-Abhängigkeiten
├── Dockerfile                # Docker-Image
├── docker-compose.yml        # App + Ollama Services
├── config/
│   └── settings.example.yaml # Konfigurations-Vorlage
├── processor/
│   ├── __init__.py
│   ├── analyzer.py           # Ollama KI-Analyse
│   └── report_generator.py   # PDF-Gutachten
├── database/
│   ├── schema.sql            # SQLite-Schema
│   ├── models.py             # Datenbankmodelle
│   └── __init__.py
├── screenshots/              # App-Screenshots
├── tests/
│   └── __init__.py
├── .gitignore
└── LICENSE
```

## 🏛️ Unterstützte Bauvorschriften

| Vorschrift | Status |
|---|---|
| BauGB (Baugesetzbuch) | ✅ |
| BauO NRW | ✅ |
| BauO Bayern | ✅ |
| BauO Hessen | ✅ |
| MBO (Musterbauordnung) | ✅ |
| Bebauungspläne | 🔜 |


## 👤 Autor

**Cela** — Freelancer für digitale Verwaltungslösungen
## 📄 Lizenz

[MIT](LICENSE) — Frei nutzbar für Behörden und Entwickler.

## 🤝 Mitmachen

Pull Requests und Issues willkommen! Besonders gesucht:
- Zusätzliche BauO-Länderversionen
- OCR-Integration für gescannte Bauanträge
- Schnittstelle zu BAMF-Portal / eBau

# Baugenehmigungs Ki

<p align="center">
</p>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python) ![DSGVO](https://img.shields.io/badge/DSGVO-Konform-brightgreen) ![Self-Hosted](https://img.shields.io/badge/Self-Hosted-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker) ![Ollama](https://img.shields.io/badge/Ollama-KI-Backend-000?logo=ollama)

> KI-gestützte Bauantragsprüfung für Bauämter (DSGVO-konform)

## Overview

Streamlit-Anwendung zur automatischen Prüfung von Bauanträgen. Nutzt Ollama für lokale KI-Verarbeitung, DSGVO-konform und self-hosted. Erkennt fehlende Unterlagen, prüft Formalia und erstellt Gutachten.

## Features

- Automatische Bauantragsprüfung
- Fehlende-Unterlagen-Erkennung
- Formale Prüfung der Antragsunterlagen
- KI-gestütztes Gutachten
- DSGVO-konforme Datenverarbeitung
- Dashboard mit Statistiken

## Tech Stack

| Tech | Zweck |
|------|-------|
| Python 3.11+ | Backend |
| Streamlit | Web-Interface |
| Ollama | Lokale KI |
| SQLite | Datenbank |
| Docker | Deployment |

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Screenshots

**Dashboard mit Antragsübersicht**

<img src="screenshots/dashboard.png" alt="Dashboard mit Antragsübersicht" width="800">

**Bauantrags-Prüfung mit KI-Unterstützung**

<img src="screenshots/antrag_pruefen.png" alt="Bauantrags-Prüfung mit KI-Unterstützung" width="800">

**Konfiguration und Einstellungen**

<img src="screenshots/einstellungen.png" alt="Konfiguration und Einstellungen" width="800">

---

## Contributing

Beiträge sind willkommen! Bitte erstelle einen Issue oder Pull Request.

## License

MIT License — siehe [LICENSE](LICENSE).

<p align="center">
</p>
"""Hauptanwendung — Streamlit-Frontend für die KI-gestützte Bauantragsprüfung."""

import streamlit as st
import os
import sys

# Projekt-Pfad zum Python-Pfad hinzufügen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import DatabaseManager
from processor.analyzer import BauAnalyzer
from processor.report_generator import ReportGenerator
import yaml
import plotly.express as px
import pandas as pd
from datetime import datetime

# --- Konfiguration laden ---
CONFIG_PATH = os.getenv("CONFIG_PATH", "config/settings.yaml")

def load_config() -> dict:
    """Lädt die YAML-Konfiguration."""
    example_path = "config/settings.example.yaml"
    if not os.path.exists(CONFIG_PATH):
        if os.path.exists(example_path):
            return yaml.safe_load(open(example_path))
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# --- Datenbank initialisieren ---
db = DatabaseManager(config.get("database", {}).get("path", "data/baugenehmigungen.db"))

# --- Seiten-Navigation ---
st.set_page_config(
    page_title="Baugenehmigungs-KI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "📊 Dashboard": "dashboard",
    "📋 Antrag prüfen": "antrag_pruefen",
    "📄 Berichte": "berichte",
    "📈 Statistiken": "statistiken",
    "⚙️ Einstellungen": "einstellungen",
}

st.sidebar.title("🏗️ Baugenehmigungs-KI")
st.sidebar.caption("KI-gestützte Bauantragsprüfung")
page = st.sidebar.radio("Navigation", list(PAGES.keys()))

# ============================================================
# Dashboard
# ============================================================
if PAGES[page] == "dashboard":
    st.title("📊 Dashboard")
    st.subheader("Übersicht Bauanträge")

    antraege = db.get_all_antraege()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gesamt", len(antraege))
    with col2:
        offen = len([a for a in antraege if a["status"] == "eingegangen"])
        st.metric("Offen", offen)
    with col3:
        in_pruefung = len([a for a in antraege if a["status"] == "in_pruefung"])
        st.metric("In Prüfung", in_pruefung)
    with col4:
        abgeschlossen = len([a for a in antraege if a["status"] in ("genehmigt", "abgelehnt")])
        st.metric("Abgeschlossen", abgeschlossen)

    st.divider()

    if antraege:
        df = pd.DataFrame(antraege)
        st.dataframe(
            df[["aktenzeichen", "antragsteller", "art", "status", "eingangsdatum"]],
            use_container_width=True,
            hide_index=True,
        )

        # Status-Diagramm
        status_counts = df["status"].value_counts()
        fig = px.pie(status_counts, values=status_counts.values, names=status_counts.index,
                      title="Verteilung Antragstatus")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Noch keine Bauanträge vorhanden. Erstellen Sie einen neuen Antrag unter 'Antrag prüfen'.")

# ============================================================
# Antrag prüfen
# ============================================================
elif PAGES[page] == "antrag_pruefen":
    st.title("📋 Antrag prüfen")

    tab1, tab2 = st.tabs(["Neuer Antrag", "KI-Analyse"])

    with tab1:
        with st.form("neuer_antrag"):
            col1, col2 = st.columns(2)
            with col1:
                aktenzeichen = st.text_input("Aktenzeichen*", placeholder="BA-2024-001")
                antragsteller = st.text_input("Antragsteller*", placeholder="Max Mustermann GmbH")
            with col2:
                art = st.selectbox("Art des Vorhabens*", [
                    "Wohngebäude", "Gewerbegebäude", "Anbau", "Dachgeschossausbau",
                    "Garage", "Terrassenüberdachung", "Sonstiges"
                ])
                bundesland = st.selectbox("Bundesland*", [
                    "NW", "BY", "HE", "BW", "SN", "NI", "SH", "HH", "HB", "RP", "SL", "BE", "BB", "MV", "ST", "TH"
                ])

            adresse = st.text_input("Adresse des Bauvorhabens*", placeholder="Musterstraße 42, 12345 Musterstadt")
            beschreibung = st.text_area("Beschreibung des Vorhabens*", height=150,
                                        placeholder="Beschreiben Sie das geplante Bauvorhaben...")
            bauvorlagen = st.file_uploader("Bauvorlagen hochladen (PDF, JPG, PNG)", type=["pdf", "jpg", "png"],
                                           accept_multiple_files=True)

            submitted = st.form_submit_button("📋 Antrag anlegen")
            if submitted and aktenzeichen and antragsteller and beschreibung:
                db.create_antrag(
                    aktenzeichen=aktenzeichen,
                    antragsteller=antragsteller,
                    art=art,
                    bundesland=bundesland,
                    adresse=adresse,
                    beschreibung=beschreibung,
                )
                st.success(f"Antrag {aktenzeichen} erfolgreich angelegt!")
                st.rerun()

    with tab2:
        st.subheader("KI-Prüfung durchführen")
        offene = [a for a in db.get_all_antraege() if a["status"] == "eingegangen"]

        if not offene:
            st.info("Keine offenen Anträge zur Prüfung.")
        else:
            selected = st.selectbox(
                "Antrag auswählen",
                options=[a["id"] for a in offene],
                format_func=lambda x: f"{next(a['aktenzeichen'] for a in offene if a['id'] == x)} — {next(a['antragsteller'] for a in offene if a['id'] == x)}",
            )

            if st.button("🔍 KI-Prüfung starten", type="primary"):
                antrag = db.get_antrag(selected)
                with st.spinner("KI analysiert Antrag gegen Bauvorschriften..."):
                    analyzer = BauAnalyzer(config)
                    ergebnis = analyzer.analyze(antrag)
                    db.create_bewertung(
                        antrag_id=selected,
                        ergebnis=ergebnis["gesamtbeurteilung"],
                        details=ergebnis["details"],
                        risiken=ergebnis["risiken"],
                        empfehlung=ergebnis["empfehlung"],
                    )
                    db.update_antrag_status(selected, "in_pruefung")
                st.success("KI-Prüfung abgeschlossen!")
                st.json(ergebnis)

# ============================================================
# Berichte
# ============================================================
elif PAGES[page] == "berichte":
    st.title("📄 Berichte")

    antraege = db.get_all_antraege()
    bewertungen = db.get_all_bewertungen()

    if not bewertungen:
        st.info("Noch keine Gutachten vorhanden.")
    else:
        selected_id = st.selectbox(
            "Antrag für Bericht auswählen",
            options=[b["antrag_id"] for b in bewertungen],
            format_func=lambda x: f"{next(b['aktenzeichen'] for b in antraege if b['id'] == x)}",
        )

        antrag = db.get_antrag(selected_id)
        bewertung = next(b for b in bewertungen if b["antrag_id"] == selected_id)

        st.subheader(f"Gutachten: {antrag['aktenzeichen']}")
        st.write(f"**Antragsteller:** {antrag['antragsteller']}")
        st.write(f"**Vorhaben:** {antrag['art']} — {antrag['adresse']}")
        st.write(f"**Erstellt am:** {bewertung['erstellt_am']}")

        st.divider()
        st.write("### Gesamtbewertung")
        st.write(bewertung["ergebnis"])
        st.write("### Empfehlung")
        st.write(bewertung["empfehlung"])

        if st.button("📥 PDF exportieren"):
            gen = ReportGenerator()
            pdf_path = gen.generate(antrag, bewertung)
            with open(pdf_path, "rb") as f:
                st.download_button("PDF herunterladen", f, file_name=f"gutachten_{antrag['aktenzeichen']}.pdf")

# ============================================================
# Statistiken
# ============================================================
elif PAGES[page] == "statistiken":
    st.title("📈 Statistiken")

    antraege = db.get_all_antraege()
    if not antraege:
        st.info("Keine Daten vorhanden.")
    else:
        df = pd.DataFrame(antraege)

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(df, x="art", title="Anträge nach Art", color="status")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.histogram(df, x="eingangsdatum", title="Anträge über Zeit", color="status")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Durchschnittliche Bearbeitungszeit (Tage)")
        bearbeitungszeiten = []
        for a in antraege:
            if a["abschlussdatum"]:
                delta = datetime.fromisoformat(a["abschlussdatum"]) - datetime.fromisoformat(a["eingangsdatum"])
                bearbeitungszeiten.append(delta.days)
        if bearbeitungszeiten:
            st.metric("Ø Bearbeitungszeit", f"{sum(bearbeitungszeiten) / len(bearbeitungszeiten):.1f} Tage")

# ============================================================
# Einstellungen
# ============================================================
elif PAGES[page] == "einstellungen":
    st.title("⚙️ Einstellungen")

    st.subheader("Ollama Backend")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Ollama URL", value=config.get("ollama", {}).get("url", "http://localhost:11434"),
                      key="ollama_url")
        st.text_input("Modell", value=config.get("ollama", {}).get("model", "llama3"), key="ollama_model")
        st.slider("Temperature", min_value=0.0, max_value=1.0, value=config.get("ollama", {}).get("temperature", 0.2),
                  key="ollama_temp")

    with col2:
        st.markdown("### Verbindungsstatus")
        try:
            import requests
            resp = requests.get(config.get("ollama", {}).get("url", "http://localhost:11434"), timeout=5)
            st.success("✅ Ollama erreichbar")
        except Exception:
            st.error("❌ Ollama nicht erreichbar")

        st.markdown("### Verfügbare Modelle")
        try:
            resp = requests.get(config.get("ollama", {}).get("url", "http://localhost:11434") + "/api/tags", timeout=5)
            models = resp.json().get("models", [])
            for m in models:
                st.write(f"• {m['name']}")
        except Exception:
            st.write("— keine Verbindung —")

    st.divider()
    st.subheader("Bauvorschriften")
    st.selectbox("Bundesland", ["NW", "BY", "HE", "BW", "SN", "NI"],
                 index=["NW", "BY", "HE", "BW", "SN", "NI"].index(config.get("bauvorschriften", {}).get("bundesland", "NW")))

    st.divider()
    st.subheader("SMTP (Benachrichtigungen)")
    st.text_input("SMTP Host", key="smtp_host")
    st.text_input("SMTP Port", value="587", key="smtp_port")
    st.text_input("Absender", key="smtp_sender")
    st.toggle("TLS verwenden", value=True, key="smtp_tls")

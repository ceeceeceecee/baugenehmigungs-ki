"""Baugenehmigungs-KI — Streamlit Frontend."""
import streamlit as st
import os
import sys
import json
import plotly.express as px
import pandas as pd
from datetime import datetime
from pathlib import Path

# Projekt-Pfad
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import DatabaseManager
from processor.analyzer import BauAnalyzer

# --- Datenbank ---
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "data" / "baugenehmigungen.db"))
db = DatabaseManager(DB_PATH)

# --- Seitenkonfiguration ---
st.set_page_config(
    page_title="Baugenehmigungs-KI",
    page_icon="\U0001f3d7\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS ---
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #151e2e;
    }
    [data-testid="stSidebar"] * {
        color: #c8d6e5 !important;
    }
    .ds-badge {
        display: inline-block;
        background: #22c55e;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .section-card {
        background: white;
        border: 1px solid #f3f4f6;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "analyzer" not in st.session_state:
    ollama_url = db.get_setting("ollama_url", os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    model = db.get_setting("ollama_model", "llama3.1:8b")
    temp = float(db.get_setting("ollama_temperature", "0.2"))
    tokens = int(db.get_setting("ollama_max_tokens", "4096"))
    st.session_state.analyzer = BauAnalyzer(ollama_url, model, temp, tokens)

# --- Sidebar ---
with st.sidebar:
    st.markdown("\U0001f3d7\ufe0f **Baugenehmigungs-KI**")
    st.caption("Bauantragspruefung | DSGVO-konform")
    st.divider()

    # Quick stats
    stats = db.get_stats()
    st.markdown("**Letzte 30 Tage**")
    st.markdown(f"Antraege: **{stats['total']}**")
    st.markdown(f"Genehmigt: **{stats['genehmigt']}**")
    st.markdown(f"Abgelehnt: **{stats['abgelehnt']}**")
    st.divider()

    # Ollama status
    ollama_ok = st.session_state.analyzer.is_available()
    status_text = "\u2705 Ollama verbunden" if ollama_ok else "\u26a0\ufe0f Ollama nicht erreichbar (Demo-Modus)"
    st.markdown(status_text)
    model_name = db.get_setting("ollama_model", "llama3.1:8b")
    st.caption(f"Modell: {model_name} (Ollama)")

PAGES = {
    "\U0001f4ca Dashboard": "dashboard",
    "\U0001f4cb Antrag pruefen": "antrag",
    "\U0001f4c4 Neuer Antrag": "neu",
    "\u2699\ufe0f Einstellungen": "einstellungen",
}
page = st.sidebar.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

# ============================================================
# DASHBOARD
# ============================================================
if PAGES[page] == "dashboard":
    st.title("\U0001f4ca Dashboard \u2014 Antragsuebersicht")

    stats = db.get_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("\u23f3 Offene Antraege", stats["offen"] + stats["in_pruefung"] + stats["nachforderung"])
    with col2:
        st.metric("\u2705 Genehmigt", stats["genehmigt"])
    with col3:
        st.metric("\u274c Zurueckgewiesen", stats["abgelehnt"])
    with col4:
        st.metric("\U0001f4c8 \u00d8 Bearbeitung", f"{stats['avg_days']} Tage")

    st.divider()

    # Antraege table
    antraege = db.get_all_antraege()
    if antraege:
        status_map = {
            "eingegangen": "\u23f3 Eingegangen",
            "in_pruefung": "\U0001f50d In Pruefung",
            "genehmigt": "\u2705 Genehmigt",
            "abgelehnt": "\u274c Abgelehnt",
            "nachforderung": "\u26a0\ufe0f Nachforderung",
        }
        for a in antraege:
            a["status_display"] = status_map.get(a["status"], a["status"])

        df = pd.DataFrame(antraege)
        st.dataframe(
            df[["aktenzeichen", "antragsteller", "projekt", "art", "status_display", "eingangsdatum"]],
            column_config={
                "aktenzeichen": st.column_config.TextColumn("Aktenzeichen"),
                "antragsteller": st.column_config.TextColumn("Antragsteller"),
                "projekt": st.column_config.TextColumn("Projekt"),
                "art": st.column_config.TextColumn("Art"),
                "status_display": st.column_config.TextColumn("Status"),
                "eingangsdatum": st.column_config.TextColumn("Eingang"),
            },
            use_container_width=True,
            hide_index=True,
            height=400,
        )

        # Weekly chart
        weekly = db.get_weekly_counts()
        if weekly:
            wdf = pd.DataFrame(weekly)
            fig = px.bar(wdf, x="week", y="count",
                        title="Antraege pro Woche",
                        labels={"week": "Woche", "count": "Anzahl"},
                        color="count",
                        color_continuous_scale=["#6366f1", "#818cf8"])
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Noch keine Bauantraege vorhanden.")

# ============================================================
# ANTRAG PRÜFEN
# ============================================================
elif PAGES[page] == "antrag":
    st.title("\U0001f4cb Antrag pruefen")

    antraege = db.get_all_antraege()
    if not antraege:
        st.info("Keine Antraege vorhanden. Erstellen Sie zuerst einen neuen Antrag.")
    else:
        # Selector
        selected_az = st.selectbox(
            "Antrag auswaehlen",
            [a["aktenzeichen"] for a in antraege],
            format_func=lambda x: f"{x} \u2014 {[a['projekt'] for a in antraege if a['aktenzeichen']==x][0]}"
        )

        antrag = db.get_antrag(selected_az)
        if antrag:
            # Status bar
            status_map = {
                "eingegangen": ("\u23f3 Eingegangen", "#f59e0b"),
                "in_pruefung": ("\U0001f50d In Pruefung", "#3b82f6"),
                "genehmigt": ("\u2705 Genehmigt", "#22c55e"),
                "abgelehnt": ("\u274c Abgelehnt", "#ef4444"),
                "nachforderung": ("\u26a0\ufe0f Nachforderung", "#f59e0b"),
            }
            label, color = status_map.get(antrag["status"], (antrag["status"], "#6b7280"))

            st.markdown(f"**{antrag['projekt']}** | {antrag['adresse']}")
            st.caption(f"Eingang: {antrag['eingangsdatum']} | Art: {antrag['art']} | Antragsteller: {antrag['antragsteller']}")

            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("\U0001f4cb Dokumenten-Check")
                unterlagen = json.loads(antrag.get("unterlagen_json", "{}"))
                if not unterlagen:
                    unterlagen = {}

                all_docs = [
                    "Bauantrag (vollstaendig)", "Lageplan (masstabsgetreu)",
                    "Bauzeichnungen (Grundriss)", "Bauzeichnungen (Schnitt)",
                    "Bauzeichnungen (Ansicht)", "Statik-Nachweis",
                    "Energieausweis", "Bodengutachten",
                    "Entwaesserungsplan", "Baumschutzgutachten",
                ]

                updated = {}
                for doc in all_docs:
                    current = unterlagen.get(doc, False)
                    updated[doc] = st.checkbox(doc, value=bool(current), key=f"doc_{doc}")

                if st.button("Unterlagen speichern"):
                    db.update_unterlagen(selected_az, updated)
                    st.success("Unterlagen aktualisiert!")
                    st.rerun()

                vorhanden = sum(1 for v in updated.values() if v)
                fehlend = sum(1 for v in updated.values() if not v)
                st.divider()
                st.markdown(f"\u2705 **Vorhanden:** {vorhanden}/{len(all_docs)}  |  \u274c **Fehlend:** {fehlend}")

            with col_right:
                st.subheader("\U0001f916 KI-Analyse (Ollama)")

                if st.button("\U0001f50d KI-Pruefung starten", type="primary", use_container_width=True):
                    with st.spinner("Analyse laeuft..."):
                        analyse = st.session_state.analyzer.analyze(antrag, updated)
                        db.update_ki_analyse(selected_az, analyse)
                        st.success("Analyse abgeschlossen!")
                        st.rerun()

                ki_data = antrag.get("ki_analyse_json")
                if ki_data:
                    analyse = json.loads(ki_data) if isinstance(ki_data, str) else ki_data

                    if analyse.get("demo_mode"):
                        st.caption("\u26a0\ufe0f Demo-Modus (Ollama nicht erreichbar)")

                    check_fields = [
                        ("formale_pruefung", "Formale Pruefung"),
                        ("plausibilitaet", "Plausibilitaets-Check"),
                        ("bebauungsplan", "Bebauungsplan-Check"),
                        ("abstandsflaechen", "Abstandsflaechen"),
                        ("bruttogrundflaeche", "Bruttogrundflaeche"),
                        ("geschossflaechenzahl", "Geschossflaechenzahl"),
                        ("denkmalschutz", "Denkmalschutz"),
                        ("naturschutz", "Naturschutz"),
                    ]

                    for field, label in check_fields:
                        check = analyse.get(field, {})
                        status = check.get("status", "unbekannt")
                        details = check.get("text", check.get("details", ""))

                        if status == "ok":
                            icon = "\u2705"
                        elif status in ("warnung", "fehler"):
                            icon = "\u26a0\ufe0f"
                        else:
                            icon = "\u2753"

                        st.markdown(f"{icon} **{label}**: {details}")

                    # Empfehlung
                    st.divider()
                    st.subheader("\U0001f4a1 KI-Empfehlung")
                    empfehlung = analyse.get("empfehlung", "Keine Empfehlung verfuegbar.")
                    bewertung = analyse.get("gesamtbewertung", "")
                    zusammenfassung = analyse.get("zusammenfassung", "")

                    color_map = {
                        "genehmigung": "#22c55e",
                        "nachforderung": "#f59e0b",
                        "ablehnung": "#ef4444",
                    }
                    c = color_map.get(str(empfehlung).lower(), "#6b7280")
                    st.markdown(f"<span style='color:{c};font-weight:bold'>Bewertung: {bewertung}/10 \u2014 Empfehlung: {empfehlung}</span>", unsafe_allow_html=True)
                    if zusammenfassung:
                        st.markdown(zusammenfassung)

                    # Action buttons
                    st.divider()
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("\u2705 Genehmigungsvorschlag", use_container_width=True):
                            db.update_status(selected_az, "genehmigt")
                            st.success("Status auf Genehmigt gesetzt!")
                            st.rerun()
                    with c2:
                        if st.button("\U0001f4cb Nachforderung senden", use_container_width=True):
                            db.update_status(selected_az, "nachforderung")
                            st.success("Nachforderung erstellt!")
                            st.rerun()
                    with c3:
                        if st.button("\u274c Ablehnung", use_container_width=True):
                            db.update_status(selected_az, "abgelehnt")
                            st.warning("Antrag abgelehnt.")
                            st.rerun()

# ============================================================
# NEUER ANTRAG
# ============================================================
elif PAGES[page] == "neu":
    st.title("\U0001f4c4 Neuer Antrag")

    with st.form("neuer_antrag"):
        c1, c2 = st.columns(2)
        with c1:
            az = st.text_input("Aktenzeichen*", placeholder="BA-2026-0148")
            antragsteller = st.text_input("Antragsteller*", placeholder="Max Mustermann GmbH")
            projekt = st.text_input("Projektname*", placeholder="Wohnanlage Musterstr.")
        with c2:
            art = st.selectbox("Art des Vorhabens*", [
                "Wohngebaeude", "Gewerbegebaeude", "Anbau",
                "Dachgeschossausbau", "Garage",
                "Terrassenueberdachung", "Sonstiges"
            ])
            bundesland = st.selectbox("Bundesland*", [
                "NW", "BY", "HE", "BW", "SN", "TH", "NI", "SH", "HH", "HB", "RP", "SL", "BB", "MV"
            ])

        adresse = st.text_input("Adresse*", placeholder="Musterstr. 1, 99867 Musterhausen")
        beschreibung = st.text_area("Beschreibung", placeholder="Beschreibung des Bauvorhabens...", height=120)

        st.divider()
        st.markdown("**Dateien hochladen** (optional)")
        files = st.file_uploader(
            "Bauzeichnungen, Lageplaene, Gutachten",
            type=["pdf", "jpg", "png", "dwg"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        submitted = st.form_submit_button("\U0001f4be Antrag speichern", type="primary", use_container_width=True)
        if submitted:
            if not az or not antragsteller or not projekt or not adresse:
                st.error("Bitte alle Pflichtfelder ausfuellen (*).")
            else:
                ok = db.create_antrag(az, antragsteller, projekt, art, adresse, bundesland, beschreibung)
                if ok:
                    st.success(f"Antrag {az} erfolgreich erstellt!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Aktenzeichen {az} existiert bereits!")

    # Recent
    st.divider()
    recent = db.get_all_antraege()[:3]
    if recent:
        st.subheader("Letzte Antraege")
        for a in recent:
            st.markdown(f"- **{a['aktenzeichen']}** | {a['projekt']} | {a['status']}")

# ============================================================
# EINSTELLUNGEN
# ============================================================
elif PAGES[page] == "einstellungen":
    st.title("\u2699\ufe0f Einstellungen")

    # KI Config
    st.subheader("\U0001f916 KI-Konfiguration")
    c1, c2 = st.columns(2)
    with c1:
        ollama_url = st.text_input("Ollama Server", value=db.get_setting("ollama_url", os.getenv("OLLAMA_HOST", "http://localhost:11434")))
        model = st.text_input("Aktives Modell", value=db.get_setting("ollama_model", "llama3.1:8b"))
        fallback = st.text_input("Fallback-Modell", value=db.get_setting("ollama_fallback", "mistral:7b"))
    with c2:
        temp = st.text_input("Temperatur", value=db.get_setting("ollama_temperature", "0.2"))
        max_tok = st.text_input("Max Tokens", value=db.get_setting("ollama_max_tokens", "4096"))
        sprache = st.text_input("Sprache", value=db.get_setting("sprache", "Deutsch"))

    if st.button("KI-Einstellungen speichern"):
        for k, v in [("ollama_url", ollama_url), ("ollama_model", model),
                     ("ollama_fallback", fallback), ("ollama_temperature", temp),
                     ("ollama_max_tokens", max_tok), ("sprache", sprache)]:
            db.set_setting(k, v)
        st.session_state.analyzer = BauAnalyzer(ollama_url, model, float(temp), int(max_tok))
        st.success("KI-Einstellungen gespeichert!")

    ollama_ok = st.session_state.analyzer.is_available()
    if ollama_ok:
        st.markdown("\u2705 **Modell geladen & bereit**")
    else:
        st.markdown("\u26a0\ufe0f **Ollama nicht erreichbar** \u2014 Demo-Modus aktiv")

    st.divider()

    # Bauamt Config
    st.subheader("\U0001f3db Bauamt-Einstellungen")
    c1, c2 = st.columns(2)
    with c1:
        behoerde = st.text_input("Behoerde", value=db.get_setting("behoerde", "Stadtverwaltung Musterhausen"))
        bauamt = st.text_input("Bauamt", value=db.get_setting("bauamt", "Bauordnungsamt"))
    with c2:
        bauo = st.text_input("BauO", value=db.get_setting("bauo", "ThueringBO (Thueringen)"))
        az_format = st.text_input("Aktenzeichen-Format", value=db.get_setting("aktenzeichen_format", "BA-{JAHR}-{NUMMER}"))
        frist = st.text_input("Standard-Frist", value=db.get_setting("standard_frist", "3 Monate"))

    if st.button("Bauamt-Einstellungen speichern"):
        for k, v in [("behoerde", behoerde), ("bauamt", bauamt), ("bauo", bauo),
                     ("aktenzeichen_format", az_format), ("standard_frist", frist)]:
            db.set_setting(k, v)
        st.success("Bauamt-Einstellungen gespeichert!")

    st.divider()

    # DSGVO
    st.subheader("\U0001f512 Datenschutz (DSGVO)")
    ds_items = [
        ("datenspeicherung", "Datenspeicherung", "Lokal (kein Cloud-Upload)"),
        ("loeschfrist", "Datenloeschung", "12 Monate automatisch"),
        ("verschluesselung", "Verschluesselung", "AES-256 (Ruhezustand)"),
        ("protokollierung", "Protokollierung", "Aktiv (Audit-Trail)"),
    ]
    c1, c2 = st.columns(2)
    cols = [c1, c2]
    for i, (key, label, default) in enumerate(ds_items):
        with cols[i % 2]:
            val = st.text_input(label, value=db.get_setting(key, default))

    if st.button("DSGVO-Einstellungen speichern"):
        for key, _, default in ds_items:
            db.set_setting(key, st.session_state.get(key, default))
        st.success("DSGVO-Einstellungen gespeichert!")

    st.divider()
    st.markdown("\U0001f512 **100% DSGVO-konform | Self-Hosted | Ollama**")

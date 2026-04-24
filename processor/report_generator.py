"""PDF-Gutachten-Generator — Erstellt formatierte Prüfgutachten als PDF."""

import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# Farbschema
FARBE_AKZENT = HexColor("#1a5276")
FARBE_ERFUELLT = HexColor("#27ae60")
FARBE_NICHT_ERFUELLT = HexColor("#e74c3c")


class ReportGenerator:
    """Generiert PDF-Gutachten für Bauanträge."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Definiert benutzerdefinierte Stile für das Gutachten."""
        self.styles.add(ParagraphStyle(
            name="Titel",
            parent=self.styles["Title"],
            fontSize=18,
            textColor=FARBE_AKZENT,
            spaceAfter=12,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="Untertitel",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=HexColor("#7f8c8d"),
            spaceAfter=20,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            name="Kapitel",
            parent=self.styles["Heading2"],
            fontSize=13,
            textColor=FARBE_AKZENT,
            spaceBefore=16,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            name="Koerper",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
        ))

    def generate(self, antrag: dict, bewertung: dict) -> str:
        """Erstellt ein PDF-Gutachten und gibt den Dateipfad zurück."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gutachten_{antrag['aktenzeichen']}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                topMargin=2 * cm, bottomMargin=2 * cm,
                                leftMargin=2.5 * cm, rightMargin=2.5 * cm)

        elements = []

        # Kopfzeile
        elements.append(Paragraph("KI-Gutachten — Bauantrag", self.styles["Titel"]))
        elements.append(Paragraph(
            f"Erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Baugenehmigungs-KI",
            self.styles["Untertitel"]
        ))
        elements.append(HRFlowable(width="100%", thickness=1, color=FARBE_AKZENT, spaceAfter=16))

        # Antragstammdaten
        elements.append(Paragraph("1. Antragstammdaten", self.styles["Kapitel"]))
        stammdaten = [
            ["Aktenzeichen", antrag.get("aktenzeichen", "—")],
            ["Antragsteller", antrag.get("antragsteller", "—")],
            ["Art des Vorhabens", antrag.get("art", "—")],
            ["Adresse", antrag.get("adresse", "—")],
            ["Eingangsdatum", antrag.get("eingangsdatum", "—")],
        ]
        t = Table(stammdaten, colWidths=[5 * cm, 10 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#ecf0f1")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#bdc3c7")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # Gesamtbewertung
        elements.append(Paragraph("2. Gesamtbewertung", self.styles["Kapitel"]))
        bewertung_text = bewertung.get("ergebnis", "Keine Bewertung")
        elements.append(Paragraph(f"<b>{bewertung_text.upper()}</b>", self.styles["Koerper"]))
        elements.append(Spacer(1, 8))

        # Prüfkriterien
        details = bewertung.get("details", [])
        if details:
            elements.append(Paragraph("3. Prüfkriterien", self.styles["Kapitel"]))
            kriterien_daten = [["Kriterium", "Status", "Kommentar"]]
            for d in details:
                status = "✓ Erfüllt" if d.get("erfuellt") else "✗ Nicht erfüllt"
                kriterien_daten.append([d.get("kriterium", ""), status, d.get("kommentar", "")])

            t2 = Table(kriterien_daten, colWidths=[4 * cm, 3 * cm, 8 * cm])
            style_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), FARBE_AKZENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#bdc3c7")),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
            # Zeilenfarben
            for i, d in enumerate(details, 1):
                if d.get("erfuellt"):
                    style_cmds.append(("TEXTCOLOR", (1, i), (1, i), FARBE_ERFUELLT))
                else:
                    style_cmds.append(("TEXTCOLOR", (1, i), (1, i), FARBE_NICHT_ERFUELLT))
            t2.setStyle(TableStyle(style_cmds))
            elements.append(t2)
            elements.append(Spacer(1, 8))

        # Risiken
        risiken = bewertung.get("risiken", [])
        if risiken:
            elements.append(Paragraph("4. Identifizierte Risiken", self.styles["Kapitel"]))
            for r in risiken:
                elements.append(Paragraph(f"• {r}", self.styles["Koerper"]))

        # Empfehlung
        elements.append(Paragraph("5. Empfehlung", self.styles["Kapitel"]))
        empfehlung = bewertung.get("empfehlung", "Keine Empfehlung vorhanden.")
        elements.append(Paragraph(empfehlung, self.styles["Koerper"]))

        # Footer
        elements.append(Spacer(1, 24))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#bdc3c7")))
        elements.append(Paragraph(
            "<i>Hinweis: Dieses Gutachten wurde KI-gestützt erstellt und dient als Vorprüfung. "
            "Eine abschließende Entscheidung obliegt dem zuständigen Sachbearbeiter.</i>",
            ParagraphStyle("Footer", parent=self.styles["Normal"], fontSize=8, textColor=HexColor("#95a5a6"))
        ))

        doc.build(elements)
        return filepath

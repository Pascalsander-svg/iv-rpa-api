"""
IV Form RPA API — Version 5.0 PDF Generator
---------------------------------------------
Generates filled IV form 001.001 as PDF using reportlab.
No browser automation. No external downloads.
Returns PDF via /pdf/<job_id>.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
import traceback
import os
import uuid
import threading
import io

app = Flask(__name__)
CORS(app)

jobs = {}
W, H = A4


def draw_form_001001_full(fields, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    dob = f"{fields.get('date_of_birth_day','')}.{fields.get('date_of_birth_month','')}.{fields.get('date_of_birth_year','')}"

    # ============================================================
    # PAGE 1: Informationen
    # ============================================================
    header(c, 1, "Informationen")
    y = H - 65
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor('#CC0000'))
    c.drawString(1.5*cm, y, "Informationen")
    c.setFillColor(colors.black)
    y -= 20
    c.setFont("Helvetica", 8.5)
    info_text = [
        "Dieses Formular dient der Anmeldung bei der Invalidenversicherung (IV) für Erwachsene,",
        "die berufliche Eingliederungsmassnahmen oder eine Invalidenrente beantragen möchten.",
        "",
        "Bitte füllen Sie alle Pflichtfelder (mit * markiert) vollständig aus.",
        "Senden Sie das ausgefüllte Formular zusammen mit den erforderlichen Beilagen an:",
        "",
    ]
    for line in info_text:
        c.drawString(1.5*cm, y, line)
        y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.5*cm, y, "WAS IV Luzern, Landenbergstrasse 35, Postfach, 6002 Luzern")
    y -= 12
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y, "Tel. 041 369 05 00 | www.was-luzern.ch/kontaktformular-iv-sachleistungen")
    y -= 25

    # Navigation sidebar hint
    c.setFillColor(HexColor('#F5F5F5'))
    c.rect(1.5*cm, y-200, 4.5*cm, 210, fill=1, stroke=0)
    c.setFillColor(HexColor('#CC0000'))
    c.rect(1.5*cm, y-200, 4.5*cm, 14, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(1.8*cm, y-193, "Informationen")
    sections = ["1. Personalien","2. Zivilstand","3. Kinder","4. Allgemeine Angaben",
                "5. Angaben zu Bildung, Beruf...","6. Angaben zur gesundheitlic...",
                "7. Zahlungsverbindung","Ermächtigung zur Erteilung v...",
                "Mitwirkungspflicht","Wahrheitsgetreue und vollstä...","Beilagen","Empfängerauswahl"]
    c.setFillColor(HexColor('#333333'))
    c.setFont("Helvetica", 7.5)
    sy = y - 207
    for s in sections:
        c.drawString(1.8*cm, sy, s)
        sy -= 13
    c.setFillColor(colors.black)

    footer(c, "Informationen")
    c.showPage()

    # ============================================================
    # PAGE 2: Personalien
    # ============================================================
    header(c, 2, "1. Personalien")
    y = H - 65
    y = section(c, y, "1. Personalien")
    y = subsection(c, y, "1.1 Persönliche Angaben")

    # Wohnsitz
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#555555'))
    c.drawString(1.5*cm, y+2, "* In welchem Land ist Ihr Wohnsitz?")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.rect(1.5*cm, y-12, 10*cm, 14, fill=0, stroke=1)
    c.drawString(1.8*cm, y-10, fields.get('country_of_residence', 'Schweiz'))
    y -= 28

    y = draw(c, y, "* Name (auch Name als ledige Person)", fields.get('last_name',''), x2=6*cm, w=11*cm)
    y = draw(c, y, "* Vornamen (alle Vornamen, Rufnamen bitte in Grossbuchstaben)", fields.get('first_name',''), x2=7*cm, w=10*cm)

    # Gender radio
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#555555'))
    c.drawString(1.5*cm, y+2, "* Geschlecht")
    c.setFillColor(colors.black)
    y -= 12
    gender = fields.get('gender','')
    y = radio(c, y, "weiblich", gender == 'weiblich', x=2*cm)
    y = radio(c, y, "männlich", gender == 'männlich', x=2*cm)
    y -= 3

    # DOB and AHV side by side
    y = draw2(c, y, [
        ("* Geburtsdatum (Tag/Monat/Jahr)", dob, 1.5*cm, 5.5*cm, 4*cm),
        ("* AHV-Nummer (13-stellig)", fields.get('ahv_number',''), 10*cm, 13.5*cm, 4.5*cm),
    ])
    y -= 5
    y = subsection(c, y, "1.2 Gesetzlicher Wohnsitz mit genauer Adresse")
    y = draw2(c, y, [
        ("* Strasse", fields.get('street',''), 1.5*cm, 3.5*cm, 7*cm),
        ("* Hausnummer", fields.get('street_number',''), 11.5*cm, 14*cm, 3.5*cm),
    ])
    y = draw2(c, y, [
        ("Postleitzahl, Ort", f"{fields.get('postal_code','')} {fields.get('city','')}", 1.5*cm, 4*cm, 5*cm),
        ("", "", 1.5*cm, 1.5*cm, 0),
    ])
    y = draw2(c, y, [
        ("* Telefonnummer", fields.get('phone',''), 1.5*cm, 4*cm, 5*cm),
        ("E-Mail", fields.get('email',''), 10*cm, 11.5*cm, 6*cm),
    ])
    y -= 5
    y = subsection(c, y, "1.3 Beistandschaft")
    y = radio(c, y, "ja", False, x=2*cm)
    y = radio(c, y, "nein", True, x=2*cm)
    y -= 5
    y = subsection(c, y, "1.4 Staatsangehörigkeit")
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#555555'))
    c.drawString(1.5*cm, y, "Ausländische Staatsangehörige — Staatsangehörigkeit:")
    c.setFillColor(colors.black)
    y -= 12
    y = draw2(c, y, [
        ("Staatsangehörigkeit", fields.get('nationality',''), 1.5*cm, 5*cm, 5*cm),
        ("Datum der Einreise in die Schweiz", "", 10.5*cm, 15*cm, 2.5*cm),
    ])
    y -= 5
    y = subsection(c, y, "1.5 Wer hat das Formular ausgefüllt?")
    y = radio(c, y, "Die versicherte Person", True, x=2*cm)
    y = radio(c, y, "Eine Drittperson", False, x=2*cm)

    footer(c, "1. Personalien")
    c.showPage()

    # ============================================================
    # PAGE 3: Zivilstand
    # ============================================================
    header(c, 3, "2. Zivilstand")
    y = H - 65
    y = section(c, y, "2. Zivilstand")
    y = subsection(c, y, "2.1 Aktuelle Situation")
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#555555'))
    c.drawString(1.5*cm, y+2, "* Zivilstand")
    c.setFillColor(colors.black)
    y -= 12
    zivilstand = fields.get('civil_status', '')
    for zs in ["ledig", "verheiratet / in eingetragener Partnerschaft", "verwitwet", "geschieden / aufgelöste Partnerschaft"]:
        y = radio(c, y, zs, zivilstand.lower() in zs.lower(), x=2*cm)
    y -= 5
    y = draw(c, y, "Name Ehepartner/in / eingetragene/r Partner/in", fields.get('spouse_name',''), x2=7*cm, w=10*cm)
    y = draw2(c, y, [
        ("Geburtsdatum", fields.get('spouse_dob',''), 1.5*cm, 4.5*cm, 4*cm),
        ("AHV-Nummer", fields.get('spouse_ahv',''), 9.5*cm, 12*cm, 5.5*cm),
    ])

    footer(c, "2. Zivilstand")
    c.showPage()

    # ============================================================
    # PAGE 4: Kinder
    # ============================================================
    header(c, 4, "3. Kinder")
    y = H - 65
    y = section(c, y, "3. Kinder")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(1.5*cm, y, "Haben Sie eigene (eheliche und aussereheliche) Kinder, Adoptivkinder, Pflegekinder oder Stiefkinder?")
    y -= 12
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#555555'))
    c.drawString(1.5*cm, y, "Bitte alle Kinder aufführen, auch über 16-jährige bzw. erwachsene oder verstorbene")
    y -= 16
    c.setFillColor(colors.black)
    has_children = fields.get('has_children', 'nein')
    y = radio(c, y, "ja", has_children == 'ja', x=2*cm)
    y = radio(c, y, "nein", has_children != 'ja', x=2*cm)

    footer(c, "3. Kinder")
    c.showPage()

    # ============================================================
    # PAGE 5: Allgemeine Angaben
    # ============================================================
    header(c, 5, "4. Allgemeine Angaben")
    y = H - 65
    y = section(c, y, "4. Allgemeine Angaben")
    y = subsection(c, y, "4.1 Wohnsitz und Erwerbstätigkeit")
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y, "Haben Sie jemals ausserhalb der Schweiz gewohnt?")
    y -= 12
    y = radio(c, y, "ja", False, x=2*cm)
    y = radio(c, y, "nein", True, x=2*cm)
    y -= 10
    y = subsection(c, y, "4.2 Frühere Anmeldungen")
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y, "Haben Sie bereits einmal eine Anmeldung bei der IV eingereicht?")
    y -= 12
    prev_iv = fields.get('previously_registered_iv', 'Nein')
    y = radio(c, y, "ja", prev_iv == 'Ja', x=2*cm)
    y = radio(c, y, "nein", prev_iv != 'Ja', x=2*cm)
    y -= 10
    y = subsection(c, y, "4.3 Arbeitsunfähigkeit")
    y = draw2(c, y, [
        ("von (TT.MM.JJ)", fields.get('date_incapacity_to_work',''), 1.5*cm, 4*cm, 4*cm),
        ("bis (TT.MM.JJ)", "", 9.5*cm, 12*cm, 4*cm),
        ("in %", "100", 15*cm, 16.5*cm, 1*cm),
    ])
    y -= 10
    y = subsection(c, y, "4.4 Versicherungen")
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y, "Sind Sie angemeldet bzw. erhalten Sie Leistungen einer:")
    y -= 14
    insurances = [
        ("Krankentaggeldversicherung", True),
        ("SUVA oder einer anderen Versicherung im Rahmen der obligatorischen Unfallversicherung", True),
        ("Alters- und Hinterlassenenversicherung (AHV)", False),
        ("beruflichen Vorsorge", False),
        ("Sozialhilfe", False),
        ("Arbeitslosenversicherung oder der regionalen Arbeitsvermittlung (RAV)", False),
    ]
    for ins_label, ins_checked in insurances:
        y = checkbox(c, y, ins_label, ins_checked, x=2*cm)
    y -= 5
    y = draw(c, y, "Krankenkasse / Versicherung", fields.get('health_insurer',''), x2=5.5*cm, w=11.5*cm)

    footer(c, "4. Allgemeine Angaben")
    c.showPage()

    # ============================================================
    # PAGE 6: Angaben zu Bildung, Beruf
    # ============================================================
    header(c, 6, "5. Angaben zu Bildung, Beruf")
    y = H - 65
    y = section(c, y, "5. Angaben zu Bildung, Beruf und bisheriger Tätigkeit")
    y = subsection(c, y, "5.1 Muttersprache")
    y = draw(c, y, "Muttersprache", fields.get('mother_tongue', ''), x2=4*cm, w=13*cm)
    y -= 5
    y = subsection(c, y, "5.2 Besuchte Schulen")
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.rect(1.5*cm, y-35, W-3*cm, 35, fill=0, stroke=1)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor('#AAAAAA'))
    c.drawString(1.8*cm, y-18, "(Schulen, Ausbildungsorte, Abschlüsse)")
    c.setFillColor(colors.black)
    y -= 45
    y = subsection(c, y, "5.3 Erlernter Beruf")
    y = draw(c, y, "Erlernter Beruf / Ausbildung", fields.get('profession',''), x2=5*cm, w=12*cm)
    y -= 5
    y = subsection(c, y, "5.4 Erwerbstätige und Personen mit Nebenbeschäftigungen")
    y = draw(c, y, "Berufsbezeichnung / Funktion", fields.get('job_title',''), x2=5.5*cm, w=11.5*cm)
    y = draw2(c, y, [
        ("Name und Adresse des Arbeitgebenden", fields.get('employer_name',''), 1.5*cm, 6*cm, 5*cm),
        ("", fields.get('employer_address',''), 11.5*cm, 11.5*cm, 6*cm),
    ])
    y = draw2(c, y, [
        ("von (TT.MM.JJ)", "", 1.5*cm, 4*cm, 4*cm),
        ("bis (TT.MM.JJ)", "", 9.5*cm, 12*cm, 4*cm),
        ("Pensum in %", "100", 15*cm, 16.5*cm, 1*cm),
    ])
    y -= 5
    y = subsection(c, y, "5.5 Nichterwerbstätige")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor('#555555'))
    c.drawString(1.5*cm, y, "Hauptbeschäftigung (z.B. Haushaltsführung, Studium):")
    c.setFillColor(colors.black)
    y -= 12
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.line(1.5*cm, y, W-1.5*cm, y)
    y -= 20

    footer(c, "5. Bildung, Beruf")
    c.showPage()

    # ============================================================
    # PAGE 7: Gesundheitliche Beeinträchtigung
    # ============================================================
    header(c, 7, "6. Gesundheitliche Beeinträchtigung")
    y = H - 65
    y = section(c, y, "6. Angaben zur gesundheitlichen Beeinträchtigung")
    y = subsection(c, y, "6.1 Nähere Angaben zur Art der gesundheitlichen Beeinträchtigung")
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.rect(1.5*cm, y-50, W-3*cm, 50, fill=0, stroke=1)
    # Fill in diagnosis
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    diag_text = fields.get('diagnosis', '')
    if diag_text:
        c.drawString(1.8*cm, y-15, diag_text)
    y -= 60
    y = draw(c, y, "Seit wann besteht die gesundheitliche Beeinträchtigung?", fields.get('onset_of_impairment',''), x2=8*cm, w=9*cm)
    y -= 5
    y = subsection(c, y, "6.2 Unfall oder Schadensereignis")
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y, "Die gesundheitliche Beeinträchtigung ist ganz oder teilweise zurückzuführen auf:")
    y -= 14
    y = checkbox(c, y, "einen Unfall (z.B. Strassenverkehr, Ausübung beruflicher oder sportlicher Aktivität)", False, x=2*cm)
    y = checkbox(c, y, "ein anderes Schadensereignis (z.B. ärztliche Sorgfaltspflichtverletzung, Infekt)", False, x=2*cm)
    y = checkbox(c, y, "eine Krankheit", True, x=2*cm)
    y -= 5
    y = subsection(c, y, "6.3 Arzt, Spital oder Pflegeheim")
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y, "Bitte geben Sie uns hier Ihren Hausarzt sowie weitere behandelnde Ärzte, Spitäler oder Pflegeheime an:")
    y -= 14
    y = draw(c, y, "Name und Adresse", fields.get('treating_physician_name','') + ', ' + fields.get('treating_physician_address',''), x2=4.5*cm, w=13*cm)
    y = draw2(c, y, [
        ("Fachrichtung", fields.get('specialty', 'Allgemeine Innere Medizin'), 1.5*cm, 4*cm, 5*cm),
        ("Telefon", fields.get('treating_physician_phone',''), 10*cm, 11.5*cm, 6*cm),
    ])
    y = draw2(c, y, [
        ("In Behandlung von (TT.MM.JJ)", fields.get('date_incapacity_to_work',''), 1.5*cm, 5.5*cm, 4*cm),
        ("In Behandlung bis", "", 10*cm, 13.5*cm, 4*cm),
    ])

    footer(c, "6. Gesundheit")
    c.showPage()

    # ============================================================
    # PAGE 8: Zahlungsverbindung
    # ============================================================
    header(c, 8, "7. Zahlungsverbindung")
    y = H - 65
    y = section(c, y, "7. Zahlungsverbindung")
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y, "Bitte geben Sie Ihre Bankverbindung für allfällige Zahlungen der IV an:")
    y -= 16
    y = radio(c, y, "Bankkonto", True, x=2*cm)
    y = radio(c, y, "Postkonto", False, x=2*cm)
    y -= 5
    y = draw(c, y, "lautend auf (Name/Vorname)", fields.get('bank_account_holder', f"{fields.get('last_name','')} {fields.get('first_name','')}"), x2=5*cm, w=12*cm)
    y = draw(c, y, "* IBAN", fields.get('iban',''), x2=3*cm, w=14*cm)
    y = draw(c, y, "Name und Adresse der Bank", fields.get('bank_name',''), x2=5*cm, w=12*cm)

    footer(c, "7. Zahlungsverbindung")
    c.showPage()

    # ============================================================
    # PAGE 9: Ermächtigung
    # ============================================================
    header(c, 9, "Ermächtigung zur Erteilung von Auskünften")
    y = H - 65
    y = section(c, y, "Ermächtigung zur Erteilung von Auskünften")
    c.setFont("Helvetica", 8.5)
    text = ("Ich ermächtige alle Ärzte, Spitäler, Versicherungen, Arbeitgeber und Behörden, "
            "der IV-Stelle alle für die Abklärung meines Anspruchs notwendigen Auskünfte zu erteilen.")
    c.drawString(1.5*cm, y, text[:80])
    y -= 12
    c.drawString(1.5*cm, y, text[80:])
    y -= 25
    y = draw(c, y, "Unterschrift", "", x2=4*cm, w=10*cm)
    y = draw2(c, y, [
        ("Ort", fields.get('city',''), 1.5*cm, 2.5*cm, 4*cm),
        ("Datum", fields.get('date_created',''), 7*cm, 8.5*cm, 5*cm),
    ])

    footer(c, "Ermächtigung")
    c.showPage()

    # ============================================================
    # PAGE 10: Mitwirkungspflicht
    # ============================================================
    header(c, 10, "Mitwirkungspflicht")
    y = H - 65
    y = section(c, y, "Mitwirkungspflicht")
    c.setFont("Helvetica", 8.5)
    lines = [
        "Die versicherte Person ist verpflichtet, an der Abklärung aktiv mitzuwirken.",
        "Sie muss alle Angaben machen, die zur Feststellung des Anspruchs und",
        "zur Bemessung der Leistungen notwendig sind.",
        "",
        "Dies umfasst insbesondere:",
        "• Mitwirkung bei medizinischen Untersuchungen",
        "• Teilnahme an Eingliederungsmassnahmen",
        "• Bekanntgabe aller relevanten Änderungen (Gesundheitszustand, Erwerbstätigkeit, Wohnsitz)",
    ]
    for line in lines:
        c.drawString(1.5*cm, y, line)
        y -= 12

    footer(c, "Mitwirkungspflicht")
    c.showPage()

    # ============================================================
    # PAGE 11: Wahrheitsgetreue Angaben
    # ============================================================
    header(c, 11, "Wahrheitsgetreue und vollständige Angaben")
    y = H - 65
    y = section(c, y, "Wahrheitsgetreue und vollständige Angaben")
    c.setFont("Helvetica", 8.5)
    lines = [
        "Ich bestätige, dass die gemachten Angaben wahrheitsgetreu und vollständig sind.",
        "Mir ist bekannt, dass unwahre Angaben strafrechtliche Folgen haben können.",
        "",
        "Ich verpflichte mich, jede Änderung meiner Verhältnisse (insbesondere bezüglich",
        "Gesundheitszustand, Erwerbstätigkeit, Wohnort) unverzüglich der IV-Stelle zu melden.",
    ]
    for line in lines:
        c.drawString(1.5*cm, y, line)
        y -= 12
    y -= 20
    y = draw(c, y, "Unterschrift der versicherten Person", "", x2=7*cm, w=10*cm)
    y = draw2(c, y, [
        ("Ort", fields.get('city',''), 1.5*cm, 2.5*cm, 4*cm),
        ("Datum", fields.get('date_created',''), 7*cm, 8.5*cm, 5*cm),
    ])

    footer(c, "Wahrheitsgetreue Angaben")
    c.showPage()

    # ============================================================
    # PAGE 12: Beilagen
    # ============================================================
    header(c, 12, "Beilagen")
    y = H - 65
    y = section(c, y, "Beilagen")
    c.setFont("Helvetica", 8.5)
    c.drawString(1.5*cm, y,
        "Untenstehend sind alle Dokumente aufgeführt, welche Sie einreichen können.")
    y -= 20

    y = subsection(c, y, "Pflichtbeilagen zum Formular")
    required = [
        ("Kopie eines amtlichen Personalausweises (z.B. Familienausweis, Ausländerausweis)", True),
        ("Arztbericht der behandelnden Ärztin / des behandelnden Arztes", True),
        ("Aktuelles Arbeitsunfähigkeitszeugnis (AU-Zeugnis)", True),
        ("Krankenversicherungsnachweis (Versicherungsausweis)", True),
    ]
    for label, checked in required:
        y = checkbox(c, y, label, checked, x=2*cm)
    y -= 10

    y = subsection(c, y, "Optionale Beilagen")
    optional = [
        "Kopie Ausbildungsabschlüsse und Belege von Lehrbetrieben, Hochschulen und Arbeitgebenden",
        "Kopie der Ernennungsurkunde Beistandschaft/Vormund",
        "Lebenschronologie",
        "Todesbein",
        "Andere",
    ]
    for label in optional:
        y = checkbox(c, y, label, False, x=2*cm)

    c.setFillColor(HexColor('#CC0000'))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(1.5*cm, y-5, "Die Kopie eines amtlichen Personalausweises ist obligatorisch.")
    c.setFillColor(colors.black)

    footer(c, "Beilagen")
    c.showPage()

    # ============================================================
    # PAGE 13: Empfängerauswahl
    # ============================================================
    header(c, 13, "Empfängerauswahl")
    y = H - 65
    y = section(c, y, "Empfängerauswahl")
    c.setFont("Helvetica", 9)
    c.drawString(1.5*cm, y, "* Bitte wählen Sie die IV-Stelle Ihres Wohnkantons:")
    y -= 20
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.rect(1.5*cm, y-14, 10*cm, 16, fill=0, stroke=1)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(1.8*cm, y-10, "Luzern — WAS IV Luzern, Landenbergstrasse 35, 6002 Luzern")
    y -= 30
    c.setFont("Helvetica-Bold", 9)
    c.drawString(1.5*cm, y, "Empfänger:")
    c.setFont("Helvetica", 9)
    c.drawString(4*cm, y, "WAS IV Luzern")
    y -= 12
    c.drawString(4*cm, y, "Landenbergstrasse 35, Postfach")
    y -= 12
    c.drawString(4*cm, y, "6002 Luzern")
    y -= 12
    c.drawString(4*cm, y, "Tel. 041 369 05 00")
    y -= 30

    # Final summary box
    c.setFillColor(HexColor('#F9F9F9'))
    c.rect(1.5*cm, y-80, W-3*cm, 85, fill=1, stroke=0)
    c.setFillColor(HexColor('#CC0000'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, y-5, "Zusammenfassung der angemeldeten Person:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    summary = [
        f"Name: {fields.get('last_name','')} {fields.get('first_name','')}",
        f"Geburtsdatum: {dob}",
        f"AHV-Nummer: {fields.get('ahv_number','')}",
        f"Adresse: {fields.get('street','')} {fields.get('street_number','')}, {fields.get('postal_code','')} {fields.get('city','')}",
        f"Arbeitsunfähig seit: {fields.get('date_incapacity_to_work','')}",
    ]
    sy = y - 20
    for s in summary:
        c.drawString(2*cm, sy, s)
        sy -= 12

    footer(c, "Empfängerauswahl")
    c.showPage()

    c.save()


def draw_form_001003(fields, output_path):
    """Form 001.003 — Registration Minors"""
    c = canvas.Canvas(output_path, pagesize=A4)

    def header():
        c.setFillColor(HexColor('#CC0000'))
        c.rect(0, H-50, W, 50, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, H-32, "AHV | IV | EO")
        c.setFont("Helvetica", 10)
        c.drawString(12*cm, H-32, "Schweizerische Eidgenossenschaft")
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(2*cm, H-75, "Anmeldung Minderjährige: Med. Massnahmen / Hilfsmittel")
        c.setFont("Helvetica", 9)
        c.drawString(2*cm, H-90, "Formular 001.003 | Kanton Luzern")
        c.setFont("Helvetica", 8)
        c.drawString(14*cm, H-90, f"Erstellt: {fields.get('date_created','')}")

    def section(y, title):
        c.setFillColor(HexColor('#E8E8E8'))
        c.rect(1.5*cm, y-5, W-3*cm, 18, fill=1, stroke=0)
        c.setFillColor(HexColor('#CC0000'))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.8*cm, y+1, title)
        c.setFillColor(colors.black)
        return y - 25

    def field(y, label, value, x1=1.5*cm, x2=5*cm, w=12*cm):
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor('#666666'))
        c.drawString(x1, y+2, label)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.setStrokeColor(HexColor('#AAAAAA'))
        c.line(x2, y, x2+w, y)
        c.drawString(x2+2, y+2, str(value) if value else "")
        return y - 18

    def field2(y, items):
        for label, value, x1, x2, w in items:
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor('#666666'))
            c.drawString(x1, y+2, label)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.setStrokeColor(HexColor('#AAAAAA'))
            c.line(x2, y, x2+w, y)
            c.drawString(x2+2, y+2, str(value) if value else "")
        return y - 18

    header()
    y = H - 110

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(1.5*cm, y, "Einzureichen bei:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(5*cm, y, "WAS IV Luzern, Landenbergstrasse 35, Postfach, 6002 Luzern")
    y -= 8
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(5*cm, y, "Tel. 041 369 05 00 | www.was-luzern.ch")
    y -= 20
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.line(1.5*cm, y, W-1.5*cm, y)
    y -= 15

    # Child details
    y = section(y, "1. Personalien des Kindes")
    dob = f"{fields.get('date_of_birth_day','')}.{fields.get('date_of_birth_month','')}.{fields.get('date_of_birth_year','')}"
    y = field2(y, [
        ("Name", fields.get('last_name',''), 1.5*cm, 3.5*cm, 5.5*cm),
        ("Vorname", fields.get('first_name',''), 9.5*cm, 11.5*cm, 6*cm),
    ])
    y = field2(y, [
        ("Geburtsdatum", dob, 1.5*cm, 4.5*cm, 4*cm),
        ("AHV-Nummer", fields.get('ahv_number',''), 9.5*cm, 12*cm, 5.5*cm),
    ])
    y = field2(y, [
        ("Geschlecht", fields.get('gender',''), 1.5*cm, 3.8*cm, 3*cm),
        ("Nationalität", fields.get('nationality',''), 9.5*cm, 12*cm, 5.5*cm),
    ])
    y = field(y, "Strasse / Nr.", f"{fields.get('street','')} {fields.get('street_number','')}", x2=4.5*cm, w=13*cm)
    y = field2(y, [
        ("PLZ", fields.get('postal_code',''), 1.5*cm, 2.8*cm, 2*cm),
        ("Ort", fields.get('city',''), 5.5*cm, 6.5*cm, 5*cm),
    ])
    y = field2(y, [
        ("Telefon", fields.get('phone',''), 1.5*cm, 3.5*cm, 4.5*cm),
        ("E-Mail", fields.get('email',''), 9*cm, 10.5*cm, 7*cm),
    ])
    y -= 5

    # Guardian
    y = section(y, "2. Gesetzliche Vertretung (Eltern / Vormund)")
    y = field2(y, [
        ("Name", fields.get('guardian_last_name',''), 1.5*cm, 3.5*cm, 5.5*cm),
        ("Vorname", fields.get('guardian_first_name',''), 9.5*cm, 11.5*cm, 6*cm),
    ])
    y = field(y, "Beziehung zum Kind", fields.get('guardian_relationship',''), x2=5*cm, w=6*cm)
    y -= 5

    # Diagnosis
    y = section(y, "3. Diagnose / Geburtsgebrechen")
    y = field(y, "Diagnose (ICD-10)", fields.get('diagnosis',''), x2=4.5*cm, w=13*cm)
    y = field(y, "GgV-EDI Ziffer", fields.get('congenital_defect_code',''), x2=4.5*cm, w=4*cm)
    y = field(y, "Beginn der Erkrankung", fields.get('onset_of_impairment',''), x2=5*cm, w=6*cm)
    y -= 5

    # Physician
    y = section(y, "4. Behandelnde Ärztin / Behandelnder Arzt")
    y = field(y, "Name Arzt/Ärztin", fields.get('treating_physician_name',''), x2=5*cm, w=12*cm)
    y = field(y, "Adresse", fields.get('treating_physician_address',''), x2=5*cm, w=12*cm)
    y = field(y, "Telefon", fields.get('treating_physician_phone',''), x2=5*cm, w=6*cm)
    y -= 5

    # Insurance
    y = section(y, "5. Versicherungsangaben")
    y = field(y, "Krankenkasse", fields.get('health_insurer',''), x2=4.5*cm, w=12.5*cm)
    y = field(y, "Bereits IV-angemeldet?", fields.get('previously_registered_iv',''), x2=6*cm, w=3*cm)
    y -= 15

    # School
    y = section(y, "6. Schulische Situation")
    y = field(y, "Schule / Bildungsstufe", fields.get('school',''), x2=5*cm, w=12*cm)
    y -= 15

    # Signature
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.line(1.5*cm, y, W-1.5*cm, y)
    y -= 20
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(1.5*cm, y, "Unterschrift gesetzl. Vertretung:")
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.line(6.5*cm, y, 15*cm, y)
    y -= 12
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(1.5*cm, y, "Ort, Datum:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawString(4.5*cm, y, f"{fields.get('city','')}, {fields.get('date_created','')}")
    y -= 25

    # Attachments
    c.setStrokeColor(HexColor('#CC0000'))
    c.setLineWidth(0.5)
    c.rect(1.5*cm, y-65, W-3*cm, 75, fill=0, stroke=1)
    c.setFillColor(HexColor('#CC0000'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, y, "Beizulegende Unterlagen:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    ay = y - 13
    for att in [
        "• Kopie amtlicher Ausweis des Kindes",
        "• Arztbericht (Formular 002.003) ausgefüllt durch behandelnde Ärztin / Arzt",
        "• Geburtszeugnis des Kindes",
        "• Krankenversicherungsnachweis",
    ]:
        c.drawString(2*cm, ay, att)
        ay -= 12

    # Footer
    c.setFillColor(HexColor('#666666'))
    c.setFont("Helvetica", 7)
    c.drawString(1.5*cm, 1.5*cm,
        "WAS IV Luzern | Landenbergstrasse 35, Postfach, 6002 Luzern | Tel. 041 369 05 00")
    c.drawRightString(W-1.5*cm, 1.5*cm, "Formular 001.003 | Version 01/26")

    c.showPage()
    c.save()


def draw_form_002003(fields, output_path):
    """Form 002.003 — Medical Report for Children"""
    c = canvas.Canvas(output_path, pagesize=A4)

    def header():
        c.setFillColor(HexColor('#CC0000'))
        c.rect(0, H-50, W, 50, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, H-32, "AHV | IV | EO")
        c.setFont("Helvetica", 10)
        c.drawString(12*cm, H-32, "Schweizerische Eidgenossenschaft")
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(2*cm, H-75, "Arztbericht: Versicherte Kinder und junge Erwachsene")
        c.setFont("Helvetica", 9)
        c.drawString(2*cm, H-90, "Formular 002.003 | Kanton Luzern")
        c.setFont("Helvetica", 8)
        c.drawString(14*cm, H-90, f"Erstellt: {fields.get('date_created','')}")

    def section(y, title):
        c.setFillColor(HexColor('#E8E8E8'))
        c.rect(1.5*cm, y-5, W-3*cm, 18, fill=1, stroke=0)
        c.setFillColor(HexColor('#CC0000'))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.8*cm, y+1, title)
        c.setFillColor(colors.black)
        return y - 25

    def field(y, label, value, x1=1.5*cm, x2=5*cm, w=12*cm):
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor('#666666'))
        c.drawString(x1, y+2, label)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.setStrokeColor(HexColor('#AAAAAA'))
        c.line(x2, y, x2+w, y)
        c.drawString(x2+2, y+2, str(value) if value else "")
        return y - 18

    def field2(y, items):
        for label, value, x1, x2, w in items:
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor('#666666'))
            c.drawString(x1, y+2, label)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.setStrokeColor(HexColor('#AAAAAA'))
            c.line(x2, y, x2+w, y)
            c.drawString(x2+2, y+2, str(value) if value else "")
        return y - 18

    header()
    y = H - 110

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#888888'))
    c.drawString(1.5*cm, y,
        "Auszufüllen durch die behandelnde Ärztin / den behandelnden Arzt und an die IV-Stelle einzusenden.")
    y -= 20
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.line(1.5*cm, y, W-1.5*cm, y)
    y -= 15

    # Child
    y = section(y, "1. Angaben zum Kind / jungen Erwachsenen")
    dob = f"{fields.get('date_of_birth_day','')}.{fields.get('date_of_birth_month','')}.{fields.get('date_of_birth_year','')}"
    y = field2(y, [
        ("Name", fields.get('last_name',''), 1.5*cm, 3.5*cm, 5.5*cm),
        ("Vorname", fields.get('first_name',''), 9.5*cm, 11.5*cm, 6*cm),
    ])
    y = field2(y, [
        ("Geburtsdatum", dob, 1.5*cm, 4.5*cm, 4*cm),
        ("AHV-Nummer", fields.get('ahv_number',''), 9.5*cm, 12*cm, 5.5*cm),
    ])
    y = field(y, "Wohnadresse", f"{fields.get('street','')} {fields.get('street_number','')}, {fields.get('postal_code','')} {fields.get('city','')}", x2=4.5*cm, w=13*cm)
    y -= 5

    # Diagnosis
    y = section(y, "2. Diagnose und Krankheitsverlauf")
    y = field(y, "Hauptdiagnose (ICD-10)", fields.get('diagnosis',''), x2=5.5*cm, w=11.5*cm)
    y = field(y, "GgV-EDI Ziffer (Geburtsgebrechen)", fields.get('congenital_defect_code',''), x2=6.5*cm, w=4*cm)
    y = field(y, "Beginn des Leidens", fields.get('onset_of_impairment',''), x2=5*cm, w=6*cm)

    # Text area for medical history
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(1.5*cm, y+2, "Krankheitsverlauf / Befund:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.rect(1.5*cm, y-55, W-3*cm, 55, fill=0, stroke=1)
    # Write medical history if available
    medical_text = fields.get('medical_history', '')
    if medical_text:
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        # Wrap text manually
        words = medical_text.split()
        line = ""
        ty = y - 10
        for word in words:
            test = line + " " + word if line else word
            if c.stringWidth(test, "Helvetica", 8) < (W - 4*cm):
                line = test
            else:
                c.drawString(1.8*cm, ty, line)
                ty -= 11
                line = word
                if ty < y - 50:
                    break
        if line:
            c.drawString(1.8*cm, ty, line)
    y -= 70
    y -= 5

    # Current treatments
    y = section(y, "3. Aktuelle Behandlungen und Therapien")
    y = field(y, "Physiotherapie", fields.get('physiotherapy',''), x2=4.5*cm, w=13*cm)
    y = field(y, "Ergotherapie", fields.get('occupational_therapy',''), x2=4.5*cm, w=13*cm)
    y = field(y, "Logopädie", fields.get('speech_therapy',''), x2=4.5*cm, w=13*cm)
    y = field(y, "Medikation", fields.get('medication',''), x2=4.5*cm, w=13*cm)
    y -= 5

    # Prognosis
    y = section(y, "4. Prognose und Empfehlungen")
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(1.5*cm, y+2, "Prognose / Empfehlung der Ärztin / des Arztes:")
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.rect(1.5*cm, y-40, W-3*cm, 40, fill=0, stroke=1)
    y -= 55

    # Physician signature
    y = section(y, "5. Angaben zur Ärztin / zum Arzt")
    y = field(y, "Name Ärztin / Arzt", fields.get('treating_physician_name',''), x2=5*cm, w=12*cm)
    y = field(y, "Adresse / Praxis", fields.get('treating_physician_address',''), x2=5*cm, w=12*cm)
    y = field(y, "Telefon", fields.get('treating_physician_phone',''), x2=5*cm, w=6*cm)
    y -= 10

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(1.5*cm, y, "Unterschrift Ärztin / Arzt:")
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.line(6*cm, y, 15*cm, y)
    y -= 12
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(1.5*cm, y, "Ort, Datum:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawString(4.5*cm, y, f"{fields.get('city','')}, {fields.get('date_created','')}")

    # Footer
    c.setFillColor(HexColor('#666666'))
    c.setFont("Helvetica", 7)
    c.drawString(1.5*cm, 1.5*cm,
        "WAS IV Luzern | Landenbergstrasse 35, Postfach, 6002 Luzern | Tel. 041 369 05 00")
    c.drawRightString(W-1.5*cm, 1.5*cm, "Formular 002.003 | Version 01/26")

    c.showPage()
    c.save()


# ============================================================
# JOB RUNNER
# ============================================================

def run_pdf_job(job_id, form_number, fields):
    try:
        from datetime import date
        fields['date_created'] = date.today().strftime("%d.%m.%Y")
        pdf_path = f"/tmp/form_{form_number}_{job_id}.pdf"

        if form_number == "001.001":
            draw_form_001001_full(fields, pdf_path)
        elif form_number == "001.003":
            draw_form_001003(fields, pdf_path)
        elif form_number == "002.003":
            draw_form_002003(fields, pdf_path)
        else:
            jobs[job_id] = {"status": "error", "message": f"Form {form_number} not yet supported."}
            return

        jobs[job_id] = {
            "status": "success",
            "message": f"Form {form_number} filled and exported as PDF.",
            "pdf_url": f"/pdf/{job_id}",
            "filename": f"IV_Formular_{form_number}_{fields.get('last_name','')}.pdf"
        }
    except Exception as e:
        import traceback
        jobs[job_id] = {"status": "error", "message": str(e), "detail": traceback.format_exc()}


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/fill-form", methods=["POST"])
def fill_form():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON body received"}), 400
    form_number = data.get("form_number")
    fields = data.get("fields", {})
    if not form_number or not fields:
        return jsonify({"status": "error", "message": "Missing form_number or fields"}), 400
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "processing"}
    thread = threading.Thread(target=run_pdf_job, args=(job_id, form_number, fields), daemon=True)
    thread.start()
    return jsonify({
        "status": "processing",
        "job_id": job_id,
        "message": "PDF generation started. Poll /status/" + job_id,
        "status_url": f"/status/{job_id}"
    })


@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found"}), 404
    return jsonify(job)


@app.route("/pdf/<job_id>", methods=["GET"])
def get_pdf(job_id):
    for form_number in ["001.001", "001.003", "002.003"]:
        path = f"/tmp/form_{form_number}_{job_id}.pdf"
        if os.path.exists(path):
            job = jobs.get(job_id, {})
            filename = job.get("filename", f"IV_Formular_{job_id}.pdf")
            return send_file(path, mimetype="application/pdf",
                             as_attachment=True, download_name=filename)
    return jsonify({"status": "error", "message": "PDF not found"}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "IV RPA API",
        "version": "6.0-full-form",
        "active_jobs": len([j for j in jobs.values() if j.get("status") == "processing"])
    })


# ============================================================
# MAIN
# ============================================================

port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)

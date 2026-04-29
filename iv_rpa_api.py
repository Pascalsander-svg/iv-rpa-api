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


def draw_form_001001(fields, output_path):
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
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, H-75, "Anmeldung für Erwachsene: Berufliche Integration / Rente")
        c.setFont("Helvetica", 9)
        c.drawString(2*cm, H-90, "Formular 001.001 | Kanton Luzern")
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
    c.drawString(5*cm, y, "Tel. 041 369 05 00 | www.was-luzern.ch/kontaktformular-iv-sachleistungen")
    y -= 20
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.line(1.5*cm, y, W-1.5*cm, y)
    y -= 15

    y = section(y, "1. Personalien der versicherten Person")
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
        ("Geschlecht", fields.get('gender',''), 1.5*cm, 3.8*cm, 4*cm),
        ("Nationalität", fields.get('nationality',''), 9.5*cm, 12*cm, 5.5*cm),
    ])
    y = field(y, "Ausländerausweis-Typ", fields.get('residence_permit',''), x2=5*cm, w=6*cm)
    y -= 5

    y = section(y, "2. Wohnadresse")
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

    y = section(y, "3. Arbeitgeber")
    y = field(y, "Name Arbeitgeber", fields.get('employer_name',''), x2=5*cm, w=12*cm)
    y = field(y, "Adresse Arbeitgeber", fields.get('employer_address',''), x2=5*cm, w=12*cm)
    y = field(y, "Arbeitsunfähig seit", fields.get('date_incapacity_to_work',''), x2=5*cm, w=6*cm)
    y -= 5

    y = section(y, "4. Gesundheitliche Situation")
    y = field(y, "Beginn der Beeinträchtigung", fields.get('onset_of_impairment',''), x2=6.5*cm, w=10.5*cm)
    y = field(y, "Behandelnde Ärztin / Arzt", fields.get('treating_physician_name',''), x2=6.5*cm, w=10.5*cm)
    y = field(y, "Adresse Arzt/Ärztin", fields.get('treating_physician_address',''), x2=6.5*cm, w=10.5*cm)
    y = field(y, "Telefon Arzt/Ärztin", fields.get('treating_physician_phone',''), x2=6.5*cm, w=6*cm)
    y -= 5

    y = section(y, "5. Versicherungsangaben")
    y = field(y, "Krankenkasse", fields.get('health_insurer',''), x2=4.5*cm, w=12.5*cm)
    y = field(y, "Bereits IV-angemeldet?", fields.get('previously_registered_iv',''), x2=6*cm, w=3*cm)
    y -= 15

    c.setStrokeColor(HexColor('#CCCCCC'))
    c.line(1.5*cm, y, W-1.5*cm, y)
    y -= 20

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(1.5*cm, y, "Unterschrift:")
    c.setStrokeColor(HexColor('#AAAAAA'))
    c.line(4.5*cm, y, 13*cm, y)
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))
    c.drawString(1.5*cm, y-12, "Ort, Datum:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawString(4.5*cm, y-12, f"{fields.get('city','')}, {fields.get('date_created','')}")
    y -= 30

    # Attachments box
    c.setStrokeColor(HexColor('#CC0000'))
    c.setLineWidth(0.5)
    box_h = 65
    c.rect(1.5*cm, y-box_h, W-3*cm, box_h+10, fill=0, stroke=1)
    c.setFillColor(HexColor('#CC0000'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, y, "Beizulegende Unterlagen:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    ay = y - 13
    for att in [
        "• Kopie amtlicher Ausweis (Pass oder Identitätskarte)",
        "• Arztbericht der behandelnden Ärztin / des behandelnden Arztes",
        "• Aktuelles Arbeitsunfähigkeitszeugnis (AU-Zeugnis)",
        "• Krankenversicherungsnachweis",
    ]:
        c.drawString(2*cm, ay, att)
        ay -= 12

    # Footer
    c.setFillColor(HexColor('#666666'))
    c.setFont("Helvetica", 7)
    c.drawString(1.5*cm, 1.5*cm,
        "WAS IV Luzern | Landenbergstrasse 35, Postfach, 6002 Luzern | Tel. 041 369 05 00")
    c.drawRightString(W-1.5*cm, 1.5*cm, "Formular 001.001 | Version 01/26")

    c.showPage()
    c.save()


def run_pdf_job(job_id, form_number, fields):
    try:
        from datetime import date
        fields['date_created'] = date.today().strftime("%d.%m.%Y")

        pdf_path = f"/tmp/form_{form_number}_{job_id}.pdf"

        if form_number == "001.001":
            draw_form_001001(fields, pdf_path)
        else:
            jobs[job_id] = {
                "status": "error",
                "message": f"Form {form_number} not yet supported."
            }
            return

        jobs[job_id] = {
            "status": "success",
            "message": f"Form {form_number} filled and exported as PDF.",
            "pdf_url": f"/pdf/{job_id}",
            "filename": f"IV_Formular_{form_number}_{fields.get('last_name','')}.pdf"
        }

    except Exception as e:
        jobs[job_id] = {
            "status": "error",
            "message": str(e),
            "detail": traceback.format_exc()
        }


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

    thread = threading.Thread(
        target=run_pdf_job,
        args=(job_id, form_number, fields),
        daemon=True
    )
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
    for form_number in ["001.001", "001.003"]:
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
        "version": "5.0-pdf-generator",
        "active_jobs": len([j for j in jobs.values() if j.get("status") == "processing"])
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

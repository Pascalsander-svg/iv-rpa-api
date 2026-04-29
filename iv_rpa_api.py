"""
IV Form RPA API — Version 4.0 PDF Direct Fill
-----------------------------------------------
Downloads the official BSV PDF, overlays filled fields using reportlab,
and returns a ready-to-print PDF. No browser automation needed.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from pypdf import PdfReader, PdfWriter
import requests
import traceback
import os
import uuid
import threading
import io

app = Flask(__name__)
CORS(app)

jobs = {}

# Field coordinates for Form 001.001 (x, y, page_index)
# Coordinates are in points (72 pts = 1 inch) from bottom-left
# Page size A4: 595 x 842 pts
# These are approximate — adjust after first test print
FIELD_COORDS_001001 = {
    # Page 1 (index 0) — Personalien
    "last_name":               (0, 155, 765),
    "first_name":              (0, 320, 765),
    "date_of_birth":           (0, 155, 735),
    "ahv_number":              (0, 320, 735),
    "street":                  (0, 155, 705),
    "street_number":           (0, 430, 705),
    "postal_code":             (0, 155, 675),
    "city":                    (0, 280, 675),
    "phone":                   (0, 155, 645),
    "email":                   (0, 320, 645),
    "nationality":             (0, 155, 615),
    "residence_permit":        (0, 320, 615),
    # Page 2 (index 1) — Arbeitgeber / Gesundheit
    "employer_name":           (1, 155, 765),
    "employer_address":        (1, 155, 735),
    "date_incapacity_to_work": (1, 155, 705),
    "onset_of_impairment":     (1, 155, 675),
    "treating_physician_name": (1, 155, 645),
    "treating_physician_addr": (1, 155, 615),
    "treating_physician_phone":(1, 155, 585),
    "health_insurer":          (1, 155, 555),
}


def create_overlay_page(fields_on_page, page_width, page_height):
    """Create a transparent PDF page with text overlay at specified coordinates."""
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0, 0, 0.6)  # Dark blue — clearly visible as filled-in data

    for field_name, x, y in fields_on_page:
        c.drawString(x, y, str(field_name))

    c.save()
    packet.seek(0)
    return PdfReader(packet)


def fill_pdf_001001(fields):
    """Download form 001.001 and overlay filled fields."""

    # Download the PDF with a real browser user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/pdf,*/*"
    }

    pdf_url = "https://www.ahv-iv.ch/p/001.001.d"
    response = requests.get(pdf_url, headers=headers, timeout=30, allow_redirects=True)

    if response.status_code != 200 or b'%PDF' not in response.content[:10]:
        raise Exception(f"Could not download PDF. Status: {response.status_code}. "
                        f"Content type: {response.headers.get('Content-Type', 'unknown')}")

    # Load the PDF
    pdf_reader = PdfReader(io.BytesIO(response.content))
    pdf_writer = PdfWriter()

    # Build field data per page
    dob = f"{fields.get('date_of_birth_day','')}.{fields.get('date_of_birth_month','')}.{fields.get('date_of_birth_year','')}"

    page_fields = {
        0: [
            (fields.get("last_name", ""),               155, 765),
            (fields.get("first_name", ""),              320, 765),
            (dob,                                        155, 735),
            (fields.get("ahv_number", ""),              320, 735),
            (fields.get("street", ""),                  155, 705),
            (fields.get("street_number", ""),           430, 705),
            (fields.get("postal_code", ""),             155, 675),
            (fields.get("city", ""),                    280, 675),
            (fields.get("phone", ""),                   155, 645),
            (fields.get("email", ""),                   320, 645),
            (fields.get("nationality", ""),             155, 615),
            (fields.get("residence_permit", ""),        320, 615),
            (fields.get("gender", ""),                  155, 585),
        ],
        1: [
            (fields.get("employer_name", ""),           155, 765),
            (fields.get("employer_address", ""),        155, 735),
            (fields.get("date_incapacity_to_work", ""), 155, 705),
            (fields.get("onset_of_impairment", ""),     155, 675),
            (fields.get("treating_physician_name", ""), 155, 645),
            (fields.get("treating_physician_address",""),155, 615),
            (fields.get("treating_physician_phone",""), 155, 585),
            (fields.get("health_insurer", ""),          155, 555),
            (fields.get("previously_registered_iv",""), 155, 525),
        ]
    }

    # Overlay each page
    for i, page in enumerate(pdf_reader.pages):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        if i in page_fields:
            overlay_reader = create_overlay_page(
                page_fields[i], page_width, page_height
            )
            overlay_page = overlay_reader.pages[0]
            page.merge_page(overlay_page)

        pdf_writer.add_page(page)

    # Add metadata
    pdf_writer.add_metadata({
        "/Title": "IV Anmeldung 001.001 — Kanton Luzern",
        "/Author": "IV Form Assistant",
        "/Subject": f"Ausgefüllt für: {fields.get('last_name','')} {fields.get('first_name','')}",
    })

    output = io.BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output


def run_pdf_job(job_id, form_number, fields):
    try:
        if form_number == "001.001":
            pdf_bytes = fill_pdf_001001(fields)
        else:
            jobs[job_id] = {
                "status": "error",
                "message": f"Form {form_number} not yet supported."
            }
            return

        pdf_path = f"/tmp/form_{form_number}_{job_id}.pdf"
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes.getvalue())

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
    form_url = data.get("form_url")
    fields = data.get("fields", {})

    if not form_number or not fields:
        return jsonify({
            "status": "error",
            "message": "Missing required fields: form_number or fields"
        }), 400

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
            return send_file(
                path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=filename
            )
    return jsonify({"status": "error", "message": "PDF not found"}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "IV RPA API",
        "version": "4.0-pdf-direct",
        "active_jobs": len([j for j in jobs.values() if j.get("status") == "processing"])
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

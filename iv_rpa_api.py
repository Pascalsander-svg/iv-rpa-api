"""
IV Form RPA API
---------------
Flask API + Playwright script that receives form field data from WatsonX Agent 2
and automatically fills in the IV online form on ahv-iv.ch.

Setup:
  pip install flask playwright
  playwright install chromium

Run locally:
  python iv_rpa_api.py

Deploy to IBM Cloud Code Engine or Render.com for production use.
"""

from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import traceback
import os

app = Flask(__name__)


def fill_form_001001(page, fields):
    """Fill in Form 001.001 — Vocational Integration / Pension (Adults)"""

    # --- Page 1: Informationen (just click next) ---
    page.wait_for_load_state("networkidle")
    page.click("text=Weiter")

    # --- Page 2: Personalien ---
    page.wait_for_load_state("networkidle")

    # Country of residence dropdown
    page.select_option("select[name*='land'], select[id*='land']",
                       label=fields.get("country_of_residence", "Schweiz"))

    # Last name
    page.fill("input[name*='name'], input[id*='name']", fields.get("last_name", ""))

    # First name
    page.fill("input[name*='vorname'], input[id*='vorname']", fields.get("first_name", ""))

    # Gender
    gender = fields.get("gender", "männlich")
    if gender == "männlich":
        page.check("input[value='maennlich'], input[value='m']")
    else:
        page.check("input[value='weiblich'], input[value='w']")

    # Date of birth
    page.select_option("select[name*='tag'], select[id*='tag']",
                       value=fields.get("date_of_birth_day", "1"))
    page.select_option("select[name*='monat'], select[id*='monat']",
                       value=fields.get("date_of_birth_month", "1"))
    page.select_option("select[name*='jahr'], select[id*='jahr']",
                       value=fields.get("date_of_birth_year", "1980"))

    # AHV number (pre-filled with 756, complete the rest)
    ahv = fields.get("ahv_number", "").replace("756.", "").replace(".", "")
    page.fill("input[name*='ahv'], input[id*='ahv']", ahv)

    # Address
    page.fill("input[name*='strasse'], input[id*='strasse']", fields.get("street", ""))
    page.fill("input[name*='hausnummer'], input[id*='hausnummer']",
              fields.get("street_number", ""))
    page.fill("input[name*='plz'], input[id*='plz']", fields.get("postal_code", ""))
    page.fill("input[name*='ort'], input[id*='ort']", fields.get("city", ""))

    # Phone and email
    page.fill("input[name*='telefon'], input[id*='telefon']", fields.get("phone", ""))
    page.fill("input[name*='email'], input[id*='email']", fields.get("email", ""))

    page.click("text=Weiter")

    # --- Page 3: Zivilstand — skip with default ---
    page.wait_for_load_state("networkidle")
    page.click("text=Weiter")

    # --- Page 4: Kinder — skip with default ---
    page.wait_for_load_state("networkidle")
    page.click("text=Weiter")

    # --- Page 5: Allgemeine Angaben ---
    page.wait_for_load_state("networkidle")

    # Nationality
    page.fill("input[name*='nationalitaet'], input[id*='nationalitaet']",
              fields.get("nationality", ""))

    # Residence permit (if foreign)
    permit = fields.get("residence_permit", "")
    if permit:
        try:
            page.select_option("select[name*='ausweis'], select[id*='ausweis']",
                               label=permit)
        except Exception:
            pass

    page.click("text=Weiter")

    # --- Page 6: Angaben zu Bildung, Beruf ---
    page.wait_for_load_state("networkidle")

    # Employer
    page.fill("input[name*='arbeitgeber'], input[id*='arbeitgeber']",
              fields.get("employer_name", ""))
    page.fill("input[name*='arbeitgeber_adresse'], input[id*='arbeitgeber_adresse']",
              fields.get("employer_address", ""))

    page.click("text=Weiter")

    # --- Page 7: Angaben zur gesundheitlichen Situation ---
    page.wait_for_load_state("networkidle")

    # Onset of impairment
    page.fill("input[name*='beginn'], input[id*='beginn']",
              fields.get("onset_of_impairment", ""))

    # Date of incapacity to work
    page.fill("input[name*='arbeitsunfaehig'], input[id*='arbeitsunfaehig']",
              fields.get("date_incapacity_to_work", ""))

    # Treating physician
    page.fill("input[name*='arzt_name'], input[id*='arzt_name']",
              fields.get("treating_physician_name", ""))
    page.fill("input[name*='arzt_adresse'], input[id*='arzt_adresse']",
              fields.get("treating_physician_address", ""))
    page.fill("input[name*='arzt_telefon'], input[id*='arzt_telefon']",
              fields.get("treating_physician_phone", ""))

    page.click("text=Weiter")

    # --- Pages 8-12: remaining sections — navigate through ---
    for _ in range(5):
        page.wait_for_load_state("networkidle")
        try:
            page.click("text=Weiter")
        except Exception:
            break

    # --- Page 13: Empfängerauswahl ---
    page.wait_for_load_state("networkidle")
    try:
        # Select Canton Lucerne
        page.select_option("select[name*='kanton'], select[id*='kanton']",
                           label="Luzern")
    except Exception:
        pass


def fill_form_001003(page, fields):
    """Fill in Form 001.003 — Minors: Medical Measures / Assistive Devices"""

    page.wait_for_load_state("networkidle")
    page.click("text=Weiter")

    # --- Page 2: Personalien Kind ---
    page.wait_for_load_state("networkidle")

    page.select_option("select[name*='land'], select[id*='land']",
                       label=fields.get("country_of_residence", "Schweiz"))
    page.fill("input[name*='name']", fields.get("last_name", ""))
    page.fill("input[name*='vorname']", fields.get("first_name", ""))

    gender = fields.get("gender", "weiblich")
    if gender == "männlich":
        page.check("input[value='maennlich'], input[value='m']")
    else:
        page.check("input[value='weiblich'], input[value='w']")

    page.select_option("select[name*='tag']", value=fields.get("date_of_birth_day", "1"))
    page.select_option("select[name*='monat']", value=fields.get("date_of_birth_month", "1"))
    page.select_option("select[name*='jahr']", value=fields.get("date_of_birth_year", "2015"))

    ahv = fields.get("ahv_number", "").replace("756.", "").replace(".", "")
    page.fill("input[name*='ahv']", ahv)

    page.fill("input[name*='strasse']", fields.get("street", ""))
    page.fill("input[name*='hausnummer']", fields.get("street_number", ""))
    page.fill("input[name*='plz']", fields.get("postal_code", ""))
    page.fill("input[name*='ort']", fields.get("city", ""))
    page.fill("input[name*='telefon']", fields.get("phone", ""))
    page.fill("input[name*='email']", fields.get("email", ""))

    page.click("text=Weiter")

    # --- Guardian page ---
    page.wait_for_load_state("networkidle")
    try:
        page.fill("input[name*='vertreter_name']", fields.get("guardian_last_name", ""))
        page.fill("input[name*='vertreter_vorname']", fields.get("guardian_first_name", ""))
    except Exception:
        pass

    page.click("text=Weiter")

    # Navigate remaining pages
    for _ in range(8):
        page.wait_for_load_state("networkidle")
        try:
            page.click("text=Weiter")
        except Exception:
            break

    # Select Canton Lucerne on last page
    try:
        page.select_option("select[name*='kanton']", label="Luzern")
    except Exception:
        pass


@app.route("/fill-form", methods=["POST"])
def fill_form():
    """
    Main API endpoint.
    Receives JSON from WatsonX Agent 2 and fills the online IV form.

    Expected input:
    {
        "form_number": "001.001",
        "form_url": "https://www.ahv-iv.ch/p/001.001.d",
        "fields": { ... }
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "No JSON body received"}), 400

    form_number = data.get("form_number")
    form_url = data.get("form_url")
    fields = data.get("fields", {})

    if not form_number or not form_url or not fields:
        return jsonify({
            "status": "error",
            "message": "Missing required fields: form_number, form_url, or fields"
        }), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(form_url, wait_until="networkidle", timeout=30000)

            if form_number == "001.001":
                fill_form_001001(page, fields)
            elif form_number == "001.003":
                fill_form_001003(page, fields)
            else:
                browser.close()
                return jsonify({
                    "status": "error",
                    "message": f"Form {form_number} is not yet supported by this RPA script."
                }), 400

            # Take screenshot of final state
            screenshot_path = f"/tmp/form_{form_number}_filled.png"
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()

        return jsonify({
            "status": "success",
            "message": f"Form {form_number} filled successfully.",
            "screenshot_url": f"/screenshot/{form_number}"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "detail": traceback.format_exc()
        }), 500


@app.route("/screenshot/<form_number>", methods=["GET"])
def get_screenshot(form_number):
    """Return the screenshot of the filled form."""
    from flask import send_file
    path = f"/tmp/form_{form_number}_filled.png"
    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return jsonify({"status": "error", "message": "Screenshot not found"}), 404


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for WatsonX Custom Extension verification."""
    return jsonify({"status": "ok", "service": "IV RPA API", "version": "1.0"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

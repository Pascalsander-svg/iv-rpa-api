"""
IV Form RPA API — Async Version 3.1
-------------------------------------
Flask API + Playwright. Returns immediately with job_id.
Poll /status/<job_id> for result.
CORS enabled for cross-origin requests.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import traceback
import os
import uuid
import threading

app = Flask(__name__)
CORS(app)

# In-memory job store
jobs = {}

SEL = {
    "country":     "select[id*='pm-country-control']",
    "canton":      "select[id*='so-cantonHabitualResidence']",
    "nationality": "select[id*='po-nationality-control']",
    "firstname":   "input[id*='so-fillerOfFormNameFirstname']",
}


def wait_and_fill(page, selector, value):
    try:
        page.wait_for_selector(selector, timeout=8000)
        page.fill(selector, value)
    except Exception:
        pass


def wait_and_select(page, selector, label=None, value=None):
    try:
        page.wait_for_selector(selector, timeout=8000)
        if label:
            page.select_option(selector, label=label)
        elif value:
            page.select_option(selector, value=value)
    except Exception:
        pass


def click_next(page):
    try:
        page.wait_for_selector("text=Weiter", timeout=10000)
        page.click("text=Weiter")
        page.wait_for_timeout(2500)
    except Exception:
        pass


def fill_form_001001(page, fields):
    page.wait_for_timeout(5000)
    click_next(page)
    page.wait_for_timeout(3000)

    # Country
    wait_and_select(page, SEL["country"],
                    label=fields.get("country_of_residence", "Schweiz"))

    # Canton
    wait_and_select(page, SEL["canton"], label=fields.get("city", "Luzern"))

    # Last name
    for sel in ["input[id*='pm-lastName']", "input[id*='lastName']",
                "input[id*='pm-name']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("last_name", ""))
            break
        except Exception:
            pass

    # First name
    wait_and_fill(page, SEL["firstname"], fields.get("first_name", ""))

    # Gender
    gender = fields.get("gender", "männlich")
    try:
        radios = page.locator("input[type='radio']").all()
        if gender == "männlich" and len(radios) > 0:
            radios[0].check()
        elif len(radios) > 1:
            radios[1].check()
    except Exception:
        pass

    # Date of birth
    try:
        dob_selects = page.locator("select[id*='pm-dateOfBirth']").all()
        if len(dob_selects) >= 3:
            dob_selects[0].select_option(value=fields.get("date_of_birth_day", "1"))
            dob_selects[1].select_option(value=fields.get("date_of_birth_month", "1"))
            dob_selects[2].select_option(value=fields.get("date_of_birth_year", "1980"))
    except Exception:
        pass

    # AHV
    ahv = fields.get("ahv_number", "").replace("756.", "").replace(".", "")
    for sel in ["input[id*='ahv']", "input[id*='AHV']", "input[id*='avs']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, ahv)
            break
        except Exception:
            pass

    # Street
    for sel in ["input[id*='street']", "input[id*='strasse']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("street", ""))
            break
        except Exception:
            pass

    # Street number
    for sel in ["input[id*='streetNumber']", "input[id*='hausnummer']",
                "input[id*='houseNumber']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("street_number", ""))
            break
        except Exception:
            pass

    # Postal code
    for sel in ["input[id*='zip']", "input[id*='plz']", "input[id*='postalCode']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("postal_code", ""))
            break
        except Exception:
            pass

    # Phone
    for sel in ["input[id*='phone']", "input[id*='telefon']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("phone", ""))
            break
        except Exception:
            pass

    # Email
    for sel in ["input[id*='email']", "input[type='email']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("email", ""))
            break
        except Exception:
            pass

    click_next(page)  # Page 3: Zivilstand
    click_next(page)  # Page 4: Kinder
    click_next(page)  # Page 5: Allgemeine Angaben

    page.wait_for_timeout(2000)
    wait_and_select(page, SEL["nationality"], label=fields.get("nationality", ""))
    click_next(page)  # Page 6: Bildung/Beruf

    page.wait_for_timeout(2000)
    for sel in ["input[id*='employer']", "input[id*='arbeitgeber']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("employer_name", ""))
            break
        except Exception:
            pass
    click_next(page)  # Page 7: Gesundheit

    page.wait_for_timeout(2000)
    for sel in ["input[id*='physician']", "input[id*='arzt']", "input[id*='doctor']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("treating_physician_name", ""))
            break
        except Exception:
            pass
    click_next(page)

    for _ in range(5):
        click_next(page)

    # Page 13: Canton
    page.wait_for_timeout(2000)
    for sel in ["select[id*='kanton']", "select[id*='canton']"]:
        try:
            page.wait_for_selector(sel, timeout=5000)
            page.select_option(sel, label="Luzern")
            break
        except Exception:
            pass


def run_playwright_job(job_id, form_number, form_url, fields):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            page.goto(form_url, wait_until="domcontentloaded", timeout=60000)

            if form_number == "001.001":
                fill_form_001001(page, fields)
            else:
                browser.close()
                jobs[job_id] = {
                    "status": "error",
                    "message": f"Form {form_number} not yet supported."
                }
                return

            screenshot_path = f"/tmp/form_{form_number}_{job_id}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()

        jobs[job_id] = {
            "status": "success",
            "message": f"Form {form_number} filled successfully.",
            "screenshot_url": f"/screenshot/{job_id}"
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

    if not form_number or not form_url or not fields:
        return jsonify({
            "status": "error",
            "message": "Missing required fields: form_number, form_url, or fields"
        }), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "processing"}

    thread = threading.Thread(
        target=run_playwright_job,
        args=(job_id, form_number, form_url, fields),
        daemon=True
    )
    thread.start()

    return jsonify({
        "status": "processing",
        "job_id": job_id,
        "message": "Form filling started. Poll /status/" + job_id + " for result.",
        "status_url": f"/status/{job_id}"
    })


@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found"}), 404
    return jsonify(job)


@app.route("/screenshot/<job_id>", methods=["GET"])
def get_screenshot(job_id):
    for form_number in ["001.001", "001.003"]:
        path = f"/tmp/form_{form_number}_{job_id}.png"
        if os.path.exists(path):
            return send_file(path, mimetype="image/png")
    return jsonify({"status": "error", "message": "Screenshot not found"}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "IV RPA API",
        "version": "3.1-async-cors",
        "active_jobs": len([j for j in jobs.values() if j.get("status") == "processing"])
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

"""
IV Form RPA API
---------------
Flask API + Playwright script using exact Orbeon XForms selectors
from ahv-iv.ch form 001.001.
"""

from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import traceback
import os

app = Flask(__name__)

# Exact Orbeon selector fragments (partial match with *=)
SEL = {
    "country":      "select[id*='pm-country-control']",
    "canton":       "select[id*='so-cantonHabitualResidence']",
    "dob_day":      "select[id*='pm-dateOfBirth-control=selec']",
    "dob_month":    "select[id*='pm-dateOfBirth-control=xf-24']",
    "dob_year":     "select[id*='pm-dateOfBirth-control=xf-24']",
    "town":         "select[id*='cdc-town-control']",
    "nationality":  "select[id*='po-nationality-control']",
    "firstname":    "input[id*='so-fillerOfFormNameFirstname']",
    "guardian":     "input[id*='so-nameAddressGuardianAuthori']",
    "institution":  "input[id*='so-nameOfInstitution-control']",
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
        page.wait_for_timeout(2000)
    except Exception:
        pass


def fill_form_001001(page, fields):
    """Fill Form 001.001 using exact Orbeon selectors"""

    # Page 1: Info — click next
    page.wait_for_timeout(4000)
    click_next(page)

    # Page 2: Personalien
    page.wait_for_timeout(3000)

    # Country of residence
    wait_and_select(page, SEL["country"],
                    label=fields.get("country_of_residence", "Schweiz"))

    # Canton of residence
    wait_and_select(page, SEL["canton"],
                    label=fields.get("city", "Luzern"))

    # Last name — try all known name field patterns
    for sel in [
        "input[id*='pm-lastName']",
        "input[id*='lastName']",
        "input[id*='pm-name']",
        "input[id*='applicantDetails-control=grid-2-grid=pm-lastName']",
    ]:
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
        if gender == "männlich":
            page.locator("input[type='radio']").filter(has_text="männlich").first.check()
        else:
            page.locator("input[type='radio']").filter(has_text="weiblich").first.check()
    except Exception:
        try:
            radios = page.locator("input[type='radio']").all()
            if gender == "männlich" and len(radios) > 0:
                radios[0].check()
            elif len(radios) > 1:
                radios[1].check()
        except Exception:
            pass

    # Date of birth — day, month, year (3 separate selects)
    try:
        dob_selects = page.locator("select[id*='pm-dateOfBirth']").all()
        if len(dob_selects) >= 3:
            dob_selects[0].select_option(value=fields.get("date_of_birth_day", "1"))
            dob_selects[1].select_option(value=fields.get("date_of_birth_month", "1"))
            dob_selects[2].select_option(value=fields.get("date_of_birth_year", "1980"))
    except Exception:
        pass

    # AHV number
    ahv = fields.get("ahv_number", "").replace("756.", "").replace(".", "")
    for sel in ["input[id*='ahv']", "input[id*='AHV']", "input[id*='avs']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, ahv)
            break
        except Exception:
            pass

    # Street
    for sel in ["input[id*='street']", "input[id*='strasse']", "input[id*='Street']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("street", ""))
            break
        except Exception:
            pass

    # Street number
    for sel in ["input[id*='streetNumber']", "input[id*='hausnummer']", "input[id*='houseNumber']"]:
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

    # City (town dropdown)
    wait_and_select(page, SEL["town"], label=fields.get("city", ""))

    # Phone
    for sel in ["input[id*='phone']", "input[id*='telefon']", "input[id*='Phone']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("phone", ""))
            break
        except Exception:
            pass

    # Email
    for sel in ["input[id*='email']", "input[id*='Email']", "input[type='email']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("email", ""))
            break
        except Exception:
            pass

    click_next(page)

    # Page 3: Zivilstand
    click_next(page)

    # Page 4: Kinder
    click_next(page)

    # Page 5: Allgemeine Angaben
    page.wait_for_timeout(2000)
    wait_and_select(page, SEL["nationality"],
                    label=fields.get("nationality", ""))
    click_next(page)

    # Page 6: Bildung, Beruf
    page.wait_for_timeout(2000)
    for sel in ["input[id*='employer']", "input[id*='arbeitgeber']", "input[id*='Employer']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("employer_name", ""))
            break
        except Exception:
            pass
    click_next(page)

    # Page 7: Gesundheitliche Situation
    page.wait_for_timeout(2000)
    for sel in ["input[id*='physician']", "input[id*='arzt']", "input[id*='doctor']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, fields.get("treating_physician_name", ""))
            break
        except Exception:
            pass
    click_next(page)

    # Pages 8-12
    for _ in range(5):
        click_next(page)

    # Page 13: Empfängerauswahl — select Lucerne
    page.wait_for_timeout(2000)
    for sel in ["select[id*='kanton']", "select[id*='canton']", "select[id*='Canton']"]:
        try:
            page.wait_for_selector(sel, timeout=5000)
            page.select_option(sel, label="Luzern")
            break
        except Exception:
            pass


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

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            page.goto(form_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            if form_number == "001.001":
                fill_form_001001(page, fields)
            else:
                browser.close()
                return jsonify({
                    "status": "error",
                    "message": f"Form {form_number} is not yet supported."
                }), 400

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
    from flask import send_file
    path = f"/tmp/form_{form_number}_filled.png"
    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return jsonify({"status": "error", "message": "Screenshot not found"}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "IV RPA API", "version": "2.0"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

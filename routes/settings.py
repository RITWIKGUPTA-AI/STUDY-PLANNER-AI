from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from utils.json_manager import read_json, write_json, delete_user_data

settings_bp = Blueprint("settings", __name__)


DEFAULT_SETTINGS = {

    "theme": "Light",

    "notifications": "On",

    "font_size": "Medium",

    "language": "English"

}


@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():

    settings = read_json("settings.json")

    if not settings:

        settings = DEFAULT_SETTINGS.copy()

        write_json("settings.json", settings)

    if request.method == "POST":

        # Reset Button

        if request.form.get("action") == "reset":

            write_json("settings.json", DEFAULT_SETTINGS)

            flash(

                "Settings reset successfully!",

                "success"

            )

            return redirect(url_for("settings.settings"))

        # Save Settings

        settings["theme"] = request.form.get(
            "theme",
            "Light"
        )

        settings["notifications"] = request.form.get(
            "notifications",
            "On"
        )

        settings["font_size"] = request.form.get(
            "font_size",
            "Medium"
        )

        language = request.form.get(
            "language",
            "English"
        ).strip()

        if language == "":

            language = "English"

        settings["language"] = language

        write_json("settings.json", settings)

        flash(

            "Settings saved successfully!",

            "success"

        )

        return redirect(url_for("settings.settings"))

    return render_template(

        "settings.html",

        settings=settings

    )


@settings_bp.route("/settings/delete-account", methods=["POST"])
def delete_account():

    username = session.get("username")
    password = request.form.get("password", "")

    if not username:
        return redirect(url_for("login"))

    users = read_json("students.json")
    user = next((u for u in users if u.get("username", "").strip().lower() == username.strip().lower()), None)

    if not user:
        flash("Account not found.", "danger")
        return redirect(url_for("settings.settings"))

    stored_password = user.get("password", "")
    is_hashed = stored_password.startswith(("pbkdf2:", "scrypt:"))
    password_ok = check_password_hash(stored_password, password) if is_hashed else (stored_password == password)

    if not password_ok:
        flash("Incorrect password — account not deleted.", "danger")
        return redirect(url_for("settings.settings"))

    delete_user_data(username)
    session.clear()

    flash("Your account and all associated data have been permanently deleted.", "success")
    return redirect(url_for("login"))
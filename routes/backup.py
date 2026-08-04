from flask import Blueprint, render_template, send_file, flash, redirect, url_for, session, request
import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
import zipfile

backup_bp = Blueprint("backup", __name__)

DATA_FOLDER = "data"
BACKUP_FOLDER = "backups"


def _is_admin_user():
    """
    This feature backs up/restores EVERY user's data in one shot (all of
    data/*.json — password hashes, profiles, tasks, everything), so it
    must be admin-only, never available to a regular logged-in student.
    """
    admin_usernames = {
        u.strip().lower()
        for u in os.environ.get("ADMIN_USERNAMES", "").split(",")
        if u.strip()
    }
    username = session.get("username", "")
    return bool(username) and username.strip().lower() in admin_usernames


def _require_admin():
    if not _is_admin_user():
        flash("Admin access only.", "danger")
        return redirect(url_for("dashboard"))
    return None


def _safe_backup_path(filename):
    """
    Resolves a backup filename to a path guaranteed to stay inside
    BACKUP_FOLDER, blocking path traversal (e.g. "../../etc/passwd").
    Returns None if the name is invalid or escapes the folder.
    """
    safe_name = secure_filename(filename)
    if not safe_name:
        return None

    backup_root = os.path.abspath(BACKUP_FOLDER)
    candidate = os.path.abspath(os.path.join(backup_root, safe_name))

    if os.path.commonpath([backup_root, candidate]) != backup_root:
        return None

    return candidate


@backup_bp.route("/backup")
def backup():

    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_name = f"StudentPlanner_Backup_{timestamp}"

    zip_path = shutil.make_archive(
        os.path.join(BACKUP_FOLDER, backup_name),
        "zip",
        DATA_FOLDER
    )

    flash("Backup created successfully!", "success")

    return send_file(zip_path, as_attachment=True)


@backup_bp.route("/backup_page")
def backup_page():

    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    backups = []

    if os.path.exists(BACKUP_FOLDER):
        backups = sorted(os.listdir(BACKUP_FOLDER), reverse=True)

    return render_template("backup.html", backups=backups)


@backup_bp.route("/backup/download/<filename>")
def download_backup(filename):

    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    file_path = _safe_backup_path(filename)
    if not file_path or not os.path.exists(file_path):
        flash("Backup file not found.", "danger")
        return redirect(url_for("backup.backup_page"))

    return send_file(file_path, as_attachment=True)


@backup_bp.route("/backup/delete/<filename>")
def delete_backup(filename):

    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    file_path = _safe_backup_path(filename)

    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        flash("Backup deleted successfully!", "success")
    else:
        flash("Backup file not found.", "danger")

    return redirect(url_for("backup.backup_page"))


@backup_bp.route("/backup/restore", methods=["POST"])
def restore_backup():

    redirect_response = _require_admin()
    if redirect_response:
        return redirect_response

    if "backup_file" not in request.files:
        flash("Please select a backup file.", "danger")
        return redirect(url_for("backup.backup_page"))

    file = request.files["backup_file"]

    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("backup.backup_page"))

    if not file.filename.endswith(".zip"):
        flash("Please upload a ZIP backup.", "danger")
        return redirect(url_for("backup.backup_page"))

    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    temp_zip = os.path.join(BACKUP_FOLDER, "temp_restore.zip")
    file.save(temp_zip)

    try:
        data_root = os.path.abspath(DATA_FOLDER)

        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            # Validate every member resolves inside DATA_FOLDER before
            # extracting anything — otherwise a crafted entry name like
            # "../../app.py" could overwrite files outside the data
            # folder ("zip slip").
            for member in zip_ref.namelist():
                member_path = os.path.abspath(os.path.join(data_root, member))
                if os.path.commonpath([data_root, member_path]) != data_root:
                    raise ValueError(f"Unsafe path in backup archive: {member}")

            zip_ref.extractall(DATA_FOLDER)

        flash("Backup restored successfully!", "success")

    except Exception:
        flash("Invalid or unsafe backup file — restore cancelled.", "danger")

    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)

    return redirect(url_for("backup.backup_page"))

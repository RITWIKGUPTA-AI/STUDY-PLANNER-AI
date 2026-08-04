from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json

subjects_bp = Blueprint("subjects", __name__)

# A pleasant default palette to auto-assign when a user doesn't pick a
# color — cycles through so subjects don't all end up the same color.
DEFAULT_PALETTE = [
    "#2F4B7C", "#F2A93B", "#2E9E6D", "#E15554",
    "#4A6BA8", "#D68F1F", "#8B5CF6", "#EC4899",
]


def _normalize_subjects(subjects):
    """
    Migrates legacy plain-string subjects (["Physics", "Chemistry"]) into
    the new {"name": ..., "color": ...} shape, so old data isn't lost.
    """
    normalized = []
    changed = False

    for i, subject in enumerate(subjects):
        if isinstance(subject, dict):
            if "color" not in subject or not subject["color"]:
                subject["color"] = DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]
                changed = True
            normalized.append(subject)
        else:
            normalized.append({
                "name": subject,
                "color": DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]
            })
            changed = True

    return normalized, changed


def get_subject_color_map():
    """
    Returns {subject_name: color_hex}, for use by any other blueprint
    (timetable, planner, attendance) that wants to color-code entries by
    subject without duplicating this lookup logic.
    """
    subjects = read_json("subjects.json")
    normalized, changed = _normalize_subjects(subjects)

    if changed:
        write_json("subjects.json", normalized)

    return {s["name"]: s["color"] for s in normalized}


@subjects_bp.route("/subjects", methods=["GET", "POST"])
def subjects():

    subjects = read_json("subjects.json")
    subjects, changed = _normalize_subjects(subjects)

    if changed:
        write_json("subjects.json", subjects)

    if request.method == "POST":

        new_subject = request.form.get("subject", "").strip()
        color = request.form.get("color", "").strip() or DEFAULT_PALETTE[len(subjects) % len(DEFAULT_PALETTE)]

        # -------------------------
        # Validation
        # -------------------------

        if new_subject == "":

            flash(
                "Subject name cannot be empty!",
                "danger"
            )

            return redirect(url_for("subjects.subjects"))

        # Duplicate validation (case-insensitive)
        for subject in subjects:

            if subject["name"].lower() == new_subject.lower():

                flash(
                    "Subject already exists!",
                    "warning"
                )

                return redirect(url_for("subjects.subjects"))

        # -------------------------
        # Save Subject
        # -------------------------

        subjects.append({"name": new_subject, "color": color})

        write_json("subjects.json", subjects)

        flash(
            "Subject added successfully!",
            "success"
        )

        return redirect(url_for("subjects.subjects"))

    # -------------------------
    # Search
    # -------------------------

    search = request.args.get("search", "").lower().strip()

    if search:

        filtered = [s for s in subjects if search in s["name"].lower()]

    else:

        filtered = subjects

    return render_template(
        "subjects.html",
        subjects=filtered,
        total=len(subjects)
    )


@subjects_bp.route("/delete_subject/<subject>")
def delete_subject(subject):

    subjects = read_json("subjects.json")
    subjects, _ = _normalize_subjects(subjects)

    before = len(subjects)
    subjects = [s for s in subjects if s["name"] != subject]

    if len(subjects) < before:

        write_json("subjects.json", subjects)

        flash(
            "Subject deleted successfully!",
            "success"
        )

    else:

        flash(
            "Subject not found!",
            "danger"
        )

    return redirect(url_for("subjects.subjects"))


@subjects_bp.route("/edit_subject/<old_name>", methods=["GET", "POST"])
def edit_subject(old_name):

    subjects = read_json("subjects.json")
    subjects, _ = _normalize_subjects(subjects)

    current = next((s for s in subjects if s["name"] == old_name), None)

    if request.method == "POST":

        new_name = request.form.get("subject", "").strip()
        color = request.form.get("color", "").strip()

        # -------------------------
        # Validation
        # -------------------------

        if new_name == "":

            flash(
                "Subject name cannot be empty!",
                "danger"
            )

            return redirect(
                url_for(
                    "subjects.edit_subject",
                    old_name=old_name
                )
            )

        # Duplicate validation
        for subject in subjects:

            if (
                subject["name"].lower() == new_name.lower()
                and subject["name"].lower() != old_name.lower()
            ):

                flash(
                    "Another subject with this name already exists!",
                    "warning"
                )

                return redirect(
                    url_for(
                        "subjects.edit_subject",
                        old_name=old_name
                    )
                )

        # -------------------------
        # Update Subject
        # -------------------------

        updated = False

        for i in range(len(subjects)):

            if subjects[i]["name"] == old_name:

                subjects[i]["name"] = new_name

                if color:
                    subjects[i]["color"] = color

                updated = True

                break

        if updated:

            write_json("subjects.json", subjects)

            flash(
                "Subject updated successfully!",
                "success"
            )

        else:

            flash(
                "Subject not found!",
                "danger"
            )

        return redirect(url_for("subjects.subjects"))

    return render_template(
        "edit_subject.html",
        old_name=old_name,
        current=current
    )

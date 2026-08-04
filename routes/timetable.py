from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json
from routes.subjects import get_subject_color_map

timetable_bp = Blueprint("timetable", __name__)


@timetable_bp.route("/timetable", methods=["GET", "POST"])
def timetable():

    timetable = read_json("timetable.json")

    # -----------------------------
    # Add Timetable Entry
    # -----------------------------

    if request.method == "POST":

        day = request.form.get("day", "").strip()
        subject = request.form.get("subject", "").strip()
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")

        if day == "" or subject == "":

            flash(
                "Please fill all fields.",
                "danger"
            )

            return redirect(url_for("timetable.timetable"))

        timetable.append({

            "day": day,
            "subject": subject,
            "start_time": start_time,
            "end_time": end_time

        })

        write_json("timetable.json", timetable)

        flash(
            "Timetable entry added successfully!",
            "success"
        )

        return redirect(url_for("timetable.timetable"))

    # -----------------------------
    # Search
    # -----------------------------

    search = request.args.get("search", "").lower()

    if search:

        filtered = []

        for row in timetable:

            if (

                search in row.get("subject", "").lower()

                or

                search in row.get("day", "").lower()

            ):

                filtered.append(row)

    else:

        filtered = timetable

    return render_template(

        "timetable.html",

        timetable=filtered,

        total=len(timetable),

        subject_colors=get_subject_color_map()

    )


# -----------------------------------
# Delete Entry
# -----------------------------------

@timetable_bp.route("/timetable/delete/<int:index>")
def delete_timetable(index):

    timetable = read_json("timetable.json")

    if 0 <= index < len(timetable):

        timetable.pop(index)

        write_json("timetable.json", timetable)

        flash(
            "Entry deleted successfully!",
            "success"
        )

    else:

        flash(
            "Entry not found!",
            "danger"
        )

    return redirect(url_for("timetable.timetable"))


# -----------------------------------
# Edit Entry
# -----------------------------------

@timetable_bp.route("/timetable/edit/<int:index>", methods=["GET", "POST"])
def edit_timetable(index):

    timetable = read_json("timetable.json")

    if index < 0 or index >= len(timetable):

        flash(
            "Entry not found!",
            "danger"
        )

        return redirect(url_for("timetable.timetable"))

    if request.method == "POST":

        timetable[index]["day"] = request.form.get("day")
        timetable[index]["subject"] = request.form.get("subject")
        timetable[index]["start_time"] = request.form.get("start_time")
        timetable[index]["end_time"] = request.form.get("end_time")

        write_json("timetable.json", timetable)

        flash(
            "Timetable updated successfully!",
            "success"
        )

        return redirect(url_for("timetable.timetable"))

    return render_template(

        "edit_timetable.html",

        entry=timetable[index],

        index=index

    )
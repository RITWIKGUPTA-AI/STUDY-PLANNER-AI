from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json
from routes.subjects import get_subject_color_map

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/attendance", methods=["GET", "POST"])
def attendance():

    records = read_json("attendance.json")

    if request.method == "POST":

        subject = request.form.get("subject", "").strip()
        date = request.form.get("date", "")
        status = request.form.get("status", "Present")

        if subject == "":

            flash("Subject cannot be empty.", "danger")
            return redirect(url_for("attendance.attendance"))

        records.append({

            "subject": subject,
            "date": date,
            "status": status

        })

        write_json("attendance.json", records)

        flash("Attendance added successfully!", "success")

        return redirect(url_for("attendance.attendance"))

    # Search

    search = request.args.get("search", "").lower()

    if search:

        filtered = []

        for item in records:

            if search in item.get("subject", "").lower():

                filtered.append(item)

    else:

        filtered = records

    # Percentage

    total = len(records)

    present = 0

    for item in records:

        if item.get("status") == "Present":

            present += 1

    percentage = 0

    if total > 0:

        percentage = round((present / total) * 100)

    return render_template(

        "attendance.html",

        attendance=filtered,

        total=total,

        percentage=percentage,

        subject_colors=get_subject_color_map()

    )


@attendance_bp.route("/attendance/delete/<int:index>")
def delete_attendance(index):

    records = read_json("attendance.json")

    if 0 <= index < len(records):

        records.pop(index)

        write_json("attendance.json", records)

        flash("Attendance deleted successfully!", "success")

    return redirect(url_for("attendance.attendance"))


@attendance_bp.route("/attendance/edit/<int:index>", methods=["GET", "POST"])
def edit_attendance(index):

    records = read_json("attendance.json")

    if index >= len(records):

        flash("Record not found.", "danger")

        return redirect(url_for("attendance.attendance"))

    if request.method == "POST":

        records[index]["subject"] = request.form.get("subject")
        records[index]["date"] = request.form.get("date")
        records[index]["status"] = request.form.get("status")

        write_json("attendance.json", records)

        flash("Attendance updated successfully!", "success")

        return redirect(url_for("attendance.attendance"))

    return render_template(

        "edit_attendance.html",

        record=records[index],

        index=index

    )
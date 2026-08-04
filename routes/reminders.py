from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json
from datetime import datetime

reminders_bp = Blueprint("reminders", __name__)


@reminders_bp.route("/reminders", methods=["GET", "POST"])
def reminders():

    reminders = read_json("reminders.json")

    # -----------------------
    # Add Reminder
    # -----------------------

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        date = request.form.get("date")
        time = request.form.get("time")

        if title == "":

            flash(
                "Reminder title cannot be empty.",
                "danger"
            )

            return redirect(url_for("reminders.reminders"))

        reminders.append({

            "title": title,
            "date": date,
            "time": time

        })

        write_json("reminders.json", reminders)

        flash(
            "Reminder added successfully!",
            "success"
        )

        return redirect(url_for("reminders.reminders"))

    # -----------------------
    # Search
    # -----------------------

    search = request.args.get("search", "").lower()

    if search:

        filtered = []

        for reminder in reminders:

            if search in reminder.get("title", "").lower():

                filtered.append(reminder)

    else:

        filtered = reminders

    today = datetime.today().strftime("%Y-%m-%d")

    today_count = 0

    overdue = 0

    for reminder in reminders:

        if reminder.get("date") == today:

            today_count += 1

        elif reminder.get("date", "") < today:

            overdue += 1

    return render_template(

        "reminders.html",

        reminders=filtered,

        total=len(reminders),

        today_count=today_count,

        overdue=overdue

    )


# -----------------------
# Delete
# -----------------------

@reminders_bp.route("/reminders/delete/<int:index>")
def delete_reminder(index):

    reminders = read_json("reminders.json")

    if 0 <= index < len(reminders):

        reminders.pop(index)

        write_json("reminders.json", reminders)

        flash(
            "Reminder deleted successfully!",
            "success"
        )

    return redirect(url_for("reminders.reminders"))


# -----------------------
# Edit
# -----------------------

@reminders_bp.route("/reminders/edit/<int:index>", methods=["GET", "POST"])
def edit_reminder(index):

    reminders = read_json("reminders.json")

    if index >= len(reminders):

        flash(
            "Reminder not found!",
            "danger"
        )

        return redirect(url_for("reminders.reminders"))

    if request.method == "POST":

        reminders[index]["title"] = request.form.get("title")
        reminders[index]["date"] = request.form.get("date")
        reminders[index]["time"] = request.form.get("time")

        write_json("reminders.json", reminders)

        flash(
            "Reminder updated successfully!",
            "success"
        )

        return redirect(url_for("reminders.reminders"))

    return render_template(

        "edit_reminder.html",

        reminder=reminders[index],

        index=index

    )
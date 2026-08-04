from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json
from routes.subjects import get_subject_color_map

planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/planner", methods=["GET", "POST"])
def planner():

    plans = read_json("planner.json")

    # Convert old data if status doesn't exist
    updated = False

    for plan in plans:

        if "status" not in plan:

            plan["status"] = "Pending"
            updated = True

    if updated:
        write_json("planner.json", plans)

    # -----------------------------
    # Add Study Plan
    # -----------------------------
    if request.method == "POST":

        subject = request.form.get("subject", "").strip()
        topic = request.form.get("topic", "").strip()
        duration = request.form.get("duration", "").strip()
        date = request.form.get("date", "").strip()

        if subject == "" or topic == "":

            flash("Please fill all required fields.", "danger")
            return redirect(url_for("planner.planner"))

        plans.append({

            "subject": subject,
            "topic": topic,
            "duration": duration,
            "date": date,
            "status": "Pending"

        })

        write_json("planner.json", plans)

        flash("Study plan added successfully!", "success")

        return redirect(url_for("planner.planner"))

    # -----------------------------
    # Search
    # -----------------------------
    search = request.args.get("search", "").lower()

    if search:

        filtered = []

        for plan in plans:

            if (

                search in plan.get("subject", "").lower()

                or

                search in plan.get("topic", "").lower()

            ):

                filtered.append(plan)

    else:

        filtered = plans

    return render_template(

        "planner.html",

        plans=filtered,

        total=len(plans),

        subject_colors=get_subject_color_map()

    )


# ---------------------------------
# Delete
# ---------------------------------

@planner_bp.route("/planner/delete/<int:index>")
def delete_plan(index):

    plans = read_json("planner.json")

    if 0 <= index < len(plans):

        plans.pop(index)

        write_json("planner.json", plans)

        flash("Plan deleted successfully!", "success")

    else:

        flash("Plan not found!", "danger")

    return redirect(url_for("planner.planner"))


# ---------------------------------
# Complete Plan
# ---------------------------------

@planner_bp.route("/planner/complete/<int:index>")
def complete_plan(index):

    plans = read_json("planner.json")

    if 0 <= index < len(plans):

        plans[index]["status"] = "Completed"

        write_json("planner.json", plans)

        flash("Study plan completed!", "success")

    return redirect(url_for("planner.planner"))


# ---------------------------------
# Pending Plan
# ---------------------------------

@planner_bp.route("/planner/pending/<int:index>")
def pending_plan(index):

    plans = read_json("planner.json")

    if 0 <= index < len(plans):

        plans[index]["status"] = "Pending"

        write_json("planner.json", plans)

        flash("Plan marked pending.", "warning")

    return redirect(url_for("planner.planner"))


# ---------------------------------
# Edit Plan
# ---------------------------------

@planner_bp.route("/planner/edit/<int:index>", methods=["GET", "POST"])
def edit_plan(index):

    plans = read_json("planner.json")

    if index < 0 or index >= len(plans):

        flash("Plan not found!", "danger")

        return redirect(url_for("planner.planner"))

    if request.method == "POST":

        plans[index]["subject"] = request.form.get("subject")
        plans[index]["topic"] = request.form.get("topic")
        plans[index]["duration"] = request.form.get("duration")
        plans[index]["date"] = request.form.get("date")
        plans[index]["status"] = request.form.get("status")

        write_json("planner.json", plans)

        flash("Study plan updated successfully!", "success")

        return redirect(url_for("planner.planner"))

    return render_template(

        "edit_plan.html",

        plan=plans[index],

        index=index

    )
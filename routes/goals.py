from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json

goals_bp = Blueprint("goals", __name__)


@goals_bp.route("/goals", methods=["GET", "POST"])
def goals():

    goal_list = read_json("goals.json")

    # Add status if missing (for old data)
    updated = False

    for goal in goal_list:

        if "status" not in goal:

            goal["status"] = "Pending"
            updated = True

    if updated:
        write_json("goals.json", goal_list)

    # --------------------------
    # Add Goal
    # --------------------------

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        target_date = request.form.get("target_date", "")
        progress = request.form.get("progress", "0")

        if title == "":

            flash("Goal title cannot be empty.", "danger")
            return redirect(url_for("goals.goals"))

        goal_list.append({

            "title": title,
            "target_date": target_date,
            "progress": progress,
            "status": "Pending"

        })

        write_json("goals.json", goal_list)

        flash("Goal added successfully!", "success")

        return redirect(url_for("goals.goals"))

    # --------------------------
    # Search
    # --------------------------

    search = request.args.get("search", "").lower()

    if search:

        filtered = []

        for goal in goal_list:

            if search in goal.get("title", "").lower():

                filtered.append(goal)

    else:

        filtered = goal_list

    return render_template(

        "goals.html",

        goals=filtered,

        total=len(goal_list)

    )


# --------------------------
# Complete Goal
# --------------------------

@goals_bp.route("/goals/complete/<int:index>")
def complete_goal(index):

    goals = read_json("goals.json")

    if 0 <= index < len(goals):

        goals[index]["status"] = "Completed"
        goals[index]["progress"] = 100

        write_json("goals.json", goals)

        flash("Goal completed!", "success")

    return redirect(url_for("goals.goals"))


# --------------------------
# Delete Goal
# --------------------------

@goals_bp.route("/goals/delete/<int:index>")
def delete_goal(index):

    goals = read_json("goals.json")

    if 0 <= index < len(goals):

        goals.pop(index)

        write_json("goals.json", goals)

        flash("Goal deleted successfully!", "success")

    else:

        flash("Goal not found.", "danger")

    return redirect(url_for("goals.goals"))


# --------------------------
# Edit Goal
# --------------------------

@goals_bp.route("/goals/edit/<int:index>", methods=["GET", "POST"])
def edit_goal(index):

    goals = read_json("goals.json")

    if index < 0 or index >= len(goals):

        flash("Goal not found.", "danger")

        return redirect(url_for("goals.goals"))

    if request.method == "POST":

        goals[index]["title"] = request.form.get("title")
        goals[index]["target_date"] = request.form.get("target_date")
        goals[index]["progress"] = request.form.get("progress")
        goals[index]["status"] = request.form.get("status")

        write_json("goals.json", goals)

        flash("Goal updated successfully!", "success")

        return redirect(url_for("goals.goals"))

    return render_template(

        "edit_goal.html",

        goal=goals[index],

        index=index

    )
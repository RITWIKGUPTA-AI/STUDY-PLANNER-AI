from flask import Blueprint, render_template, request, redirect, url_for
from utils.json_manager import read_json, write_json
from services.gamification_service import compute_auto_achievements, compute_streak

achievements_bp = Blueprint("achievements", __name__)


@achievements_bp.route("/achievements", methods=["GET", "POST"])
def achievements():

    achievements = read_json("achievements.json")

    if request.method == "POST":

        achievement = {
            "title": request.form["title"],
            "description": request.form["description"],
            "date": request.form["date"]
        }

        achievements.append(achievement)

        write_json("achievements.json", achievements)

        return redirect(url_for("achievements.achievements"))

    # Real, automatically-detected achievements based on the user's actual
    # stored activity (streaks, tasks completed, etc.) — shown alongside
    # the manual diary below rather than replacing it.
    tasks = read_json("tasks.json")
    planner = read_json("planner.json")
    goals = read_json("goals.json")
    attendance = read_json("attendance.json")

    auto_achievements, streak = compute_auto_achievements(tasks, planner, goals, attendance)

    return render_template(
        "achievements.html",
        achievements=achievements,
        auto_achievements=auto_achievements,
        streak=streak
    )


@achievements_bp.route("/achievements/delete/<int:index>")
def delete_achievement(index):

    achievements = read_json("achievements.json")

    if 0 <= index < len(achievements):

        achievements.pop(index)

        write_json("achievements.json", achievements)

    return redirect(url_for("achievements.achievements"))
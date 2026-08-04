from flask import Blueprint, render_template, send_file, session, after_this_request
from utils.json_manager import read_json
from datetime import datetime, timedelta
import csv
import os
import tempfile

analytics_bp = Blueprint("analytics", __name__)


def _parse_date(value):
    """Best-effort date parser; returns None if it can't be parsed."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _real_weekly_study_hours(planner):
    """Sums real planner durations (minutes) per day for the last 7 days."""

    today = datetime.today().date()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]

    minutes_by_day = {d: 0 for d in days}

    for plan in planner:
        if not isinstance(plan, dict):
            continue
        parsed = _parse_date(plan.get("date", ""))
        if not parsed:
            continue
        d = parsed.date()
        if d in minutes_by_day:
            try:
                minutes_by_day[d] += int(plan.get("duration", 0) or 0)
            except (ValueError, TypeError):
                pass

    labels = [d.strftime("%a") for d in days]
    values = [round(minutes_by_day[d] / 60, 2) for d in days]

    return labels, values


def _real_monthly_study_hours(planner):
    """Sums real planner durations (minutes) per month for the last 6 months."""

    today = datetime.today().replace(day=1)
    months = []
    cursor = today
    for _ in range(6):
        months.append(cursor)
        # step back one month
        prev_month_end = cursor - timedelta(days=1)
        cursor = prev_month_end.replace(day=1)
    months.reverse()

    minutes_by_month = {(m.year, m.month): 0 for m in months}

    for plan in planner:
        if not isinstance(plan, dict):
            continue
        parsed = _parse_date(plan.get("date", ""))
        if not parsed:
            continue
        key = (parsed.year, parsed.month)
        if key in minutes_by_month:
            try:
                minutes_by_month[key] += int(plan.get("duration", 0) or 0)
            except (ValueError, TypeError):
                pass

    labels = [m.strftime("%b") for m in months]
    values = [round(minutes_by_month[(m.year, m.month)] / 60, 2) for m in months]

    return labels, values


def _real_subject_distribution(subjects, planner):
    """Real total study minutes (converted to hours) per subject, from planner entries."""

    minutes_by_subject = {}

    for plan in planner:
        if not isinstance(plan, dict):
            continue
        subject_name = plan.get("subject", "").strip()
        if not subject_name:
            continue
        try:
            minutes_by_subject[subject_name] = minutes_by_subject.get(subject_name, 0) + int(plan.get("duration", 0) or 0)
        except (ValueError, TypeError):
            pass

    labels = []
    values = []

    for subject in subjects:
        name = subject.get("name", "Subject") if isinstance(subject, dict) else str(subject)
        labels.append(name)
        values.append(round(minutes_by_subject.get(name, 0) / 60, 2))

    return labels, values


@analytics_bp.route("/analytics")
def analytics():

    subjects = read_json("subjects.json")
    tasks = read_json("tasks.json")
    notes = read_json("notes.json")
    goals = read_json("goals.json")
    planner = read_json("planner.json")
    attendance = read_json("attendance.json")
    reminders = read_json("reminders.json")
    timetable = read_json("timetable.json")

    # ======================================
    # Task Statistics
    # ======================================

    completed_tasks = 0
    pending_tasks = 0
    high_priority = 0
    medium_priority = 0
    low_priority = 0

    for task in tasks:
        if isinstance(task, dict):
            if task.get("status") == "Completed":
                completed_tasks += 1
            else:
                pending_tasks += 1

            if task.get("priority") == "High":
                high_priority += 1
            elif task.get("priority") == "Medium":
                medium_priority += 1
            elif task.get("priority") == "Low":
                low_priority += 1

    task_progress = round(completed_tasks * 100 / len(tasks), 2) if tasks else 0

    # ======================================
    # Goal Statistics
    # ======================================

    completed_goals = 0
    pending_goals = 0

    for goal in goals:
        if isinstance(goal, dict):
            if goal.get("status") == "Completed":
                completed_goals += 1
            else:
                pending_goals += 1

    goal_progress = round(completed_goals * 100 / len(goals), 2) if goals else 0

    # ======================================
    # Attendance
    # ======================================

    present = 0
    absent = 0

    for item in attendance:
        if isinstance(item, dict):
            if item.get("status") == "Present":
                present += 1
            else:
                absent += 1

    attendance_percentage = round(present * 100 / len(attendance), 2) if attendance else 0

    # ======================================
    # Planner Statistics
    # ======================================

    total_minutes = 0
    for plan in planner:
        if isinstance(plan, dict):
            try:
                total_minutes += int(plan.get("duration", 0) or 0)
            except (ValueError, TypeError):
                pass

    total_hours = round(total_minutes / 60, 2)

    # ======================================
    # Real Weekly / Monthly / Subject Data
    # (previously hardcoded fake numbers — now computed from each user's
    # own planner entries)
    # ======================================

    weekly_labels, weekly_data = _real_weekly_study_hours(planner)
    monthly_labels, monthly_data = _real_monthly_study_hours(planner)
    subject_labels, subject_values = _real_subject_distribution(subjects, planner)

    return render_template(
        "analytics.html",
        subject_count=len(subjects),
        task_count=len(tasks),
        note_count=len(notes),
        goal_count=len(goals),
        planner_count=len(planner),
        reminder_count=len(reminders),
        timetable_count=len(timetable),
        attendance_count=len(attendance),
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        completed_goals=completed_goals,
        pending_goals=pending_goals,
        task_progress=task_progress,
        goal_progress=goal_progress,
        attendance_percentage=attendance_percentage,
        present=present,
        absent=absent,
        total_minutes=total_minutes,
        total_hours=total_hours,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority,
        weekly_data=weekly_data,
        weekly_labels=weekly_labels,
        monthly_data=monthly_data,
        monthly_labels=monthly_labels,
        subject_labels=subject_labels,
        subject_values=subject_values
    )


@analytics_bp.route("/analytics/export/csv")
def export_csv():

    # Use a unique temp file per request instead of one shared filename on
    # disk — the old version could leak one user's export to another if two
    # requests overlapped.
    username = session.get("username", "user")

    fd, filepath = tempfile.mkstemp(prefix=f"analytics_{username}_", suffix=".csv")

    with os.fdopen(fd, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Category", "Value"])
        writer.writerow(["Subjects", len(read_json("subjects.json"))])
        writer.writerow(["Tasks", len(read_json("tasks.json"))])
        writer.writerow(["Notes", len(read_json("notes.json"))])
        writer.writerow(["Goals", len(read_json("goals.json"))])
        writer.writerow(["Planner", len(read_json("planner.json"))])
        writer.writerow(["Attendance", len(read_json("attendance.json"))])
        writer.writerow(["Reminders", len(read_json("reminders.json"))])
        writer.writerow(["Timetable", len(read_json("timetable.json"))])

    @after_this_request
    def _cleanup(response):
        try:
            os.remove(filepath)
        except OSError:
            pass
        return response

    return send_file(
        filepath,
        as_attachment=True,
        download_name="analytics_report.csv"
    )

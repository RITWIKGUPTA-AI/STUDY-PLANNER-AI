from datetime import datetime, timedelta


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _studied_dates(planner):
    """Set of dates where the user logged at least one planner session with duration > 0."""
    dates = set()
    for plan in planner:
        if not isinstance(plan, dict):
            continue
        try:
            duration = int(plan.get("duration", 0) or 0)
        except (ValueError, TypeError):
            duration = 0
        if duration <= 0:
            continue
        d = _parse_date(plan.get("date", ""))
        if d:
            dates.add(d)
    return dates


def compute_streak(planner):
    """
    Current consecutive-day study streak, based on real planner entries.
    Today doesn't break an existing streak if not logged yet — it only
    resets once a full day has passed with nothing logged.
    """
    dates = _studied_dates(planner)

    if not dates:
        return 0

    today = datetime.today().date()

    if today in dates:
        cursor = today
    elif (today - timedelta(days=1)) in dates:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


def compute_auto_achievements(tasks, planner, goals, attendance):
    """
    Rule-based achievements computed from the user's real, stored activity —
    unlike the old manual diary, these unlock/lock themselves automatically.
    Returns a list of {title, description, icon, unlocked} dicts.
    """

    completed_tasks = sum(
        1 for t in tasks if isinstance(t, dict) and t.get("status") == "Completed"
    )
    completed_goals = sum(
        1 for g in goals if isinstance(g, dict) and g.get("status") == "Completed"
    )

    total_minutes = 0
    for plan in planner:
        if isinstance(plan, dict):
            try:
                total_minutes += int(plan.get("duration", 0) or 0)
            except (ValueError, TypeError):
                pass
    total_hours = total_minutes / 60

    present = sum(1 for a in attendance if isinstance(a, dict) and a.get("status") == "Present")
    attendance_pct = (present * 100 / len(attendance)) if attendance else 0

    streak = compute_streak(planner)

    rules = [
        {
            "title": "First Step",
            "description": "Logged your first study session.",
            "icon": "🌱",
            "unlocked": len(planner) >= 1,
        },
        {
            "title": "3-Day Streak",
            "description": "Studied 3 days in a row.",
            "icon": "🔥",
            "unlocked": streak >= 3,
        },
        {
            "title": "7-Day Streak",
            "description": "Studied 7 days in a row.",
            "icon": "🔥",
            "unlocked": streak >= 7,
        },
        {
            "title": "30-Day Streak",
            "description": "Studied 30 days in a row.",
            "icon": "🏆",
            "unlocked": streak >= 30,
        },
        {
            "title": "Task Master",
            "description": "Completed 10 tasks.",
            "icon": "✅",
            "unlocked": completed_tasks >= 10,
        },
        {
            "title": "Task Champion",
            "description": "Completed 50 tasks.",
            "icon": "🏅",
            "unlocked": completed_tasks >= 50,
        },
        {
            "title": "Century Club",
            "description": "Logged 100 total study hours.",
            "icon": "💯",
            "unlocked": total_hours >= 100,
        },
        {
            "title": "Goal Getter",
            "description": "Completed 5 goals.",
            "icon": "🎯",
            "unlocked": completed_goals >= 5,
        },
        {
            "title": "Perfect Attendance",
            "description": "100% attendance across at least 5 records.",
            "icon": "📅",
            "unlocked": attendance_pct == 100 and len(attendance) >= 5,
        },
    ]

    return rules, streak

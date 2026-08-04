import json
import os
from flask import session, has_request_context

DATA_FOLDER = "data"

# These files are shared across the whole app (accounts, etc.) and are
# intentionally NOT split per student.
GLOBAL_FILES = {
    "students.json",
    "login.json",
    "exam_data.json",
    "password_resets.json",
    "support_tickets.json",
    "cbt_leaderboard.json",
}

# Personal files that hold a *list* of items per student (tasks, notes...).
# Anything not listed here that isn't global is treated as a per-user
# *dict* (e.g. profile.json, settings.json).
LIST_FILES = {
    "tasks.json",
    "notes.json",
    "goals.json",
    "subjects.json",
    "attendance.json",
    "timetable.json",
    "planner.json",
    "reminders.json",
    "achievements.json",
    "mistakes.json",
    "ai_history.json",
    "cbt_tests.json",
    "cbt_attempts.json",
}


def _current_user():
    """
    The key personal data is namespaced under. Falls back to "_guest" if
    called outside a logged-in request (shouldn't normally happen now that
    every route requires login, but this keeps read/write_json crash-proof).
    """
    if has_request_context():
        return session.get("username") or "_guest"
    return "_guest"


def _empty_default(filename):
    return [] if filename in LIST_FILES else {}


def read_json(filename):

    filepath = os.path.join(DATA_FOLDER, filename)

    if not os.path.exists(filepath):
        return _empty_default(filename)

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            raw = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return _empty_default(filename)
    except Exception:
        return _empty_default(filename)

    if filename in GLOBAL_FILES:
        return raw

    # Personal data is stored under a "_by_user" wrapper so every student
    # account gets its own tasks/notes/goals/etc. instead of one shared list.
    if isinstance(raw, dict) and "_by_user" in raw:
        return raw["_by_user"].get(_current_user(), _empty_default(filename))

    # A file from before per-user storage existed (a flat list/dict shared
    # by everyone). It gets replaced the first time this user saves new
    # data for this file — each account then starts with a clean slate.
    return _empty_default(filename)


def write_json(filename, data):

    filepath = os.path.join(DATA_FOLDER, filename)

    if filename in GLOBAL_FILES:
        try:
            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        except Exception as error:
            print(error)
        return

    # Load the existing per-user wrapper (if any) so we only overwrite the
    # current user's slice, leaving every other student's data untouched.
    wrapper = {"_by_user": {}}

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                existing = json.load(file)
            if isinstance(existing, dict) and "_by_user" in existing:
                wrapper = existing
        except Exception:
            pass

    wrapper["_by_user"][_current_user()] = data

    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(wrapper, file, indent=4)
    except Exception as error:
        print(error)


def delete_user_data(username):
    """
    Wipes one user's slice out of every per-user data file (tasks, notes,
    profile, settings, everything under a "_by_user" wrapper) and removes
    their entry from students.json. Used by account deletion — required
    for Play Store apps that support account creation.
    """
    if not username:
        return

    for filename in os.listdir(DATA_FOLDER):
        if not filename.endswith(".json") or filename in GLOBAL_FILES:
            continue

        filepath = os.path.join(DATA_FOLDER, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                raw = json.load(file)
        except Exception:
            continue

        if isinstance(raw, dict) and "_by_user" in raw and username in raw["_by_user"]:
            del raw["_by_user"][username]
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    json.dump(raw, file, indent=4)
            except Exception as error:
                print(error)

    students = read_json("students.json")
    if isinstance(students, list):
        students = [u for u in students if u.get("username", "").strip().lower() != username.strip().lower()]
        write_json("students.json", students)


def create_support_ticket(username, feature, description):
    from datetime import datetime
    import uuid

    tickets = read_json("support_tickets.json")
    if not isinstance(tickets, list):
        tickets = []

    ticket = {
        "id": uuid.uuid4().hex[:8],
        "username": username,
        "feature": feature,
        "description": description,
        "status": "open",  # open -> resolved, or open -> refunded
        "created_at": datetime.now().isoformat(),
    }

    tickets.append(ticket)
    write_json("support_tickets.json", tickets)
    return ticket["id"]


def get_support_tickets():
    tickets = read_json("support_tickets.json")
    return tickets if isinstance(tickets, list) else []


def update_ticket_status(ticket_id, status):
    tickets = get_support_tickets()
    for t in tickets:
        if t.get("id") == ticket_id:
            t["status"] = status
    write_json("support_tickets.json", tickets)


def create_reset_token(username):
    """Creates a random, single-use, 30-minute reset token for this user."""
    import secrets
    from datetime import datetime, timedelta

    tokens = read_json("password_resets.json")
    if not isinstance(tokens, dict):
        tokens = {}

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(minutes=30)).isoformat()

    tokens[token] = {"username": username, "expires_at": expires_at}
    write_json("password_resets.json", tokens)

    return token


def validate_reset_token(token):
    """Returns the username for a still-valid token, or None if it's missing/expired."""
    from datetime import datetime

    tokens = read_json("password_resets.json")
    if not isinstance(tokens, dict):
        return None

    entry = tokens.get(token)
    if not entry:
        return None

    try:
        expires_at = datetime.fromisoformat(entry["expires_at"])
    except (ValueError, KeyError):
        return None

    if datetime.now() > expires_at:
        return None

    return entry.get("username")


def consume_reset_token(token):
    """Deletes a token after it's been used, so it can't be replayed."""
    tokens = read_json("password_resets.json")
    if isinstance(tokens, dict) and token in tokens:
        del tokens[token]
        write_json("password_resets.json", tokens)





from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import uuid
from datetime import datetime
import json
from services.ai_service import solve_image
from dotenv import load_dotenv
load_dotenv()
from services.ai_service import ask_ai
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)
from services.ai_service import generate_revision_plan
from services.ai_service import analyze_weakness
from services.ai_service import exam_readiness
from utils.json_manager import (
    read_json,
    write_json,
    create_reset_token,
    validate_reset_token,
    consume_reset_token,
    create_support_ticket,
    get_support_tickets,
    update_ticket_status
)
from services.email_service import send_password_reset_email
from services.visual_aid_service import with_diagram_request, extract_diagram, build_illustration_url
from utils.helpers import get_current_date, get_current_time
from flask import request, render_template, redirect, url_for
from services.voice_service import speech_to_text
from services.pdf_service import extract_pdf_text
from services.ai_service import summarize_pdf
from services.ai_service import ask_voice_ai
from routes.subjects import subjects_bp
from routes.tasks import tasks_bp
from routes.planner import planner_bp
from routes.notes import notes_bp
from routes.goals import goals_bp
from routes.attendance import attendance_bp
from routes.timetable import timetable_bp
from routes.analytics import analytics_bp
from routes.settings import settings_bp
from routes.reminders import reminders_bp
from routes.profile import profile_bp
from routes.achievements import achievements_bp
from routes.backup import backup_bp
from routes.search import search_bp
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from services.ai_service import (
    generate_topic_quiz,
    generate_cbt_test,
    sanitize_test_for_client,
    evaluate_cbt_test,
    generate_scorecard_insights,
    EXAM_PATTERNS,
)
from services.ai_service import generate_flashcards
from services.ai_service import analyze_progress
from services.ai_service import generate_study_plan
from flask_compress import Compress

app = Flask(__name__)
Compress(app)


@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


# Changes every time the app starts, so browsers fetch fresh CSS/JS after
# a restart/deploy instead of serving a stale cached copy.
APP_VERSION = str(int(datetime.now().timestamp()))


@app.context_processor
def inject_app_version():
    return {"app_version": APP_VERSION}


@app.context_processor
def inject_is_admin():
    return {"is_admin_user": is_admin(session.get("username"))}


UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
PDF_FOLDER = "static/pdfs"

app.config["PDF_FOLDER"] = PDF_FOLDER

os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Reject uploads over 10MB outright (protects against disk/memory
# exhaustion from oversized PDF/image uploads).
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_PDF_EXTENSIONS = {"pdf"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def has_allowed_extension(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# Session cookie hardening: JS can never read the session cookie, it's
# never sent on cross-site requests, and (in production, behind HTTPS)
# it's only ever sent over an encrypted connection.
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"


@app.errorhandler(413)
def file_too_large(error):
    flash("That file is too large — please upload something under 10MB.", "danger")
    return redirect(request.referrer or url_for("dashboard")), 413



# Secret key
# IMPORTANT: set a real SECRET_KEY environment variable in production.
# Falling back to a hardcoded string would let anyone forge login sessions,
# so we generate a random one instead if it's missing (sessions just won't
# survive an app restart until you set a permanent one in your environment).
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

if not os.environ.get("SECRET_KEY"):
    print("WARNING: SECRET_KEY is not set. Using a temporary random key for "
          "this run — all users will be logged out on every restart. Set a "
          "permanent SECRET_KEY in your .env / hosting environment variables.")

# Admin — comma-separated usernames allowed to review support tickets and
# issue refunds. Set this in your .env, e.g. ADMIN_USERNAMES=yourusername
ADMIN_USERNAMES = {
    u.strip().lower()
    for u in os.environ.get("ADMIN_USERNAMES", "").split(",")
    if u.strip()
}

if not ADMIN_USERNAMES:
    print("WARNING: ADMIN_USERNAMES is not set. No one can access the "
          "/admin/tickets support dashboard until you set this in your "
          ".env, e.g. ADMIN_USERNAMES=yourusername")


def is_admin(username):
    return bool(username) and username.strip().lower() in ADMIN_USERNAMES


# --------------------------------------------------------------
# Minimal brute-force protection for /login. This is process-local
# (fine for a single-instance deployment); for multi-instance hosting,
# swap this for a shared store like Redis.
# --------------------------------------------------------------
_LOGIN_ATTEMPTS = {}
_LOGIN_MAX_ATTEMPTS = 8
_LOGIN_WINDOW_SECONDS = 60


def _is_rate_limited(ip):
    entry = _LOGIN_ATTEMPTS.get(ip)
    if not entry:
        return False
    count, first_seen = entry
    if datetime.now().timestamp() - first_seen > _LOGIN_WINDOW_SECONDS:
        return False
    return count >= _LOGIN_MAX_ATTEMPTS


def _record_failed_attempt(ip):
    now = datetime.now().timestamp()
    count, first_seen = _LOGIN_ATTEMPTS.get(ip, (0, now))
    if now - first_seen > _LOGIN_WINDOW_SECONDS:
        count, first_seen = 0, now
    _LOGIN_ATTEMPTS[ip] = (count + 1, first_seen)


def _clear_rate_limit(ip):
    _LOGIN_ATTEMPTS.pop(ip, None)

# Register Blueprints
app.register_blueprint(search_bp)
app.register_blueprint(subjects_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(achievements_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(planner_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(timetable_bp)
app.register_blueprint(analytics_bp)


# ===================================================
# Global login gate
# ---------------------------------------------------
# Previously, login checks were scattered per-route and most blueprint
# routes (tasks, notes, goals, subjects, attendance, timetable, planner,
# reminders, achievements, backup, profile, settings, search, analytics)
# and several app.py routes (dashboard, mistake-notebook, daily-coach,
# formula-sheet, competitive-ai, ai-quiz, ai-summarizer, voice-question)
# had NO login check at all — anyone could view or edit any data without
# logging in. Flask resolves the matching route before before_request
# handlers run, so a single hook here reliably protects every route,
# including all blueprints, without editing each one by hand.
# ===================================================

PUBLIC_ENDPOINTS = {
    "login",
    "register",
    "static",
    "logout",
    "dark_theme",
    "light_theme",
    "forgot_password",
    "reset_password",
    "privacy_policy",
    "terms",
    "refund_policy",
    "robots_txt",
    "sitemap_xml",
}

# Endpoints called via JS fetch() that expect a JSON response, not an
# HTML redirect, when login is required.
JSON_ENDPOINTS = {
    "ask_ai_api",
    "todays_reminders_api",
    "exam_hub_list",
    "exam_hub_pattern",
    "exam_hub_generate",
    "exam_hub_submit",
    "exam_hub_history",
}

# All AI-powered features are free and available to every logged-in user.
# (Premium gating has been removed — nothing in the app is paywalled anymore.)


@app.before_request
def require_login():

    if request.endpoint is None:
        return

    if request.endpoint in PUBLIC_ENDPOINTS:
        return

    if "username" not in session:

        if request.endpoint == "ask_ai_api":
            return jsonify({"answer": "Please log in again to use the AI Tutor."}), 401

        if request.endpoint in JSON_ENDPOINTS:
            return jsonify({"error": "Please log in again."}), 401

        flash("Please log in to continue.", "danger")
        return redirect(url_for("login"))


@app.route("/voice-question")
def voice_question():

    question = speech_to_text()

    if question == "":

        return render_template(

            "voice_ai.html",

            question="",

            answer="Could not recognize your voice."

        )

    answer = ask_voice_ai(question)

    return render_template(

        "voice_ai.html",

        question=question,

        answer=answer

    )
@app.route("/exam-readiness",methods=["GET","POST"])
def exam_readiness_page():

    if "username" not in session:
        return redirect(url_for("login"))

    report=""
    mermaid_code=""
    image_url=""

    if request.method=="POST":

        progress=request.form["progress"]

        revision=request.form["revision"]

        weakness=request.form["weakness"]

        mock=request.form["mock"]

        hours=request.form["hours"]

        exam=request.form.get("exam", "")

        if exam:
            progress += f"\n\nTarget Exam: {exam}"

        report, mermaid_code = exam_readiness(

            progress,

            revision,

            weakness,

            mock,

            hours

        )

        image_url = build_illustration_url(exam if exam else "exam readiness")

    return render_template(

        "exam_readiness.html",

        report=report,
        mermaid_code=mermaid_code,
        image_url=image_url

    )
@app.route("/ai-weakness", methods=["GET","POST"])
def ai_weakness():

    if "username" not in session:
        return redirect(url_for("login"))

    report=""
    mermaid_code=""
    image_url=""

    if request.method=="POST":

        quiz=request.form["quiz"]

        mock=request.form["mock"]

        tasks=request.form["tasks"]

        subjects=request.form["subjects"]

        exam=request.form.get("exam", "")

        if exam:
            subjects += f"\n\nTarget Exam: {exam}"

        report, mermaid_code = analyze_weakness(

            quiz,

            mock,

            tasks,

            subjects

        )

        image_url = build_illustration_url(subjects)

    return render_template(

        "ai_weakness.html",

        report=report,
        mermaid_code=mermaid_code,
        image_url=image_url

    )
@app.route("/ai-revision-planner", methods=["GET","POST"])
def ai_revision_planner():

    if "username" not in session:
        return redirect(url_for("login"))

    plan=""
    mermaid_code=""
    image_url=""

    if request.method=="POST":

        subjects=request.form.get("subjects")

        exam_date=request.form.get("exam_date")

        weak_topics=request.form.get("weak_topics")

        study_hours=request.form.get("study_hours")

        exam=request.form.get("exam", "")

        if exam:
            subjects = f"{subjects}\n\nTarget Exam: {exam}"

        plan, mermaid_code = generate_revision_plan(

            subjects,

            exam_date,

            weak_topics,

            study_hours

        )

        image_url = build_illustration_url(subjects)

    return render_template(

        "ai_revision_planner.html",

        plan=plan,
        mermaid_code=mermaid_code,
        image_url=image_url

    )
@app.route("/daily-coach", methods=["GET","POST"])
def daily_coach():

    plan = ""
    mermaid_code = ""
    image_url = ""

    if request.method == "POST":

        name = request.form.get("name")

        goal = request.form.get("goal")

        hours = request.form.get("hours")

        exam = request.form.get("exam", "")

        exam_line = f"\nTarget Exam:\n{exam}\n" if exam else ""

        prompt = f"""
You are a professional AI study mentor.

Student Name:
{name}

Today's Goal:
{goal}
{exam_line}
Available Study Hours:
{hours}

Generate:

1. Morning Study Plan

2. Afternoon Study Plan

3. Evening Study Plan

4. Revision

5. Break Timing

6. Motivation

Keep it easy to follow.
"""

        raw = ask_ai(with_diagram_request(prompt))
        plan, mermaid_code = extract_diagram(raw)
        image_url = build_illustration_url(goal)

    return render_template(
        "ai_daily_coach.html",
        plan=plan,
        mermaid_code=mermaid_code,
        image_url=image_url
    )
@app.route("/formula-sheet", methods=["GET","POST"])
def formula_sheet():

    result = ""
    mermaid_code = ""
    image_url = ""

    if request.method == "POST":

        subject = request.form.get("subject")

        chapter = request.form.get("chapter")

        exam = request.form.get("exam", "")

        exam_line = f"\nTarget Exam:\n{exam}\n" if exam else ""

        prompt = f"""
Create a complete revision sheet.

Subject:
{subject}

Chapter:
{chapter}
{exam_line}
Include:

1. Important formulas

2. Important concepts

3. Tricks

4. Short Notes

5. Common mistakes

6. Important Questions

7. Last minute revision tips

Use headings and bullet points.

"""

        raw = ask_ai(with_diagram_request(prompt))
        result, mermaid_code = extract_diagram(raw)
        image_url = build_illustration_url(f"{subject} {chapter}")

    return render_template(
        "ai_formula_sheet.html",
        result=result,
        mermaid_code=mermaid_code,
        image_url=image_url
    )
@app.route("/mistake-notebook", methods=["GET","POST"])
def mistake_notebook():

    mistakes = read_json("mistakes.json")

    if request.method == "POST":

        mistakes.append({

            "question": request.form.get("question"),

            "wrong_answer": request.form.get("wrong_answer"),

            "correct_answer": request.form.get("correct_answer"),

            "topic": request.form.get("topic")

        })

        write_json("mistakes.json", mistakes)

        flash("Mistake Saved Successfully!", "success")

        return redirect(url_for("mistake_notebook"))

    mistakes = read_json("mistakes.json")

    return render_template(

        "ai_mistake_notebook.html",

        mistakes=mistakes

    )
@app.route("/competitive-ai", methods=["GET", "POST"])
def competitive_ai():

    roadmap = ""
    mermaid_code = ""
    image_url = ""

    if request.method == "POST":

        exam = request.form.get("exam", "")

        level = request.form.get("level", "")

        hours = request.form.get("hours", "")

        weak = request.form.get("weak_subjects", "")
        prompt = f"""
You are India's best mentor for competitive exams.

Student Details

Exam : {exam}

Current Level : {level}

Daily Study Hours : {hours}

Weak Subjects :

{weak}

Prepare a COMPLETE PERSONALIZED STUDY ROADMAP.

Generate the response using headings.

Include:

1. Student Analysis

2. Current Preparation Level

3. Daily Study Timetable (Morning to Night)

4. Weekly Study Schedule

5. Monthly Roadmap

6. Subject-wise Priority

7. Chapter-wise Priority

8. Important Topics

9. NCERT Strategy

10. Best Books

11. Best YouTube Channels

12. Mock Test Plan

13. Revision Strategy

14. Common Mistakes

15. Time Management Tips

16. AIR Rank Strategy

17. Motivation

18. Final Success Tips

Make it detailed.

Use emojis.

Use bullet points.

Keep it beautifully formatted.

"""

        raw = ask_ai(with_diagram_request(prompt))
        roadmap, mermaid_code = extract_diagram(raw)
        image_url = build_illustration_url(exam if exam else "competitive exam preparation")

    return render_template(
        "competitive_exam_ai.html",
        roadmap=roadmap,
        mermaid_code=mermaid_code,
        image_url=image_url
    )
@app.route("/ai-study-plan", methods=["GET", "POST"])
def ai_study_plan():

    if "username" not in session:
        return redirect(url_for("login"))

    plan = ""
    mermaid_code = ""
    image_url = ""

    if request.method == "POST":

        subjects = request.form["subjects"]
        exam_date = request.form["exam_date"]
        study_hours = request.form["study_hours"]
        pending_tasks = request.form.get("pending_tasks", "")
        exam = request.form.get("exam", "")

        if exam:
            subjects = f"{subjects}\n\nTarget Exam: {exam}"

        plan, mermaid_code = generate_study_plan(
            subjects,
            exam_date,
            study_hours,
            pending_tasks
        )

        image_url = build_illustration_url(subjects)

    return render_template(
        "ai_study_plan.html",
        plan=plan,
        mermaid_code=mermaid_code,
        image_url=image_url
    )
@app.route("/ai-progress")
def ai_progress():

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    tasks = read_json("tasks.json")
    goals = read_json("goals.json")
    attendance = read_json("attendance.json")

    report = analyze_progress(
        tasks,
        goals,
        attendance
    )

    return render_template(
        "ai_progress.html",
        report=report
    )
@app.route("/ai-flashcards", methods=["GET","POST"])
def ai_flashcards():

    if "username" not in session:
        return redirect(url_for("login"))

    flashcards=""
    mermaid_code=""
    image_url=""

    if request.method=="POST":

        topic=request.form["topic"]

        exam=request.form.get("exam", "")

        if exam:
            topic = f"{topic} (Target Exam: {exam})"

        flashcards, mermaid_code = generate_flashcards(topic)
        image_url = build_illustration_url(topic)

    return render_template(

        "ai_flashcards.html",

        flashcards=flashcards,
        mermaid_code=mermaid_code,
        image_url=image_url

    )
@app.route("/ai-visual-explainer", methods=["GET", "POST"])
def ai_visual_explainer():

    explanation = ""
    mermaid_code = ""
    image_url = ""
    concept = ""

    if request.method == "POST":

        import re
        import urllib.parse

        concept = request.form.get("concept", "").strip()
        exam = request.form.get("exam", "")

        exam_line = f" for a student preparing for {exam}" if exam else ""

        prompt = f"""
You are an expert visual teacher explaining concepts to students{exam_line}.

Concept: {concept}

Respond in exactly this structure:

1. A clear, simple explanation (3-6 sentences, easy to follow).

2. A Mermaid.js diagram that visually represents the structure, process, or
relationships in this concept (use flowchart TD, or mindmap, whichever
fits best). Wrap ONLY the diagram code in a fenced code block starting
with ```mermaid and ending with ```. Keep node labels short (2-5 words).
Do not include any explanation inside the code block, only valid Mermaid
syntax.
"""

        raw = ask_ai(prompt)

        # Pull the fenced ```mermaid ... ``` block out of the AI's answer,
        # and treat everything else as the plain-text explanation.
        match = re.search(r"```mermaid\s*(.*?)```", raw, re.DOTALL)

        if match:
            mermaid_code = match.group(1).strip()
            explanation = (raw[:match.start()] + raw[match.end():]).strip()
        else:
            explanation = raw

        # Illustrative image via Pollinations (free, no API key required —
        # see https://pollinations.ai). This calls out to a third-party
        # service each time the page loads the <img>, so image quality/
        # uptime depends on their free tier, not on us.
        image_prompt = f"educational illustration of {concept}, colorful, clear, digital art, for students"
        image_url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(image_prompt)

    return render_template(
        "ai_visual_explainer.html",
        explanation=explanation,
        mermaid_code=mermaid_code,
        image_url=image_url,
        concept=concept
    )

@app.route("/ai-mock-test")
def ai_mock_test():

    if "username" not in session:
        return redirect(url_for("login"))

    exam_summaries = {}
    for key, info in EXAM_PATTERNS.items():
        total_questions = sum(s.get("mcq_count", 0) + s.get("numerical_count", 0) for s in info["sections"])
        total_marks = sum(
            (s.get("mcq_count", 0) + s.get("numerical_count", 0)) * s["marks_correct"]
            for s in info["sections"]
        )
        exam_summaries[key] = {
            "name": info["name"],
            "full_name": info.get("full_name"),
            "conducting_body": info.get("conducting_body"),
            "duration_minutes": info["duration_minutes"],
            "sections": info["sections"],
            "total_questions": total_questions,
            "total_marks": round(total_marks, 2),
            "syllabus_note": info.get("syllabus_note"),
        }

    return render_template(
        "ai_mock_test.html",
        exams=exam_summaries
    )


@app.route("/api/exam-hub/list")
def exam_hub_list():

    if "username" not in session:
        return jsonify({"error": "Please log in again."}), 401

    return jsonify({key: info["name"] for key, info in EXAM_PATTERNS.items()})


@app.route("/api/exam-hub/history")
def exam_hub_history():

    if "username" not in session:
        return jsonify({"error": "Please log in again."}), 401

    attempts = read_json("cbt_attempts.json")
    if not isinstance(attempts, list):
        attempts = []

    by_exam = {}
    for a in attempts:
        by_exam.setdefault(a["exam_key"], []).append({
            "date": a["date"],
            "marks_obtained": a["marks_obtained"],
            "max_marks": a["max_marks"],
            "percentage": a["percentage"],
            "percentile": a["percentile"],
            "predicted_rank": a["predicted_rank"],
        })

    summary = {}
    for exam_key, records in by_exam.items():
        records_sorted = sorted(records, key=lambda r: r["date"])
        best = max(records_sorted, key=lambda r: r["percentage"])
        summary[exam_key] = {
            "attempts_count": len(records_sorted),
            "best_percentage": best["percentage"],
            "latest_percentage": records_sorted[-1]["percentage"],
            "history": records_sorted[-10:],  # most recent 10 for the trend view
        }

    return jsonify(summary)


@app.route("/api/exam-hub/pattern/<exam_key>")
def exam_hub_pattern(exam_key):

    if "username" not in session:
        return jsonify({"error": "Please log in again."}), 401

    info = EXAM_PATTERNS.get(exam_key.upper())
    if not info:
        return jsonify({"error": "Unknown exam."}), 404

    total_questions = sum(s.get("mcq_count", 0) + s.get("numerical_count", 0) for s in info["sections"])
    total_marks = sum(
        (s.get("mcq_count", 0) + s.get("numerical_count", 0)) * s["marks_correct"]
        for s in info["sections"]
    )

    return jsonify({
        "exam_key": exam_key.upper(),
        "name": info["name"],
        "full_name": info.get("full_name"),
        "conducting_body": info.get("conducting_body"),
        "duration_minutes": info["duration_minutes"],
        "sections": info["sections"],
        "total_questions": total_questions,
        "total_marks": round(total_marks, 2),
        "candidate_pool": info.get("candidate_pool"),
        "syllabus_note": info.get("syllabus_note"),
    })


@app.route("/api/exam-hub/generate", methods=["POST"])
def exam_hub_generate():

    if "username" not in session:
        return jsonify({"error": "Please log in again."}), 401

    data = request.get_json(silent=True) or {}
    exam_key = (data.get("exam_key") or "").upper()

    if exam_key not in EXAM_PATTERNS:
        return jsonify({"error": "Unknown exam."}), 400

    # There's no limit on how many mock tests a student can take for an
    # exam — every "Start Test" click generates a brand new AI paper. To
    # keep unlimited retakes actually useful (not the same ground every
    # time), steer this fresh generation away from topics covered in the
    # student's last couple of attempts on this exam.
    attempts = read_json("cbt_attempts.json")
    if not isinstance(attempts, list):
        attempts = []
    recent_for_exam = [a for a in attempts if a.get("exam_key") == exam_key][-2:]
    avoid_topics = []
    for a in recent_for_exam:
        avoid_topics.extend(a.get("topics_covered", []))

    test = generate_cbt_test(exam_key, avoid_topics=avoid_topics)

    if test.get("error"):
        return jsonify({"error": test.get("message", "Could not generate the test.")}), 502

    # Keep the answer key server-side only, one active generated paper per
    # exam per user (retaking the same exam replaces its own slot — this
    # only caps how many *answer keys* we cache at once, not how many
    # tests a student can take).
    saved_tests = read_json("cbt_tests.json")
    if not isinstance(saved_tests, list):
        saved_tests = []
    saved_tests = [t for t in saved_tests if t.get("exam_key") != exam_key]
    saved_tests.append(test)
    saved_tests = saved_tests[-8:]
    write_json("cbt_tests.json", saved_tests)

    return jsonify(sanitize_test_for_client(test))


@app.route("/api/exam-hub/submit", methods=["POST"])
def exam_hub_submit():

    if "username" not in session:
        return jsonify({"error": "Please log in again."}), 401

    data = request.get_json(silent=True) or {}
    test_id = data.get("test_id")
    answers = data.get("answers") or {}
    marked_ids = data.get("marked_for_review") or []
    total_time_seconds = data.get("total_time_seconds")

    saved_tests = read_json("cbt_tests.json")
    if not isinstance(saved_tests, list):
        saved_tests = []

    test = next((t for t in saved_tests if t.get("test_id") == test_id), None)
    if not test:
        return jsonify({"error": "This test has expired. Please generate a new one."}), 404

    # Blend this score into the exam's leaderboard for a more accurate,
    # crowd-informed percentile as more people attempt it.
    leaderboard = read_json("cbt_leaderboard.json")
    if not isinstance(leaderboard, dict):
        leaderboard = {}
    historical_percentages = leaderboard.get(test["exam_key"], [])

    scorecard = evaluate_cbt_test(
        test,
        answers,
        marked_ids=marked_ids,
        total_time_seconds=total_time_seconds,
        historical_percentages=historical_percentages
    )

    historical_percentages.append(scorecard["percentage"])
    leaderboard[test["exam_key"]] = historical_percentages[-500:]
    write_json("cbt_leaderboard.json", leaderboard)

    insights = generate_scorecard_insights(test["exam_name"], scorecard)
    scorecard["ai_insights"] = insights

    # Save a lightweight attempt record (no full question text) for
    # unlimited-history progress tracking, plus the topics covered so the
    # *next* attempt on this exam can avoid repeating them.
    attempts = read_json("cbt_attempts.json")
    if not isinstance(attempts, list):
        attempts = []
    topics_covered = list(dict.fromkeys(
        q.get("topic") for q in test["questions"] if q.get("topic")
    ))
    attempts.append({
        "test_id": scorecard["test_id"],
        "exam_key": scorecard["exam_key"],
        "exam_name": scorecard["exam_name"],
        "marks_obtained": scorecard["marks_obtained"],
        "max_marks": scorecard["max_marks"],
        "percentage": scorecard["percentage"],
        "percentile": scorecard["percentile"],
        "predicted_rank": scorecard["predicted_rank"],
        "date": datetime.now().isoformat(),
        "topics_covered": topics_covered,
    })
    # Keep a generous history (unlimited retakes deserve a real progress
    # trail) while still bounding file growth.
    write_json("cbt_attempts.json", attempts[-300:])

    return jsonify(scorecard)


@app.route("/ai-pdf", methods=["GET", "POST"])
def ai_pdf():

    if "username" not in session:
        return redirect(url_for("login"))

    summary = ""

    filename = ""

    mermaid_code = ""

    image_url = ""

    if request.method == "POST":

        pdf = request.files.get("pdf")

        if pdf and pdf.filename != "":

            if not has_allowed_extension(pdf.filename, ALLOWED_PDF_EXTENSIONS):
                flash("Please upload a valid PDF file.", "danger")
                return redirect(url_for("ai_pdf"))

            original_name = secure_filename(pdf.filename)
            filename = f"{uuid.uuid4().hex}.pdf"

            filepath = os.path.join(

                app.config["PDF_FOLDER"],
                filename

            )

            pdf.save(filepath)

            try:
                text = extract_pdf_text(filepath)

                summary, mermaid_code = summarize_pdf(text)
            finally:
                # This file is only ever used to extract text for the AI
                # summary above — nothing links back to it afterwards, so
                # don't leave it sitting in a publicly-servable static
                # folder (or accumulating on disk) once we're done with it.
                if os.path.exists(filepath):
                    os.remove(filepath)

            image_url = build_illustration_url(original_name.rsplit(".", 1)[0])

    return render_template(

        "ai_pdf.html",

        summary=summary,

        filename=filename,

        mermaid_code=mermaid_code,

        image_url=image_url

    )
@app.route("/ai-image", methods=["GET", "POST"])
def ai_image():

    if "username" not in session:
        return redirect(url_for("login"))

    answer = ""

    image_path = ""

    if request.method == "POST":

        file = request.files.get("image")

        if file and file.filename != "":

            if not has_allowed_extension(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash("Please upload a valid image (PNG, JPG, JPEG, WEBP, or GIF).", "danger")
                return redirect(url_for("ai_image"))

            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"

            filepath = os.path.join(

                app.config["UPLOAD_FOLDER"],
                filename

            )

            file.save(filepath)

            image_path = filepath

            try:
                answer = solve_image(filepath)
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)

    return render_template(

        "ai_image.html",

        answer=answer,

        image=image_path

    )
@app.route("/dark-theme")
def dark_theme():

    session["theme"] = "dark"

    return redirect(request.referrer or url_for("dashboard"))


@app.route("/light-theme")
def light_theme():

    session["theme"] = "light"

    return redirect(request.referrer or url_for("dashboard"))
@app.route("/ai-quiz", methods=["GET", "POST"])
def ai_quiz():

    quiz = ""
    mermaid_code = ""
    image_url = ""

    if request.method == "POST":

        topic = request.form["topic"]

        exam = request.form.get("exam", "")

        quiz, mermaid_code = generate_topic_quiz(
            subject=exam if exam else "General",
            topic=topic,
            difficulty="Medium",
            questions=10
        )

        image_url = build_illustration_url(topic)

    return render_template(
        "ai_quiz.html",
        quiz=quiz,
        mermaid_code=mermaid_code,
        image_url=image_url
    )
@app.route("/ai-summarizer", methods=["GET", "POST"])
def ai_summarizer():

    summary = ""
    mermaid_code = ""
    image_url = ""

    if request.method == "POST":

        notes = request.form["notes"]

        prompt = f"""
Summarize the following notes into short, exam-ready bullet points.
Highlight key terms and important facts.

Notes:
{notes}
"""

        raw = ask_ai(with_diagram_request(prompt))
        summary, mermaid_code = extract_diagram(raw)
        image_url = build_illustration_url(notes[:100])

    return render_template(
        "ai_summarizer.html",
        summary=summary,
        mermaid_code=mermaid_code,
        image_url=image_url
    )


    
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        username = request.form["username"].strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")

        if not email:
            flash("Email is required (used for password recovery).", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        users = read_json("students.json")


        # check duplicate username (case-insensitive so "Sam" and "sam" can't both register)

        for user in users:

            if user.get("username", "").strip().lower() == username.lower():

                flash("Username already exists", "danger")

                return redirect(
                    url_for("register")
                )


        new_user = {

            "name": name,
            "username": username,
            "email": email,
            "password": generate_password_hash(password),
            "tasks": [],
            "notes": [],
            "goals": []

        }


        users.append(new_user)


        write_json(
            "students.json",
            users
        )


        flash("Account created successfully. Login now.", "success")

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# --------------------------------
# Login
# --------------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        client_ip = request.remote_addr or "unknown"
        if _is_rate_limited(client_ip):
            flash("Too many login attempts. Please wait a minute and try again.", "danger")
            return render_template("login.html", register_available=True)

        users = read_json("students.json")

        for user in users:

            if user.get("username", "").strip().lower() != username.lower():
                continue

            stored_password = user.get("password", "")

            # Hashed passwords always start with a method prefix like
            # "pbkdf2:" or "scrypt:". Older accounts created before this
            # fix was applied may still have a plaintext password stored —
            # support both so nobody gets locked out of an existing account.
            is_hashed = stored_password.startswith(("pbkdf2:", "scrypt:"))

            if is_hashed:
                password_ok = check_password_hash(stored_password, password)
            else:
                password_ok = (stored_password == password)

            if password_ok:

                # Auto-upgrade legacy plaintext passwords to a hash
                # the next time that user logs in successfully.
                if not is_hashed:
                    user["password"] = generate_password_hash(password)
                    write_json("students.json", users)

                _clear_rate_limit(client_ip)
                session["username"] = user.get("username")
                session["name"] = user.get("name")

                return redirect(url_for("dashboard"))

        _record_failed_attempt(client_ip)
        flash("Invalid username or password", "danger")

    return render_template("login.html", register_available=True)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        identifier = request.form.get("identifier", "").strip().lower()

        users = read_json("students.json")

        matched_user = None
        for user in users:
            if (
                user.get("username", "").strip().lower() == identifier
                or user.get("email", "").strip().lower() == identifier
            ):
                matched_user = user
                break

        # Always show the same message whether or not the account exists —
        # otherwise this form could be used to check which usernames/emails
        # are registered.
        generic_message = (
            "If an account with that username/email exists, we've sent a "
            "password reset link to its registered email."
        )

        if matched_user and matched_user.get("email"):

            token = create_reset_token(matched_user["username"])
            reset_url = url_for("reset_password", token=token, _external=True)

            send_password_reset_email(
                matched_user["email"],
                matched_user["username"],
                reset_url
            )

        flash(generic_message, "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    username = validate_reset_token(token)

    if not username:
        flash("This password reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("reset_password.html", token=token)

        users = read_json("students.json")

        for user in users:
            if user.get("username", "").strip().lower() == username.lower():
                user["password"] = generate_password_hash(password)
                break

        write_json("students.json", users)
        consume_reset_token(token)

        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)

# Dashboard
# --------------------------------
@app.route("/dashboard")
def dashboard():

    from utils.json_manager import read_json
    from datetime import datetime

    subjects = read_json("subjects.json")
    tasks = read_json("tasks.json")
    notes = read_json("notes.json")
    goals = read_json("goals.json")
    reminders = read_json("reminders.json")
    timetable = read_json("timetable.json")
    attendance = read_json("attendance.json")
    planner = read_json("planner.json")
    profile = read_json("profile.json")

    today = datetime.now().strftime("%Y-%m-%d")

    # Today's reminders
    todays_reminders = []

    for reminder in reminders:
        if reminder.get("date") == today:
            todays_reminders.append(reminder)

    # Today's timetable
    day_name = datetime.now().strftime("%A")

    todays_classes = []

    for entry in timetable:
        if entry.get("day") == day_name:
            todays_classes.append(entry)

    # Attendance %

    total_classes = len(attendance)

    present = 0

    for item in attendance:
        if item.get("status") == "Present":
            present += 1

    attendance_percent = 0

    if total_classes > 0:
        attendance_percent = round((present / total_classes) * 100)

    completed_goals = 0

    for goal in goals:
        if goal.get("status") == "Completed":
            completed_goals += 1
    # Recent Tasks

    recent_tasks = tasks[-5:]

    # Recent Notes

    recent_notes = notes[-5:]
    quotes = [

        "Success is the sum of small efforts repeated every day.",

        "Discipline beats motivation.",

        "Dream big. Start small. Act now.",

        "Stay focused and never give up.",

        "Today's preparation is tomorrow's success.",

        "Consistency creates excellence.",

        "Every study session brings you closer to your goal."

    ]

    import random

    quote = random.choice(quotes)

    from services.gamification_service import compute_streak
    from routes.analytics import _real_weekly_study_hours

    streak = compute_streak(planner)
    weekly_labels, weekly_hours = _real_weekly_study_hours(planner)

    return render_template(

        "dashboard.html",

        current_date=get_current_date(),

        current_time=get_current_time(),
        quote=quote,

        study_hours=weekly_hours,

        study_days=weekly_labels,

        streak=streak,

        subjects=len(subjects),

        tasks=len(tasks),

        notes=len(notes),

        goals=len(goals),
        recent_tasks=recent_tasks,

        recent_notes=recent_notes,

        reminders=len(reminders),

        timetable=len(timetable),

        planner=len(planner),

        attendance=len(attendance),

        attendance_percent=attendance_percent,

        completed_goals=completed_goals,

        todays_reminders=todays_reminders,

        todays_classes=todays_classes,

        profile=profile

    )
# ===================================================
# AI Chat API
# (ask_ai is imported from services.ai_service above —
#  do not redefine it here, it previously shadowed the
#  working import and called an undefined function)
# ===================================================

@app.route("/ai-tutor", methods=["GET", "POST"])
def ai_tutor():

    if "username" not in session:
        return redirect(url_for("login"))

    answer = ""

    if request.method == "POST":

        question = request.form.get("question")

        if question:

            answer = ask_ai(question)

    return render_template(
        "ai_tutor.html",
        answer=answer
    )


@app.route("/ask-ai", methods=["POST"])
def ask_ai_api():

    if "username" not in session:
        return jsonify({"answer": "Please log in again to use the AI Tutor."}), 401

    data = request.get_json(silent=True) or {}

    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"answer": "Please type a question first."}), 400

    raw = ask_ai(with_diagram_request(question))
    answer, mermaid_code = extract_diagram(raw)
    image_url = build_illustration_url(question[:120])

    return jsonify({
        "answer": answer,
        "mermaid_code": mermaid_code,
        "image_url": image_url
    })

# Premium subscriptions have been removed — every feature is free for
# every signed-in user. These routes are kept only so any old bookmarks
# or links to them don't break; they just send people to the dashboard.
@app.route("/premium")
@app.route("/buy-premium")
def premium():

    if "username" not in session:
        return redirect(url_for("login"))

    flash("Good news — every feature is free now, no subscription needed!", "success")
    return redirect(url_for("dashboard"))


# ===================================================
# Support Tickets — AI feature issue reporting
# ---------------------------------------------------
# Flow: a user reports a broken feature -> an admin reviews it in
# /admin/tickets and marks it "Resolved" once it's fixed.
# ===================================================

@app.route("/report-issue", methods=["GET", "POST"])
def report_issue():

    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        feature = request.form.get("feature", "").strip()
        description = request.form.get("description", "").strip()

        if not feature or not description:
            flash("Please select a feature and describe the issue.", "danger")
            return redirect(url_for("report_issue"))

        ticket_id = create_support_ticket(session["username"], feature, description)

        flash(
            f"Issue reported (ticket #{ticket_id}). We'll review it and "
            f"get back to you.",
            "success"
        )
        return redirect(url_for("my_tickets"))

    return render_template("report_issue.html")


@app.route("/my-tickets")
def my_tickets():

    if "username" not in session:
        return redirect(url_for("login"))

    all_tickets = get_support_tickets()
    my_own = [t for t in all_tickets if t.get("username") == session["username"]]
    my_own.sort(key=lambda t: t.get("created_at", ""), reverse=True)

    return render_template("my_tickets.html", tickets=my_own)


@app.route("/admin/tickets")
def admin_tickets():

    if "username" not in session or not is_admin(session["username"]):
        flash("Admin access only.", "danger")
        return redirect(url_for("dashboard"))

    all_tickets = get_support_tickets()
    all_tickets.sort(key=lambda t: t.get("created_at", ""), reverse=True)

    return render_template("admin_tickets.html", tickets=all_tickets)


@app.route("/admin/tickets/<ticket_id>/resolve", methods=["POST"])
def admin_resolve_ticket(ticket_id):

    if "username" not in session or not is_admin(session["username"]):
        flash("Admin access only.", "danger")
        return redirect(url_for("dashboard"))

    update_ticket_status(ticket_id, "resolved")
    flash(f"Ticket #{ticket_id} marked as resolved.", "success")
    return redirect(url_for("admin_tickets"))


# Logout
# --------------------------------
@app.route("/api/todays-reminders")
def todays_reminders_api():

    if "username" not in session:
        return jsonify({"reminders": []}), 401

    reminders = read_json("reminders.json")

    today = datetime.now().strftime("%Y-%m-%d")

    due_today = [
        r for r in reminders
        if isinstance(r, dict) and r.get("date") == today
    ]

    return jsonify({"reminders": due_today})


@app.route("/robots.txt")
def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /$",
        "Allow: /login",
        "Allow: /register",
        "Allow: /privacy-policy",
        "Allow: /terms",
        "Allow: /refund-policy",
        # Everything else needs a login and has nothing useful to index —
        # keep crawlers out of it rather than wasting crawl budget.
        "Disallow: /dashboard",
        "Disallow: /api/",
        "Disallow: /ai-",
        "Disallow: /backup",
        "Disallow: /admin",
        "Disallow: /settings",
        "Disallow: /profile",
        f"Sitemap: {request.url_root.rstrip('/')}/sitemap.xml",
    ]
    return app.response_class("\n".join(lines), mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    base = request.url_root.rstrip("/")
    public_paths = ["/", "/login", "/register", "/privacy-policy", "/terms", "/refund-policy"]

    urls = "\n".join(
        f"  <url><loc>{base}{path}</loc></url>" for path in public_paths
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>"
    )
    return app.response_class(xml, mimetype="application/xml")


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy_policy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/refund-policy")
def refund_policy():
    return render_template("refund_policy.html")


@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


# --------------------------------
# Run Application
# --------------------------------
if __name__ == "__main__":
    # Debug mode must never be on in production — it exposes a remote code
    # execution console (the Werkzeug debugger) to anyone who can trigger
    # an unhandled exception. Set FLASK_DEBUG=1 locally if you need it.
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug_mode)
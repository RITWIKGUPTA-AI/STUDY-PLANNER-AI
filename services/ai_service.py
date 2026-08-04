import os
import json
import random
import base64
import math
import uuid
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from services.visual_aid_service import with_diagram_request, extract_diagram

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY is not set. AI features will not work "
          "until it is added to your .env file or hosting environment variables.")

# Use a placeholder so the Groq() constructor itself doesn't crash the whole
# app on import when the key is missing. Calls will still fail gracefully
# with a clear message (see the try/except blocks below) instead of crashing
# at startup.
client = Groq(api_key=GROQ_API_KEY or "missing-api-key")

def generate_ai_response(prompt):

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AI Study Assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.7,
            max_tokens=4096

        )

        return response.choices[0].message.content

    except Exception as e:

        print("\n========== GROQ ERROR ==========")
        print(e)
        print("================================\n")

        return f"AI Error: {e}"
def analyze_progress(tasks, goals, attendance):

    prompt = f"""
You are an AI Study Mentor.

Analyze this student's progress.

Tasks:
{tasks}

Goals:
{goals}

Attendance:
{attendance}

Generate:

1. Overall Progress (%)

2. Study Consistency

3. Strong Subjects

4. Weak Subjects

5. Improvement Suggestions

6. Estimated Exam Readiness Score (0-100)

7. Daily Study Recommendation

Use simple language.
"""

    return generate_ai_response(prompt)
def generate_study_plan(subjects, exam_date, study_hours, pending_tasks):

    prompt = f"""
You are an expert study coach.

Create a personalized study timetable.

Subjects:
{subjects}

Exam Date:
{exam_date}

Available Study Hours:
{study_hours}

Pending Tasks:
{pending_tasks}

Generate:

1. Today's Schedule

2. Subject Order

3. Revision Time

4. Breaks

5. Daily Target

6. Motivation Tip

Format nicely.
"""

    return extract_diagram(generate_ai_response(with_diagram_request(prompt)))
def generate_revision_plan(
    subjects,
    exam_date,
    weak_topics,
    study_hours
):

    prompt = f"""
You are an expert study coach.

Create a smart revision timetable.

Subjects:
{subjects}

Exam Date:
{exam_date}

Weak Topics:
{weak_topics}

Available Study Hours:
{study_hours}

Generate:

1. Daily Revision Plan

2. Weekly Revision Plan

3. Monthly Revision Plan

4. Important Chapters

5. Formula Revision

6. Mock Test Schedule

7. Final 7-Day Crash Plan

8. Motivation Tip

Make the timetable easy to follow.
"""

    return extract_diagram(generate_ai_response(with_diagram_request(prompt)))
def analyze_weakness(
    quiz_results,
    mock_results,
    completed_tasks,
    subjects
):

    prompt = f"""
You are an expert academic mentor.

Analyze this student's performance.

Quiz Results:
{quiz_results}

Mock Test Results:
{mock_results}

Completed Tasks:
{completed_tasks}

Subjects:
{subjects}

Generate a report with:

1. Overall Performance

2. Strong Subjects

3. Weak Subjects

4. Weak Chapters

5. Accuracy %

6. Suggested Study Hours

7. Priority Chapters

8. Next 7-Day Improvement Plan

9. Recommended Mock Tests

10. Motivation Message

Write in a neat format.
"""

    return extract_diagram(generate_ai_response(with_diagram_request(prompt)))
def exam_readiness(
        progress,
        revision,
        weakness,
        mock_score,
        study_hours):

    prompt = f"""
You are an expert educational AI.

Analyze this student.

Progress:
{progress}

Revision Plan:
{revision}

Weakness Report:
{weakness}

Latest Mock Score:
{mock_score}

Daily Study Hours:
{study_hours}

Generate a professional dashboard.

Include:

Overall Exam Readiness Score (0-100)

Confidence Level

Strong Subjects

Weak Subjects

Most Important Chapters

Revision Status

Predicted Performance

Daily Target

Weekly Goal

Suggested Mock Test

Motivational Message

Use headings.
"""

    return extract_diagram(generate_ai_response(with_diagram_request(prompt)))
def summarize_pdf(text):

    prompt = f"""
You are an expert teacher.

Read the following study material.

1. Give an easy summary.
2. Highlight important concepts.
3. List important formulas.
4. Give revision tips.

{text[:15000]}
"""

    return extract_diagram(generate_ai_response(with_diagram_request(prompt)))
def generate_flashcards(topic):

    prompt = f"""
You are an expert teacher.

Create 25 revision flashcards for:

{topic}

Rules:

Question:
Answer:

Keep answers short.

Highlight important formulas where needed.

Make them suitable for JEE, NEET and Boards.
"""

    return extract_diagram(generate_ai_response(with_diagram_request(prompt)))
def generate_topic_quiz(subject, topic, difficulty, questions):

    prompt = f"""
You are an expert quiz creator.

Create a {difficulty} difficulty quiz on the topic: {topic}
{f"Tailor it for the {subject} exam pattern and style." if subject and subject != "General" else ""}

Number of Questions: {questions}

For each question:
1. Write the question clearly.
2. Give 4 options (A, B, C, D).
3. Mark the correct answer.
4. Give a one-line explanation.

Format neatly with numbering.
"""

    return extract_diagram(generate_ai_response(with_diagram_request(prompt)))
# ===================================================================
# CBT Exam Simulator — official-pattern mock tests for the
# Competitive Exam Hub (JEE Main, NEET, UPSC, GATE, CAT, CUET, SSC,
# Banking). Each entry mirrors the exam's real section layout,
# question mix (MCQ / Numerical), marking scheme, duration, and an
# approximate candidate pool used for percentile/rank estimation.
# ===================================================================
EXAM_PATTERNS = {
    "JEE_MAIN": {
        "name": "JEE Main",
        "full_name": "Joint Entrance Examination (Main) — Paper 1, B.E./B.Tech",
        "conducting_body": "National Testing Agency (NTA)",
        "duration_minutes": 180,
        "sections": [
            {"name": "Physics", "mcq_count": 20, "numerical_count": 5, "marks_correct": 4, "marks_wrong_mcq": 1, "marks_wrong_numerical": 1},
            {"name": "Chemistry", "mcq_count": 20, "numerical_count": 5, "marks_correct": 4, "marks_wrong_mcq": 1, "marks_wrong_numerical": 1},
            {"name": "Mathematics", "mcq_count": 20, "numerical_count": 5, "marks_correct": 4, "marks_wrong_mcq": 1, "marks_wrong_numerical": 1},
        ],
        "candidate_pool": 1200000,
        "mean_percentage": 32,
        "std_percentage": 15,
        "syllabus_note": "All 75 questions compulsory — Section B numericals are no longer optional (2025+ pattern) and now also carry negative marking."
    },
    "NEET": {
        "name": "NEET UG",
        "full_name": "National Eligibility cum Entrance Test — Undergraduate",
        "conducting_body": "National Testing Agency (NTA)",
        "duration_minutes": 180,
        "sections": [
            {"name": "Physics", "mcq_count": 45, "numerical_count": 0, "marks_correct": 4, "marks_wrong_mcq": 1},
            {"name": "Chemistry", "mcq_count": 45, "numerical_count": 0, "marks_correct": 4, "marks_wrong_mcq": 1},
            {"name": "Botany", "mcq_count": 45, "numerical_count": 0, "marks_correct": 4, "marks_wrong_mcq": 1},
            {"name": "Zoology", "mcq_count": 45, "numerical_count": 0, "marks_correct": 4, "marks_wrong_mcq": 1},
        ],
        "candidate_pool": 2200000,
        "mean_percentage": 38,
        "std_percentage": 17,
        "syllabus_note": "180 compulsory MCQs, no optional section (pre-COVID format restored)."
    },
    "UPSC": {
        "name": "UPSC CSE Prelims",
        "full_name": "Civil Services (Preliminary) Examination — General Studies Paper I",
        "conducting_body": "Union Public Service Commission (UPSC)",
        "duration_minutes": 120,
        "sections": [
            {"name": "General Studies", "mcq_count": 100, "numerical_count": 0, "marks_correct": 2, "marks_wrong_mcq": 0.66},
        ],
        "candidate_pool": 550000,
        "mean_percentage": 45,
        "std_percentage": 12,
        "syllabus_note": "Polity, Economy, History, Geography, Environment, Science & Current Affairs. 1/3rd negative marking."
    },
    "GATE": {
        "name": "GATE",
        "full_name": "Graduate Aptitude Test in Engineering",
        "conducting_body": "IISc / IITs (National Coordination Board)",
        "duration_minutes": 180,
        "sections": [
            {"name": "General Aptitude", "mcq_count": 10, "numerical_count": 0, "marks_correct": 1.5, "marks_wrong_mcq": 0.5},
            {"name": "Core Subject & Engineering Mathematics", "mcq_count": 45, "numerical_count": 10, "marks_correct": 1.5, "marks_wrong_mcq": 0.5, "marks_wrong_numerical": 0},
        ],
        "candidate_pool": 900000,
        "mean_percentage": 28,
        "std_percentage": 15,
        "syllabus_note": "65 questions, 100 marks. Mix of 1/2-mark MCQs and Numerical Answer Type (NAT has no negative marking)."
    },
    "CAT": {
        "name": "CAT",
        "full_name": "Common Admission Test",
        "conducting_body": "Indian Institutes of Management (IIM)",
        "duration_minutes": 120,
        "sections": [
            {"name": "VARC (Verbal Ability & Reading Comprehension)", "mcq_count": 19, "numerical_count": 5, "marks_correct": 3, "marks_wrong_mcq": 1, "marks_wrong_numerical": 0},
            {"name": "DILR (Data Interpretation & Logical Reasoning)", "mcq_count": 16, "numerical_count": 4, "marks_correct": 3, "marks_wrong_mcq": 1, "marks_wrong_numerical": 0},
            {"name": "QA (Quantitative Ability)", "mcq_count": 14, "numerical_count": 8, "marks_correct": 3, "marks_wrong_mcq": 1, "marks_wrong_numerical": 0},
        ],
        "candidate_pool": 300000,
        "mean_percentage": 35,
        "std_percentage": 15,
        "syllabus_note": "68 questions across 3 sections (sectional time limits apply in the real exam). TITA (non-MCQ) questions carry no negative marking."
    },
    "CUET": {
        "name": "CUET UG",
        "full_name": "Common University Entrance Test — Undergraduate (General Test)",
        "conducting_body": "National Testing Agency (NTA)",
        "duration_minutes": 60,
        "sections": [
            {"name": "General Test (Reasoning, GK & Numerical Ability)", "mcq_count": 50, "numerical_count": 0, "marks_correct": 5, "marks_wrong_mcq": 1},
        ],
        "candidate_pool": 1300000,
        "mean_percentage": 40,
        "std_percentage": 15,
        "syllabus_note": "General Test pattern simulated here; domain-subject papers instead follow the Class 12 NCERT syllabus."
    },
    "SSC": {
        "name": "SSC CGL",
        "full_name": "Staff Selection Commission — Combined Graduate Level, Tier I",
        "conducting_body": "Staff Selection Commission (SSC)",
        "duration_minutes": 60,
        "sections": [
            {"name": "General Intelligence & Reasoning", "mcq_count": 25, "numerical_count": 0, "marks_correct": 2, "marks_wrong_mcq": 0.5},
            {"name": "General Awareness", "mcq_count": 25, "numerical_count": 0, "marks_correct": 2, "marks_wrong_mcq": 0.5},
            {"name": "Quantitative Aptitude", "mcq_count": 25, "numerical_count": 0, "marks_correct": 2, "marks_wrong_mcq": 0.5},
            {"name": "English Comprehension", "mcq_count": 25, "numerical_count": 0, "marks_correct": 2, "marks_wrong_mcq": 0.5},
        ],
        "candidate_pool": 2500000,
        "mean_percentage": 42,
        "std_percentage": 14,
        "syllabus_note": "100 questions, 200 marks. -0.5 mark for every wrong answer."
    },
    "BANKING": {
        "name": "IBPS PO Prelims",
        "full_name": "Institute of Banking Personnel Selection — Probationary Officer, Prelims",
        "conducting_body": "IBPS",
        "duration_minutes": 60,
        "sections": [
            {"name": "English Language", "mcq_count": 30, "numerical_count": 0, "marks_correct": 1, "marks_wrong_mcq": 0.25},
            {"name": "Quantitative Aptitude", "mcq_count": 35, "numerical_count": 0, "marks_correct": 1, "marks_wrong_mcq": 0.25},
            {"name": "Reasoning Ability", "mcq_count": 35, "numerical_count": 0, "marks_correct": 1, "marks_wrong_mcq": 0.25},
        ],
        "candidate_pool": 2000000,
        "mean_percentage": 40,
        "std_percentage": 15,
        "syllabus_note": "100 questions, 100 marks. Real exam enforces 20-minute sectional timing."
    },
}


def _extract_json(raw):
    """Pulls a JSON array/object out of a raw AI response, tolerating code fences and stray text."""
    if not raw:
        raise ValueError("empty AI response")

    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    text = text.strip()

    starts = [i for i in (text.find("["), text.find("{")) if i != -1]
    if starts:
        text = text[min(starts):]

    return json.loads(text)


def _generate_question_batch(exam_name, section_name, qtype, count, marks_correct, marks_wrong, start_id, avoid_topics=None):
    """Asks the AI for `count` fresh questions of one type for one exam section."""
    if count <= 0:
        return []

    if qtype == "mcq":
        type_instructions = (
            'Multiple Choice Questions with exactly 4 options labelled A, B, C, D. '
            '"correct_answer" must exactly match one of the option strings.'
        )
        options_example = '["A) ...", "B) ...", "C) ...", "D) ..."]'
    else:
        type_instructions = (
            'Numerical Answer Type questions with NO options. '
            '"correct_answer" must be the final numeric value only (e.g. "12" or "3.5").'
        )
        options_example = "[]"

    avoid_line = ""
    if avoid_topics:
        sample = list(dict.fromkeys(avoid_topics))[:25]  # dedupe, cap prompt size
        avoid_line = (
            "\nThe student has already practiced these topics in recent attempts — "
            "cover DIFFERENT topics/chapters this time so every retake feels fresh:\n"
            + ", ".join(sample) + "\n"
        )

    prompt = f"""
You are an official question paper setter for {exam_name}.

Generate exactly {count} fresh, original, exam-standard questions for the section "{section_name}".

Question type: {type_instructions}

Rules:
- Match the real difficulty, phrasing style, and syllabus coverage of previous years' {exam_name} papers.
- Do not repeat questions or trivially rephrase the same concept twice.
- Give a short "topic" tag (2-4 words, the specific chapter/concept) per question, useful for analytics.
- Give a concise step-by-step "explanation" for the correct answer.
{avoid_line}
Return ONLY a valid JSON array, no markdown, no commentary:
[
  {{
    "question": "...",
    "options": {options_example},
    "correct_answer": "...",
    "topic": "...",
    "explanation": "..."
  }}
]
"""

    raw = generate_ai_response(prompt)

    try:
        data = _extract_json(raw)
    except Exception:
        raw = generate_ai_response(prompt + "\n\nReturn ONLY the JSON array. Nothing else.")
        try:
            data = _extract_json(raw)
        except Exception:
            data = []

    if not isinstance(data, list):
        data = []

    questions = []
    for q in data[:count]:
        if not isinstance(q, dict) or not q.get("question") or not q.get("correct_answer"):
            continue
        questions.append({
            "id": start_id + len(questions),
            "section": section_name,
            "type": qtype,
            "question": str(q.get("question", "")).strip(),
            "options": q.get("options") or [],
            "correct_answer": str(q.get("correct_answer", "")).strip(),
            "topic": q.get("topic", section_name),
            "explanation": q.get("explanation", "No explanation provided."),
            "marks_correct": marks_correct,
            "marks_wrong": marks_wrong,
        })

    return questions


def generate_cbt_test(exam_key, avoid_topics=None):
    """
    Builds a complete, official-pattern CBT mock test: every section, the
    exact official question mix (MCQ + Numerical), and the real marking
    scheme, generated fresh via AI in per-section batches for reliability.

    There's no cap on how many times this can be called for the same
    exam — every call is a brand new AI generation. `avoid_topics` (recent
    topics the student has already been tested on) steers the AI away
    from repeating the same ground on every retake, so unlimited practice
    attempts actually stay useful instead of getting repetitive.
    """
    exam_key = (exam_key or "").upper()
    info = EXAM_PATTERNS.get(exam_key)
    if not info:
        return {"error": True, "message": f"Unknown exam: {exam_key}"}

    all_questions = []
    section_meta = []
    next_id = 1
    BATCH_SIZE = 15

    for section in info["sections"]:
        for qtype, total_count in (("mcq", section.get("mcq_count", 0)), ("numerical", section.get("numerical_count", 0))):
            remaining = total_count
            while remaining > 0:
                batch_count = min(BATCH_SIZE, remaining)
                marks_wrong = section.get(
                    "marks_wrong_mcq" if qtype == "mcq" else "marks_wrong_numerical",
                    section.get("marks_wrong_mcq", 0)
                )
                batch = _generate_question_batch(
                    info["name"], section["name"], qtype, batch_count,
                    section["marks_correct"], marks_wrong, next_id,
                    avoid_topics=avoid_topics
                )
                all_questions.extend(batch)
                next_id += len(batch)
                remaining -= batch_count

        section_meta.append({
            "name": section["name"],
            "count": section.get("mcq_count", 0) + section.get("numerical_count", 0),
        })

    if not all_questions:
        return {"error": True, "message": "The AI service couldn't generate this test right now. Please try again."}

    test_id = uuid.uuid4().hex[:12]

    return {
        "test_id": test_id,
        "exam_key": exam_key,
        "exam_name": info["name"],
        "full_name": info.get("full_name", info["name"]),
        "duration_minutes": info["duration_minutes"],
        "total_questions": len(all_questions),
        "total_marks": round(sum(q["marks_correct"] for q in all_questions), 2),
        "sections": section_meta,
        "questions": all_questions,
        "generated_at": datetime.now().isoformat(),
    }


def sanitize_test_for_client(test):
    """Strips correct answers/explanations before sending a test to the browser."""
    return {
        "test_id": test["test_id"],
        "exam_key": test["exam_key"],
        "exam_name": test["exam_name"],
        "full_name": test.get("full_name"),
        "duration_minutes": test["duration_minutes"],
        "total_questions": test["total_questions"],
        "total_marks": test["total_marks"],
        "sections": test["sections"],
        "questions": [
            {
                "id": q["id"],
                "section": q["section"],
                "type": q["type"],
                "question": q["question"],
                "options": q["options"],
            }
            for q in test["questions"]
        ],
    }


def _normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _estimate_percentile_and_rank(exam_key, percentage, historical_percentages=None):
    info = EXAM_PATTERNS.get(exam_key, {})
    mean = info.get("mean_percentage", 40)
    std = info.get("std_percentage", 15) or 1
    candidate_pool = info.get("candidate_pool", 1000000)

    z = (percentage - mean) / std
    percentile = round(_normal_cdf(z) * 100, 2)

    if historical_percentages and len(historical_percentages) >= 5:
        below = sum(1 for p in historical_percentages if p <= percentage)
        empirical_percentile = round((below / len(historical_percentages)) * 100, 2)
        percentile = round((percentile + empirical_percentile) / 2, 2)

    percentile = max(0.1, min(99.99, percentile))
    predicted_rank = max(1, round(candidate_pool * (1 - percentile / 100)))

    return percentile, predicted_rank, candidate_pool


def evaluate_cbt_test(test, answers, marked_ids=None, total_time_seconds=None, historical_percentages=None):
    """Grades a submitted CBT attempt against the server-held answer key and builds the full scorecard."""
    marked_ids = set(str(m) for m in (marked_ids or []))
    answers = answers or {}

    section_stats = {}
    detailed = []
    correct = incorrect = unanswered = 0
    marks_obtained = 0.0

    for q in test["questions"]:
        qid = str(q["id"])
        user_ans = answers.get(qid)
        section = q["section"]
        stats = section_stats.setdefault(section, {"correct": 0, "incorrect": 0, "unanswered": 0, "marks": 0.0, "max_marks": 0.0})
        stats["max_marks"] += q["marks_correct"]

        if not user_ans:
            status = "unanswered"
            unanswered += 1
            stats["unanswered"] += 1
        else:
            is_correct = str(user_ans).strip().lower() == str(q["correct_answer"]).strip().lower()
            if is_correct:
                status = "correct"
                correct += 1
                marks_obtained += q["marks_correct"]
                stats["correct"] += 1
                stats["marks"] += q["marks_correct"]
            else:
                status = "incorrect"
                incorrect += 1
                marks_obtained -= q["marks_wrong"]
                stats["incorrect"] += 1
                stats["marks"] -= q["marks_wrong"]

        detailed.append({
            "id": q["id"],
            "section": section,
            "topic": q.get("topic"),
            "question": q["question"],
            "options": q.get("options"),
            "user_answer": user_ans or "Not Attempted",
            "correct_answer": q["correct_answer"],
            "status": status,
            "marked_for_review": qid in marked_ids,
            "explanation": q.get("explanation"),
        })

    total_questions = len(test["questions"])
    attempted = correct + incorrect
    max_marks = test["total_marks"]
    accuracy = round((correct / attempted) * 100, 2) if attempted else 0.0
    percentage = round((marks_obtained / max_marks) * 100, 2) if max_marks else 0.0
    percentage_clamped = max(0.0, min(100.0, percentage))

    percentile, predicted_rank, candidate_pool = _estimate_percentile_and_rank(
        test["exam_key"], percentage_clamped, historical_percentages
    )

    for stats in section_stats.values():
        stats["marks"] = round(stats["marks"], 2)
        stats["max_marks"] = round(stats["max_marks"], 2)

    return {
        "test_id": test["test_id"],
        "exam_key": test["exam_key"],
        "exam_name": test["exam_name"],
        "marks_obtained": round(marks_obtained, 2),
        "max_marks": round(max_marks, 2),
        "percentage": percentage_clamped,
        "accuracy": accuracy,
        "total_questions": total_questions,
        "attempted": attempted,
        "correct": correct,
        "incorrect": incorrect,
        "unanswered": unanswered,
        "marked_for_review_count": len(marked_ids),
        "section_stats": section_stats,
        "percentile": percentile,
        "predicted_rank": predicted_rank,
        "candidate_pool": candidate_pool,
        "total_time_seconds": total_time_seconds,
        "details": detailed,
    }


def generate_scorecard_insights(exam_name, scorecard):
    """AI mentor commentary generated from the graded scorecard (no question content needed)."""
    section_lines = "\n".join(
        f"- {name}: {stats['correct']} correct, {stats['incorrect']} incorrect, "
        f"{stats['unanswered']} unattempted, {stats['marks']}/{stats['max_marks']} marks"
        for name, stats in scorecard.get("section_stats", {}).items()
    )

    prompt = f"""
You are an expert exam mentor analyzing a student's {exam_name} mock test performance.

Score: {scorecard['marks_obtained']} / {scorecard['max_marks']} ({scorecard['percentage']}%)
Accuracy: {scorecard['accuracy']}%
Correct: {scorecard['correct']}  Incorrect: {scorecard['incorrect']}  Unattempted: {scorecard['unanswered']}
Estimated Percentile: {scorecard['percentile']}
Predicted Rank: ~{scorecard['predicted_rank']} out of {scorecard['candidate_pool']} candidates

Section-wise performance:
{section_lines}

Generate a short, encouraging but honest mentor report with:
1. Overall Verdict (1-2 lines)
2. Strongest Section
3. Weakest Section & why it's likely happening
4. Negative Marking Impact (was guessing costing marks?)
5. Top 3 Priority Topics to revise next
6. A focused 5-day improvement plan
7. One motivational line

Keep it concise, use headings, and speak directly to the student.
"""

    return generate_ai_response(prompt)
# AI Tutor
def solve_image(image_path):

    try:

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        ext = os.path.splitext(image_path)[1].lower().replace(".", "") or "png"
        if ext == "jpg":
            ext = "jpeg"

        prompt = """
You are an expert tutor.

Solve the question in this image step by step.

Explain everything in simple language.

Show every calculation.

Explain every concept.
"""

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{ext};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.4,
            max_tokens=4096,
        )

        return response.choices[0].message.content

    except Exception as e:

        print("\n========== GROQ IMAGE ERROR ==========")
        print(e)
        print("=======================================\n")

        return f"AI Error: {e}"
def ask_ai(question):

    try:

        prompt = f"""
You are an intelligent AI Study Tutor.

Help students understand concepts clearly.

Explain step by step.

If it is Mathematics, solve it.

If it is Physics, explain with examples.

If it is Chemistry, explain reactions simply.

If it is Biology, explain in easy language.

If it is Computer Science, explain with examples.

Student Question:

{question}
"""

        return generate_ai_response(prompt)

    except Exception as error:

        return f"Error: {error}"
def ask_voice_ai(question):

    prompt = f"""
You are an expert AI tutor.

Student asked:

{question}

Explain in a simple,
easy,
step-by-step manner.

If it is numerical,
solve it.

If it is theory,
explain with examples.
"""

    return generate_ai_response(prompt)
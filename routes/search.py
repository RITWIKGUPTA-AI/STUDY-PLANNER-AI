from flask import Blueprint, render_template, request, jsonify
from utils.json_manager import read_json
search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
def search():

    query = request.args.get("q", "").strip().lower()

    results = []

    files = [

        ("Subjects", "subjects.json"),
        ("Tasks", "tasks.json"),
        ("Notes", "notes.json"),
        ("Goals", "goals.json"),
        ("Planner", "planner.json"),
        ("Attendance", "attendance.json"),
        ("Timetable", "timetable.json"),
        ("Reminders", "reminders.json")

    ]

    if query:

        for module, filename in files:

            data = read_json(filename)

            for item in data:

                # Dictionary data
                if isinstance(item, dict):

                    text = " ".join(

                        str(value)

                        for value in item.values()

                    ).lower()

                else:

                    text = str(item).lower()

                if query in text:

                    results.append({

                        "module": module,

                        "data": item

                    })

    return render_template(

        "search.html",

        query=query,

        results=results,

        total=len(results)

    )
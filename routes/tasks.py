from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json

tasks_bp = Blueprint("tasks", __name__)


# ==========================================
# Tasks Home
# ==========================================

@tasks_bp.route("/tasks", methods=["GET", "POST"])
def tasks():

    task_list = read_json("tasks.json")

    # --------------------------------------
    # Convert old string data to dictionary
    # --------------------------------------

    converted = False

    for i in range(len(task_list)):

        if isinstance(task_list[i], str):

            task_list[i] = {

                "title": task_list[i],

                "priority": "Medium",

                "due_date": "",

                "status": "Pending"

            }

            converted = True

    if converted:

        write_json("tasks.json", task_list)

    # --------------------------------------
    # Add New Task
    # --------------------------------------

    if request.method == "POST":

        title = request.form.get("title", "").strip()

        priority = request.form.get("priority", "Medium")

        due_date = request.form.get("due_date", "")

        if title == "":

            flash(

                "Task title cannot be empty!",

                "danger"

            )

            return redirect(url_for("tasks.tasks"))

        duplicate = False

        for task in task_list:

            if task["title"].lower() == title.lower():

                duplicate = True

                break

        if duplicate:

            flash(

                "Task already exists!",

                "warning"

            )

            return redirect(url_for("tasks.tasks"))

        task_list.append({

            "title": title,

            "priority": priority,

            "due_date": due_date,

            "status": "Pending"

        })

        write_json("tasks.json", task_list)

        flash(

            "Task added successfully!",

            "success"

        )

        return redirect(url_for("tasks.tasks"))

    # --------------------------------------
    # Search
    # --------------------------------------

    search = request.args.get(

        "search",

        ""

    ).lower()

    if search:

        filtered = []

        for task in task_list:

            if (

                search in task["title"].lower()

                or search in task["priority"].lower()

                or search in task["status"].lower()

                or search in task["due_date"].lower()

            ):

                filtered.append(task)

    else:

        filtered = task_list

    # --------------------------------------
    # Sort by Due Date
    # --------------------------------------

    filtered = sorted(

        filtered,

        key=lambda x: x.get("due_date", "")

    )

    # --------------------------------------
    # Statistics
    # --------------------------------------

    completed = 0

    pending = 0

    high_priority = 0

    medium_priority = 0

    low_priority = 0

    for task in task_list:

        if task["status"] == "Completed":

            completed += 1

        else:

            pending += 1

        if task["priority"] == "High":

            high_priority += 1

        elif task["priority"] == "Medium":

            medium_priority += 1

        else:

            low_priority += 1

    if len(task_list) > 0:

        progress = round(

            completed * 100 / len(task_list),

            2

        )

    else:

        progress = 0

    # --------------------------------------
    # Dashboard Data
    # --------------------------------------

    return render_template(

        "tasks.html",

        tasks=filtered,

        total=len(task_list),

        completed=completed,

        pending=pending,

        progress=progress,

        high_priority=high_priority,

        medium_priority=medium_priority,

        low_priority=low_priority

    )
# ==========================================
# Delete Task
# ==========================================

@tasks_bp.route("/delete_task/<int:index>")
def delete_task(index):

    task_list = read_json("tasks.json")

    if 0 <= index < len(task_list):

        deleted = task_list.pop(index)

        write_json("tasks.json", task_list)

        flash(

            f'"{deleted["title"]}" deleted successfully!',

            "success"

        )

    else:

        flash(

            "Task not found!",

            "danger"

        )

    return redirect(url_for("tasks.tasks"))


# ==========================================
# Complete Task
# ==========================================

@tasks_bp.route("/complete_task/<int:index>")
def complete_task(index):

    task_list = read_json("tasks.json")

    if 0 <= index < len(task_list):

        task_list[index]["status"] = "Completed"

        write_json("tasks.json", task_list)

        flash(

            "Task marked as completed!",

            "success"

        )

    else:

        flash(

            "Task not found!",

            "danger"

        )

    return redirect(url_for("tasks.tasks"))


# ==========================================
# Mark Pending
# ==========================================

@tasks_bp.route("/pending_task/<int:index>")
def pending_task(index):

    task_list = read_json("tasks.json")

    if 0 <= index < len(task_list):

        task_list[index]["status"] = "Pending"

        write_json("tasks.json", task_list)

        flash(

            "Task marked as pending!",

            "warning"

        )

    else:

        flash(

            "Task not found!",

            "danger"

        )

    return redirect(url_for("tasks.tasks"))


# ==========================================
# Edit Task
# ==========================================

@tasks_bp.route("/edit_task/<int:index>", methods=["GET", "POST"])
def edit_task(index):

    task_list = read_json("tasks.json")

    if index < 0 or index >= len(task_list):

        flash(

            "Task not found!",

            "danger"

        )

        return redirect(url_for("tasks.tasks"))

    task = task_list[index]

    if request.method == "POST":

        title = request.form.get(

            "title",

            ""

        ).strip()

        priority = request.form.get(

            "priority",

            "Medium"

        )

        due_date = request.form.get(

            "due_date",

            ""

        )

        status = request.form.get(

            "status",

            "Pending"

        )

        if title == "":

            flash(

                "Task title cannot be empty!",

                "danger"

            )

            return redirect(

                url_for(

                    "tasks.edit_task",

                    index=index

                )

            )

        duplicate = False

        for i, item in enumerate(task_list):

            if (

                i != index

                and item["title"].lower() == title.lower()

            ):

                duplicate = True

                break

        if duplicate:

            flash(

                "Another task with this title already exists!",

                "warning"

            )

            return redirect(

                url_for(

                    "tasks.edit_task",

                    index=index

                )

            )

        task["title"] = title

        task["priority"] = priority

        task["due_date"] = due_date

        task["status"] = status

        task_list[index] = task

        write_json(

            "tasks.json",

            task_list

        )

        flash(

            "Task updated successfully!",

            "success"

        )

        return redirect(

            url_for("tasks.tasks")

        )

    return render_template(

        "edit_task.html",

        task=task,

        index=index

    )


# ==========================================
# Clear Completed Tasks
# ==========================================

@tasks_bp.route("/clear_completed")
def clear_completed():

    task_list = read_json("tasks.json")

    remaining = []

    deleted = 0

    for task in task_list:

        if task["status"] == "Completed":

            deleted += 1

        else:

            remaining.append(task)

    write_json(

        "tasks.json",

        remaining

    )

    flash(

        f"{deleted} completed task(s) removed.",

        "success"

    )

    return redirect(

        url_for("tasks.tasks")

    )
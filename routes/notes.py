from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/share-target", methods=["GET"])
def share_target():
    """
    Handler for the manifest's share_target: when a user shares a link or
    text from another app ("Share" → Student Study Planner), Android/Chrome
    opens this URL with the shared content pre-filled, and we drop it
    straight into a new note.
    """
    shared_title = request.args.get("title", "").strip()
    shared_text = request.args.get("text", "").strip()
    shared_url = request.args.get("url", "").strip()

    content_parts = [p for p in (shared_text, shared_url) if p]
    content = "\n\n".join(content_parts)

    if not shared_title and not content:
        return redirect(url_for("notes.notes"))

    notes = read_json("notes.json")
    notes.append({
        "title": shared_title or "Shared note",
        "subject": "",
        "content": content or "(no content shared)",
    })
    write_json("notes.json", notes)

    flash("Saved as a new note from your share.", "success")
    return redirect(url_for("notes.notes"))


@notes_bp.route("/notes", methods=["GET", "POST"])
def notes():

    notes = read_json("notes.json")

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        content = request.form.get("content", "").strip()

        if title == "" or content == "":

            flash("Please fill all required fields.", "danger")
            return redirect(url_for("notes.notes"))

        new_note = {

            "title": title,
            "subject": subject,
            "content": content

        }

        notes.append(new_note)

        write_json("notes.json", notes)

        flash("Note added successfully!", "success")

        return redirect(url_for("notes.notes"))

    # Search

    search = request.args.get("search", "").lower()

    if search:

        filtered = []

        for note in notes:

            title = note.get("title", "").lower()
            subject = note.get("subject", "").lower()
            content = note.get("content", "").lower()

            if (

                search in title or
                search in subject or
                search in content

            ):

                filtered.append(note)

    else:

        filtered = notes

    return render_template(

        "notes.html",

        notes=filtered,

        total=len(notes)

    )


@notes_bp.route("/notes/delete/<int:index>")
def delete_note(index):

    notes = read_json("notes.json")

    if 0 <= index < len(notes):

        notes.pop(index)

        write_json("notes.json", notes)

        flash("Note deleted successfully!", "success")

    else:

        flash("Invalid note.", "danger")

    return redirect(url_for("notes.notes"))


@notes_bp.route("/notes/edit/<int:index>", methods=["GET", "POST"])
def edit_note(index):

    notes = read_json("notes.json")

    if index < 0 or index >= len(notes):

        flash("Note not found.", "danger")

        return redirect(url_for("notes.notes"))

    if request.method == "POST":

        notes[index]["title"] = request.form.get("title", "").strip()
        notes[index]["subject"] = request.form.get("subject", "").strip()
        notes[index]["content"] = request.form.get("content", "").strip()

        write_json("notes.json", notes)

        flash("Note updated successfully!", "success")

        return redirect(url_for("notes.notes"))

    return render_template(

        "edit_note.html",

        note=notes[index],

        index=index

    )
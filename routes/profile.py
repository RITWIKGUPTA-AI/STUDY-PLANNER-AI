from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.json_manager import read_json, write_json

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
def profile():

    profile = read_json("profile.json")

    if not profile:

        profile = {

            "name": "",
            "email": "",
            "phone": "",
            "class": "",
            "target_exam": "",
            "school": "",
            "city": "",
            "bio": ""

        }

        write_json("profile.json", profile)

    return render_template(

        "profile.html",

        profile=profile

    )


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():

    profile = read_json("profile.json")

    if request.method == "POST":

        profile["name"] = request.form.get("name")
        profile["email"] = request.form.get("email")
        profile["phone"] = request.form.get("phone")
        profile["class"] = request.form.get("class")
        profile["target_exam"] = request.form.get("target_exam")
        profile["school"] = request.form.get("school")
        profile["city"] = request.form.get("city")
        profile["bio"] = request.form.get("bio")

        write_json("profile.json", profile)

        flash(

            "Profile updated successfully!",

            "success"

        )

        return redirect(url_for("profile.profile"))

    return render_template(

        "edit_profile.html",

        profile=profile

    )
document.addEventListener("DOMContentLoaded", function () {

    const button = document.getElementById("themeButton");

    if (button) {

        button.addEventListener("click", function () {

            document.body.classList.toggle("dark");

        });

    }

});
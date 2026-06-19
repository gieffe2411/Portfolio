import flask
from flask import Flask, render_template
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", title="Copertina", page="home")

@app.route("/friends")
def friends():
    return render_template("friends.html", title="Amici", page="friends")

@app.route("/professional")
def professional():
    return render_template("professional.html", title="Professionale", page="professional")

@app.route("/public")
def public():
    return render_template("public.html", title="Pubblico", page="public")


if __name__ == "__main__":
    app.run(debug=True)
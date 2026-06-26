import flask
from flask import Flask, render_template
import requests
app = Flask(__name__)


USER_ID = "972113138612854824"

def get_discord_data():
    try:
        res = requests.get(f"https://api.lanyard.rest/v1/users/{USER_ID}", timeout=3)
        data = res.json()

        if not data["success"]:
            return None

        d = data["data"]

        activity = None
        if d["activities"]:
            act = d["activities"][0]
            activity = act.get("state")

        return {
            "username": d["discord_user"].get("display_name") or d["discord_user"]["username"],
            "avatar": f"https://cdn.discordapp.com/avatars/{d['discord_user']['id']}/{d['discord_user']['avatar']}.png",
            "status": d["discord_status"],
            "activity": activity,
            "emoji": d["activities"][0]["emoji"]["name"]
        }

    except:
        return None

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
    return render_template("public.html", title="Pubblico", page="public", discord=get_discord_data())


if __name__ == "__main__":
    app.run(debug=True)
import time
from functools import wraps
from config import admin_password, secret_key, user_id

import requests
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, abort
)

import storage

app = Flask(__name__)

# --- Configuration con il modulo config.py ---------------------------------------------------
app.secret_key = secret_key
ADMIN_PASSWORD = admin_password or "123"
USER_ID = user_id or "972113138612854824"


def get_discord_data():
    try:
        res = requests.get(f"https://api.lanyard.rest/v1/users/{USER_ID}", timeout=3)
        data = res.json()

        if not data["success"]:
            return None

        d = data["data"]

        activity = None
        emoji = None
        if d["activities"]:
            act = d["activities"][0]
            activity = act.get("state")
            emoji = (act.get("emoji") or {}).get("name")

        return {
            "user_id": d["discord_user"]["id"],
            "username": d["discord_user"].get("display_name") or d["discord_user"]["username"],
            "avatar": f"https://cdn.discordapp.com/avatars/{d['discord_user']['id']}/{d['discord_user']['avatar']}.png",
            "status": d["discord_status"],
            "activity": activity,
            "emoji": emoji,
        }

    except Exception:
        return None


# --- Access control for gated pages -------------------------------------

def page_access_required(page_name):
    """Decorator: only allow access if the visitor has a valid session grant
    for this specific page, or supplies a valid ?token=... which is
    redeemed once and then remembered in the session.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            token = request.args.get("token")

            if token:
                granted_page = storage.redeem(token)
                if granted_page == page_name:
                    # Remember access for this browser session, then
                    # redirect to a clean URL so the token isn't sitting
                    # in the address bar / browser history / referrer headers.
                    granted = session.get("granted_pages", [])
                    if page_name not in granted:
                        granted.append(page_name)
                    session["granted_pages"] = granted
                    return redirect(url_for(view_func.__name__))
                else:
                    abort(403)

            if page_name in session.get("granted_pages", []):
                return view_func(*args, **kwargs)

            abort(403)
        return wrapped
    return decorator


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


# --- Admin auth -----------------------------------------------------------

def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            next_url = request.args.get("next") or url_for("admin")
            return redirect(next_url)
        error = "Wrong password."
    return render_template("login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin", methods=["GET"])
@admin_required
def admin():
    links = storage.list_links()
    return render_template(
        "admin.html",
        links=links,
        pages=sorted(storage.VALID_PAGES),
        base_url=request.host_url.rstrip("/"),
        now=time.time(),
    )


@app.route("/admin/generate", methods=["POST"])
@admin_required
def admin_generate():
    page = request.form.get("page")
    label = request.form.get("label", "").strip()
    expires_hours = request.form.get("expires_hours", "").strip()
    max_uses = request.form.get("max_uses", "").strip()

    expires_in = float(expires_hours) * 3600 if expires_hours else None
    max_uses_val = int(max_uses) if max_uses else None

    if page not in storage.VALID_PAGES:
        abort(400)

    storage.create_link(page, label=label, expires_in=expires_in, max_uses=max_uses_val)
    return redirect(url_for("admin"))


@app.route("/admin/revoke/<token>", methods=["POST"])
@admin_required
def admin_revoke(token):
    storage.revoke_link(token)
    return redirect(url_for("admin"))


@app.route("/admin/delete/<token>", methods=["POST"])
@admin_required
def admin_delete(token):
    storage.delete_link(token)
    return redirect(url_for("admin"))


# --- Public site routes -----------------------------------------------

@app.route("/")
def home():
    return render_template("index.html", title="Copertina", page="home")


@app.route("/friends")
@page_access_required("friends")
def friends():
    return render_template("friends.html", title="Amici", page="friends", discord=get_discord_data())


@app.route("/professional")
@page_access_required("professional")
def professional():
    return render_template("professional.html", title="Professionale", page="professional", discord=get_discord_data())


@app.route("/public")
def public():
    return render_template("public.html", title="Pubblico", page="public", discord=get_discord_data())


if __name__ == "__main__":
    app.run(debug=True)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgitb; cgitb.enable()
import os, html

from utils import (
    SITE_ROOT, TABLE_USER,
    html_page, parse_urlencoded, read_post_body, redirect,
    db, check_password_dev, set_cookie, create_session
)

def render_form(msg: str = "") -> str:
    note = f'<p style="color:red;">{html.escape(msg)}</p>' if msg else ""
    return f"""
    <h1>Log in</h1>{note}
    <form method="post" action="{SITE_ROOT}cgi/login.py">
      <label for="e">Email</label>
      <input id="e" name="email" type="email" required>
      <label for="p">Password</label>
      <input id="p" name="password" type="password" required>
      <button type="submit">Log in</button>
    </form>
    <p>New user? <a href="{SITE_ROOT}cgi/register.py">Register here</a>.</p>
    """

def main():
    method = (os.environ.get("REQUEST_METHOD") or "GET").upper()

    if method == "GET":
        print("Content-Type: text/html\n")
        print(html_page("Login", render_form()))
        return

    # POST
    form = parse_urlencoded(read_post_body())
    email = (form.get("email") or "").strip().lower()
    pw    = form.get("password") or ""

    if not email or not pw:
        print("Content-Type: text/html\n")
        print(html_page("Login", render_form("Email and password are required.")))
        return

    # Fetch user by email (parameterized)
    user_row = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(f"SELECT user_id, password_hash FROM `{TABLE_USER}` WHERE email=%s LIMIT 1", (email,))
            user_row = cur.fetchone()
    except Exception as e:
        print("Content-Type: text/html\n")
        print(html_page("Login Error", f"<h1>Database Error</h1><pre>{html.escape(str(e))}</pre>"))
        return
    finally:
        try:
            cn.close()
        except Exception:
            pass

    # Verify password (SHA-256 or plaintext dev)
    if not user_row or not check_password_dev(pw, (user_row.get("password_hash") or "")):
        print("Content-Type: text/html\n")
        print(html_page("Login", render_form("Invalid credentials.")))
        return

    # Create session + cookie, redirect to dashboard
    sid = create_session(user_row["user_id"])
    cookie = set_cookie("SID", sid, path=SITE_ROOT, http_only=True)
    redirect(f"{SITE_ROOT}cgi/dashboard.py", extra_headers=[cookie])

if __name__ == "__main__":
    main()

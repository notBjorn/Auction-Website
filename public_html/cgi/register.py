#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgitb; cgitb.enable()
import os, html

from utils import (
    SITE_ROOT, TABLE_USER, MIN_PW_LEN,
    html_page, parse_urlencoded, read_post_body, redirect,
    db, sha256_hex, validate_email, normalize_name_from_email
)

def render_form(msg: str = "", values: dict | None = None) -> str:
    v = values or {}
    note = f'<p style="color:red;">{html.escape(msg)}</p>' if msg else ""
    email_val = html.escape(v.get("email",""))
    name_val  = html.escape(v.get("user_name",""))
    return f"""
    <h1>Create Account</h1>
    {note}
    <form method="post" action="{SITE_ROOT}cgi/register.py" novalidate>
      <label for="n">Display name</label>
      <input id="n" name="user_name" type="text" required value="{name_val}">
      <label for="e">Email</label>
      <input id="e" name="email" type="email" required value="{email_val}">
      <label for="p">Password</label>
      <input id="p" name="password" type="password" required minlength="{MIN_PW_LEN}">
      <label for="c">Confirm Password</label>
      <input id="c" name="confirm" type="password" required minlength="{MIN_PW_LEN}">
      <button type="submit">Register</button>
    </form>
    <p>Already have an account? <a href="{SITE_ROOT}cgi/login.py">Log in</a>.</p>
    """

def main():
    method = (os.environ.get("REQUEST_METHOD") or "GET").upper()

    if method == "GET":
        print("Content-Type: text/html\n")
        print(html_page("Register", render_form()))
        return

    # POST
    form = parse_urlencoded(read_post_body())
    user_name = (form.get("user_name") or "").strip()
    email     = (form.get("email") or "").strip().lower()
    pw        = form.get("password") or ""
    confirm   = form.get("confirm") or ""

    # Server-side validation
    if not email or not pw or not confirm:
        print("Content-Type: text/html\n")
        print(html_page("Register", render_form("All fields are required.", form)))
        return
    if not validate_email(email):
        print("Content-Type: text/html\n")
        print(html_page("Register", render_form("Please enter a valid email address.", form)))
        return
    if len(pw) < MIN_PW_LEN:
        print("Content-Type: text/html\n")
        print(html_page("Register", render_form(f"Password must be at least {MIN_PW_LEN} characters.", form)))
        return
    if pw != confirm:
        print("Content-Type: text/html\n")
        print(html_page("Register", render_form("Passwords do not match.", form)))
        return
    if not user_name:
        user_name = normalize_name_from_email(email)

    pw_hash = sha256_hex(pw)

    # Insert user if email not taken
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM `{TABLE_USER}` WHERE email=%s LIMIT 1", (email,))
            if cur.fetchone():
                print("Content-Type: text/html\n")
                print(html_page("Register", render_form("That email is already registered. Try logging in.", form)))
                return

            cur.execute(
                f"INSERT INTO `{TABLE_USER}` (user_name, email, password_hash, created) VALUES (%s, %s, %s, NOW())",
                (user_name, email, pw_hash)
            )
            cn.commit()
    except Exception as e:
        print("Content-Type: text/html\n")
        print(html_page("Registration Error", f"<h1>Database Error</h1><pre>{html.escape(str(e))}</pre>"))
        return
    finally:
        try:
            cn.close()
        except Exception:
            pass

    # Success → login page
    redirect(f"{SITE_ROOT}cgi/login.py")

if __name__ == "__main__":
    main()

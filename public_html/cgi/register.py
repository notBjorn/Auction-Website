#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — register.py
# Renders a registration form, validates input, creates a new user record,
# and redirects to the login page on success.
# =============================================================================

# ====== Imports / Setup ======================================================
import cgitb;

cgitb.enable()
import os, html

from utils import (
    SITE_ROOT, TABLE_USER, MIN_PW_LEN,
    html_page, parse_urlencoded, read_post_body, redirect,
    db, sha256_hex, validate_email, normalize_name_from_email
)
from styles import THEME as s


# ====== View: Registration Form =============================================
def render_form(msg: str = "", values: dict | None = None) -> str:
    v = values or {}
    email_val = html.escape(v.get("email", ""))
    name_val = html.escape(v.get("user_name", ""))

    # Styled Alert Box
    note = ""
    if msg:
        note = f'<div class="{s["alert_error"]}">{html.escape(msg)}</div>'

    return f"""
    <div class="{s['layout_auth']}">
        <div class="{s['card_auth']}">

            <div class="text-center">
                <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">Create Account</h1>
                <p class="mt-2 text-sm text-gray-600">Join the auction community today</p>
            </div>

            {note}

            <form class="mt-8 space-y-6" method="post" action="{SITE_ROOT}cgi/register.py" novalidate>

                <div>
                    <label for="n" class="{s['label']}">Display Name</label>
                    <input id="n" name="user_name" type="text" value="{name_val}" required class="{s['input']}">
                </div>

                <div>
                    <label for="e" class="{s['label']}">Email Address</label>
                    <input id="e" name="email" type="email" value="{email_val}" required class="{s['input']}">
                </div>

                <div>
                    <label for="p" class="{s['label']}">Password</label>
                    <input id="p" name="password" type="password" required minlength="{MIN_PW_LEN}" class="{s['input']}">
                </div>

                <div>
                    <label for="c" class="{s['label']}">Confirm Password</label>
                    <input id="c" name="confirm" type="password" required minlength="{MIN_PW_LEN}" class="{s['input']}">
                </div>

                <button type="submit" class="{s['btn_full']}">Register</button>
            </form>

            <div class="text-center text-sm">
                <span class="text-gray-600">Already have an account?</span>
                <a href="{SITE_ROOT}cgi/login.py" class="font-medium text-indigo-600 hover:text-indigo-500">
                    Log in
                </a>
            </div>

        </div>
    </div>
    """


# ====== Controller: Main Request Handler =====================================
def main():
    """
    GET  -> render registration form.
    POST -> validate input, insert user (if email unused), redirect to login.
    """
    method = (os.environ.get("REQUEST_METHOD") or "GET").upper()

    # ----- GET: show the form -------------------------------------------------
    if method == "GET":
        print("Content-Type: text/html\n")
        print(html_page("Register", render_form()))
        return

    # ----- POST: parse form ---------------------------------------------------
    form = parse_urlencoded(read_post_body())
    user_name = (form.get("user_name") or "").strip()
    email = (form.get("email") or "").strip().lower()
    pw = form.get("password") or ""
    confirm = form.get("confirm") or ""

    # ====== Validation: Server-side checks ===================================
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

    # ====== Model: Insert user if email not taken =============================
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
        # ====== Error View: Database Error ===================================
        print("Content-Type: text/html\n")
        print(html_page("Registration Error", f"<h1>Database Error</h1><pre>{html.escape(str(e))}</pre>"))
        return
    finally:
        try:
            cn.close()
        except Exception:
            pass

    # ====== Redirect: Success -> Login =======================================
    redirect(f"{SITE_ROOT}cgi/login.py")


# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgitb; cgitb.enable()
import os, sys, html, re, hashlib
import urllib.parse as urlparse
import pymysql.cursors

# --------- CONFIG (same as login.py) ----------
DB_HOST = "localhost"
DB_USER = "cs370_section2_cafcode"
DB_PASS = "edocfac_001"                 # <- our real DB password
DB_NAME = "cs370_section2_cafcode"
TABLE   = "User"
SITE_ROOT = "/~cafcode/"                # for links/paths
# --------------------------------------------------------

EMAIL_RE   = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PW_LEN = 6                         # adjust if you want 8+

def db():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def html_page(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><title>{html.escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head><body>
{body_html}
</body></html>"""

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_urlencoded(body: str) -> dict:
    parsed = urlparse.parse_qs(body, keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in parsed.items()}

def read_post_body() -> str:
    length = int(os.environ.get("CONTENT_LENGTH") or 0)
    return sys.stdin.read(length) if length > 0 else ""

def render_form(msg: str = "", values: dict | None = None) -> str:
    v = values or {}
    note = f'<p style="color:red;">{html.escape(msg)}</p>' if msg else ""
    # Preserve email/name on error, never password
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

def redirect(location: str):
    print("Status: 303 See Other")
    print(f"Location: {location}")
    print("Content-Type: text/html\n")
    print(html_page("Redirecting…", f'<p>Redirecting to <a href="{html.escape(location)}">{html.escape(location)}</a>…</p>'))

def normalize_name_from_email(email: str) -> str:
    local = email.split("@", 1)[0]
    return local if local else "User"

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
    if not EMAIL_RE.match(email):
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
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            # Is email already registered?
            cur.execute(f"SELECT 1 FROM `{TABLE}` WHERE email=%s LIMIT 1", (email,))
            if cur.fetchone():
                print("Content-Type: text/html\n")
                print(html_page("Register", render_form("That email is already registered. Try logging in.", form)))
                return

            # Insert new user
            cur.execute(
                f"INSERT INTO `{TABLE}` (user_name, email, password_hash, created) VALUES (%s, %s, %s, NOW())",
                (user_name, email, pw_hash)
            )
            cn.commit()

    except Exception as e:
        print("Content-Type: text/html\n")
        print(html_page("Registration Error", f"<h1>Database Error</h1><pre>{html.escape(str(e))}</pre>"))
        return
    finally:
        if cn:
            try: cn.close()
            except Exception: pass

    # Success → send to login
    redirect(f"{SITE_ROOT}cgi/login.py")

if __name__ == "__main__":
    main()

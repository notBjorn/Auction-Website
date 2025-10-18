#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgitb; cgitb.enable()
import os, sys, html, re, hashlib, secrets
import urllib.parse as urlparse
import pymysql.cursors

# --------- CONFIG (edit these for our account) ----------
DB_HOST = "localhost"
DB_USER = "cs370_section2_cafcode"
DB_PASS = "edocfac_001"                 # <- our real DB password
DB_NAME = "cs370_section2_cafcode"
TABLE_USER    = "User"                 # table with email + password_hash
TABLE_SESSION = "Session"              # session table (see schema note below)
SITE_ROOT     = "/~cafcode/"            # our site root for cookies/paths
# --------------------------------------------------------

def db():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def html_page(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
{body_html}
</body>
</html>"""

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

def read_post_body() -> str:
    length = int(os.environ.get("CONTENT_LENGTH") or 0)
    return sys.stdin.read(length) if length > 0 else ""

def parse_urlencoded(body: str) -> dict:
    parsed = urlparse.parse_qs(body, keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in parsed.items()}

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# DEV-only checker: allows SHA-256 hex or plaintext (for early bring-up).
def check_password_dev(entered: str, stored: str) -> bool:
    s = (stored or "").strip()
    if not s:
        return False
    if re.fullmatch(r"[0-9a-fA-F]{64}", s):  # SHA-256 hex?
        return sha256_hex(entered).lower() == s.lower()
    return entered == s  # plaintext fallback (remove later)

def set_cookie(name: str, value: str, path=SITE_ROOT, http_only=True, max_age=None):
    parts = [f"{name}={value}", f"Path={path}", "SameSite=Lax"]
    if http_only:
        parts.append("HttpOnly")
    # Add "Secure" when you’re on HTTPS
    if max_age is not None:
        parts.append(f"Max-Age={max_age}")
    return "Set-Cookie: " + "; ".join(parts)

def redirect(location: str, extra_headers=None):
    print("Status: 303 See Other")
    print(f"Location: {location}")
    if extra_headers:
        for h in extra_headers:
            print(h)
    print("Content-Type: text/html\n")
    print(html_page("Redirecting…",
                    f'<p>Redirecting to <a href="{html.escape(location)}">{html.escape(location)}</a>…</p>'))

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

    # Fetch user by email
    cn = None
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
        if cn:
            try: cn.close()
            except Exception: pass

    # Verify password (SHA-256 or plaintext dev)
    if not user_row or not check_password_dev(pw, (user_row.get("password_hash") or "")):
        print("Content-Type: text/html\n")
        print(html_page("Login", render_form("Invalid credentials.")))
        return

    # Create a DB-backed session and set SID cookie
    sid = secrets.token_hex(32)  # 64 hex chars
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            # Optional: clean up any very old sessions for this user (not required)
            # cur.execute(f"DELETE FROM `{TABLE_SESSION}` WHERE user_id=%s AND TIMESTAMPDIFF(DAY, last_seen, NOW()) > 7", (user_row["user_id"],))
            cur.execute(
                f"INSERT INTO `{TABLE_SESSION}` (session_id, user_id, last_seen) VALUES (%s, %s, NOW())",
                (sid, user_row["user_id"])
            )
            cn.commit()
    except Exception as e:
        print("Content-Type: text/html\n")
        print(html_page("Login Error", f"<h1>Session Error</h1><pre>{html.escape(str(e))}</pre>"))
        return
    finally:
        if cn:
            try: cn.close()
            except Exception: pass

    cookie = set_cookie("SID", sid, path=SITE_ROOT, http_only=True)
    redirect(f"{SITE_ROOT}cgi/dashboard.py", extra_headers=[cookie])

if __name__ == "__main__":
    main()

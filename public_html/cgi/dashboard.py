#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgitb; cgitb.enable()
import os, html, re
import pymysql.cursors

# --------- CONFIG (keep in sync with login/register) ----------
DB_HOST   = "localhost"
DB_USER   = "cs370_section2_cafcode"
DB_PASS   = "edocfac_001"                 # <- set ours
DB_NAME   = "cs370_section2_cafcode"
TABLE_USER    = "User"
TABLE_SESSION = "Session"
SITE_ROOT     = "/~cafcode/"              # our site root
INACTIVITY_SECONDS = 300                 # 5 minutes
# --------------------------------------------------------------

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

def redirect(location: str, extra_headers=None):
    print("Status: 303 See Other")
    print(f"Location: {location}")
    if extra_headers:
        for h in extra_headers: print(h)
    print("Content-Type: text/html\n")
    print(html_page("Redirecting…", f'<p>Redirecting to <a href="{html.escape(location)}">{html.escape(location)}</a>…</p>'))

def parse_cookies(raw: str) -> dict:
    out = {}
    if not raw: return out
    for p in raw.split(";"):
        k, _, v = p.strip().partition("=")
        if k: out[k] = v
    return out

def set_cookie(name: str, value: str, path=SITE_ROOT, http_only=True, max_age=None):
    parts = [f"{name}={value}", f"Path={path}", "SameSite=Lax"]
    if http_only: parts.append("HttpOnly")
    if max_age is not None: parts.append(f"Max-Age={max_age}")
    return "Set-Cookie: " + "; ".join(parts)

def expire_cookie(name: str, path=SITE_ROOT):
    return set_cookie(name, "deleted", path=path, http_only=True, max_age=0)

def require_valid_session():
    """Returns (user_row, sid) if valid; handles timeout by returning (None, None)."""
    cookies = parse_cookies(os.environ.get("HTTP_COOKIE", ""))
    sid = cookies.get("SID")
    if not sid or not re.fullmatch(r"[0-9a-fA-F]{64}", sid):
        return (None, None)

    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            # Get session and user
            cur.execute(f"""
                SELECT s.user_id,
                       TIMESTAMPDIFF(SECOND, s.last_seen, NOW()) AS idle_sec,
                       u.email
                  FROM `{TABLE_SESSION}` s
                  JOIN `{TABLE_USER}` u ON u.user_id = s.user_id
                 WHERE s.session_id = %s
                 LIMIT 1
            """, (sid,))
            row = cur.fetchone()
            if not row:
                return (None, None)

            # Timeout?
            if (row["idle_sec"] or 0) > INACTIVITY_SECONDS:
                # delete session
                cur.execute(f"DELETE FROM `{TABLE_SESSION}` WHERE session_id=%s", (sid,))
                cn.commit()
                return (None, sid)

            # Still valid → refresh last_seen
            cur.execute(f"UPDATE `{TABLE_SESSION}` SET last_seen = NOW() WHERE session_id=%s", (sid,))
            cn.commit()
            return (row, sid)
    finally:
        if cn:
            try: cn.close()
            except Exception: pass

def main():
    user, sid = require_valid_session()

    # Not logged in or timed out
    if not user:
        headers = []
        if sid:
            # timed out: expire cookie
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # Logged in → show a minimal dashboard
    email = html.escape(user["email"])
    print("Content-Type: text/html\n")
    print(html_page("Dashboard", f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Welcome, {email}</h2>
  <p>Login succeeded for <code>{html.escape(SITE_ROOT)}</code>.</p>
  <p><a href="{SITE_ROOT}cgi/logout.py">Log out</a></p>
</main>
"""))

if __name__ == "__main__":
    main()

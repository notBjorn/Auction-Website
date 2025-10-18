#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgitb; cgitb.enable()
import os, re
import pymysql.cursors

# --- Config (match our other files) ---
DB_HOST = "localhost"
DB_USER = "cs370_section2_cafcode"
DB_PASS = "edocfac_001"                 # <- our real DB password
DB_NAME = "cs370_section2_cafcode"
TABLE_SESSION = "Session"
SITE_ROOT = "/~cafcode/"                # cookie path & redirect base
# ---------------------------------------

def db():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def parse_cookies(raw: str) -> dict:
    out = {}
    if raw:
        for p in raw.split(";"):
            k, _, v = p.strip().partition("=")
            if k:
                out[k] = v
    return out

def set_cookie(name, value, path=SITE_ROOT, http_only=True, max_age=None):
    parts = [f"{name}={value}", f"Path={path}", "SameSite=Lax"]
    if http_only:
        parts.append("HttpOnly")
    # Add "Secure" when HTTPS is enforced
    if max_age is not None:
        parts.append(f"Max-Age={max_age}")
    return "Set-Cookie: " + "; ".join(parts)

def expire_cookie(name, path=SITE_ROOT):
    return set_cookie(name, "deleted", path=path, http_only=True, max_age=0)

def main():
    # Read SID cookie (if present)
    cookies = parse_cookies(os.environ.get("HTTP_COOKIE", ""))
    sid = cookies.get("SID")

    # Best effort: delete session from DB if SID looks valid
    if sid and re.fullmatch(r"[0-9a-fA-F]{64}", sid):
        try:
            cn = db()
            with cn.cursor() as cur:
                cur.execute(f"DELETE FROM `{TABLE_SESSION}` WHERE session_id=%s", (sid,))
                cn.commit()
        except Exception:
            # swallow errors—logout should still clear cookie & redirect
            pass
        finally:
            try: cn.close()
            except Exception: pass

    # Redirect to login, expiring SID cookie
    print("Status: 303 See Other")
    print(f"Location: {SITE_ROOT}cgi/login.py")
    print(expire_cookie("SID", path=SITE_ROOT))
    print("Content-Type: text/html\n")
    print(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Logged out</title></head>
<body>
  <p>Logging out… <a href="{SITE_ROOT}cgi/login.py">Continue</a></p>
</body></html>""")

if __name__ == "__main__":
    main()

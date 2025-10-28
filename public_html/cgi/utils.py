#!/usr/bin/env python3

# utils.py
# Common helpers for CS370 Auction Website (Python CGI)

import os, sys, re, html, hashlib, secrets
import urllib.parse as urlparse
import pymysql.cursors
from typing import Any, Dict, List, Optional, Tuple

# ====== CONFIG (keep in sync across scripts) =================================
DB_HOST = "localhost"
DB_USER = "cs370_section2_cafcode"
DB_PASS = "edocfac_001"          # <-- set your real DB password
DB_NAME = "cs370_section2_cafcode"

TABLE_USER    = "User"
TABLE_SESSION = "Session"

# Web path root for cookies/links (your account root on Blue)
SITE_ROOT = "/~cafcode/"

# Session timeout
INACTIVITY_SECONDS = 300  # 5 minutes
# ============================================================================


# ====== DB ==================================================================
def db():
    """Get a new MySQL connection (DictCursor). Caller must close()."""
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def query_one(sql: str, args: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()
    finally:
        if cn:
            try: cn.close()
            except Exception: pass

def query_all(sql: str, args: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(sql, args)
            return list(cur.fetchall())
    finally:
        if cn:
            try: cn.close()
            except Exception: pass

def exec_write(sql: str, args: Tuple[Any, ...] = ()) -> int:
    """Execute INSERT/UPDATE/DELETE; returns affected rows."""
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(sql, args)
            cn.commit()
            return cur.rowcount
    finally:
        if cn:
            try: cn.close()
            except Exception: pass
# ============================================================================


# ====== HTML / HTTP ==========================================================
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

def print_headers(extra_headers: Optional[List[str]] = None, status: str = "200 OK", content_type: str = "text/html"):
    print(f"Status: {status}")
    if extra_headers:
        for h in extra_headers:
            print(h)
    print(f"Content-Type: {content_type}\n")

def redirect(location: str, extra_headers: Optional[List[str]] = None, status: str = "303 See Other"):
    print_headers(extra_headers=([f"Location: {location}"] + (extra_headers or [])), status=status)
    print(html_page("Redirecting…", f'<p>Redirecting to <a href="{html.escape(location)}">{html.escape(location)}</a>…</p>'))

# Form parsing (application/x-www-form-urlencoded)
def read_post_body() -> str:
    length = int(os.environ.get("CONTENT_LENGTH") or 0)
    return sys.stdin.read(length) if length > 0 else ""

def parse_urlencoded(body: str) -> Dict[str, str]:
    parsed = urlparse.parse_qs(body, keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in parsed.items()}

def html_escape(s: str) -> str:
    return html.escape(s or "")
# ============================================================================


# ====== Cookies ==============================================================
def parse_cookies(raw: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if raw:
        for p in raw.split(";"):
            k, _, v = p.strip().partition("=")
            if k:
                out[k] = v
    return out

def set_cookie(name: str, value: str, path: str = SITE_ROOT, http_only: bool = True, max_age: Optional[int] = None, same_site: str = "Lax", secure: bool = False) -> str:
    parts = [f"{name}={value}", f"Path={path}", f"SameSite={same_site}"]
    if http_only:
        parts.append("HttpOnly")
    if secure:
        parts.append("Secure")
    if max_age is not None:
        parts.append(f"Max-Age={max_age}")
    return "Set-Cookie: " + "; ".join(parts)

def expire_cookie(name: str, path: str = SITE_ROOT) -> str:
    return set_cookie(name, "deleted", path=path, http_only=True, max_age=0)
# ============================================================================


# ====== Auth / Passwords =====================================================
EMAIL_RE   = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PW_LEN = 6

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

def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip().lower()))

def normalize_name_from_email(email: str) -> str:
    local = (email or "").split("@", 1)[0]
    return local if local else "User"
# ============================================================================


# ====== Sessions (5-minute idle timeout) ====================================
def create_session(user_id: int) -> str:
    """Create a session row and return SID (hex)."""
    sid = secrets.token_hex(32)  # 64 hex chars
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(
                f"INSERT INTO `{TABLE_SESSION}` (session_id, user_id, last_seen) VALUES (%s, %s, NOW())",
                (sid, user_id)
            )
            cn.commit()
    finally:
        if cn:
            try: cn.close()
            except Exception: pass
    return sid

def delete_session(sid: str) -> None:
    if not sid: return
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(f"DELETE FROM `{TABLE_SESSION}` WHERE session_id=%s", (sid,))
            cn.commit()
    finally:
        if cn:
            try: cn.close()
            except Exception: pass

def get_cookie(name: str) -> Optional[str]:
    cookies = parse_cookies(os.environ.get("HTTP_COOKIE", ""))
    return cookies.get(name)

def require_valid_session() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Returns (user_row, sid) when valid & active; returns (None, sid_or_None) if not valid/expired.
    Also refreshes last_seen on valid access.
    """
    sid = get_cookie("SID")
    if not sid or not re.fullmatch(r"[0-9a-fA-F]{64}", sid):
        return (None, None)

    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(f"""
                SELECT s.user_id,
                       TIMESTAMPDIFF(SECOND, s.last_seen, NOW()) AS idle_sec,
                       u.email, u.user_id, u.user_name
                  FROM `{TABLE_SESSION}` s
                  JOIN `{TABLE_USER}` u ON u.user_id = s.user_id
                 WHERE s.session_id = %s
                 LIMIT 1
            """, (sid,))
            row = cur.fetchone()
            if not row:
                return (None, sid)

            idle = int(row.get("idle_sec") or 0)
            if idle > INACTIVITY_SECONDS:
                # Expired: delete and signal caller
                cur.execute(f"DELETE FROM `{TABLE_SESSION}` WHERE session_id=%s", (sid,))
                cn.commit()
                return (None, sid)

            # Refresh activity
            cur.execute(f"UPDATE `{TABLE_SESSION}` SET last_seen = NOW() WHERE session_id=%s", (sid,))
            cn.commit()
            return (row, sid)
    finally:
        if cn:
            try: cn.close()
            except Exception: pass
# ============================================================================


# ====== CSRF (optional; easy to add to Session table) ========================
# If you add a csrf_token column to Session, these helpers are ready to use.

def issue_csrf(sid: str) -> str:
    """Create/rotate a CSRF token tied to the session."""
    token = secrets.token_hex(16)
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(f"UPDATE `{TABLE_SESSION}` SET csrf_token=%s WHERE session_id=%s", (token, sid))
            cn.commit()
    finally:
        if cn:
            try: cn.close()
            except Exception: pass
    return token

def get_csrf(sid: str) -> Optional[str]:
    cn = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(f"SELECT csrf_token FROM `{TABLE_SESSION}` WHERE session_id=%s LIMIT 1", (sid,))
            row = cur.fetchone()
            return (row or {}).get("csrf_token")
    finally:
        if cn:
            try: cn.close()
            except Exception: pass

def verify_csrf(sid: str, provided: str) -> bool:
    expected = get_csrf(sid)
    return bool(expected) and (provided or "") == expected
# ============================================================================


# ====== Misc input helpers ===================================================
def to_decimal_str(x: str) -> Optional[str]:
    """
    Return a normalized decimal string if x is a valid money-like number;
    otherwise None. (Keep as string; let MySQL DECIMAL handle storage)
    """
    s = (x or "").strip()
    if not s:
        return None
    if not re.fullmatch(r"-?\d+(\.\d{1,2})?", s):  # allow cents
        return None
    return s
# ============================================================================

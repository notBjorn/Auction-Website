#!/usr/bin/env python3
import os, sys, html, configparser, datetime as dt, secrets
import pymysql, bcrypt

# ---- Config & DB ----
def load_config(path="~/auction-auth/config/app.ini"):
    cfg = configparser.ConfigParser()
    cfg.read(path)
    return cfg
CFG = load_config()

def db():
    return pymysql.connect(
        host='localhost',
        user='cs370_section2_cafcode',       # your team's MySQL username
        password='edocfac_001', # your team's MySQL password
        database='cs370_section2_cafcode',   # your team's database
        cursorclass=pymysql.cursors.DictCursor
    )

# ---- HTTP helpers ----
def header(extra=None):
    print("Content-Type: text/html; charset=utf-8")
    if extra:
        for h in extra: print(h)
    print()

def redirect(location, status="303 See Other", extra=None):
    print(f"Status: {status}")
    print(f"Location: {location}")
    if extra:
        for h in extra: print(h)
    print()
    sys.exit(0)

def html_page(title, body):
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title></head><body><main>{body}</main></body></html>"""

def read_post_body():
    try: n = int(os.environ.get("CONTENT_LENGTH","0"))
    except ValueError: n = 0
    return sys.stdin.buffer.read(n).decode("utf-8", errors="replace")

def url_decode(s):
    s = s.replace("+"," "); out=[]; i=0
    while i < len(s):
        if s[i]=="%" and i+2<len(s):
            out.append(chr(int(s[i+1:i+3],16))); i+=3
        else:
            out.append(s[i]); i+=1
    return "".join(out)

def parse_urlencoded(s):
    out={}
    for pair in s.split("&"):
        if not pair: continue
        k, _, v = pair.partition("=")
        out[url_decode(k)] = url_decode(v)
    return out

# ---- Cookies & CSRF ----
def get_cookies():
    raw = os.environ.get("HTTP_COOKIE","")
    cookies={}
    for part in raw.split(";"):
        if "=" in part:
            k,v = part.strip().split("=",1)
            cookies[k]=v
    return cookies

def set_cookie(name, val, max_age=None, secure=False):
    bits=["Path=/","HttpOnly","SameSite=Lax"]
    if max_age is not None: bits.append(f"Max-Age={int(max_age)}")
    if secure: bits.append("Secure")
    return f"Set-Cookie: {name}={val}; " + "; ".join(bits)

def expire_cookie(name):
    return f"Set-Cookie: {name}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"

def new_token(nbytes=32):  # 64 hex chars
    return secrets.token_hex(nbytes)

# Temporary CSRF for unauthenticated forms
def ensure_temp_csrf():
    c = get_cookies()
    tok = c.get("XSRF") or new_token(32)
    return tok, set_cookie("XSRF", tok, max_age=1800)

# ---- Passwords ----
def hash_pw(pw:str)->bytes:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

def check_pw(pw:str, stored_text:str)->bool:
    return bcrypt.checkpw(pw.encode(), stored_text.encode())

# ---- Sessions ----
def now_utc(): return dt.datetime.utcnow()

def create_session(user_id:int, cn):
    sid = new_token(32); csrf = new_token(32)
    ttl = int(CFG["session"]["ttl_minutes"])
    expires = now_utc() + dt.timedelta(minutes=ttl)
    with cn.cursor() as cur:
        cur.execute(
            "INSERT INTO sessions(id,user_id,csrf_token,expires_at,last_seen) VALUES(%s,%s,%s,%s,%s)",
            (sid, user_id, csrf, expires, now_utc()))
    cn.commit()
    return sid, csrf, ttl*60

def get_session(cn):
    sid = get_cookies().get("SID")
    if not sid: return None
    with cn.cursor(dictionary=True) as cur:
        cur.execute("""
                    SELECT s.id sid, s.user_id, s.csrf_token, s.expires_at,
                           u.email, u.user_name
                    FROM sessions s JOIN `User` u ON u.user_id=s.user_id
                    WHERE s.id=%s AND s.expires_at>UTC_TIMESTAMP()""", (sid,))
        row = cur.fetchone()
        if not row: return None
        cur.execute("UPDATE sessions SET last_seen=UTC_TIMESTAMP() WHERE id=%s", (sid,))
        cn.commit()
        return row

def destroy_session(cn):
    sid = get_cookies().get("SID")
    if not sid: return
    with cn.cursor() as cur:
        cur.execute("DELETE FROM sessions WHERE id=%s", (sid,))
    cn.commit()


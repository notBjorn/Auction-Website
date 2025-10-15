#!/home/cafcode/auction-auth/.venv/bin/python3
import os, re, html
from utils import *

def render_form(csrf, msg=""):
    note = f'<p style="color:red;">{html.escape(msg)}</p>' if msg else ""
    return f"""
    <h1>Create account</h1>{note}
    <form method="post" action="/cgi-bin/register.py">
      <input type="hidden" name="csrf" value="{csrf}">
      <label for="u">Username</label>
      <input id="u" name="user_name" required maxlength="50">
      <label for="e">Email</label>
      <input id="e" name="email" type="email" required>
      <label for="p">Password</label>
      <input id="p" name="password" type="password" required minlength="8">
      <label for="p2">Confirm password</label>
      <input id="p2" name="password2" type="password" required minlength="8">
      <button type="submit">Register</button>
    </form>"""

def main():
    cn = db()
    method = os.environ.get("REQUEST_METHOD","GET").upper()

    if method == "GET":
        xsrf, cookie = ensure_temp_csrf()
        body = render_form(xsrf)
        header([cookie])
        print(html_page("Register", body))
        return

    # POST
    formdata = parse_urlencoded(read_post_body())
    xsrf_cookie = get_cookies().get("XSRF")
    if not formdata.get("csrf") or formdata["csrf"] != xsrf_cookie:
        header(); print(html_page("Error","<p>Invalid CSRF token.</p>")); return

    user_name = (formdata.get("user_name","") or "").strip()
    email     = (formdata.get("email","") or "").strip().lower()
    pw        = formdata.get("password","") or ""
    pw2       = formdata.get("password2","") or ""

    if not (1 <= len(user_name) <= 50):
        header(); print(html_page("Register", render_form(xsrf_cookie, "Username is required (max 50)."))); return
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        header(); print(html_page("Register", render_form(xsrf_cookie, "Invalid email."))); return
    if len(pw) < 8 or pw != pw2:
        header(); print(html_page("Register", render_form(xsrf_cookie, "Password too short or mismatch."))); return

    hashed = hash_pw(pw).decode("utf-8")  # store text hash (VARCHAR)
    try:
        with cn.cursor() as cur:
            cur.execute("INSERT INTO `User`(user_name,email,password_hash) VALUES(%s,%s,%s)",
                        (user_name, email, hashed))
            user_id = cur.lastrowid
    except Exception:
        header(); print(html_page("Register", render_form(xsrf_cookie, "Username or email already exists."))); return

    sid, csrf, max_age = create_session(user_id, cn)
    cookie_sid = set_cookie("SID", sid, max_age=max_age, secure=False)
    cookie_kill_xsrf = expire_cookie("XSRF")
    redirect("/cgi-bin/dashboard.py", extra=[cookie_sid, cookie_kill_xsrf])

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
import os, html
#from utils import *

# def render_form(csrf, msg=""):
#    note = f'<p style="color:red;">{html.escape(msg)}</p>' if msg else ""
#    return f""
#    <h1>Log in</h1>{note}
#    <form method="post" action="/cgi/login.py">
#      <input type="hidden" name="csrf" value="{csrf}">
#      <label for="e">Email</label>
#      <input id="e" name="email" type="email" required>
#      <label for="p">Password</label>
#      <input id="p" name="password" type="password" required>
#      <button type="submit">Log in</button>
#    </form>""

def main():
    username = "username"
    password = "username"
#    cn = db()
    method = os.environ.get("REQUEST_METHOD","GET").upper()

    if method == "GET":
        xsrf, cookie = ensure_temp_csrf()
        body = render_form(xsrf)
        header([cookie])
        print(html_page("Login", body))
        return

    # POST
    formdata = parse_urlencoded(read_post_body())
#    xsrf_cookie = get_cookies().get("XSRF")
#    if not formdata.get("csrf") or formdata["csrf"] != xsrf_cookie:
#        header(); print(html_page("Error","<p>Invalid CSRF token.</p>")); return

    email = (formdata.get("email","") or "").strip().lower()
    pw    = formdata.get("password","") or ""

print ("Content type: text/html\n\n")
print ("<html>")
print ("<body>")
print ("<p> username is </p>"+username)
print ("<p> pword is </p>"+password)
print ("</body>")
print ("</html>")

#    with cn.cursor(dictionary=True) as cur:
#        cur.execute("SELECT user_id, password_hash FROM `User` WHERE email=%s", (email,))
#        row = cur.fetchone()

#    if not row or not check_pw(pw, row["password_hash"]):
#        header(); print(html_page("Login", render_form(xsrf_cookie, "Invalid credentials."))); return

#    sid, csrf, max_age = create_session(row["user_id"], cn)
#    cookie_sid = set_cookie("SID", sid, max_age=max_age, secure=False)
#    cookie_kill_xsrf = expire_cookie("XSRF")
#    redirect("/cgi-bin/dashboard.py", extra=[cookie_sid, cookie_kill_xsrf])

if __name__ == "__main__":
    main()


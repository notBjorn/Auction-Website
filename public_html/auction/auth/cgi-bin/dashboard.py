#!/usr/bin/env python3
from utils import *
def main():
    cn = db()
    sess = get_session(cn)
    if not sess:
        redirect("/cgi-bin/login.py")
    body = f"""
    <h1>Welcome, {html.escape(sess['user_name'])}</h1>
    <p>{html.escape(sess['email'])}</p>
    <form method="post" action="/cgi-bin/logout.py">
      <input type="hidden" name="csrf" value="{sess['csrf_token']}">
      <button type="submit">Log out</button>
    </form>"""
    header(); print(html_page("Dashboard", body))
if __name__ == "__main__":
    main()


#!/usr/bin/env python3
from utils import *
def main():
    '''
    cn = db()
    sess = get_session(cn)
    if not sess:
        # Ensure path includes your user directory
        redirect("/~cafcode/cgi/login.py")

    body = f"""
    <h1>Welcome, {html.escape(sess['user_name'])}</h1>
    <p>{html.escape(sess['email'])}</p>
    <form method="post" action="/~cafcode/cgi/logout.py">
      <input type="hidden" name="csrf" value="{sess['csrf_token']}">
      <button type="submit">Log out</button>
    </form>"""
    '''
    header()
    print(html_page("Dashboard", "<h1>:)</h1>"))
if __name__ == "__main__":
    main()


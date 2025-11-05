#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cgitb; cgitb.enable()
import html, os
import cgi
from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie,
    require_valid_session, db
)

# ==============================
# Constants
# ==============================
# Example:
# TIMEOUT_SECONDS = 3600


# ==============================
# Rendering Functions (HTML)
# ==============================
def render_page(message: str = "", data=None):
    """Render the main HTML page for this CGI."""
    body = f"""
<h1>Page Title</h1>
{f'<p role="alert">{html.escape(message)}</p>' if message else ''}
<!-- Add your form or table or other content here -->
<p><a href="{SITE_ROOT}index.html">Return to Home</a></p>
"""
    print("Content-Type: text/html; charset=utf-8\n")
    print(html_page("Page Title", body))


# ==============================
# Core Logic Functions
# ==============================
def perform_action(conn, user, form):
    """Perform whatever database or business logic is needed."""
    # Example structure:
    # with conn.cursor() as cur:
    #     cur.execute("SQL HERE", (...))
    #     conn.commit()
    return "Action completed."


# ==============================
# Main Request Handler
# ==============================
def main():
    # --- Session check ---
    user, sid = require_valid_session()
    if not user:
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # --- Handle GET vs POST ---
    method = os.environ.get("REQUEST_METHOD", "GET")
    if method == "GET":
        render_page()
        return

    # --- Parse form data ---
    form = cgi.FieldStorage()

    # --- DB connection + action ---
    conn = db()
    try:
        message = perform_action(conn, user, form)
    finally:
        conn.close()

    # --- Render page again (with result) ---
    render_page(message)


# ==============================
# Entrypoint
# ==============================
if __name__ == "__main__":
    main()


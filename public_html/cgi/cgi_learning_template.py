#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================
# AUCTION WEBSITE CGI SCRIPT TEMPLATE  —  "Teaching Edition"
# ============================================================
# This file provides a standard structure (skeleton) for all our .py CGI scripts.
# Every page in our site (login, register, sell, transactions, etc.) follows
# this same general layout.
#
# Use this file as a starting point when creating new CGI scripts.
# Just rename functions and fill in the parts you need.
# ============================================================


# ------------------------------------------
# 1. MODULE IMPORTS
# ------------------------------------------
# Enables helpful debugging output in the browser if a script crashes.
# (Displays Python tracebacks in HTML.)
import cgitb; cgitb.enable(display=0, logdir="/home/student/rsharma/public_html/cgi/logs")

# Built-in Python modules:
import html   # Used to safely escape user input before showing it on a webpage
import os     # Lets us access environment variables like REQUEST_METHOD
import cgi    # Parses incoming GET/POST form data from HTML forms

# Our custom project utility library (shared across all scripts)
from utils import (
    SITE_ROOT,             # Root path of our website (e.g., "/~cafcode/auction/")
    html_page,             # Helper: wraps the <body> HTML in a full page structure
    redirect,              # Helper: sends an HTTP redirect to another page
    expire_cookie,         # Helper: removes a cookie (used for logout/session expiry)
    require_valid_session, # Helper: verifies if a user is logged in and session is valid
    db                     # Helper: opens a connection to our MySQL database
)


# ------------------------------------------
# 2. CONSTANTS (OPTIONAL)
# ------------------------------------------
# Use this section for any fixed values used by this page.
# Example: time limits, maximum input lengths, or default values.
# (You can delete this section if not needed.)
# Example:
# MAX_BID_INCREMENT = 100.00
# SESSION_TIMEOUT = 3600  # seconds


# ------------------------------------------
# 3. RENDERING FUNCTIONS (HTML)
# ------------------------------------------
# These functions output HTML back to the browser.
# They build and print the <body> content for GET requests
# or to show success/error messages after form submissions.

def render_page(message: str = "", data=None):
    """
    Builds and prints the HTML for this page.

    Parameters:
        message (str): Optional feedback or error message shown to the user.
        data:         Optional data passed in from database or other logic.
    """
    body = f"""
<h1>Page Title</h1>

<!-- Display a message if one exists -->
{f'<p role="alert">{html.escape(message)}</p>' if message else ''}

<!-- Example form (replace or remove as needed) -->
<form method="post" action="{SITE_ROOT}cgi/example.py" novalidate>
  <label for="example">Example field:</label><br>
  <input type="text" id="example" name="example_input" required><br><br>
  <button type="submit">Submit</button>
</form>

<p><a href="{SITE_ROOT}index.html">Return to Home</a></p>
"""
    # CGI headers must come before any content.
    print("Content-Type: text/html; charset=utf-8\n")
    # html_page() wraps the body inside a full HTML structure.
    print(html_page("Page Title", body))


# ------------------------------------------
# 4. CORE LOGIC FUNCTIONS
# ------------------------------------------
# These handle the actual logic of the page — database queries,
# updates, validation, etc. They should not print HTML directly.
# Instead, they return messages or data for the rendering function to display.

def perform_action(conn, user, form):
    """
    Perform this page’s main action, such as inserting or reading data.

    Parameters:
        conn : database connection (from utils.db())
        user : dictionary with user info (from require_valid_session)
        form : FieldStorage object containing submitted form data

    Returns:
        str : message to show to user (success or error)
    """
    # Example structure:
    # description = form.getfirst("description", "").strip()
    # if not description:
    #     return "Description cannot be empty."
    #
    # with conn.cursor() as cur:
    #     cur.execute("INSERT INTO ExampleTable (user_id, text) VALUES (%s, %s)",
    #                 (user["user_id"], description))
    #     conn.commit()

    return "Action completed successfully."


# ------------------------------------------
# 5. MAIN REQUEST HANDLER
# ------------------------------------------
# This is the entry point for every CGI request.
# It decides whether the request came from a GET (load page)
# or a POST (form submission) and calls the right functions.

def main():
    # --- Step 1: Verify the user session ---
    user, sid = require_valid_session()
    if not user:
        # If no valid user, redirect to login page.
        # Also expire any existing cookie to force re-login.
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # --- Step 2: Check if this is a GET or POST request ---
    method = os.environ.get("REQUEST_METHOD", "GET")
    if method == "GET":
        # Display the form (default page view)
        render_page()
        return

    # --- Step 3: Parse form input for POST requests ---
    form = cgi.FieldStorage()

    # --- Step 4: Connect to database and perform the action ---
    conn = db()
    try:
        message = perform_action(conn, user, form)
    finally:
        # Always close the connection, even if something fails.
        conn.close()

    # --- Step 5: Render the page again with the result message ---
    render_page(message)


# ------------------------------------------
# 6. SCRIPT ENTRY POINT
# ------------------------------------------
# This ensures that main() only runs when the script is executed directly,
# not when it’s imported as a module.

if __name__ == "__main__":
    main()

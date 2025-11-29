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
import cgitb; cgitb.enable()

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
    Builds and prints the HTML for this page using the full shared styling
    system (header, card layout, CSS variables, buttons, etc.).

    This version is “Teaching Mode” — comments explain **why each part exists**,
    not just what it does.

    PARAMETERS:
        message (str): Optional success/error/info message for the user.
        data:         Optional data sent in from perform_action() or DB queries.
    """

    # Decide how to display the message:
    # - If truthy → style it as a red error/alert box.
    # - If empty  → show a muted instructional line.
    message_html = (
        f'<p class="error" role="alert">{html.escape(message)}</p>'
        if message
        else '<p class="muted">Use this template to practice CGI + CSS layout.</p>'
    )

    # -------------------------------------------------------------------------
    #  MAIN PAGE HTML
    #
    #  The <style> block defines our "design system":
    #    - CSS variables (colors)
    #    - header layout
    #    - card layout
    #    - button styles
    #    - simple table style
    #
    #  After the <style> block, the HTML structure follows this pattern:
    #
    #        <header class="top"> ... </header>
    #        <main class="content">
    #           <section class="card"> ... </section>
    #           <section class="card"> ... </section>
    #        </main>
    #
    #  This is the *same pattern* used on login.py and dashboard.py.
    # -------------------------------------------------------------------------
    body = f"""
<style>
  /* ============================================================
     1. CSS COLOR VARIABLES
     ------------------------------------------------------------
     We set these once and reuse them everywhere by calling:
         var(--brand), var(--bg), var(--card), etc.

     This makes the entire site easy to re-theme.
  ============================================================ */
  :root {{
    --brand: #0a58ca;
    --brand-600: #0947a5;
    --bg: #f6f7fb;
    --text: #1f2937;
    --muted: #6b7280;
    --card: #ffffff;
    --border-subtle: #e5e7eb;
  }}

  /* ============================================================
     2. GLOBAL BASE STYLES
     ------------------------------------------------------------
     System font, no margins, full-height layout, and a
     flex-column structure so the footer sticks to the bottom.
  ============================================================ */
  * {{
    box-sizing: border-box;
  }}
  html, body {{
    height: 100%;
    margin: 0;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    color: var(--text);
    background: var(--bg);
  }}
  body {{
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }}

  /* ============================================================
     3. TOP HEADER BAR ("dashboard-style" header)
     ------------------------------------------------------------
     - Flexbox places brand on the left and actions on the right.
     - White background with subtle bottom border.
  ============================================================ */
  header.top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    background: var(--card);
    border-bottom: 1px solid var(--border-subtle);
  }}
  .brand {{
    display: grid;
    gap: .25rem;
  }}
  .brand h1 {{
    margin: 0;
    font-size: 1.15rem;
    letter-spacing: .2px;
    font-weight: 800;
    color: var(--brand-600);
  }}
  .brand .sub {{
    color: var(--muted);
    font-size: .9rem;
  }}

  /* ============================================================
     4. MAIN CONTENT AREA
     ------------------------------------------------------------
     - Centers page content in a max-width column.
     - Cards provide consistent spacing and visual grouping.
  ============================================================ */
  main.content {{
    flex: 1;
    padding: 1.5rem;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
  }}

  .card {{
    background: var(--card);
    border: 1px solid var(--border-subtle);
    border-radius: .9rem;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
  }}
  .card h2 {{
    margin-top: 0;
    margin-bottom: .4rem;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--brand-600);
  }}
  .muted {{
    color: var(--muted);
    font-size: .95rem;
    margin-top: 0;
  }}

  /* ============================================================
     5. STATUS / ERROR BOX
     ------------------------------------------------------------
     - Red background
     - Border + text color tuned for accessibility
  ============================================================ */
  .error {{
    margin: .75rem 0 0;
    padding: .5rem .75rem;
    border-radius: .5rem;
    background: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
    font-size: .9rem;
  }}

  /* ============================================================
     6. BUTTON STYLES
     ------------------------------------------------------------
     Two types:
       - .btn-primary  → solid brand color
       - .btn-outline  → transparent with colored border
  ============================================================ */
  .btn {{
    display: inline-block;
    padding: .35rem .75rem;
    border-radius: .45rem;
    font-size: .9rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    border: 1px solid transparent;
  }}
  .btn-primary {{
    background: var(--brand);
    border-color: var(--brand-600);
    color: #fff;
  }}
  .btn-primary:hover {{
    background: var(--brand-600);
  }}
  .btn-outline {{
    background: transparent;
    border-color: var(--brand-600);
    color: var(--brand-600);
  }}
  .btn-outline:hover {{
    background: rgba(10, 88, 202, .06);
  }}

  /* ============================================================
     7. SIMPLE TABLE STYLE
     ------------------------------------------------------------
     Great for auction listings, transaction history, etc.
  ============================================================ */
  table.data {{
    width: 100%;
    border-collapse: collapse;
    font-size: .9rem;
  }}
  table.data th,
  table.data td {{
    padding: .5rem .6rem;
    border-bottom: 1px solid var(--border-subtle);
    text-align: left;
  }}
  table.data th {{
    font-weight: 600;
    color: var(--muted);
    background: #f9fafb;
  }}
  table.data tr:hover {{
    background: #f3f4f6;
  }}

  /* ============================================================
     8. RESPONSIVE ADJUSTMENTS
     ------------------------------------------------------------
     On small screens, the header stacks vertically.
  ============================================================ */
  @media (max-width: 720px) {{
    header.top {{
      flex-direction: column;
      align-items: flex-start;
      gap: .75rem;
    }}
  }}
</style>

<!-- ============================================================
     PAGE STRUCTURE
     ============================================================ -->

<header class="top">
  <div class="brand">
    <h1>CGI Learning Template</h1>
    <div class="sub">Practice CGI + CSS + Layout</div>
  </div>
  <div>
    <a href="{SITE_ROOT}index.html" class="btn btn-outline">Home</a>
    <a href="{SITE_ROOT}cgi/login.py" class="btn btn-primary">Log in</a>
  </div>
</header>

<main class="content" role="main">
  <!-- ======================= Card #1: Interactive Form ===================== -->
  <section class="card">
    <h2>Example Form (Interactive Playground)</h2>
    {message_html}

    <!--
      NOTE:
      This form posts back to THIS SAME SCRIPT.
      You can modify or expand the form to experiment.
    -->
    <form method="post" action="{SITE_ROOT}cgi/cgi_learning_template.py" novalidate>
      <label for="example">Example field:</label><br>
      <input
        type="text"
        id="example"
        name="example_input"
        style="margin-top:.25rem; padding:.35rem .5rem; border-radius:.4rem;
               border:1px solid #d1d5db; min-width:16ch;"
        required
      ><br><br>

      <button type="submit" class="btn btn-primary">Submit</button>
    </form>
  </section>

  <!-- ======================= Card #2: Learning Notes ======================= -->
  <section class="card">
    <h2>Notes</h2>
    <p class="muted">
      This page shares the SAME layout and CSS variables used in
      <strong>login.py</strong> and <strong>dashboard.py</strong>.  
      Edit the &lt;style&gt; block above and refresh the page to see how
      each rule changes the UI.
    </p>
  </section>
</main>
"""

    # Output full HTML
    # CGI headers must come before any content.
    print("Content-Type: text/html; charset=utf-8\n")
    # html_page() wraps the body inside a full HTML structure.
    print(html_page("CGI Learning Template", body))



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

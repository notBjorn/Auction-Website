#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py (Minimal Working Version)
# Purpose: Just confirm that navigation and CGI execution are working.
# =============================================================================

import cgitb; cgitb.enable()  # show errors in browser
from utils import html_page, require_valid_session, db

def main():
    # --- Step 1: Validate user session ---
    user_id, email = require_valid_session()  # redirects to login if invalid

    # --- Step 2: Connect to DB (optional for now) ---
    connection = db()
    cursor = connection.cursor()

    # --- Step 3: Minimal HTML output ---
    html = f"""
    <h1>Transactions</h1>
    <p>Welcome, {email}!</p>
    <p>This is the minimal working transactions page.</p>
    <p>If you see this, navigation and CGI execution are working correctly.</p>
    <p><a href="/~cafcode/dashboard.py">Back to Dashboard</a></p>
    """

    # --- Step 4: Output the page ---
    print(html_page("Transactions", html))

    # --- Step 5: Clean up ---
    cursor.close()
    connection.close()

# Standard CGI entry point
if __name__ == "__main__":
    main()

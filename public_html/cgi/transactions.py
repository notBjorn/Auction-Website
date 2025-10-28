#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py (Minimal Working Version)
# Confirms navigation + session handling. No DB access yet.
# =============================================================================

import cgitb; cgitb.enable()
import html
from utils import SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session

def main():
    user, sid = require_valid_session()

    # Not logged in or session expired → bounce to login, expire SID if present
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # Logged in → minimal page
    email = html.escape(user.get("email", ""))
    print("Content-Type: text/html\n")
    print(html_page("Transactions", f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Transactions</h2>
  <p>Welcome, {email}!</p>
  <p>If you can see this page, routing & session auth are working.</p>
  <nav>
    <ul>
      <li><a href="{SITE_ROOT}cgi/dashboard.py">Back to Dashboard</a></li>
      <li><a href="{SITE_ROOT}cgi/logout.py">Log out</a></li>
    </ul>
  </nav>
</main>
"""))

if __name__ == "__main__":
    main()

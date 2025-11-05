#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — dashboard.py
# Displays the logged-in user's dashboard. Requires a valid session.
# If the session is missing or expired, redirect to the login page and
# expire the SID cookie when present.
# =============================================================================

# ====== Imports / Setup ======================================================
import cgitb; cgitb.enable()
import html

from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session
)

# ====== Controller: Main Request Handler =====================================
def main():
    user, sid = require_valid_session()

    # ----- Not logged in or timed out ----------------------------------------
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # ----- Valid session: render dashboard -----------------------------------
    email = html.escape(user.get("email", ""))
    print("Content-Type: text/html\n")
    print(html_page("Dashboard", f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Welcome, {email}</h2>
  <nav>
    <ul>
      <li><a href="{SITE_ROOT}cgi/transactions.py">Your Transactions</a></li>
      <li><a href="{SITE_ROOT}cgi/sell.py">Sell an Item</a></li>
      <li><a href="{SITE_ROOT}cgi/logout.py">Log out</a></li>
    </ul>
  </nav>
</main>
"""))

# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()

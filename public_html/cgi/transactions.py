#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py (Section Placeholders Only)
# Adds the four sections: Selling, Purchases, Current Bids, Didn't Win.
# No database queries yet — just structure.
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

    email = html.escape(user.get("email", ""))

    body = f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Transactions</h2>
  <p>Welcome, {email}!</p>

  <section>
    <h3>1) Selling</h3>
    <p class="muted">No data yet. (We’ll plug in a query here.)</p>
  </section>

  <section>
    <h3>2) Purchases</h3>
    <p class="muted">No data yet. (We’ll plug in a query here.)</p>
  </section>

  <section>
    <h3>3) Current Bids</h3>
    <p class="muted">No data yet. (We’ll plug in a query here.)</p>
    <!-- Later: simple form to increase max bid -->
  </section>

  <section>
    <h3>4) Didn’t Win</h3>
    <p class="muted">No data yet. (We’ll plug in a query here.)</p>
  </section>

  <nav style="margin-top:1rem;">
    <a href="{SITE_ROOT}cgi/dashboard.py">Back to Dashboard</a> &middot;
    <a href="{SITE_ROOT}cgi/logout.py">Log out</a>
  </nav>
</main>

<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; line-height: 1.4; }}
  h1, h2 {{ margin-bottom: .25rem; }}
  main {{ max-width: 900px; margin: 1rem auto; padding: 0 1rem; }}
  section {{ border: 1px solid #ddd; border-radius: .5rem; padding: .75rem 1rem; margin: .75rem 0; }}
  .muted {{ color: #666; }}
</style>
"""
    print("Content-Type: text/html\n")
    print(html_page("Transactions", body))

if __name__ == "__main__":
    main()

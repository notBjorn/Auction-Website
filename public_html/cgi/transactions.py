#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py
# Selling + Purchases + Current Bids + Didn't Win (all LIVE).
# =============================================================================

import cgitb; cgitb.enable()
import html
from decimal import Decimal
from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db
)

from transactions_helpers import (
    fetch_selling_active, fetch_selling_sold,
    fetch_purchases, fetch_current_bids, fetch_didnt_win,
    render_selling_table, render_purchases_table,
    render_current_bids_table, render_didnt_win_table
)


# ------------------------------ CONTROLLER -----------------------------------

def main():
    user, sid = require_valid_session()
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    email   = html.escape(user.get("email", ""))
    user_id = user.get("user_id")
    user_name = html.escape(user.get("user_name", ""))

    conn = db()
    try:
        selling_active = fetch_selling_active(conn, user_id)
        selling_sold   = fetch_selling_sold(conn, user_id)
        purchases      = fetch_purchases(conn, user_id)
        current_bids   = fetch_current_bids(conn, user_id)
        didnt_win      = fetch_didnt_win(conn, user_id)
    finally:
        conn.close()


    body = f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Transactions</h2>
  <p>Welcome, {user_name}!</p>

  <section>
    <h3>1) Selling</h3>
    <h4>Active</h4>
    {render_selling_table(selling_active, "You are not selling anything yet.")}
    <h4>Sold</h4>
    {render_selling_table(selling_sold, "You have not sold anything yet.")}
  </section>

  <section>
    <h3>2) Purchases</h3>
    {render_purchases_table(purchases)}
    <p class="note">Note: End time is computed as start_time + duration (seconds).</p>
  </section>

  <section>
    <h3>3) Current Bids</h3>
    {render_current_bids_table(current_bids)}
  </section>

  <section>
    <h3>4) Didn’t Win</h3>
    {render_didnt_win_table(didnt_win)}
  </section>

  <nav style="margin-top:1rem;">
    <a href="{SITE_ROOT}cgi/dashboard.py">Back to Dashboard</a> &middot;
    <a href="{SITE_ROOT}cgi/logout.py">Log out</a>
  </nav>
</main>

<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; line-height: 1.45; }}
  main {{ max-width: 900px; margin: 1rem auto; padding: 0 1rem; }}
  section {{ border: 1px solid #ddd; border-radius: .5rem; padding: .75rem 1rem; margin: .9rem 0; }}
  .muted {{ color: #666; }}
  .note {{ color: #444; font-size: .95rem; }}
  .warn {{ color: #b45309; font-weight: 600; }}
  .tbl {{ width: 100%; border-collapse: collapse; }}
  .tbl th, .tbl td {{ padding: .5rem .6rem; border-bottom: 1px solid #e5e5e5; text-align: left; }}
  .tbl th {{ background: #fafafa; }}
  form.inline {{ display: inline-flex; gap: .35rem; align-items: center; }}
  input[type=number] {{ width: 8ch; }}
  button {{ cursor: pointer; }}
</style>
"""
    print("Content-Type: text/html\n")
    print(html_page("Transactions", body))

if __name__ == "__main__":
    main()

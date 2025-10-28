#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py
# Renders four sections; "Purchases" is LIVE with a real SQL query.
# =============================================================================

import cgitb; cgitb.enable()
import html
from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db
)

def fetch_purchases(conn, user_id):
    """
    A 'purchase' is defined as an ended auction where this user placed the
    highest bid. Final price is that highest bid.
    NOTE: We assume Auctions.duration is in SECONDS. If not, change INTERVAL unit.
    """
    sql = """
          SELECT
              A.auction_id,
              I.item_name,
              mb.max_amount    AS final_price,
              DATE_ADD(A.start_time, INTERVAL A.duration SECOND) AS end_time
          FROM Auctions A
                   JOIN Items    I  ON I.item_id = A.item_id
                   JOIN (
              SELECT auction_id, MAX(bid_amount) AS max_amount
              FROM Bids
              GROUP BY auction_id
          ) mb ON mb.auction_id = A.auction_id
                   JOIN Bids     B  ON B.auction_id = A.auction_id
              AND B.bid_amount = mb.max_amount
          WHERE A.status = 'ended'
            AND B.bidder_id = %s
          ORDER BY end_time DESC, A.auction_id DESC
              LIMIT 100 \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()

def render_purchases_table(rows):
    if not rows:
        return '<p class="muted">No purchases yet.</p>'

    # Minimal table; all values HTML-escaped
    out = []
    out.append('<table class="tbl">')
    out.append('<thead><tr><th>Auction</th><th>Item</th><th>Final Price</th><th>Ended</th></tr></thead>')
    out.append('<tbody>')
    for r in rows:
        auction_id = html.escape(str(r.get("auction_id", "")))
        item_name  = html.escape(str(r.get("item_name", "")))
        final_pr   = html.escape(str(r.get("final_price", "")))
        end_time   = html.escape(str(r.get("end_time", "")))
        out.append(f"<tr><td>#{auction_id}</td><td>{item_name}</td><td>${final_pr}</td><td>{end_time}</td></tr>")
    out.append('</tbody></table>')
    return "\n".join(out)

def main():
    user, sid = require_valid_session()

    # Not logged in or session expired → bounce to login, expire SID if present
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    email   = html.escape(user.get("email", ""))
    user_id = user.get("user_id")

    # Open DB just for Purchases (others are placeholders for now)
    conn = db()
    try:
        purchases = fetch_purchases(conn, user_id)
    finally:
        conn.close()

    purchases_html = render_purchases_table(purchases)

    body = f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Transactions</h2>
  <p>Welcome, {email}!</p>

  <section>
    <h3>1) Selling</h3>
    <p class="muted">Coming soon.</p>
  </section>

  <section>
    <h3>2) Purchases</h3>
    {purchases_html}
    <p class="note">Note: End time is computed as start_time + duration (assuming seconds).</p>
  </section>

  <section>
    <h3>3) Current Bids</h3>
    <p class="muted">Coming soon.</p>
  </section>

  <section>
    <h3>4) Didn’t Win</h3>
    <p class="muted">Coming soon.</p>
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
  .tbl {{ width: 100%; border-collapse: collapse; }}
  .tbl th, .tbl td {{ padding: .5rem .6rem; border-bottom: 1px solid #e5e5e5; text-align: left; }}
  .tbl th {{ background: #fafafa; }}
</style>
"""
    print("Content-Type: text/html\n")
    print(html_page("Transactions", body))

if __name__ == "__main__":
    main()

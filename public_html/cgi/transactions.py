#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py
# Selling and Purchases are LIVE. Current Bids / Didn’t Win are placeholders.
# =============================================================================

import cgitb; cgitb.enable()
import html
from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db
)

# --------------------------- QUERY HELPERS -----------------------------------

def fetch_selling(conn, user_id):
    """
    Selling = auctions for items owned by this user.
    Shows basic auction info. End time = start_time + duration (seconds).
    """
    sql = """
          SELECT
              A.auction_id,
              I.item_name,
              A.status,
              A.start_price,
              A.start_time,
              DATE_ADD(A.start_time, INTERVAL A.duration SECOND) AS end_time
          FROM Items I
                   JOIN Auctions A ON A.item_id = I.item_id
          WHERE I.owner_id = %s
          ORDER BY A.start_time DESC, A.auction_id DESC
              LIMIT 200 \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()

def fetch_purchases(conn, user_id):
    """
    A 'purchase' is an ended auction where this user placed the highest bid.
    Final price is that highest bid. Duration stored in SECONDS.
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

# --------------------------- RENDER HELPERS ----------------------------------

def render_selling_table(rows):
    if not rows:
        return '<p class="muted">You are not selling anything yet.</p>'

    out = []
    out.append('<table class="tbl">')
    out.append('<thead><tr>'
               '<th>Auction</th><th>Item</th><th>Status</th>'
               '<th>Start Price</th><th>Start</th><th>End</th>'
               '</tr></thead>')
    out.append('<tbody>')
    for r in rows:
        auction_id = html.escape(str(r.get("auction_id","")))
        item_name  = html.escape(str(r.get("item_name","")))
        status     = html.escape(str(r.get("status","")))
        start_pr   = html.escape(str(r.get("start_price","")))
        start_ts   = html.escape(str(r.get("start_time","")))
        end_ts     = html.escape(str(r.get("end_time","")))
        out.append(
            f"<tr>"
            f"<td>#{auction_id}</td>"
            f"<td>{item_name}</td>"
            f"<td>{status}</td>"
            f"<td>${start_pr}</td>"
            f"<td>{start_ts}</td>"
            f"<td>{end_ts}</td>"
            f"</tr>"
        )
    out.append('</tbody></table>')
    return "\n".join(out)

def render_purchases_table(rows):
    if not rows:
        return '<p class="muted">No purchases yet.</p>'

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

    # DB work for live sections
    conn = db()
    try:
        selling   = fetch_selling(conn, user_id)
        purchases = fetch_purchases(conn, user_id)
    finally:
        conn.close()

    selling_html   = render_selling_table(selling)
    purchases_html = render_purchases_table(purchases)

    body = f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Transactions</h2>
  <p>Welcome, {email}!</p>

  <section>
    <h3>1) Selling</h3>
    {selling_html}
  </section>

  <section>
    <h3>2) Purchases</h3>
    {purchases_html}
    <p class="note">Note: End time is computed as start_time + duration (seconds).</p>
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

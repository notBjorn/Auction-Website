#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py
# Selling + Purchases + Current Bids are LIVE. Didn’t Win is a placeholder.
# =============================================================================

import cgitb; cgitb.enable()
import html
from decimal import Decimal
from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db
)

# --------------------------- QUERY HELPERS -----------------------------------

def fetch_selling(conn, user_id):
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

def fetch_current_bids(conn, user_id):
    """
    Current Bids = running auctions where this user has bid.
    Shows current leading price, your max, and whether you are leading.
    """
    sql = """
          SELECT
              A.auction_id,
              I.item_name,
              A.start_price,
              A.start_time,
              DATE_ADD(A.start_time, INTERVAL A.duration SECOND) AS end_time,
              u.user_max,
              allmax.max_amount AS current_price,
              (u.user_max = allmax.max_amount) AS is_leading
          FROM Auctions A
                   JOIN Items I ON I.item_id = A.item_id
                   JOIN (
              SELECT auction_id, MAX(bid_amount) AS user_max
              FROM Bids
              WHERE bidder_id = %s
              GROUP BY auction_id
          ) u ON u.auction_id = A.auction_id
                   LEFT JOIN (
              SELECT auction_id, MAX(bid_amount) AS max_amount
              FROM Bids
              GROUP BY auction_id
          ) allmax ON allmax.auction_id = A.auction_id
          WHERE A.status = 'running'
          ORDER BY end_time ASC, A.auction_id ASC
              LIMIT 200 \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()

# --------------------------- RENDER HELPERS ----------------------------------

def render_money(x):
    if x is None: return "-"
    try:
        return f"{Decimal(x):.2f}"
    except Exception:
        return html.escape(str(x))

def render_selling_table(rows):
    if not rows:
        return '<p class="muted">You are not selling anything yet.</p>'
    out = []
    out.append('<table class="tbl">')
    out.append('<thead><tr>'
               '<th>Auction</th><th>Item</th><th>Status</th>'
               '<th>Start Price</th><th>Start</th><th>End</th>'
               '</tr></thead><tbody>')
    for r in rows:
        out.append(
            f"<tr>"
            f"<td>#{html.escape(str(r.get('auction_id','')))}</td>"
            f"<td>{html.escape(str(r.get('item_name','')))}</td>"
            f"<td>{html.escape(str(r.get('status','')))}</td>"
            f"<td>${render_money(r.get('start_price'))}</td>"
            f"<td>{html.escape(str(r.get('start_time','')))}</td>"
            f"<td>{html.escape(str(r.get('end_time','')))}</td>"
            f"</tr>"
        )
    out.append('</tbody></table>')
    return "\n".join(out)

def render_purchases_table(rows):
    if not rows:
        return '<p class="muted">No purchases yet.</p>'
    out = []
    out.append('<table class="tbl">')
    out.append('<thead><tr><th>Auction</th><th>Item</th><th>Final Price</th><th>Ended</th></tr></thead><tbody>')
    for r in rows:
        out.append(
            f"<tr>"
            f"<td>#{html.escape(str(r.get('auction_id','')))}</td>"
            f"<td>{html.escape(str(r.get('item_name','')))}</td>"
            f"<td>${render_money(r.get('final_price'))}</td>"
            f"<td>{html.escape(str(r.get('end_time','')))}</td>"
            f"</tr>"
        )
    out.append('</tbody></table>')
    return "\n".join(out)

def render_current_bids_table(rows):
    if not rows:
        return '<p class="muted">You have no active bids.</p>'

    out = []
    out.append('<table class="tbl">')
    out.append('<thead><tr>'
               '<th>Auction</th><th>Item</th>'
               '<th>Current Price</th><th>Your Max</th><th>Status</th>'
               '<th>Increase Max</th>'
               '</tr></thead><tbody>')
    for r in rows:
        auction_id = r.get('auction_id')
        item_name  = html.escape(str(r.get('item_name','')))
        current_px = r.get('current_price') or r.get('start_price')
        your_max   = r.get('user_max')
        is_leading = bool(r.get('is_leading'))

        # compute a minimal allowed next bid on the server
        try:
            base = Decimal(current_px or 0)
        except Exception:
            base = Decimal("0")
        min_next = base + Decimal("0.01")

        out.append(
            "<tr>"
            f"<td>#{html.escape(str(auction_id))}</td>"
            f"<td>{item_name}</td>"
            f"<td>${render_money(current_px)}</td>"
            f"<td>${render_money(your_max)}</td>"
            f"<td>{'Leading' if is_leading else '<span class=\"warn\">Outbid</span>'}</td>"
            f"<td>"
            f"  <form method=\"post\" action=\"{SITE_ROOT}cgi/bid_update.py\" class=\"inline\">"
            f"    <input type=\"hidden\" name=\"auction_id\" value=\"{html.escape(str(auction_id))}\">"
            f"    <input type=\"number\" name=\"bid_amount\" step=\"0.01\" min=\"{min_next}\" "
            f"           placeholder=\"{min_next}\" required>"
            f"    <button type=\"submit\">Raise</button>"
            f"  </form>"
            f"</td>"
            "</tr>"
        )
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

    conn = db()
    try:
        selling      = fetch_selling(conn, user_id)
        purchases    = fetch_purchases(conn, user_id)
        current_bids = fetch_current_bids(conn, user_id)
    finally:
        conn.close()

    body = f"""
<header><h1>CS370 Auction Portal</h1></header>
<main>
  <h2>Transactions</h2>
  <p>Welcome, {email}!</p>

  <section>
    <h3>1) Selling</h3>
    {render_selling_table(selling)}
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

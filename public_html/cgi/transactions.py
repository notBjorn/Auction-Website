#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py (LEAN FINAL USING utils.py)
# =============================================================================

import cgitb; cgitb.enable()
import html

from utils import (
    html_page, require_valid_session, SITE_ROOT,
    redirect, expire_cookie, query_all
)

# ====== SQL DEFINITIONS =======================================================
SQL_SELLING_OPEN = """
                   SELECT a.auction_id, i.item_id, i.title, a.end_time,
                          (SELECT MAX(b.amount) FROM Bid b WHERE b.auction_id = a.auction_id) AS current_high
                   FROM Auction a
                            JOIN Item i ON i.item_id = a.item_id
                   WHERE i.seller_id = %s
                     AND a.status = 'OPEN'
                   ORDER BY a.end_time ASC \
                   """

SQL_SELLING_SOLD = """
                   SELECT a.auction_id, i.item_id, i.title, a.end_time,
                          w.amount AS winning_amount,
                          u.user_name AS winner_name
                   FROM Auction a
                            JOIN Item i ON i.item_id = a.item_id
                            JOIN (
                       SELECT b1.auction_id, b1.bidder_id, b1.amount
                       FROM Bid b1
                                JOIN (
                           SELECT auction_id, MAX(amount) AS max_amt
                           FROM Bid
                           GROUP BY auction_id
                       ) mx ON mx.auction_id = b1.auction_id AND mx.max_amt = b1.amount
                   ) w ON w.auction_id = a.auction_id
                            JOIN User u ON u.user_id = w.bidder_id
                   WHERE i.seller_id = %s
                     AND a.status = 'CLOSED'
                   ORDER BY a.end_time DESC \
                   """

SQL_PURCHASES_WON = """
                    SELECT a.auction_id, i.item_id, i.title, a.end_time,
                           s.user_name AS seller_name,
                           w.amount AS winning_amount
                    FROM Auction a
                             JOIN Item i ON i.item_id = a.item_id
                             JOIN User s ON s.user_id = i.seller_id
                             JOIN (
                        SELECT b1.auction_id, b1.bidder_id, b1.amount
                        FROM Bid b1
                                 JOIN (
                            SELECT auction_id, MAX(amount) AS max_amt
                            FROM Bid
                            GROUP BY auction_id
                        ) mx ON mx.auction_id = b1.auction_id AND mx.max_amt = b1.amount
                    ) w ON w.auction_id = a.auction_id
                    WHERE a.status = 'CLOSED'
                      AND w.bidder_id = %s
                    ORDER BY a.end_time DESC \
                    """

SQL_CURRENT_BIDS = """
                   SELECT a.auction_id, i.item_id, i.title, a.end_time,
                          (SELECT MAX(b2.amount) FROM Bid b2 WHERE b2.auction_id = a.auction_id) AS current_high,
                          (SELECT MAX(b3.amount) FROM Bid b3
                           WHERE b3.auction_id = a.auction_id AND b3.bidder_id = %s) AS my_high
                   FROM Auction a
                            JOIN Item i ON i.item_id = a.item_id
                   WHERE a.status = 'OPEN'
                     AND EXISTS (
                       SELECT 1 FROM Bid bx
                       WHERE bx.auction_id = a.auction_id AND bx.bidder_id = %s
                   )
                   ORDER BY a.end_time ASC \
                   """

SQL_DIDNT_WIN = """
                SELECT a.auction_id, i.item_id, i.title, a.end_time,
                       w.amount AS winning_amount,
                       u.user_name AS winner_name
                FROM Auction a
                         JOIN Item i ON i.item_id = a.item_id
                         JOIN (
                    SELECT b1.auction_id, b1.bidder_id, b1.amount
                    FROM Bid b1
                             JOIN (
                        SELECT auction_id, MAX(amount) AS max_amt
                        FROM Bid
                        GROUP BY auction_id
                    ) mx ON mx.auction_id = b1.auction_id AND mx.max_amt = b1.amount
                ) w ON w.auction_id = a.auction_id
                         JOIN User u ON u.user_id = w.bidder_id
                WHERE a.status = 'CLOSED'
                  AND EXISTS (
                    SELECT 1 FROM Bid me
                    WHERE me.auction_id = a.auction_id AND me.bidder_id = %s
                )
                  AND w.bidder_id <> %s
                ORDER BY a.end_time DESC \
                """

# ====== RENDER HELPERS =======================================================

def _fmt_money(val):
    if val is None:
        return "—"
    try:
        return f"${float(val):.2f}"
    except Exception:
        return html.escape(str(val))

def _fmt_dt(dt):
    # utils/db may return Python datetime or str; handle both
    try:
        return html.escape(dt.strftime("%Y-%m-%d %H:%M"))
    except Exception:
        return html.escape(str(dt or ""))

def render_nav():
    return f"""
<nav>
  <a href="{SITE_ROOT}cgi/dashboard.py">Dashboard</a>
  <a href="{SITE_ROOT}cgi/transactions.py"><strong>Transactions</strong></a>
  <a href="{SITE_ROOT}cgi/logout.py">Log Out</a>
</nav>
""".strip()

def render_selling(open_rows, sold_rows):
    # Active
    if open_rows:
        trs = []
        for r in open_rows:
            trs.append(
                "<tr>"
                f"<td>{html.escape(r.get('title',''))}</td>"
                f"<td>{_fmt_dt(r.get('end_time'))}</td>"
                f"<td>{_fmt_money(r.get('current_high'))}</td>"
                f"<td><a href='{SITE_ROOT}cgi/auction.py?id={r['auction_id']}'>View</a></td>"
                "</tr>"
            )
        active_html = (
            "<table><thead><tr><th>Title</th><th>Ends</th><th>Current Highest</th><th></th></tr></thead>"
            f"<tbody>{''.join(trs)}</tbody></table>"
        )
    else:
        active_html = "<p>No active listings yet.</p>"

    # Sold
    if sold_rows:
        trs = []
        for r in sold_rows:
            trs.append(
                "<tr>"
                f"<td>{html.escape(r.get('title',''))}</td>"
                f"<td>{_fmt_dt(r.get('end_time'))}</td>"
                f"<td>{_fmt_money(r.get('winning_amount'))}</td>"
                f"<td>{html.escape(r.get('winner_name',''))}</td>"
                "</tr>"
            )
        sold_html = (
            "<table><thead><tr><th>Title</th><th>Ended</th><th>Final Price</th><th>Winner</th></tr></thead>"
            f"<tbody>{''.join(trs)}</tbody></table>"
        )
    else:
        sold_html = "<p>No sold items yet.</p>"

    return (
            "<section id='selling'>"
            "<h2>Selling</h2>"
            "<h3>Active Listings</h3>" + active_html +
            "<h3>Sold Items</h3>" + sold_html +
            "</section>"
    )

def render_purchases(rows):
    if not rows:
        return "<section id='purchases'><h2>Purchases</h2><p>No purchases yet.</p></section>"
    trs = []
    for r in rows:
        trs.append(
            "<tr>"
            f"<td>{html.escape(r.get('title',''))}</td>"
            f"<td>{html.escape(r.get('seller_name',''))}</td>"
            f"<td>{_fmt_money(r.get('winning_amount'))}</td>"
            f"<td>{_fmt_dt(r.get('end_time'))}</td>"
            "</tr>"
        )
    return (
        "<section id='purchases'><h2>Purchases</h2>"
        "<table><thead><tr><th>Title</th><th>Seller</th><th>Final Price</th><th>Ended</th></tr></thead>"
        f"<tbody>{''.join(trs)}</tbody></table></section>"
    )

def render_current_bids(rows):
    if not rows:
        return "<section id='current-bids'><h2>Current Bids</h2><p>No current bids yet.</p></section>"
    trs = []
    for r in rows:
        cur_high = r.get("current_high")
        my_high  = r.get("my_high")
        status = "Outbid"
        try:
            if my_high is not None and (cur_high is None or float(my_high) >= float(cur_high)):
                status = "You are currently highest"
        except Exception:
            pass
        form_html = (
            f"<form method='post' action='{SITE_ROOT}cgi/bid_update.py' class='inline-form'>"
            f"<input type='hidden' name='auction_id' value='{r['auction_id']}'>"
            f"<label>New Max: <input name='amount' type='number' step='0.01' min='0.01' required></label>"
            f"<button type='submit'>Increase Max Bid</button>"
            f"</form>"
        )
        trs.append(
            "<tr>"
            f"<td>{html.escape(r.get('title',''))}</td>"
            f"<td>{_fmt_dt(r.get('end_time'))}</td>"
            f"<td>{_fmt_money(cur_high)}</td>"
            f"<td>{status}</td>"
            f"<td>{form_html}</td>"
            "</tr>"
        )
    return (
        "<section id='current-bids'><h2>Current Bids</h2>"
        "<table><thead><tr><th>Title</th><th>Ends</th><th>Current Highest</th><th>Status</th><th></th></tr></thead>"
        f"<tbody>{''.join(trs)}</tbody></table></section>"
    )

def render_didnt_win(rows):
    if not rows:
        return "<section id='didnt-win'><h2>Didn't Win</h2><p>No lost auctions yet.</p></section>"
    trs = []
    for r in rows:
        trs.append(
            "<tr>"
            f"<td>{html.escape(r.get('title',''))}</td>"
            f"<td>{_fmt_dt(r.get('end_time'))}</td>"
            f"<td>{_fmt_money(r.get('winning_amount'))}</td>"
            f"<td>{html.escape(r.get('winner_name',''))}</td>"
            "</tr>"
        )
    return (
        "<section id='didnt-win'><h2>Didn't Win</h2>"
        "<table><thead><tr><th>Title</th><th>Ended</th><th>Winning Bid</th><th>Winner</th></tr></thead>"
        f"<tbody>{''.join(trs)}</tbody></table></section>"
    )

# ====== MAIN ================================================================

def main():
    # 1) Session
    user, sid = require_valid_session()
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return
    uid = user["user_id"] if isinstance(user, dict) and "user_id" in user else int(user)

    # 2) Queries (via utils.query_all)
    selling_open   = query_all(SQL_SELLING_OPEN,  (uid,))
    selling_sold   = query_all(SQL_SELLING_SOLD,  (uid,))
    purchases_won  = query_all(SQL_PURCHASES_WON, (uid,))
    current_bids   = query_all(SQL_CURRENT_BIDS,  (uid, uid))
    didnt_win      = query_all(SQL_DIDNT_WIN,     (uid, uid))

    # 3) Render
    body_html = "\n".join([
        "<h1>My Transactions</h1>",
        render_nav(),
        render_selling(selling_open, selling_sold),
        render_purchases(purchases_won),
        render_current_bids(current_bids),
        render_didnt_win(didnt_win),
    ])

    # 4) Response
    print("Content-Type: text/html\n")
    print(html_page("My Transactions", body_html))

# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()

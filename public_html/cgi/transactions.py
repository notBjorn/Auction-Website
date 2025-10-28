#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py (COMMENT SCAFFOLD)
# Purpose: Display a logged-in user's transaction-related activity in four
#          required categories only:
#            1) Selling
#            2) Purchases
#            3) Current Bids
#            4) Didn't Win
#
# Constraints (per rubric):
#   - Server-side CGI only (no JS required for core logic).
#   - Auth via our own session table (no third-party auth).
#   - Backed by MySQL.
#   - Output must be valid HTML5.
#   - Provide a control to increase a user's maximum bid on items in "Current Bids".
# =============================================================================


# ====== Imports / Site Utilities (used by our project) =======================
import cgitb; cgitb.enable()
from utils import (
    html_page, require_valid_session, SITE_ROOT,
    redirect, expire_cookie
)

# Get user_id from the session; if missing → redirect to login.
# Open DB connection.
# Run the four query blocks above (or consolidate with CTEs if you prefer).
# Render results with headings:
# “Selling” → subsections “Open” and “Sold”
# “Purchases”
# “Current Bids” (with “Increase Max Bid” links)
# “Didn’t Win”
#Close DB; send the response.


# ====== SQL Sketches (parameterized; no string concatenation) ================
# -- 1) Selling (OPEN):
# SELECT a.auction_id, i.item_id, i.title, a.end_time
#   FROM Auction a
#   JOIN Item i ON i.item_id = a.item_id
#  WHERE i.seller_id = %s AND a.status = 'OPEN'
#  ORDER BY a.end_time ASC;
#
# -- 1b) Selling (SOLD):
# SELECT a.auction_id, i.item_id, i.title, a.end_time
#   FROM Auction a
#   JOIN Item i ON i.item_id = a.item_id
#  WHERE i.seller_id = %s AND a.status = 'CLOSED'
#  ORDER BY a.end_time DESC;
#
# -- 2) Purchases (won by current user):
# SELECT a.auction_id, i.item_id, i.title, MAX(b.amount) AS winning_bid
#   FROM Auction a
#   JOIN Item i ON i.item_id = a.item_id
#   JOIN Bid  b ON b.auction_id = a.auction_id
#  WHERE a.status = 'CLOSED'
#    AND b.bidder_id = %s
#  GROUP BY a.auction_id
# HAVING MAX(b.amount) = (
#     SELECT MAX(b2.amount) FROM Bid b2 WHERE b2.auction_id = a.auction_id
# )
#  ORDER BY a.end_time DESC;
#
# -- 3) Current Bids (OPEN auctions with at least one bid by current user):
# SELECT a.auction_id, i.item_id, i.title,
#        (SELECT MAX(b2.amount) FROM Bid b2 WHERE b2.auction_id = a.auction_id) AS current_high,
#        (SELECT MAX(b3.amount) FROM Bid b3 WHERE b3.auction_id = a.auction_id AND b3.bidder_id = %s) AS my_high
#   FROM Auction a
#   JOIN Item i ON i.item_id = a.item_id
#  WHERE a.status = 'OPEN'
#    AND EXISTS (SELECT 1 FROM Bid bx WHERE bx.auction_id = a.auction_id AND bx.bidder_id = %s)
#  ORDER BY a.end_time ASC;
#
# -- 4) Didn't Win (bid but lost on CLOSED auctions):
# SELECT a.auction_id, i.item_id, i.title,
#        (SELECT MAX(b2.amount) FROM Bid b2 WHERE b2.auction_id = a.auction_id) AS winning_bid
#   FROM Auction a
#   JOIN Item i ON i.item_id = a.item_id
#  WHERE a.status = 'CLOSED'
#    AND EXISTS (SELECT 1 FROM Bid bx WHERE bx.auction_id = a.auction_id AND bx.bidder_id = %s)
#    AND (SELECT MAX(bm.amount) FROM Bid bm WHERE bm.auction_id = a.auction_id AND bm.bidder_id = %s)
#        < (SELECT MAX(bw.amount) FROM Bid bw WHERE bw.auction_id = a.auction_id)
#  ORDER BY a.end_time DESC;


# ====== Controller ===========================================================
def main():
#   1) Ensure valid login:
    user, sid = require_valid_session()     # returns current user's user_id or redirects
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

#   2) Fetch four datasets using the SQL above (with parameter uid where needed):
#       selling_open   = query_all(SQL_SELLING_OPEN,   [uid])
#       selling_closed = query_all(SQL_SELLING_CLOSED, [uid])
#       purchases      = query_all(SQL_PURCHASES,      [uid])
#       current_bids   = query_all(SQL_CURRENT_BIDS,   [uid, uid])
#       didnt_win      = query_all(SQL_DIDNT_WIN,      [uid, uid])

#   3) Render a single HTML5 page with four sections:
#       - Section: "Selling"
#           Subsection: "Active Listings"  (selling_open)
#           Subsection: "Sold Items"       (selling_closed)
#       - Section: "Purchases"             (purchases)
#       - Section: "Current Bids"          (current_bids)
#           For each row:
#             • Show item title and current_high
#             • If my_high < current_high => display "Outbid" notice
#             • Always show a small form/button to "Increase Max Bid"
#               -> action points to /cgi/update_bid.py?auction_id=... (GET or POST)
#       - Section: "Didn't Win"            (didnt_win)
#           Show the winning_bid for each item

# ====== HTML Structure (keep valid, minimal, and semantic) ===================
body = f"""
<h1>My Transactions</h1>
<nav>
    <a href="{SITE_ROOT}cgi/dashboard.py">Dashboard</a>
    <a href="{SITE_ROOT}cgi/logout.py">Log Out</a>
    <strong>Transactions</strong>
</nav>

<section id="selling">
    <h2>Selling</h2>
    <h3>Active Listings</h3>
    <p>No active listings yet.</p>
    <h3>Sold Items</h3>
    <p>No sold items yet.</p>
</section>

<section id ="purchases">
    <h2>Purchases</h2>
    <p>No purchases yet.</p>
</section>

<section id ="current-bids">
    <h2>Current Bids</h2>
    <p>No current bids yet.</p>
</section>

<section id="didnt-win">
    <h2>Didn't Win</h2>
    <p>No lost auctions yet.</p>
</section>
"""

# 3) Emit full HTML5 via our helper (prints headers + markup)
print("Content-Type: text/html\n")
print(html_page("My Transactions", body))
# =============================================================================

#   4) No filters/pagination required by rubric. Keep markup simple and valid.
#      Keep all dynamic values HTML-escaped. No inline JS needed.

#   5) Print via html_page(title, body_html) helper (or equivalent):
#       html = build_html(selling_open, selling_closed, purchases, current_bids, didnt_win)
#       print(html_page("My Transactions", html))




# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()

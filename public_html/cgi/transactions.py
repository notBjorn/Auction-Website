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
# Run the four query blocks
# Render results with headings:
# “Selling” → subsections “Open” and “Sold”
# “Purchases”
# “Current Bids” (with “Increase Max Bid” links)
# “Didn’t Win”
#Close DB; send the response.


# ====== SQL DEFINITIONS (parameterized; no string concat) ====================
# - Keep SQL here as simple, reviewable constants.
# - These are *shape* guides; add columns/aliases as you need for rendering.

# ====== Purpose: Lists the current open auctions that the logged-in user is selling. ======
SQL_SELLING_OPEN = """
                   SELECT a.auction_id, i.item_id, i.title, a.end_time,
                          (SELECT MAX(b.amount) FROM Bid b WHERE b.auction_id = a.auction_id) AS current_high
                   FROM Auction a
                            JOIN Item i ON i.item_id = a.item_id
                   WHERE i.seller_id = %s
                     AND a.status = 'OPEN'
                   ORDER BY a.end_time ASC; \
                   """

# ====== Purpose: Shows all closed auctions that this user sold. ======
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
                   ORDER BY a.end_time DESC; \
                   """

# ====== Purpose: Shows auctions that the user won as a buyer. ======
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
                    ORDER BY a.end_time DESC; \
                    """

# ====== Purpose: Lists auctions still open that this user has bid on. ======
SQL_CURRENT_BIDS = """
                   SELECT a.auction_id, i.item_id, i.title, a.end_time,
                          (SELECT MAX(b2.amount) FROM Bid b2 WHERE b2.auction_id = a.auction_id) AS current_high,
                          (SELECT MAX(b3.amount) FROM Bid b3
                           WHERE b3.auction_id = a.auction_id AND b3.bidder_id = %s) AS my_high
                   FROM Auction a
                            JOIN Item i ON i.item_id = a.item_id
                   WHERE a.status = 'OPEN'
                     AND EXISTS (SELECT 1 FROM Bid bx
                                 WHERE bx.auction_id = a.auction_id AND bx.bidder_id = %s)
                   ORDER BY a.end_time ASC; \
                   """

# ====== Purpose: Shows auctions the user participated in but lost. ======
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
                  AND EXISTS (SELECT 1 FROM Bid me
                              WHERE me.auction_id = a.auction_id AND me.bidder_id = %s)
                  AND w.bidder_id <> %s
                ORDER BY a.end_time DESC; \
                """


# ====== MAIN CONTROLLER ======================================================
def main():
    # -------------------------------------------------------------------------
    # 1) SESSION GUARD:
    #    - Ensure the user is logged in. If not, expire cookie and redirect.
    #    - Extract the current user's user_id (uid) for query parameters.
    # -------------------------------------------------------------------------
    user, sid = require_valid_session()     # returns current user's user_id or redirects
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # -------------------------------------------------------------------------
    # 2) DB CONNECTION / QUERY EXECUTION:
    #    - Open a DB connection (from utils, or inline here if allowed).
    #    - Execute the 4 query sets (selling_open, selling_sold, purchases_won,
    #      current_bids, didnt_win), passing uid as needed.
    #    - Keep results as simple lists of dicts for rendering.
    #    - Handle exceptions with cgitb (already enabled) or a friendly page.
    # -------------------------------------------------------------------------
    # Example sketch if you have utils.query_all():
    # selling_open   = query_all(SQL_SELLING_OPEN,   [uid])
    # selling_sold   = query_all(SQL_SELLING_SOLD,   [uid])
    # purchases_won  = query_all(SQL_PURCHASES_WON,  [uid])
    # current_bids   = query_all(SQL_CURRENT_BIDS,   [uid, uid])
    # didnt_win      = query_all(SQL_DIDNT_WIN,      [uid, uid])

    # If you don't have query helpers, add a tiny wrapper here (still 2 files total).

    # -------------------------------------------------------------------------
    # 3) HTML RENDERING (SERVER-SIDE ONLY):
    #    - Build four <section> blocks:
    #        a) Selling → "Active Listings" (selling_open), "Sold Items" (selling_sold)
    #        b) Purchases (purchases_won)
    #        c) Current Bids (current_bids) → show "Outbid" when my_high < current_high
    #           and always include a small form pointing to bid_update.py
    #        d) Didn't Win (didnt_win)
    #    - For empty result sets, show the provided empty-state messages.
    #    - Keep markup semantic: <section>, <h2>/<h3>, <table> or <ul>, etc.
    #    - Escape dynamic text (titles, names).
    # -------------------------------------------------------------------------
    # body_parts = []
    # body_parts.append(render_nav())
    # body_parts.append(render_selling(selling_open, selling_sold))
    # body_parts.append(render_purchases(purchases_won))
    # body_parts.append(render_current_bids(current_bids))
    # body_parts.append(render_didnt_win(didnt_win))
    #
    # body_html = "\n".join(body_parts)

    # -------------------------------------------------------------------------
    # 4) HTTP RESPONSE:
    #    - Output the final HTML5 document via html_page(title, body_html).
    #    - Do not print any headers except Content-Type (html_page may handle).
    # -------------------------------------------------------------------------
    # print("Content-Type: text/html\n")
    # print(html_page("My Transactions", body_html))

    # NOTE: The actual rendering functions are kept in this file (below) to
    # keep the two-file requirement. They're simple string builders.
    # pass


# ====== RENDER HELPERS (simple string builders; no DB calls) =================
# - Each function receives rows (list[dict]) and returns an HTML snippet.
# - Use html.escape for titles/user names if your html_page doesn't.
# - Keep the "Increase Max Bid" form pointing to bid_update.py (POST).

# def render_nav(): ...

# def render_selling(open_rows, sold_rows): ...
#   - <section id="selling">
#   - <h2>Selling</h2>
#   - Subsection "Active Listings": table with Title | Ends | Current Highest | [View]
#     * If current_high is NULL: show "—" or "Starting price"
#   - Subsection "Sold Items": table with Title | Ended | Final Price | Winner
#   - Empty states if lists are empty.

# def render_purchases(rows): ...
#   - <section id="purchases">
#   - Columns: Title | Seller | Final Price | Ended
#   - Empty state if none.

# def render_current_bids(rows): ...
#   - <section id="current-bids">
#   - Columns: Title | Ends | Current Highest | Status | [Increase Max Bid form]
#   - Status rules:
#       * if my_high is NULL or my_high < current_high → "Outbid"
#       * else → "You are currently highest"
#   - Form posts to: f"{SITE_ROOT}cgi/bid_update.py"
#       <form method="post" action=".../bid_update.py">
#         <input type="hidden" name="auction_id" value="{auction_id}">
#         <label>New Max: <input name="amount" type="number" step="0.01" required></label>
#         <button type="submit">Increase Max Bid</button>
#       </form>
#   - Always show the form (rubric says include a control regardless of status).

# def render_didnt_win(rows): ...
#   - <section id="didnt-win">
#   - Columns: Title | Ended | Winning Bid | Winner
#   - Optional: also show "Your Max" if you add that to the SQL.
#   - Empty state if none.

# ====== HTML Structure (For testing only, this needs to be rendered dynamically above) ===================
# ====== Delete this section once 2 & 3 function properly =======
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — bid_update.py
# Minimal handler to raise a user's max bid on a running auction.
# =============================================================================

import cgitb; cgitb.enable(display=0, logdir="/home/student/rsharma/public_html/cgi/logs")
import sys, html
from decimal import Decimal, InvalidOperation
from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db
)

def bad_request(msg, back_href):
    print("Content-Type: text/html\n")
    print(html_page("Bid Error", f"""
    <h1>Bid Error</h1>
    <p>{html.escape(msg)}</p>
    <p><a href="{back_href}">Back to Transactions</a></p>
    """))
    sys.exit(0)

def main():
    user, sid = require_valid_session()
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # --- Read POST fields ---
    try:
        import cgi
        form = cgi.FieldStorage()
        auction_id = int(form.getfirst("auction_id", "").strip())
        bid_amount_str = form.getfirst("bid_amount", "").strip()
        bid_amount = Decimal(bid_amount_str)
    except (ValueError, InvalidOperation, AttributeError):
        bad_request("Invalid form data.", f"{SITE_ROOT}cgi/transactions.py")

    # --- DB checks & insert ---
    conn = db()
    try:
        with conn.cursor() as cur:
            # 1) Ensure auction exists and is running
            cur.execute("""
                        SELECT A.auction_id, A.item_id, A.start_price, A.status
                        FROM Auctions A
                        WHERE A.auction_id = %s
                        """, (auction_id,))
            row = cur.fetchone()
            if not row:
                bad_request("Auction not found.", f"{SITE_ROOT}cgi/transactions.py")
            if row["status"] != "running":
                bad_request("Auction is not running.", f"{SITE_ROOT}cgi/transactions.py")

            start_price = row["start_price"]

            # 2) Get current max bid on this auction
            cur.execute("""
                        SELECT MAX(bid_amount) AS max_amt
                        FROM Bids
                        WHERE auction_id = %s
                        """, (auction_id,))
            mx = cur.fetchone()
            current_max = mx["max_amt"] if mx and mx["max_amt"] is not None else start_price

            # 3) Enforce minimal increment: strictly greater than current_max
            if bid_amount <= current_max:
                bad_request(f"Your bid must be greater than current price ${current_max}.",
                            f"{SITE_ROOT}cgi/transactions.py")

            # 4) Insert bid
            cur.execute("""
                        INSERT INTO Bids (auction_id, bidder_id, bid_amount, bid_time)
                        VALUES (%s, %s, %s, NOW())
                        """, (auction_id, user["user_id"], str(bid_amount)))
            conn.commit()

    finally:
        conn.close()

    # Redirect back to transactions
    redirect(SITE_ROOT + "cgi/transactions.py")

if __name__ == "__main__":
    main()

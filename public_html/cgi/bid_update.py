#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — bid_update.py
# Handles POST from "Increase Max Bid" form, then redirects to transactions.py
# =============================================================================

import cgitb; cgitb.enable()
import re

from utils import (
    SITE_ROOT, html_page, require_valid_session,
    read_post_body, parse_urlencoded, to_decimal_str,
    query_one, exec_write, redirect, expire_cookie
)

def bad_request(msg: str):
    # Emit a simple error page with proper headers so you see the problem
    print("Content-Type: text/html\n")
    print(html_page("Bid Error", f"<h1>Bid Error</h1><p>{msg}</p>"))

def main():
    # 1) Session check
    user, sid = require_valid_session()
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return
    uid = user["user_id"]

    # 2) Read & validate POST
    body = read_post_body()
    form = parse_urlencoded(body)

    auction_id_raw = (form.get("auction_id") or "").strip()
    amount_raw     = (form.get("amount") or "").strip()

    if not re.fullmatch(r"\d+", auction_id_raw):
        return bad_request("Missing or invalid auction_id.")
    auction_id = int(auction_id_raw)

    amount_norm = to_decimal_str(amount_raw)
    if amount_norm is None:
        return bad_request("Please enter a valid amount (e.g., 12.34).")
    if float(amount_norm) <= 0.0:
        return bad_request("Bid must be greater than 0.00.")

    # 3) Guard: ensure auction exists and is OPEN; forbid self-bidding
    row = query_one("""
                    SELECT a.status, i.seller_id
                    FROM Auctions a
                             JOIN Item i ON i.item_id = a.item_id
                    WHERE a.auction_id = %s
                        LIMIT 1
                    """, (auction_id,))
    if not row:
        return bad_request("Auction not found.")
    if row.get("status") != "OPEN":
        return bad_request("This auction is closed; you can’t increase your bid.")
    if int(row.get("seller_id")) == int(uid):
        return bad_request("You can’t bid on your own auction.")

    # 4) Insert new bid row (simple model; proxy logic could replace this later)
    affected = exec_write("""
                          INSERT INTO Bids (auction_id, bidder_id, amount, bid_time)
                          VALUES (%s, %s, %s, NOW())
                          """, (auction_id, uid, amount_norm))

    if affected <= 0:
        return bad_request("Could not record your bid. Please try again.")

    # 5) Redirect back to transactions
    redirect(SITE_ROOT + "cgi/transactions.py")

if __name__ == "__main__":
    main()

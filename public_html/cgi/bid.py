#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cgitb; cgitb.enable()
import html, os
from decimal import Decimal, InvalidOperation
import cgi

from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie,
    require_valid_session, db
)

# Import Styles
from styles import THEME as s

# ---------- Queries ----------

def fetch_running_auctions(conn, user_id):
    """
    Return running auctions the current user does NOT own,
    with a computed current price (max bid or starting price).
    """
    sql = """
          SELECT
              A.auction_id,
              I.item_name,
              COALESCE(MAX(B.bid_amount), A.start_price) AS current_price
          FROM Auctions A
                   JOIN Items    I ON I.item_id = A.item_id
                   LEFT JOIN Bids B ON B.auction_id = A.auction_id
          WHERE A.status = 'running'
            AND I.owner_id <> %s
          GROUP BY A.auction_id, I.item_name, A.start_price
          ORDER BY I.item_name
              LIMIT 200 \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()


def place_bid(conn, auction_id, user_id, bid_amount_str):
    """
    Atomic bid placement with row lock:
    - checks not owner, running, not ended
    - bid is numeric and > current price
    """
    with conn.cursor() as cur:
        cur.execute("START TRANSACTION")

        # Lock the auction row and fetch owner/timing
        cur.execute("""
                    SELECT
                        A.auction_id, A.start_price, A.status,
                        DATE_ADD(A.start_time, INTERVAL A.duration SECOND) AS end_time,
                        I.owner_id
                    FROM Auctions A
                             JOIN Items I ON I.item_id = A.item_id
                    WHERE A.auction_id = %s
                        FOR UPDATE
                    """, (auction_id,))
        row = cur.fetchone()

        if not row:
            cur.execute("ROLLBACK"); return False, "Auction not found."
        if row["status"] != "running":
            cur.execute("ROLLBACK"); return False, "Auction is not running."
        if row["owner_id"] == user_id:
            cur.execute("ROLLBACK"); return False, "You can’t bid on your own item."

        # Time check
        cur.execute("SELECT NOW() AS now")
        now = cur.fetchone()["now"]
        if now >= row["end_time"]:
            cur.execute("ROLLBACK"); return False, "Auction already ended."

        # Current price (max bid or starting price)
        cur.execute("SELECT MAX(bid_amount) AS max_amt FROM Bids WHERE auction_id = %s", (auction_id,))
        mx = cur.fetchone()
        current_price = mx["max_amt"] if mx and mx["max_amt"] is not None else row["start_price"]

        # Parse/validate bid
        try:
            bid_val = Decimal(str(bid_amount_str))
        except (InvalidOperation, TypeError):
            cur.execute("ROLLBACK"); return False, "Bid must be a valid number."
        if bid_val <= Decimal(str(current_price)):
            cur.execute("ROLLBACK"); return False, f"Bid must exceed current price ${current_price}."

        # Insert bid
        cur.execute("""
                    INSERT INTO Bids(auction_id, bidder_id, bid_amount, bid_time)
                    VALUES (%s, %s, %s, NOW())
                    """, (auction_id, user_id, str(bid_val)))

        cur.execute("COMMIT")
        return True, "Bid placed!"


# ---------- Rendering ----------

def render_form(auctions, message: str = ""):
    opts = []
    if auctions:
        for a in auctions:
            label = f'{a["item_name"]} — current ${a["current_price"]:.2f}'
            opts.append(f'<option value="{a["auction_id"]}">{html.escape(label)}</option>')
    else:
        opts.append('<option value="">(No running auctions available)</option>')

    note = f'<div class="{s["error_box"]}">{html.escape(message)}</div>' if message else ""

    body = f"""
    <div class="{s['page_center']}">
        <div class="{s['card_centered']}">
            <div class="text-center">
                <h1 class="{s['h1_center']}">Place a Bid</h1>
                <p class="{s['subtext']}">Select an item and enter your max bid</p>
            </div>

            {note}

            <form method="post" action="{SITE_ROOT}cgi/bid.py" class="mt-8 space-y-6">
                <div>
                    <label for="auction_id" class="{s['label']}">Select Item</label>
                    <select id="auction_id" name="auction_id" required class="{s['select']}">
                        {''.join(opts)}
                    </select>
                </div>

                <div>
                    <label for="bid_amount" class="{s['label']}">Your Bid ($)</label>
                    <input type="number" step="0.01" min="0.01" id="bid_amount" name="bid_amount" required class="{s['input']}">
                    <p class="mt-1 text-xs text-gray-500">Enter increments of $0.01</p>
                </div>

                <button type="submit" class="{s['btn_primary']}">Place Bid</button>
            </form>

            <div class="mt-6 flex justify-between text-sm">
                <a href="{SITE_ROOT}cgi/display_auctions.py" class="text-indigo-600 hover:text-indigo-500 font-medium">Browse Items</a>
                <a href="{SITE_ROOT}cgi/dashboard.py" class="text-gray-500 hover:text-gray-900">Back to Dashboard</a>
            </div>
        </div>
    </div>
    """
    print("Content-Type: text/html; charset=utf-8\n")
    print(html_page("Bid on an Item", body))


# ---------- Controller ----------

def main():
    # Require a valid session
    user, sid = require_valid_session()
    if not user:
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # GET → show form; POST → attempt bid then re-render
    method = os.environ.get("REQUEST_METHOD", "GET").upper()
    conn = db()

    try:
        if method == "GET":
            auctions = fetch_running_auctions(conn, user["user_id"])
            render_form(auctions)
            return

        # POST
        form = cgi.FieldStorage()
        auction_id_str = (form.getfirst("auction_id") or "").strip()
        bid_amount_str = (form.getfirst("bid_amount") or "").strip()

        # Basic field checks
        if not auction_id_str or not bid_amount_str:
            auctions = fetch_running_auctions(conn, user["user_id"])
            render_form(auctions, "Please select an item and enter a bid.")
            return

        try:
            auction_id = int(auction_id_str)
        except ValueError:
            auctions = fetch_running_auctions(conn, user["user_id"])
            render_form(auctions, "Invalid auction id.")
            return

        ok, msg = place_bid(conn, auction_id, user["user_id"], bid_amount_str)
        auctions = fetch_running_auctions(conn, user["user_id"])
        render_form(auctions, msg)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================
# CS370 Auction Website - display_auctions.py
# Displays all running auctions with current prices, time
# remaining, and allows users to browse and bid on items.
# ============================================================


# ------------------------------------------
# 1. MODULE IMPORTS
# ------------------------------------------
import cgitb; cgitb.enable()

import html
import os
import cgi
from datetime import datetime
from decimal import Decimal

from utils import (
    SITE_ROOT,
    html_page,
    redirect,
    expire_cookie,
    require_valid_session,
    db
)


# ------------------------------------------
# 2. CONSTANTS (OPTIONAL)
# ------------------------------------------
# None needed for this page


# ------------------------------------------
# 3. RENDERING FUNCTIONS (HTML)
# ------------------------------------------

def format_time_remaining(seconds):
    """Convert seconds to human-readable format."""
    if seconds is None or seconds <= 0:
        return "Ended"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def render_money(value):
    """Format a value as money."""
    if value is None:
        return "0.00"
    try:
        return f"{Decimal(value):.2f}"
    except:
        return "0.00"


def render_page(message: str = "", auctions=None, user_status=None):
    """
    Builds and prints the HTML for this page.

    Parameters:
        message (str): Optional feedback or error message shown to the user.
        auctions: List of auction dictionaries from database.
        user_status: Dictionary mapping auction_id to user's bid status.
    """
    auctions = auctions or []
    user_status = user_status or {}

    # Build auction cards
    if not auctions:
        auctions_html = '<p class="empty-state">No running auctions available at this time.</p>'
    else:
        cards = []
        for auction in auctions:
            auction_id = auction['auction_id']
            item_name = html.escape(auction['item_name'] or "Untitled Item")
            description = html.escape(auction['description'] or "No description")
            category = html.escape(auction['category'] or "General")
            current_price = render_money(auction['current_price'])
            bid_count = auction['bid_count'] or 0
            time_remaining = format_time_remaining(auction['seconds_remaining'])

            # Get user's status on this auction
            status = user_status.get(auction_id, {})
            has_bid = status.get('has_bid', False)
            is_winning = status.get('is_winning', False)

            # Determine minimum next bid
            try:
                min_bid = Decimal(auction['current_price'] or auction['start_price']) + Decimal("0.01")
            except:
                min_bid = Decimal("0.01")

            # Build status badge
            status_badge = ""
            if has_bid:
                if is_winning:
                    status_badge = '<span class="badge winning">You\'re Winning!</span>'
                else:
                    status_badge = '<span class="badge outbid">Outbid</span>'

            # Truncate description for card view
            short_desc = description[:100] + "..." if len(description) > 100 else description

            card_html = f"""
            <div class="auction-card">
                <div class="card-header">
                    <h3>{item_name}</h3>
                    <span class="category-badge">{category}</span>
                </div>
                
                <div class="card-body">
                    <p class="description">{short_desc}</p>
                    
                    <div class="auction-stats">
                        <div class="stat">
                            <span class="label">Current Price</span>
                            <span class="value price">${current_price}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Bids</span>
                            <span class="value">{bid_count}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Time Left</span>
                            <span class="value time">{time_remaining}</span>
                        </div>
                    </div>
                    
                    {status_badge}
                </div>
                
                <div class="card-footer">
                    <form method="post" action="{SITE_ROOT}cgi/bid.py" class="bid-form">
                        <input type="hidden" name="auction_id" value="{auction_id}">
                        <div class="bid-input-group">
                            <span class="currency">$</span>
                            <input type="number" 
                                   name="bid_amount" 
                                   step="0.01" 
                                   min="{min_bid}" 
                                   placeholder="{min_bid}"
                                   required>
                            <button type="submit" class="btn-bid">Place Bid</button>
                        </div>
                    </form>
                </div>
            </div>
            """
            cards.append(card_html)

        auctions_html = '<div class="auctions-grid">' + ''.join(cards) + '</div>'

    body = f"""
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        background: #f5f7fa;
        color: #1f2937;
    }}
    
    .page-header {{
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 1.5rem 2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    .page-header h1 {{
        margin: 0;
        font-size: 1.75rem;
        color: #0a58ca;
    }}
    
    .nav-links {{
        display: flex;
        gap: 1rem;
        margin: 1.5rem 2rem;
    }}
    
    .nav-links a {{
        text-decoration: none;
        color: #0a58ca;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background: white;
        border: 1px solid #e5e7eb;
        transition: all 0.2s;
    }}
    
    .nav-links a:hover {{
        background: #f9fafb;
        border-color: #0a58ca;
    }}
    
    .container {{
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }}
    
    .page-title {{
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        color: #1f2937;
    }}
    
    .empty-state {{
        background: white;
        padding: 3rem;
        text-align: center;
        border-radius: 0.75rem;
        border: 1px solid #e5e7eb;
        color: #6b7280;
    }}
    
    .auctions-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 1.5rem;
    }}
    
    .auction-card {{
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        overflow: hidden;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
    }}
    
    .auction-card:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }}
    
    .card-header {{
        padding: 1.25rem;
        border-bottom: 1px solid #f3f4f6;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }}
    
    .card-header h3 {{
        margin: 0;
        font-size: 1.15rem;
        color: #1f2937;
        flex: 1;
    }}
    
    .category-badge {{
        background: #eff6ff;
        color: #1e40af;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        white-space: nowrap;
    }}
    
    .card-body {{
        padding: 1.25rem;
        flex: 1;
    }}
    
    .description {{
        color: #6b7280;
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 0 0 1rem 0;
    }}
    
    .auction-stats {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1rem;
    }}
    
    .stat {{
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }}
    
    .stat .label {{
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }}
    
    .stat .value {{
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
    }}
    
    .stat .value.price {{
        color: #059669;
    }}
    
    .stat .value.time {{
        color: #dc2626;
    }}
    
    .badge {{
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }}
    
    .badge.winning {{
        background: #d1fae5;
        color: #065f46;
    }}
    
    .badge.outbid {{
        background: #fee2e2;
        color: #991b1b;
    }}
    
    .card-footer {{
        padding: 1rem 1.25rem;
        background: #f9fafb;
        border-top: 1px solid #e5e7eb;
    }}
    
    .bid-form {{
        margin: 0;
    }}
    
    .bid-input-group {{
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }}
    
    .currency {{
        font-size: 1.1rem;
        font-weight: 600;
        color: #6b7280;
    }}
    
    .bid-input-group input {{
        flex: 1;
        padding: 0.625rem;
        border: 1px solid #d1d5db;
        border-radius: 0.5rem;
        font-size: 1rem;
        transition: all 0.2s;
    }}
    
    .bid-input-group input:focus {{
        outline: none;
        border-color: #0a58ca;
        box-shadow: 0 0 0 3px rgba(10,88,202,0.1);
    }}
    
    .btn-bid {{
        padding: 0.625rem 1.5rem;
        background: #0a58ca;
        color: white;
        border: none;
        border-radius: 0.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
    }}
    
    .btn-bid:hover {{
        background: #084298;
    }}
    
    .btn-bid:active {{
        transform: translateY(1px);
    }}
    
    @media (max-width: 768px) {{
        .auctions-grid {{
            grid-template-columns: 1fr;
        }}
    }}
</style>

<div class="page-header">
    <h1>Browse Auctions</h1>
</div>

<!-- Display a message if one exists -->
{f'<p role="alert" style="margin: 1rem 2rem; padding: 1rem; background: #fee2e2; color: #991b1b; border-radius: 0.5rem;">{html.escape(message)}</p>' if message else ''}

<div class="nav-links">
    <a href="{SITE_ROOT}cgi/dashboard.py">Dashboard</a>
    <a href="{SITE_ROOT}cgi/transactions.py">Your Transactions</a>
    <a href="{SITE_ROOT}cgi/sell.py">Sell an Item</a>
    <a href="{SITE_ROOT}cgi/logout.py">Log out</a>
</div>

<div class="container">
    <h2 class="page-title">Running Auctions</h2>
    {auctions_html}
</div>
"""

    # CGI headers must come before any content.
    print("Content-Type: text/html; charset=utf-8\n")
    # html_page() wraps the body inside a full HTML structure.
    print(html_page("Browse Auctions", body))


# ------------------------------------------
# 4. CORE LOGIC FUNCTIONS
# ------------------------------------------

def fetch_all_running_auctions(conn, user_id):
    """
    Fetch all running auctions that the current user does NOT own.

    Parameters:
        conn: database connection
        user_id: current user's ID

    Returns:
        list: List of auction dictionaries
    """
    sql = """
          SELECT
              A.auction_id,
              I.item_name,
              I.description,
              I.category,
              A.start_price,
              A.start_time,
              DATE_ADD(A.start_time, INTERVAL A.duration SECOND) AS end_time,
              COALESCE(MAX(B.bid_amount), A.start_price) AS current_price,
              COUNT(B.bid_id) AS bid_count,
              TIMESTAMPDIFF(SECOND, NOW(), DATE_ADD(A.start_time, INTERVAL A.duration SECOND)) AS seconds_remaining
          FROM Auctions A
                   JOIN Items I ON I.item_id = A.item_id
                   LEFT JOIN Bids B ON B.auction_id = A.auction_id
          WHERE A.status = 'running'
            AND I.owner_id <> %s
            AND NOW() < DATE_ADD(A.start_time, INTERVAL A.duration SECOND)
          GROUP BY A.auction_id, I.item_name, I.description, I.category,
                   A.start_price, A.start_time, A.duration
          ORDER BY seconds_remaining ASC, A.auction_id ASC
              LIMIT 500 \
          """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()


def check_user_bid_status(conn, auction_ids, user_id):
    """
    Check user's bid status on multiple auctions at once.

    Parameters:
        conn: database connection
        auction_ids: list of auction IDs to check
        user_id: current user's ID

    Returns:
        dict: Mapping of auction_id to status dict with 'has_bid' and 'is_winning'
    """
    if not auction_ids:
        return {}

    # Build a mapping of auction_id -> user's max bid
    placeholders = ','.join(['%s'] * len(auction_ids))
    sql = f"""
        SELECT 
            B.auction_id,
            MAX(B.bid_amount) AS user_max
        FROM Bids B
        WHERE B.auction_id IN ({placeholders})
          AND B.bidder_id = %s
        GROUP BY B.auction_id
    """

    with conn.cursor() as cur:
        cur.execute(sql, tuple(auction_ids) + (user_id,))
        user_bids = {row['auction_id']: row['user_max'] for row in cur.fetchall()}

    # Get overall max bids for these auctions
    sql2 = f"""
        SELECT 
            auction_id,
            MAX(bid_amount) AS overall_max
        FROM Bids
        WHERE auction_id IN ({placeholders})
        GROUP BY auction_id
    """

    with conn.cursor() as cur:
        cur.execute(sql2, tuple(auction_ids))
        overall_max = {row['auction_id']: row['overall_max'] for row in cur.fetchall()}

    # Build status dictionary
    status = {}
    for aid in auction_ids:
        if aid in user_bids:
            user_max = user_bids[aid]
            overall = overall_max.get(aid)
            status[aid] = {
                'has_bid': True,
                'is_winning': (user_max == overall) if overall else False
            }
        else:
            status[aid] = {'has_bid': False, 'is_winning': False}

    return status


# ------------------------------------------
# 5. MAIN REQUEST HANDLER
# ------------------------------------------

def main():
    # --- Step 1: Verify the user session ---
    user, sid = require_valid_session()
    if not user:
        # If no valid user, redirect to login page.
        # Also expire any existing cookie to force re-login.
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # --- Step 2: Check if this is a GET or POST request ---
    method = os.environ.get("REQUEST_METHOD", "GET")
    if method == "GET":
        # Display the auctions (default page view)
        pass  # Continue to step 4
    elif method == "POST":
        # This page doesn't handle POST - bidding is done via bid.py
        # If somehow a POST arrives here, just show the page
        pass

    # --- Step 4: Connect to database and fetch auctions ---
    conn = db()
    try:
        auctions = fetch_all_running_auctions(conn, user["user_id"])

        # Get user's bid status for all auctions
        auction_ids = [a['auction_id'] for a in auctions]
        user_status = check_user_bid_status(conn, auction_ids, user["user_id"])

    finally:
        # Always close the connection, even if something fails.
        conn.close()

    # --- Step 5: Render the page with auction data ---
    render_page(message="", auctions=auctions, user_status=user_status)


# ------------------------------------------
# 6. SCRIPT ENTRY POINT
# ------------------------------------------

if __name__ == "__main__":
    main()
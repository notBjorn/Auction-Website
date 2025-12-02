#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================
# CS370 Auction Website - display_auctions.py
# Displays all running auctions with Tailwind styling.
# ============================================================

import cgitb;

cgitb.enable()
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
# 2. RENDERING FUNCTIONS
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


def render_page(message: str = "", auctions=None, user_status=None, user_name="User", email=""):
    """
    Builds the Tailwind HTML for the auction browser.
    """
    auctions = auctions or []
    user_status = user_status or {}

    # --- Build Auction Cards ---
    if not auctions:
        auctions_html = '''
        <div class="col-span-full text-center py-20 bg-white rounded-xl border border-gray-200 border-dashed">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900">No auctions running</h3>
            <p class="mt-1 text-sm text-gray-500">Check back later or start your own auction.</p>
            <div class="mt-6">
                <a href="{SITE_ROOT}cgi/sell.py" class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none">
                    Sell an Item
                </a>
            </div>
        </div>
        '''.format(SITE_ROOT=SITE_ROOT)
    else:
        cards = []
        for auction in auctions:
            auction_id = auction['auction_id']
            item_name = html.escape(auction['item_name'] or "Untitled Item")
            description = html.escape(auction['description'] or "No description")
            category = html.escape(auction['category'] or "General")
            current_price = render_money(auction['current_price'])
            bid_count = auction['bid_count'] or 0

            seconds_left = auction['seconds_remaining']
            time_remaining = format_time_remaining(seconds_left)

            # Color code time remaining
            time_class = "text-gray-900"
            if seconds_left and seconds_left < 3600:  # Less than 1 hour
                time_class = "text-red-600 animate-pulse"
            elif seconds_left and seconds_left < 86400:  # Less than 1 day
                time_class = "text-orange-600"

            # Get user's status
            status = user_status.get(auction_id, {})
            has_bid = status.get('has_bid', False)
            is_winning = status.get('is_winning', False)

            try:
                min_bid = Decimal(auction['current_price'] or auction['start_price']) + Decimal("0.01")
            except:
                min_bid = Decimal("0.01")

            # Status Badge
            status_badge = ""
            if has_bid:
                if is_winning:
                    status_badge = '<div class="mt-3 w-full text-center bg-green-50 text-green-700 text-xs font-bold px-2 py-1 rounded border border-green-100">Winning</div>'
                else:
                    status_badge = '<div class="mt-3 w-full text-center bg-red-50 text-red-700 text-xs font-bold px-2 py-1 rounded border border-red-100">Outbid</div>'

            # Truncate description
            short_desc = description[:90] + "..." if len(description) > 90 else description

            card_html = f"""
            <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col hover:shadow-md transition duration-200">
                <div class="p-5 border-b border-gray-100 flex justify-between items-start gap-3">
                    <h3 class="font-bold text-gray-900 text-lg leading-tight line-clamp-1" title="{item_name}">{item_name}</h3>
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 whitespace-nowrap">
                        {category}
                    </span>
                </div>

                <div class="p-5 flex-1 flex flex-col">
                    <p class="text-sm text-gray-500 mb-6 line-clamp-2 flex-1">{short_desc}</p>

                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <div>
                            <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Current</p>
                            <p class="text-lg font-bold text-emerald-600">${current_price}</p>
                        </div>
                        <div class="text-center">
                            <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Bids</p>
                            <p class="text-lg font-bold text-gray-700">{bid_count}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Ends In</p>
                            <p class="text-sm font-bold {time_class}">{time_remaining}</p>
                        </div>
                    </div>
                    {status_badge}
                </div>

                <div class="bg-gray-50 p-4 border-t border-gray-100">
                    <form method="post" action="{SITE_ROOT}cgi/bid.py" class="flex gap-2">
                        <input type="hidden" name="auction_id" value="{auction_id}">

                        <div class="relative flex-1">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span class="text-gray-500 sm:text-sm">$</span>
                            </div>
                            <input type="number" 
                                   name="bid_amount" 
                                   step="0.01" 
                                   min="{min_bid}" 
                                   placeholder="{min_bid}"
                                   required
                                   class="appearance-none block w-full pl-7 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-400 focus:outline-none focus:placeholder-gray-500 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition">
                        </div>

                        <button type="submit" class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition">
                            Bid
                        </button>
                    </form>
                </div>
            </div>
            """
            cards.append(card_html)

        auctions_html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">' + ''.join(cards) + '</div>'

    # --- Error Message Alert ---
    alert_html = ""
    if message:
        alert_html = f'''
        <div class="mb-6 bg-red-50 border-l-4 border-red-500 p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-red-700">{html.escape(message)}</p>
                </div>
            </div>
        </div>
        '''

    # --- Main Layout ---
    body = f"""
    <div class="min-h-screen md:grid md:grid-cols-[260px_1fr]">

        <aside class="bg-[#0b1736] text-blue-50 flex flex-col gap-6 p-6">
            <div>
                <h1 class="text-xl font-extrabold text-white tracking-wide">CS370 Auction</h1>
                <div class="text-indigo-300 text-sm font-medium">Portal</div>
            </div>

            <div class="bg-white/5 border border-white/10 rounded-xl p-4">
                <p class="font-semibold text-white">Welcome, {user_name}</p>
                <p class="text-xs text-indigo-200 mt-1 break-all">{email}</p>
            </div>

            <nav class="flex flex-col gap-2">
                <a href="{SITE_ROOT}cgi/transactions.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path></svg>
                    Your Transactions
                </a>

                <a href="{SITE_ROOT}cgi/display_auctions.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-600 text-white font-medium shadow-md">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    See what's for Sale
                </a>

                <a href="{SITE_ROOT}cgi/bid.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    Bid on an Item
                </a>

                <a href="{SITE_ROOT}cgi/sell.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                    Sell an Item
                </a>

                <a href="{SITE_ROOT}cgi/dashboard.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition mt-4 border-t border-white/10 pt-4">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12"></path></svg>
                    Back to Dashboard
                </a>

                <a href="{SITE_ROOT}cgi/logout.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-red-300 hover:bg-red-500/20 hover:text-red-100 transition">
                   <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                   Log out
                </a>
            </nav>
        </aside>

        <div class="bg-gray-50 flex flex-col">

            <header class="bg-white border-b border-gray-200 px-8 py-5 shadow-sm sticky top-0 z-10 flex justify-between items-center">
                <h2 class="text-2xl font-bold text-gray-900">Browse Auctions</h2>
                <div class="text-sm text-gray-500">Live Updates</div>
            </header>

            <main class="flex-1 p-6 md:p-8">
                {alert_html}
                {auctions_html}
            </main>
        </div>
    </div>
    """

    print("Content-Type: text/html\n")
    print(html_page("Browse Auctions", body))


# ------------------------------------------
# 4. CORE LOGIC FUNCTIONS
# ------------------------------------------

def fetch_all_running_auctions(conn, user_id):
    # Fetch running auctions where current user is NOT owner
    sql = """
          SELECT A.auction_id, \
                 I.item_name, \
                 I.description, \
                 I.category, \
                 A.start_price, \
                 A.start_time, \
                 COALESCE(MAX(B.bid_amount), A.start_price)                                       AS current_price, \
                 COUNT(B.bid_id)                                                                  AS bid_count, \
                 TIMESTAMPDIFF(SECOND, NOW(), DATE_ADD(A.start_time, INTERVAL A.duration SECOND)) AS seconds_remaining
          FROM Auctions A
                   JOIN Items I ON I.item_id = A.item_id
                   LEFT JOIN Bids B ON B.auction_id = A.auction_id
          WHERE A.status = 'running'
            AND I.owner_id <> %s
            AND NOW() < DATE_ADD(A.start_time, INTERVAL A.duration SECOND)
          GROUP BY A.auction_id, I.item_name, I.description, I.category,
                   A.start_price, A.start_time, A.duration
          ORDER BY seconds_remaining ASC, A.auction_id ASC LIMIT 100;
          """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()


def check_user_bid_status(conn, auction_ids, user_id):
    if not auction_ids:
        return {}

    placeholders = ','.join(['%s'] * len(auction_ids))

    # Get user's max bid per auction
    sql = f"SELECT auction_id, MAX(bid_amount) AS user_max FROM Bids WHERE auction_id IN ({placeholders}) AND bidder_id = %s GROUP BY auction_id"
    with conn.cursor() as cur:
        cur.execute(sql, tuple(auction_ids) + (user_id,))
        user_bids = {row['auction_id']: row['user_max'] for row in cur.fetchall()}

    # Get overall max bid per auction
    sql2 = f"SELECT auction_id, MAX(bid_amount) AS overall_max FROM Bids WHERE auction_id IN ({placeholders}) GROUP BY auction_id"
    with conn.cursor() as cur:
        cur.execute(sql2, tuple(auction_ids))
        overall_max = {row['auction_id']: row['overall_max'] for row in cur.fetchall()}

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
    user, sid = require_valid_session()
    if not user:
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    method = os.environ.get("REQUEST_METHOD", "GET")

    conn = db()
    try:
        auctions = fetch_all_running_auctions(conn, user["user_id"])
        auction_ids = [a['auction_id'] for a in auctions]
        user_status = check_user_bid_status(conn, auction_ids, user["user_id"])
    finally:
        conn.close()

    render_page(
        message="",
        auctions=auctions,
        user_status=user_status,
        user_name=html.escape(user.get("user_name", "User")),
        email=html.escape(user.get("email", ""))
    )


if __name__ == "__main__":
    main()
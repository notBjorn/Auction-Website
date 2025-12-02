#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — transactions.py
# =============================================================================

import cgitb;

cgitb.enable()
import html
from utils import (SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db)
from transactions_helpers import (
    fetch_selling_active, fetch_selling_sold, fetch_purchases, fetch_current_bids, fetch_didnt_win,
    render_selling_table, render_purchases_table, render_current_bids_table, render_didnt_win_table
)


def main():
    user, sid = require_valid_session()
    if not user:
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    email = html.escape(user.get("email", ""))
    user_name = html.escape(user.get("user_name", ""))
    user_id = user.get("user_id")

    conn = db()
    try:
        selling_active = fetch_selling_active(conn, user_id)
        selling_sold = fetch_selling_sold(conn, user_id)
        purchases = fetch_purchases(conn, user_id)
        current_bids = fetch_current_bids(conn, user_id)
        didnt_win = fetch_didnt_win(conn, user_id)
    finally:
        conn.close()

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
                <a href="{SITE_ROOT}cgi/dashboard.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
                    Dashboard
                </a>

                <a href="{SITE_ROOT}cgi/transactions.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-600 text-white font-medium shadow-md">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path></svg>
                    Your Transactions
                </a>

                <a href="{SITE_ROOT}cgi/display_auctions.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    Browse Auctions
                </a>

                <a href="{SITE_ROOT}cgi/sell.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                    Sell an Item
                </a>

                <a href="{SITE_ROOT}cgi/logout.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-red-300 hover:bg-red-500/20 hover:text-red-100 transition mt-auto border-t border-white/10 pt-4">
                   <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                   Log out
                </a>
            </nav>
        </aside>

        <div class="bg-gray-50 flex flex-col">
            <header class="bg-white border-b border-gray-200 px-8 py-5 shadow-sm sticky top-0 z-10">
                <h2 class="text-2xl font-bold text-gray-900">Transaction History</h2>
            </header>

            <main class="flex-1 p-6 md:p-10 space-y-8">
                <section class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div class="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 class="text-lg font-bold text-gray-800">1) Selling</h3>
                    </div>
                    <div class="p-6 space-y-8">
                        <div>
                            <h4 class="text-xs font-bold text-indigo-500 uppercase tracking-wide mb-3">Active Listings</h4>
                            <div class="overflow-x-auto">{render_selling_table(selling_active, "You are not selling anything yet.")}</div>
                        </div>
                        <div class="border-t border-gray-100 pt-6">
                            <h4 class="text-xs font-bold text-green-600 uppercase tracking-wide mb-3">Sold Items</h4>
                            <div class="overflow-x-auto">{render_selling_table(selling_sold, "You have not sold anything yet.")}</div>
                        </div>
                    </div>
                </section>

                <section class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div class="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 class="text-lg font-bold text-gray-800">2) Purchases</h3>
                    </div>
                    <div class="p-6 overflow-x-auto">
                        {render_purchases_table(purchases)}
                    </div>
                </section>

                <section class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div class="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 class="text-lg font-bold text-gray-800">3) Current Bids</h3>
                    </div>
                    <div class="p-6 overflow-x-auto">
                        {render_current_bids_table(current_bids)}
                    </div>
                </section>

                <section class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div class="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                        <h3 class="text-lg font-bold text-gray-800">4) Didn't Win</h3>
                    </div>
                    <div class="p-6 overflow-x-auto">
                        {render_didnt_win_table(didnt_win)}
                    </div>
                </section>
            </main>
        </div>
    </div>
    <style>
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background-color: #f9fafb; color: #6b7280; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.75rem 1.5rem; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        td {{ border-bottom: 1px solid #e5e7eb; padding: 1rem 1.5rem; font-size: 0.875rem; color: #1f2937; }}
        td button, td input[type="submit"] {{ background-color: #4f46e5; color: white; padding: 0.25rem 0.75rem; border-radius: 0.375rem; font-weight: 500; font-size: 0.875rem; border: none; cursor: pointer; }}
        td button:hover {{ background-color: #4338ca; }}
    </style>
    """

    print("Content-Type: text/html\n")
    print(html_page("Transactions", body))


if __name__ == "__main__":
    main()
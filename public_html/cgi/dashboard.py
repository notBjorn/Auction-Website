#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — dashboard.py
# =============================================================================

import cgitb;

cgitb.enable()
import html
from utils import (SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db)
from transactions_helpers import (fetch_current_bids, render_current_bids_table, fetch_selling_active,
                                  render_selling_table)


def main():
    user, sid = require_valid_session()
    if not user:
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    email = html.escape(user.get("email", ""))
    user_name = html.escape(user.get("user_name", ""))
    user_id = user.get("user_id")

    # Fetch Data
    conn = db()
    try:
        current_bids = fetch_current_bids(conn, user_id)
        selling_active = fetch_selling_active(conn, user_id)
    finally:
        conn.close()

    # Build Content Sections
    active_sections = ""
    if current_bids:
        active_sections += f"""
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
            <div class="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
                <h3 class="font-bold text-gray-800">Current Bids</h3>
                <span class="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded-full">Live</span>
            </div>
            <div class="p-6 overflow-x-auto">{render_current_bids_table(current_bids)}</div>
        </div>
        """

    if selling_active:
        active_sections += f"""
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
            <div class="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                <h3 class="font-bold text-gray-800">Active Listings</h3>
            </div>
            <div class="p-6 overflow-x-auto">{render_selling_table(selling_active, "You are not selling anything yet.")}</div>
        </div>
        """

    # If nothing is happening
    if not active_sections:
        active_sections = """
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-10 text-center">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <h3 class="text-lg font-medium text-gray-900">No active updates</h3>
            <p class="mt-1 text-gray-500">You haven't bid on or sold any items yet.</p>
            <div class="mt-6 flex justify-center gap-3">
                <a href="{SITE_ROOT}cgi/display_auctions.py" class="text-indigo-600 font-medium hover:text-indigo-500">Browse Items &rarr;</a>
            </div>
        </div>
        """.format(SITE_ROOT=SITE_ROOT)

    # --- RENDER PAGE ---
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
                <a href="{SITE_ROOT}cgi/dashboard.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-600 text-white font-medium shadow-md">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
                    Dashboard
                </a>

                <a href="{SITE_ROOT}cgi/transactions.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
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
            <header class="bg-white border-b border-gray-200 px-8 py-5 shadow-sm sticky top-0 z-10 flex justify-between items-center">
                <h2 class="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
                <div class="text-sm text-gray-500">Welcome Back</div>
            </header>

            <main class="flex-1 p-6 md:p-10">
                {active_sections}
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
    print(html_page("Dashboard", body))


if __name__ == "__main__":
    main()
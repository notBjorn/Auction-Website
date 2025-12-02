#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cgitb;

cgitb.enable()
import html, os
from utils import (SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db, to_decimal_str)

SEVEN_DAYS_SECONDS = 7 * 24 * 60 * 60


def render_form(message: str = "", user_name="User", email=""):
    # Error Alert styling
    alert = ""
    if message:
        color = "bg-green-100 text-green-800 border-green-200" if "created" in message.lower() else "bg-red-50 text-red-700 border-red-200"
        alert = f'<div class="p-4 mb-6 rounded-md border {color}">{html.escape(message)}</div>'

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
                <a href="{SITE_ROOT}cgi/transactions.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path></svg>
                    Your Transactions
                </a>
                <a href="{SITE_ROOT}cgi/display_auctions.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                    Browse Auctions
                </a>
                <a href="{SITE_ROOT}cgi/sell.py" class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-600 text-white font-medium shadow-md">
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
                <h2 class="text-2xl font-bold text-gray-900">Create New Listing</h2>
            </header>

            <main class="flex-1 p-6 md:p-10 flex justify-center">
                <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-200 w-full max-w-2xl">
                    {alert}
                    <form method="post" action="{SITE_ROOT}cgi/sell.py" class="space-y-6">

                        <div>
                            <label for="title" class="block text-sm font-medium text-gray-700 mb-1">Item Title</label>
                            <input type="text" id="title" name="title" required placeholder="e.g. MacBook Pro M1 2021" class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm h-10">
                        </div>

                        <div>
                            <label for="desc" class="block text-sm font-medium text-gray-700 mb-1">Item Description</label>
                            <textarea id="desc" name="description" required rows="4" placeholder="Describe the condition, specs, etc..." class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"></textarea>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label for="price" class="block text-sm font-medium text-gray-700 mb-1">Starting Price ($)</label>
                                <div class="relative rounded-md shadow-sm">
                                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span class="text-gray-500 sm:text-sm">$</span>
                                    </div>
                                    <input type="number" id="price" name="starting_price" step="0.01" min="0" required class="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md h-10 border">
                                </div>
                            </div>

                            <div>
                                <label for="start" class="block text-sm font-medium text-gray-700 mb-1">Start Date & Time</label>
                                <input type="datetime-local" id="start" name="start_dt" required class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm h-10">
                            </div>
                        </div>

                        <div class="bg-blue-50 p-4 rounded-md">
                            <p class="text-sm text-blue-700 flex items-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                All auctions run for exactly <b>7 days</b> (168 hours).
                            </p>
                        </div>

                        <div class="flex justify-end pt-4">
                            <button type="submit" class="w-full md:w-auto inline-flex justify-center py-2 px-6 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Create Auction
                            </button>
                        </div>
                    </form>
                </div>
            </main>
        </div>
    </div>
    """
    print("Content-Type: text/html\n")
    print(html_page("Sell an Item", body))


def create_auction(conn, owner_id, title, description, starting_price, start_dt):
    title = (title or "").strip()
    description = (description or "").strip()

    if not title or not description or not starting_price or not start_dt:
        return "All fields are required."

    sp = to_decimal_str(starting_price)
    if sp is None:
        return "Starting price must be a valid number."

    with conn.cursor() as cur:
        cur.execute("START TRANSACTION")

        # 1. Insert Item (Now includes item_name AND description)
        cur.execute("""
                    INSERT INTO Items (owner_id, item_name, description, created_at)
                    VALUES (%s, %s, %s, NOW())
                    """, (owner_id, title, description))

        cur.execute("SELECT LAST_INSERT_ID() AS id")
        item_id = cur.fetchone()["id"]

        # 2. Insert Auction
        cur.execute("""
                    INSERT INTO Auctions (item_id, start_time, duration, status, start_price)
                    VALUES (%s, %s, %s, CASE WHEN %s <= NOW() THEN 'running' ELSE 'scheduled' END, %s)
                    """, (item_id, start_dt, SEVEN_DAYS_SECONDS, start_dt, sp))

        cur.execute("COMMIT")
    return "Auction created successfully!"


def main():
    user, sid = require_valid_session()
    if not user:
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    email = html.escape(user.get("email", ""))
    user_name = html.escape(user.get("user_name", ""))

    if os.environ.get("REQUEST_METHOD", "GET") == "GET":
        render_form(user_name=user_name, email=email)
        return

    import cgi
    form = cgi.FieldStorage()
    conn = db()
    try:
        # Pass the new 'title' field to the creation function
        message = create_auction(
            conn,
            user["user_id"],
            form.getfirst("title", ""),  # New field
            form.getfirst("description", ""),
            form.getfirst("starting_price", ""),
            form.getfirst("start_dt", "")
        )
    finally:
        conn.close()

    render_form(message, user_name=user_name, email=email)


if __name__ == "__main__":
    main()
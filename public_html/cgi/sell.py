#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cgitb; cgitb.enable()
import html, os
from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie,
    require_valid_session, db, to_decimal_str
)

SEVEN_DAYS_SECONDS = 7 * 24 * 60 * 60  # 168 hours = 604800 seconds


def render_form(user, message: str = "", values=None):
    """
    Render the Sell form with a nicer layout, but keep the old,
    working field names and sticky values.
    """
    values = values or {}

    item_name = html.escape(values.get("item_name", ""))
    desc = html.escape(values.get("description", ""))
    price = html.escape(values.get("starting_price", ""))
    start = html.escape(values.get("start_dt", ""))

    # message styling (green for "created", red otherwise)
    alert = ""
    if message:
        is_success = "created" in message.lower()
        color = (
            "bg-green-100 text-green-800 border-green-200"
            if is_success else
            "bg-red-50 text-red-700 border-red-200"
        )
        alert = f'<div class="p-4 mb-6 rounded-md border {color}"><strong>{html.escape(message)}</strong></div>'

    user_name = html.escape(user.get("user_name") or user.get("username", "User"))
    email = html.escape(user.get("email", ""))

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
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 01-3 3v8a3 3 0 003 3z"></path></svg>
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
                    <form method="post" action="{SITE_ROOT}cgi/sell.py" class="space-y-6" novalidate>

                        <div>
                            <label for="item_name" class="block text-sm font-medium text-gray-700 mb-1">Item Name</label>
                            <input type="text" id="item_name" name="item_name" required
                                   placeholder="e.g. MacBook Pro M1 2021"
                                   value="{item_name}"
                                   class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm h-10">
                        </div>

                        <div>
                            <label for="desc" class="block text-sm font-medium text-gray-700 mb-1">Item Description</label>
                            <textarea id="desc" name="description" required rows="4"
                                      placeholder="Describe the condition, specs, etc..."
                                      class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">{desc}</textarea>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label for="price" class="block text-sm font-medium text-gray-700 mb-1">Starting Price ($)</label>
                                <div class="relative rounded-md shadow-sm">
                                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <span class="text-gray-500 sm:text-sm">$</span>
                                    </div>
                                    <input type="number" id="price" name="starting_price" step="0.01" min="0" required
                                           value="{price}"
                                           class="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md h-10 border">
                                </div>
                            </div>

                            <div>
                                <label for="start" class="block text-sm font-medium text-gray-700 mb-1">Start Date & Time</label>
                                <input type="datetime-local" id="start" name="start_dt" required
                                       value="{start}"
                                       class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm h-10">
                                <p class="text-xs text-gray-500 mt-1">All auctions last 168 hours (7 days).</p>
                            </div>
                        </div>

                        <div class="flex justify-end pt-4">
                            <button type="submit" class="w-full md:w-auto inline-flex justify-center py-2 px-6 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Create Auction
                            </button>
                        </div>

                        <p class="mt-4 text-sm text-gray-500">
                            <a href="{SITE_ROOT}cgi/transactions.py" class="text-indigo-600 hover:text-indigo-800">Back to Transactions</a>
                            &nbsp;|&nbsp;
                            <a href="{SITE_ROOT}cgi/dashboard.py" class="text-indigo-600 hover:text-indigo-800">Back to Dashboard</a>
                        </p>
                    </form>
                </div>
            </main>
        </div>
    </div>
    """

    print("Content-Type: text/html; charset=utf-8\n")
    print(html_page("Sell an Item", body))


def create_auction(conn, owner_id, item_name, description, starting_price, start_dt):
    """
    This is your original working backend logic.
    """
    item_name = (item_name or "").strip()
    description = (description or "").strip()
    if not item_name or not description or not starting_price or not start_dt:
        return ("error", "All fields are required.")

    sp = to_decimal_str(starting_price)
    if sp is None:
        return ("error", "Starting price must be a valid number (up to 2 decimals).")

    def normalize_html_datetime(dt_str: str) -> str:
        if not dt_str:
            return ""
        dt = dt_str.replace("T", " ")
        if len(dt) == 16:
            dt += ":00"
        return dt

    start_dt = normalize_html_datetime(start_dt)

    with conn.cursor() as cur:
        cur.execute("START TRANSACTION")

        # Insert Item (matches your original schema)
        cur.execute("""
                    INSERT INTO Items (owner_id, item_name, category, description, posted_date, last_modified)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """, (owner_id, item_name, "General", description))

        cur.execute("SELECT LAST_INSERT_ID() AS id")
        item_id = cur.fetchone()["id"]

        # Insert Auction
        cur.execute("""
                    INSERT INTO Auctions (item_id, start_price, start_time, duration, status)
                    VALUES (
                               %s,
                               %s,
                               %s,
                               %s,
                               CASE WHEN %s <= NOW() THEN 'running' ELSE 'scheduled' END
                           )
                    """, (item_id, sp, start_dt, SEVEN_DAYS_SECONDS, start_dt))

        # Get the new auction_id
        cur.execute("SELECT LAST_INSERT_ID() AS id")
        auction_id = cur.fetchone()["id"]

        cur.execute("COMMIT")

    return ("ok", auction_id)


def main():
    # Require a valid session
    user, sid = require_valid_session()
    if not user:
        headers = [expire_cookie("SID", path=SITE_ROOT)] if sid else []
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    method = os.environ.get("REQUEST_METHOD", "GET").upper()
    if method == "GET":
        render_form(user)
        return

    import cgi
    form = cgi.FieldStorage()
    values = {
        "item_name":      form.getfirst("item_name", ""),
        "description":    form.getfirst("description", ""),
        "starting_price": form.getfirst("starting_price", ""),
        "start_dt":       form.getfirst("start_dt", "")
    }

    conn = db()
    try:
        try:
            status, payload = create_auction(
                conn, user["user_id"],
                values["item_name"],
                values["description"],
                values["starting_price"],
                values["start_dt"]
            )
            if status == "ok":
                # PRG: Redirect so refresh/double-click doesn’t re-POST
                redirect(f"{SITE_ROOT}cgi/transactions.py?flash=auction_created&aid={payload}")
                return
            else:
                message = payload  # error string from create_auction
        except Exception as e:
            message = f"Error creating auction: {html.escape(str(e))}"
    finally:
        conn.close()

    # On error, re-render with sticky values
    render_form(user, message, values)


if __name__ == "__main__":
    main()

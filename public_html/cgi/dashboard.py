#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — dashboard.py
# Displays the logged-in user's dashboard. Requires a valid session.
# If the session is missing or expired, redirect to the login page and
# expire the SID cookie when present.
# =============================================================================

# ====== Imports / Setup ======================================================
import cgitb; cgitb.enable()
import html

from utils import (
    SITE_ROOT, html_page, redirect, expire_cookie, require_valid_session, db
)

from transactions_helpers import (
    fetch_current_bids,
    render_current_bids_table,
    fetch_selling_active,
    render_selling_table,
)

from styles import THEME as s

# ====== Controller: Main Request Handler =====================================
def main():
    user, sid = require_valid_session()

    # ----- Not logged in or timed out ----------------------------------------
    if not user:
        headers = []
        if sid:
            headers.append(expire_cookie("SID", path=SITE_ROOT))
        redirect(SITE_ROOT + "cgi/login.py", extra_headers=headers)
        return

    # ----- Valid session: load user + active transactions --------------------
    email     = html.escape(user.get("email", ""))
    user_name = html.escape(user.get("user_name", ""))
    user_id   = user.get("user_id")

    # Fetch current bids and active selling for this user
    conn = db()
    try:
        current_bids   = fetch_current_bids(conn, user_id)
        selling_active = fetch_selling_active(conn, user_id)
    finally:
        conn.close()

    # Build up one string with zero, one, or two cards
    active_sections = ""

    if current_bids:
        active_sections += f"""
    <section class="card">
      <h3 style="margin-top:0;">Current Bids</h3>
      <p class="muted">
        These auctions are currently running. You can raise your max bid directly from here.
      </p>
      {render_current_bids_table(current_bids)}
    </section>
    """

    if selling_active:
        active_sections += f"""
    <section class="card">
      <h3 style="margin-top:0;">Active Listings</h3>
      <p class="muted">
        These are your current items for sale.
      </p>
      {render_selling_table(selling_active, "You are not selling anything yet.")}
    </section>
    """

    def wrap_table(title, subtitle, table_html):
        return f"""
        <section class="{s['card_dashboard']}">
            <div class="{s['card_header']}">
                <h3 class="{s['h3_card']}">{title}</h3>
                <p class="text-sm text-gray-500">{subtitle}</p>
            </div>
            <div class="{s['table_wrapper']}">
                <div class="p-6">
                    {table_html} 
                </div>
            </div>
        </section>
        """

    content = ""
    if current_bids:
        content += wrap_table("Current Bids", "Auctions you are participating in",
                              render_current_bids_table(current_bids))
    if selling_active:
        content += wrap_table("Active Listings", "Items you are currently selling",
                              render_selling_table(selling_active, "No items."))

    # Sidebar HTML construction
    sidebar = f"""
    <aside class="{s['sidebar_bg']}">
        <div class="mb-6">
            <h1 class="text-2xl font-bold text-white tracking-wide">Auction Portal</h1>
        </div>
        <div class="bg-white/10 rounded-lg p-4 mb-4">
             <p class="text-white font-medium">Welcome, {html.escape(user.get("user_name", ""))}</p>
        </div>
        <nav class="flex flex-col gap-2">
            <a href="{SITE_ROOT}cgi/dashboard.py" class="{s['nav_link_active']}">Dashboard</a>
            <a href="{SITE_ROOT}cgi/transactions.py" class="{s['nav_link']}">My Transactions</a>
            <a href="{SITE_ROOT}cgi/display_auctions.py" class="{s['nav_link']}">Browse Auctions</a>
            <a href="{SITE_ROOT}cgi/sell.py" class="{s['nav_link']}">Sell Item</a>
            <a href="{SITE_ROOT}cgi/logout.py" class="{s['nav_link']} text-red-300 hover:text-red-100">Logout</a>
        </nav>
    </aside>
    """

    body = f"""
    <div class="{s['dashboard_grid']}">
        {sidebar}
        <div class="bg-gray-50">
            <header class="bg-white border-b border-gray-200 px-8 py-5">
                <h2 class="{s['h2_dashboard']}">Dashboard</h2>
            </header>
            <main class="p-8">
                {content if content else '<div class="text-gray-500 italic">No active updates.</div>'}
            </main>
        </div>
    </div>
    """

    print("Content-Type: text/html\n")
    print(html_page("Dashboard", body))


# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()

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
)

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

    # Fetch current bids (active transactions) for this user
    conn = db()
    try:
        current_bids = fetch_current_bids(conn, user_id)
    finally:
        conn.close()

    if current_bids:
        active_section = f"""
    <section class="card">
      <h3 style="margin-top:0;">Current Bids</h3>
      <p class="muted">
        These auctions are currently running. You can raise your max bid directly from here.
      </p>
      {render_current_bids_table(current_bids)}
    </section>
    """
    else:
        active_section = ""

    # ----- Valid session: render dashboard -----------------------------------
    print("Content-Type: text/html\n")
    print(html_page("Dashboard", f"""
<!-- ===========================
     DASHBOARD LAYOUT (LEFT SIDEBAR)
     =========================== -->

<style>
  /* ---------- Color and layout variables ---------- */
  :root {{
    --brand: #0a58ca;          /* Primary blue for links/buttons */
    --brand-600: #0947a5;      /* Slightly darker blue for hover states */
    --bg: #f6f7fb;             /* Light gray background for the main page */
    --text: #1f2937;           /* Default text color (dark gray) */
    --muted: #6b7280;          /* Secondary text color (lighter gray) */
    --card: #ffffff;           /* White background for content cards */
  }}

  * {{ box-sizing: border-box; }}
  html, body {{ height: 100%; }}

  /* ---------- Base layout using CSS Grid ---------- */
  body {{
    margin: 0;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    color: var(--text);
    background: var(--bg);
    display: grid;
    grid-template-columns: 260px 1fr;   /* Left column for sidebar, right for main content */
    min-height: 100vh;                  /* Full screen height */
  }}

  /* ---------- Sidebar styling ---------- */
  aside {{
    background: #0b1736;                /* Dark navy background for contrast */
    color: #eef2ff;                     /* Light text color for readability */
    padding: 1.25rem 1rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;                          /* Space between sidebar sections */
  }}

  /* ---------- Brand (site name + subtitle) ---------- */
  .brand {{
    display: grid;
    gap: .25rem;
  }}
  .brand h1 {{
    margin: 0;
    font-size: 1.15rem;
    letter-spacing: .2px;
    font-weight: 800;
    color: #fff;
  }}
  .brand .sub {{
    color: #A8B3FF;
    font-size: .9rem;
  }}

  /* ---------- User info card in sidebar ---------- */
  .user {{
    background: rgba(255,255,255,.06);  /* Slightly transparent overlay */
    border: 1px solid rgba(255,255,255,.08);
    border-radius: .75rem;
    padding: .75rem .9rem;
  }}
  .user .hello {{ margin: 0; font-weight: 600; }}
  .user .meta {{
    margin: .15rem 0 0;
    color: #cbd5ff;
    font-size: .85rem;
    word-break: break-word;
  }}

  /* ---------- Sidebar navigation links ---------- */
  nav.sidebar {{
    display: grid;
    gap: .5rem;
    margin-top: .25rem;
  }}
  nav.sidebar a {{
    display: flex; align-items: center;
    gap: .5rem;
    padding: .65rem .75rem;
    border-radius: .6rem;
    text-decoration: none;
    color: #eef2ff;
    border: 1px solid transparent;
    transition: background .15s ease, border-color .15s ease, transform .04s ease;
  }}
  nav.sidebar a:hover {{
    background: rgba(255,255,255,.08);
    border-color: rgba(255,255,255,.12);
  }}
  nav.sidebar a:active {{ transform: translateY(1px); }}
  nav.sidebar a.primary {{
    background: var(--brand);
    border-color: var(--brand-600);
    color: #fff;
  }}

  /* ---------- Top bar for main content ---------- */
  header.top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    background: var(--card);
    border-bottom: 1px solid #e5e7eb;
  }}
  header.top .title {{
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--brand-600);
  }}
  header.top a.logout {{
    text-decoration: none;
    color: #6b7280;
    font-weight: 600;
  }}

  /* ---------- Main content area ---------- */
  main.content {{
    padding: 1.25rem;
  }}

  /* Card styling for the main dashboard content */
  .card {{
    background: var(--card);
    border: 1px solid #e5e7eb;
    border-radius: .9rem;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
  }}

  /* ---------- Table styling for current bids ---------- */
  .muted {{ color: var(--muted); font-size: .95rem; }}
  .tbl {{ width: 100%; border-collapse: collapse; margin-top: .5rem; }}
  .tbl th, .tbl td {{
    padding: .4rem .5rem;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
    font-size: .9rem;
  }}
  .tbl th {{
    background: #f9fafb;
    font-weight: 600;
  }}
  .warn {{ color: #b45309; font-weight: 600; }}
  form.inline {{
    display: inline-flex;
    gap: .35rem;
    align-items: center;
    margin: 0;
  }}
  input[type=number] {{
    width: 7ch;
    padding: .2rem .3rem;
  }}
  button {{
    cursor: pointer;
    border-radius: .375rem;
    border: 1px solid #d1d5db;
    padding: .25rem .6rem;
    background: #f9fafb;
  }}
  button:hover {{
    background: #f3f4f6;
  }}

  /* ---------- Responsive layout for smaller screens ---------- */
  @media (max-width: 760px) {{
    body {{
      grid-template-columns: 1fr;     /* Collapse into single column */
      grid-template-rows: auto 1fr;   /* Sidebar on top, content below */
    }}
    aside {{ grid-row: 1; }}
  }}
</style>

<!-- ========== HTML Structure ========== -->

<!-- Sidebar -->
<aside>
  <!-- Portal Title + Subtitle -->
  <div class="brand" role="banner">
    <h1>CS370 Auction Portal</h1>
    <div class="sub">Dashboard</div>
  </div>

  <!-- Logged-in User Info -->
  <section class="user" aria-label="User">
    <p class="hello">Welcome, {user_name or "bidder"}</p>
    <p class="meta">{email}</p>
  </section>

  <!-- Navigation Links -->
  <nav class="sidebar" aria-label="Main navigation">
    <a class="primary" href="{SITE_ROOT}cgi/transactions.py">Your Transactions</a>
    <a href="{SITE_ROOT}cgi/bid.py">Bid on an Item</a>
    <a href="{SITE_ROOT}cgi/sell.py">Sell an Item</a>
    <a href="{SITE_ROOT}cgi/logout.py">Log out</a>
  </nav>
</aside>

<!-- Right-side Main Area -->
<div>
  <!-- Top Bar above main content -->
  <header class="top">
    <h2 class="title">Dashboard</h2>
    <a class="logout" href="{SITE_ROOT}cgi/logout.py">Log out</a>
  </header>

  <!-- Main content section -->
  <main class="content" role="main">
    <section class="card">
      <p>This is your dashboard. Choose an action from the left.</p>
    </section>
    {active_section}
  </main>
</div>
"""))


# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()

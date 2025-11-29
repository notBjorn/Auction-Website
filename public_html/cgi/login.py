#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — login.py
# Handles login form display, credential verification, session creation,
# and redirect to the dashboard.
# =============================================================================

# ====== Imports / Setup ======================================================
import cgitb; cgitb.enable()
import os, html

from utils import (
    SITE_ROOT, TABLE_USER,
    html_page, parse_urlencoded, read_post_body, redirect,
    db, check_password_dev, set_cookie, create_session
)

from display_auctions import (
    render_money,
    format_time_remaining,
    fetch_all_running_auctions,
)

def fetch_public_running_auctions(conn):
    sql = """
          SELECT
              A.auction_id,
              I.item_name,
              I.description,
              I.category,
              A.start_price,
              COALESCE(MAX(B.bid_amount), A.start_price) AS current_price,
              COUNT(B.bid_id) AS bid_count,
              TIMESTAMPDIFF(SECOND, NOW(),
                                    DATE_ADD(A.start_time, INTERVAL A.duration SECOND)
              ) AS seconds_remaining
          FROM Auctions A
                   JOIN Items I USING (item_id)
                   LEFT JOIN Bids B ON B.auction_id = A.auction_id
          WHERE A.status='running'
          GROUP BY A.auction_id
          ORDER BY seconds_remaining ASC
              LIMIT 500; \
          """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()

# ====== helper function to bring auctions (as smaller cards) to login page =====

def render_auction_cards_for_login(auctions):
    """Return just the auction cards HTML (No nav bars, no headers)."""
    if not auctions:
        return '<p class="placeholder">No running auctions right now.</p>'

    cards = []
    for a in auctions:
        item_name = html.escape(a["item_name"] or "Untitled")
        desc = html.escape(a["description"] or "")
        short_desc = desc[:90] + "..." if len(desc) > 90 else desc
        price = render_money(a["current_price"])
        bid_count = a["bid_count"] or 0
        time_left = format_time_remaining(a["seconds_remaining"])

        card = f"""
        <div class="auction-mini-card">
            <h3>{item_name}</h3>
            <p class="mini-desc">{short_desc}</p>
            <div class="mini-stats">
                <span>${price}</span>
                <span>{bid_count}</span>
                <span>{time_left}</span>
            </div>
        </div>
        """
        cards.append(card)

    return '<div class="auction-mini-grid">' + ''.join(cards) + '</div>'

# ====== View: Full Login Page (styled like dashboard) =======================
def render_login_page(msg: str = "", auctions_html: str = "") -> str:
    """
    Render the full login page with:
      - Top header bar (brand on left, login form on right)
      - Main section with placeholder 'Auction Listing TBD'
    """
    error_html = (
        f'<p class="error" role="alert">{html.escape(msg)}</p>'
        if msg else ""
    )

    return f"""
<style>
  /* ---------- Color and layout variables (match dashboard) ---------- */
  :root {{
    --brand: #0a58ca;          /* Primary blue for links/buttons */
    --brand-600: #0947a5;      /* Slightly darker blue for hover states */
    --bg: #f6f7fb;             /* Light gray background for the main page */
    --text: #1f2937;           /* Default text color (dark gray) */
    --muted: #6b7280;          /* Secondary text color (lighter gray) */
    --card: #ffffff;           /* White background for content cards */
  }}

  * {{ box-sizing: border-box; }}
  html, body {{
    height: 100%;
    margin: 0;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    color: var(--text);
    background: var(--bg);
  }}

  body {{
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }}

  /* ---------- Top header bar ---------- */
  header.top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    background: var(--card);
    border-bottom: 1px solid #e5e7eb;
  }}

  .brand {{
    display: grid;
    gap: .25rem;
  }}
  .brand h1 {{
    margin: 0;
    font-size: 1.15rem;
    letter-spacing: .2px;
    font-weight: 800;
    color: var(--brand-600);
  }}
  .brand .sub {{
    color: var(--muted);
    font-size: .9rem;
  }}

  /* ---------- Inline login form (top-right) ---------- */
  form.login-inline {{
    display: inline-flex;
    align-items: center;
    gap: .5rem;
    margin: 0;
  }}
  form.login-inline label {{
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0,0,0,0);
    border: 0;
  }}
  form.login-inline input[type="email"],
  form.login-inline input[type="password"] {{
    padding: .35rem .5rem;
    border-radius: .4rem;
    border: 1px solid #d1d5db;
    font-size: .9rem;
    min-width: 14ch;
  }}
  form.login-inline input::placeholder {{
    color: #9ca3af;
  }}
  form.login-inline button {{
    cursor: pointer;
    border-radius: .4rem;
    border: 1px solid var(--brand-600);
    padding: .35rem .7rem;
    background: var(--brand);
    color: #fff;
    font-size: .9rem;
    font-weight: 600;
  }}
  form.login-inline button:hover {{
    background: var(--brand-600);
  }}
  form.login-inline a.register-link {{
    margin-left: .5rem;
    font-size: .9rem;
    text-decoration: none;
    color: var(--brand-600);
    font-weight: 500;
  }}
  form.login-inline a.register-link:hover {{
    text-decoration: underline;
  }}

  /* ---------- Main content area ---------- */
  main.content {{
    flex: 1;
    padding: 1.5rem;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
  }}

  .card {{
    background: var(--card);
    border: 1px solid #e5e7eb;
    border-radius: .9rem;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
  }}

  .card h2 {{
    margin-top: 0;
    margin-bottom: .4rem;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--brand-600);
  }}

  .muted {{
    color: var(--muted);
    font-size: .95rem;
    margin-top: 0;
  }}

  .error {{
    margin: .75rem 0 0;
    padding: .5rem .75rem;
    border-radius: .5rem;
    background: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
    font-size: .9rem;
  }}

  .placeholder {{
    text-align: center;
    padding: 2.25rem 0 2rem;
    font-size: 1rem;
    color: var(--muted);
    font-style: italic;
  }}

  hr.divider {{
    border: none;
    border-top: 1px dashed #d1d5db;
    margin: 1.25rem 0;
  }}

  /* ---------- Responsive tweaks ---------- */
  @media (max-width: 720px) {{
    header.top {{
      flex-direction: column;
      align-items: flex-start;
      gap: .75rem;
    }}
    form.login-inline {{
      width: 100%;
      flex-wrap: wrap;
      justify-content: flex-start;
    }}
  }}
  
  /* ---------- Auction mini-cards (for login page) ---------- */

.auction-mini-grid {{
    display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}}

.auction-mini-card {{
    background: var(--card);
  border: 1px solid #e5e7eb;
  border-radius: .6rem;
  padding: .75rem 1rem;
}}

.auction-mini-card h3 {{
    margin: 0 0 .5rem 0;
  font-size: 1rem;
  color: var(--brand-600);
}}

.mini-desc {{
    color: var(--muted);
  font-size: .85rem;
  margin: 0 0 .75rem 0;
}}

.mini-stats {{
    display: flex;
  justify-content: space-between;
  font-size: .85rem;
  color: var(--text);
  font-weight: 600;
}}

</style>

<header class="top">
  <div class="brand" role="banner">
    <h1>CS370 Auction Portal</h1>
    <div class="sub">Log in to access your dashboard</div>
    {error_html}
  </div>

  <!-- Login form on the upper right -->
  <form class="login-inline" method="post" action="{SITE_ROOT}cgi/login.py">
    <label for="e">Email</label>
    <input id="e" name="email" type="email" placeholder="Email" required>
    <label for="p">Password</label>
    <input id="p" name="password" type="password" placeholder="Password" required>
    <button type="submit">Log in</button>
    <a class="register-link" href="{SITE_ROOT}cgi/register.py">Register</a>
  </form>
</header>

<main class="content" role="main">
  <section class="card">
    <h2>Browse Auctions</h2>
    {auctions_html or '<p class="muted">No running auctions right now.</p>'}
  </section>
</main>
"""

# ====== Controller: Request Routing =========================================
def main():
    """
    GET  -> render login page.
    POST -> validate input, verify credentials, create session, redirect.
    """
    method = (os.environ.get("REQUEST_METHOD") or "GET").upper()

    # ----- GET: show the styled login page ----------------------------------
    if method == "GET":
        auctions = []
        try:
            cn = db()
            # Use the public query that does NOT filter by owner_id
            auctions = fetch_public_running_auctions(cn)
        except Exception:
            auctions = []
        finally:
            try:
                cn.close()
            except Exception:
                pass

        auction_html = render_auction_cards_for_login(auctions)

        print("Content-Type: text/html\n")
        print(html_page("Login", render_login_page(auctions_html=auction_html)))
        return


    # ----- POST: parse/validate form ----------------------------------------
    form = parse_urlencoded(read_post_body())
    email = (form.get("email") or "").strip().lower()
    pw    = form.get("password") or ""

    if not email or not pw:
        print("Content-Type: text/html\n")
        print(html_page("Login", render_login_page("Email and password are required.")))
        return

    # ====== Model: Lookup user by email (parameterized) ======================
    user_row = None
    try:
        cn = db()
        with cn.cursor() as cur:
            cur.execute(
                f"SELECT user_id, password_hash FROM `{TABLE_USER}` WHERE email=%s LIMIT 1",
                (email,)
            )
            user_row = cur.fetchone()
    except Exception as e:
        # ====== Error View: Database Error ===================================
        print("Content-Type: text/html\n")
        print(html_page("Login Error",
                        f"<h1>Database Error</h1><pre>{html.escape(str(e))}</pre>"))
        return
    finally:
        try:
            cn.close()
        except Exception:
            pass

    # ====== Auth: Verify Password (SHA-256 or plaintext dev) =================
    if not user_row or not check_password_dev(pw, (user_row.get("password_hash") or "")):
        print("Content-Type: text/html\n")
        print(html_page("Login", render_login_page("Invalid credentials.")))
        return

    # ====== Sessions: Create Session + Set Cookie ============================
    sid = create_session(user_row["user_id"])
    cookie = set_cookie("SID", sid, path=SITE_ROOT, http_only=True)

    # ====== Redirect: Dashboard ==============================================
    redirect(f"{SITE_ROOT}cgi/dashboard.py", extra_headers=[cookie])

# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()

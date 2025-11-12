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
    Render a simple HTML form for selling an item.

    :param user: Dictionary containing user info (e.g. username, email)
    :param message: Optional success or error text displayed at the top of the page
    :param values: Optional dictionary with prefilled form data if validation failed
    :return: None (prints HTML output to stdout for CGI)
    """

    values = values or {}   # If values is None or empty, replace it with an empty dictionary {}
    # prevents Python errors later when we try to access fields from it

    desc = html.escape(values.get("description", ""))
    price = html.escape(values.get("starting_price", ""))
    start = html.escape(values.get("start_dt", ""))

    # f"""...""" means we're using an f-string where {...} allows inserting variables directly
    body = f"""   
<h1>Sell an Item</h1>
{f'<p role="alert"><strong>{html.escape(message)}</strong></p>' if message else ''}

<!-- This section builds the form visible to the user --> 
<form method="post" action="{SITE_ROOT}cgi/sell.py" novalidate>

  <!-- Item description field -->
  <label for="desc">Describe your item</label><br>
  <textarea id="desc" name="description" required>{desc}</textarea><br><br>
  
  <!-- Starting price input -->
  <label for="price">Starting price ($)</label><br>
  <input type="number" id="price" name="starting_price" step="0.01" min="0" value="{price}" required><br><br>
  
  <label for="start">When do you want to start your auction?</label><br>
  <small><em>Select both date and time using the drop down below.</em></small><br>
  <input type="datetime-local" id="start" name="start_dt" value="{start}" required><br>
  <small>All auctions last 168 hours (7 days).</small><br><br>
  
  <button type="submit">Create Auction</button>
</form>

<p>
  <a href="{SITE_ROOT}cgi/transactions.py">Back to Transactions</a> |
  <a href="{SITE_ROOT}cgi/dashboard.py">Back to Dashboard</a>
</p>
"""
    print("Content-Type: text/html; charset=utf-8\n")
    print(html_page("Sell an Item", body))


def create_auction(conn, owner_id, description, starting_price, start_dt):
    description = (description or "").strip()
    if not description or not starting_price or not start_dt:
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

        # Insert Item
        cur.execute("""
                    INSERT INTO Items (owner_id, item_name, category, description, posted_date, last_modified)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """, (owner_id, description, "General", description))

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
        "description":     form.getfirst("description", ""),
        "starting_price":  form.getfirst("starting_price", ""),
        "start_dt":        form.getfirst("start_dt", "")
    }

    conn = db()
    try:
        try:
            status, payload = create_auction(
                conn, user["user_id"],
                values["description"],
                values["starting_price"],
                values["start_dt"]
            )
            if status == "ok":
                # PRG: Redirect so refresh/double-click doesn’t re-POST
                # You can read this in transactions.py to show a flash
                redirect(f"{SITE_ROOT}cgi/transactions.py?flash=auction_created&aid={payload}")
                return
            else:
                message = payload  # error string from create_auction
        except Exception as e:
            message = f"Error creating auction: {html.escape(str(e))}"
    finally:
        conn.close()

    # On error, fall back to re-render with sticky values
    render_form(user, message, values)




if __name__ == "__main__":
    main()

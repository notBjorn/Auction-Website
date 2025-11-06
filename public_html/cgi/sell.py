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
  <label for="desc">Description</label><br>
  <textarea id="desc" name="description" required>{desc}</textarea><br><br>
  
  <!-- Starting price input -->
  <label for="price">Starting price ($)</label><br>
  <input type="number" id="price" name="starting_price" step="0.01" min="0" value="{price}" required><br><br>
  
  <label for="start">Start date & time</label><br>
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
    """
    Server-side validation and DB inserts
    Keep errors short and specific for the UI
    """

    description = (description or "").strip()
    if not description or not starting_price or not start_dt:
        return "All fields are required."

    # money as string: MySQL DECIMAL will store precisely
    sp = to_decimal_str(starting_price)
    if sp is None:
        return "Starting price must be a valid number (up to 2 decimals)."

    with conn.cursor() as cur:
        cur.execute("START TRANSACTION")
        # 1) Create the Item record
        cur.execute("""
                    INSERT INTO Items (owner_id, item_name, created_at)
                    VALUES (%s, %s, NOW())
                    """, (owner_id, description))

        cur.execute("SELECT LAST_INSERT_ID() AS id")
        item_id = cur.fetchone()["id"]

        # 2) Auction (status based on start time; duration fixed 7 days)
        cur.execute("""
                    INSERT INTO Auctions (item_id, start_time, duration, status, start_price)
                    VALUES (
                               %s,
                               %s,
                               %s,
                               CASE WHEN %s <= NOW() THEN 'running' ELSE 'scheduled' END,
                               %s
                           )
                    """, (item_id, start_dt, SEVEN_DAYS_SECONDS, start_dt, sp))

        cur.execute("COMMIT")

    return "Auction created!"


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
        "description":      form.getfirst("description", ""),
        "starting_price":   form.getfirst("starting_price", ""),
        "start_dt":         form.getfirst("start_dt", "")
    }

    conn = db()
    try:
        message = create_auction(
            conn, user["user_id"],
            values["description"],
            values["starting_price"],
            values["start_dt"]
        )
    finally:
        conn.close()
    # Re-render the form with a message and sticky values
    render_form(user, message, values)


if __name__ == "__main__":
    main()

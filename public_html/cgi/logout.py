#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =============================================================================
# CS370 Auction Website — logout.py
# Ends the current user session by deleting the session record and expiring
# the SID cookie. Redirects back to the login page afterward.
# =============================================================================

# ====== Imports / Setup ======================================================
import cgitb; cgitb.enable(display=0, logdir="/home/student/rsharma/public_html/cgi/logs")

from utils import SITE_ROOT, get_cookie, delete_session, expire_cookie, redirect

# ====== Controller: Main Request Handler =====================================
def main():
    sid = get_cookie("SID")
    if sid:
        try:
            delete_session(sid)
        except Exception:
            pass  # best-effort cleanup

    # ----- Expire cookie and redirect ----------------------------------------
    headers = [expire_cookie("SID", path=SITE_ROOT)]
    redirect(f"{SITE_ROOT}cgi/login.py", extra_headers=headers)

# ====== Entry Point ==========================================================
if __name__ == "__main__":
    main()

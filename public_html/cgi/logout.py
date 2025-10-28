#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgitb; cgitb.enable()

from utils import SITE_ROOT, get_cookie, delete_session, expire_cookie, redirect

def main():
    sid = get_cookie("SID")
    if sid:
        try:
            delete_session(sid)
        except Exception:
            pass  # best-effort

    # expire cookie + redirect
    headers = [expire_cookie("SID", path=SITE_ROOT)]
    redirect(f"{SITE_ROOT}cgi/login.py", extra_headers=headers)

if __name__ == "__main__":
    main()

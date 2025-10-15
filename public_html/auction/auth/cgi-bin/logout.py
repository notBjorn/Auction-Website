#!/home/cafcode/auction-auth/.venv/bin/python3
from utils import *
def main():
    if os.environ.get("REQUEST_METHOD","GET") == "GET":
        redirect("/cgi-bin/dashboard.py")
    cn = db()
    sess = get_session(cn)
    form = parse_urlencoded(read_post_body())
    if not (sess and form.get("csrf") == sess["csrf_token"]):
        header(); print(html_page("Error","<p>Invalid CSRF token.</p>")); return
    destroy_session(cn)
    cookie = expire_cookie("SID")
    redirect("/cgi-bin/login.py", extra=[cookie])
if __name__ == "__main__":
    main()


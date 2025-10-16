#!/usr/bin/python3
import pymysql.cursors

print("Content-Type: text/html\n")  # Required CGI header

# --- Database connection info ---
connection = pymysql.connect(
    host='localhost',
    user='cs370_section2_cafcode',       # your team's MySQL username
    password='edocfac_001', # your team's MySQL password
    database='cs370_section2_cafcode',   # your team's database
    cursorclass=pymysql.cursors.DictCursor
)

# --- Run a simple SQL query ---
with connection.cursor() as cursor:
    cursor.execute("SELECT NOW() AS date_and_time;")
    result = cursor.fetchone()

# --- Display the result in HTML ---
print("<html><body>")
print("<h1>Database Connection Test</h1>")
print(f"<p>Current MySQL Time: {result['date_and_time']}</p>")
print("</body></html>")

connection.close()

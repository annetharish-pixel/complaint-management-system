from flask import Flask, render_template, request, redirect, session
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = "complaint123"

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("complaints.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT UNIQUE,
        name TEXT,
        department TEXT,
        complaint TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        department TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        department = request.form["department"]

        conn = sqlite3.connect("complaints.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users(name,email,password,department) VALUES(?,?,?,?)",
            (name, email, password, department)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ---------------- USER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("complaints.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = user[0]
            return redirect("/submit")

        return "<h2>Invalid Email or Password</h2>"

    return render_template("login.html")

# ---------------- ADMIN LOGIN ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/complaints")

        return "<h2>Invalid Admin Username or Password</h2>"

    return render_template("admin.html")

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- SUBMIT COMPLAINT ----------------
@app.route("/submit", methods=["GET", "POST"])
def submit():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        complaint_id = "CMP" + str(uuid.uuid4().int)[:6]

        name = request.form["name"]
        department = request.form["department"]
        complaint = request.form["complaint"]

        conn = sqlite3.connect("complaints.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO complaints(complaint_id, name, department, complaint, status) VALUES(?,?,?,?,?)",
            (complaint_id, name, department, complaint, "Pending")
        )

        conn.commit()
        conn.close()

        return f"""
        <h2>Complaint Submitted Successfully!</h2>
        <h3>Your Complaint ID: {complaint_id}</h3>
        <br>
        <a href='/'>Go Home</a>
        """

    return render_template("submit.html")


# ---------------- VIEW COMPLAINTS ----------------

@app.route("/complaints", methods=["GET", "POST"])
def complaints():

    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("complaints.db")
    cursor = conn.cursor()

    if request.method == "POST":
        search = request.form["search"]

        cursor.execute("""
        SELECT * FROM complaints
        WHERE complaint_id LIKE ?
        OR name LIKE ?
        OR department LIKE ?
        """, ('%'+search+'%', '%'+search+'%', '%'+search+'%'))

    else:
        cursor.execute("SELECT * FROM complaints")

    data = cursor.fetchall()

    conn.close()

    return render_template("complaints.html", data=data)


# ---------------- RESOLVE COMPLAINT ----------------

@app.route("/resolve/<int:id>")
def resolve(id):

    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("complaints.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE complaints SET status=? WHERE id=?",
        ("Resolved", id)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- TRACK COMPLAINT ----------------

@app.route("/track", methods=["GET", "POST"])
def track():

    result = None

    if request.method == "POST":

        complaint_id = request.form["complaint_id"]

        conn = sqlite3.connect("complaints.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM complaints WHERE complaint_id=?",
            (complaint_id,)
        )

        result = cursor.fetchone()

        conn.close()

    return render_template("track.html", result=result)

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("complaints.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        resolved=resolved
    )
    # ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
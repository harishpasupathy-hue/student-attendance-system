from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "attendance_secret_key"

DATABASE = "attendance.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE,
            name TEXT,
            department TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()


# Login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    total_present = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE status='Present'"
    ).fetchone()[0]

    total_absent = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE status='Absent'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_present=total_present,
        total_absent=total_absent
    )


# Student management
@app.route("/students", methods=["GET", "POST"])
def students():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    if request.method == "POST":

        roll_no = request.form["roll_no"]
        name = request.form["name"]
        department = request.form["department"]

        try:
            conn.execute(
                "INSERT INTO students (roll_no, name, department) VALUES (?, ?, ?)",
                (roll_no, name, department)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            pass

    students_list = conn.execute(
        "SELECT * FROM students ORDER BY roll_no"
    ).fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=students_list
    )


# Delete student
@app.route("/delete/<int:id>")
def delete_student(id):

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    conn.execute(
        "DELETE FROM attendance WHERE student_id=?",
        (id,)
    )

    conn.execute(
        "DELETE FROM students WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/students")


# Mark attendance
@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    students_list = conn.execute(
        "SELECT * FROM students ORDER BY roll_no"
    ).fetchall()

    if request.method == "POST":

        date = request.form["date"]

        for student in students_list:

            status = request.form.get(
                "status_" + str(student["id"])
            )

            if status:

                conn.execute(
                    "INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
                    (student["id"], date, status)
                )

        conn.commit()

    conn.close()

    return render_template(
        "attendance.html",
        students=students_list
    )


# Attendance report
@app.route("/report")
def report():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    students_list = conn.execute(
        "SELECT * FROM students ORDER BY roll_no"
    ).fetchall()

    report_data = []

    for student in students_list:

        total = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id=?",
            (student["id"],)
        ).fetchone()[0]

        present = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Present'",
            (student["id"],)
        ).fetchone()[0]

        if total > 0:
            percentage = round((present / total) * 100, 2)
        else:
            percentage = 0

        report_data.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "department": student["department"],
            "total": total,
            "present": present,
            "percentage": percentage
        })

    conn.close()

    return render_template(
        "report.html",
        report=report_data
    )


# Logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
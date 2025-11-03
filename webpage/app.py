import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# Get absolute path to the project root (one level up from /webpage)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database path (located in project root)
DB_PATH = os.path.join(BASE_DIR, "data.db")

def get_professor_courses(professor_name):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 
            C.CourseCode,
            C.CourseName,
            C.CourseType,
            C.Semester,
            E.Date,
            E.Time,
            E.Room1, E.Room2, E.Room3, E.Room4, E.Room5
        FROM Courses AS C
        LEFT JOIN ExamSchedule AS E
        ON C.CourseCode = E.CourseCode
        AND C.CourseType = E.CourseType
        AND C.CoordinatorName = E.CoordinatorName
        AND C.Semester = E.Semester
        WHERE C.CoordinatorName = ?
        ORDER BY C.Semester, C.CourseCode, E.Date, E.Time
    """, (professor_name,))

    rows = cursor.fetchall()
    connection.close()

    # Clean and format rooms
    courses = []
    for r in rows:
        rooms = [r["Room1"], r["Room2"], r["Room3"], r["Room4"], r["Room5"]]
        rooms = [room for room in rooms if room not in (None, "", "—")]
        courses.append({
            "CourseCode": r["CourseCode"],
            "CourseName": r["CourseName"],
            "CourseType": r["CourseType"],
            "Semester": r["Semester"],
            "Date": r["Date"],
            "Time": r["Time"],
            "Rooms": rooms
        })

    return courses

def get_student_entries(student_id):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # --- Step 1: Get student's seating arrangement ---
    cursor.execute("""
        SELECT 
            Date, time_slot, Room,
            CASE 
                WHEN StudentIdA = ? THEN SeatNoA 
                ELSE SeatNoB 
            END AS SeatNo,
            CASE 
                WHEN StudentIdA = ? THEN StudentIdA 
                ELSE StudentIdB 
            END AS StudentId,
            CASE 
                WHEN StudentIdA = ? THEN NameA 
                ELSE NameB 
            END AS Name,
            CASE 
                WHEN StudentIdA = ? THEN BatchA 
                ELSE BatchB 
            END AS Batch
        FROM Arrangement
        WHERE StudentIdA = ? OR StudentIdB = ?
        ORDER BY Date, time_slot, Room
    """, (student_id, student_id, student_id, student_id, student_id, student_id))
    arrangement_rows = [dict(row) for row in cursor.fetchall()]

    # --- Step 2: Get all courses this student is enrolled in (with course details) ---
    cursor.execute("""
        SELECT 
            E.CourseCode,
            E.CourseType,
            E.Semester,
            E.CoordinatorName,
            C.CourseName,
            ES.Date,
            ES.Time AS time_slot
        FROM Enrollments AS E
        JOIN Courses AS C
            ON E.CourseCode = C.CourseCode
           AND E.CourseType = C.CourseType
           AND E.Semester = C.Semester
           AND E.CoordinatorName = C.CoordinatorName
        JOIN ExamSchedule AS ES
            ON E.CourseCode = ES.CourseCode
           AND E.CourseType = ES.CourseType
           AND E.Semester = ES.Semester
           AND E.CoordinatorName = ES.CoordinatorName
        WHERE E.Id = ?
    """, (student_id,))
    course_rows = [dict(row) for row in cursor.fetchall()]

    connection.close()

    # --- Step 3: Merge both datasets based on date and time slot ---
    merged = []
    for seat in arrangement_rows:
        matching_courses = [
            {
                "CourseCode": c["CourseCode"],
                "CourseName": c["CourseName"],
                "CourseType": c["CourseType"],
                "Semester": c["Semester"],
                "CoordinatorName": c["CoordinatorName"]
            }
            for c in course_rows
            if str(c["Date"]) == str(seat["Date"]) and str(c["time_slot"]) == str(seat["time_slot"])
        ]

        if matching_courses:    
            seat["Courses"] = matching_courses
        else:
            seat["Courses"] = []

        merged.append(seat)

    return merged


@app.route("/", methods=["GET", "POST"])
def home():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Fetch dropdown options for "Classes" mode
    cursor.execute("SELECT DISTINCT Date FROM Arrangement ORDER BY Date;")
    dates = [row["Date"] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT time_slot FROM Arrangement ORDER BY time_slot;")
    times = [row["time_slot"] for row in cursor.fetchall()]

    cursor.execute("SELECT RoomNo FROM Rooms ORDER BY RoomNo;")
    rooms = [row["RoomNo"] for row in cursor.fetchall()]

    connection.close()

    # Student form submitted
    if "student_id" in request.form:
        student_id = request.form.get("student_id").strip()
        results = get_student_entries(student_id)
        return render_template("result.html", student_id=student_id, results=results)

    # Professor form submitted
    elif "professor_name" in request.form:
        name = request.form.get("professor_name").strip()
        results = get_professor_courses(name)
        return render_template("professor_result.html", professor=name, results=results)

    # Class form submitted
    elif all(k in request.form for k in ["date", "time_slot", "room"]):
        date = request.form.get("date")
        time = request.form.get("time_slot")
        room = request.form.get("room")

        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute("""
            SELECT 
                Date, time_slot, Room,
                SeatNoA, StudentIdA, NameA, BatchA,
                SeatNoB, StudentIdB, NameB, BatchB
            FROM Arrangement
            WHERE Date = ? AND time_slot = ? AND Room = ?
            ORDER BY SeatNoA, SeatNoB
        """, (date, time, room))
        results = cursor.fetchall()
        connection.close()

        return render_template(
            "class_result.html",
            results=results,
            date=date,
            time=time,
            room=room
        )

    # Default: show the page with all dropdown data
    return render_template("index.html", dates=dates, times=times, rooms=rooms)


@app.route("/student", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        student_id = request.form.get("student_id").strip()
        results = get_student_entries(student_id)
        return render_template("result.html", student_id=student_id, results=results)
    return render_template("index.html")

@app.route("/professor", methods=["POST"])
def professor_lookup():
    name = request.form["professor_name"]
    results = get_professor_courses(name)
    return render_template("professor_result.html", results=results, professor=name)

@app.route("/class", methods=["GET", "POST"])
def class_lookup():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Fetch dropdown options
    cursor.execute("SELECT DISTINCT Date FROM Arrangement ORDER BY Date;")
    dates = [row["Date"] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT time_slot FROM Arrangement ORDER BY time_slot;")
    times = [row["time_slot"] for row in cursor.fetchall()]

    cursor.execute("SELECT RoomNo FROM Rooms ORDER BY RoomNo;")
    rooms = [row["RoomNo"] for row in cursor.fetchall()]

    results = []
    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time_slot")
        room = request.form.get("room")

        cursor.execute("""
            SELECT 
                Date, time_slot, Room,
                SeatNoA, StudentIdA, NameA, BatchA,
                SeatNoB, StudentIdB, NameB, BatchB
            FROM Arrangement
            WHERE Date = ? AND time_slot = ? AND Room = ?
            ORDER BY CAST(REPLACE(SeatNoA, 'A', '') AS INTEGER)
        """, (date, time, room))
        results = cursor.fetchall()

    connection.close()

    return render_template(
        "class_result.html",
        dates=dates,
        times=times,
        rooms=rooms,
        results=results
    )

if __name__ == "__main__":
    app.run(debug=True)

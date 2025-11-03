import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# Get absolute path to the project root (one level up from /webpage)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database path (located in project root)
DB_PATH = os.path.join(BASE_DIR, "data.db")

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
def index():
    if request.method == "POST":
        student_id = request.form.get("student_id").strip()
        results = get_student_entries(student_id)
        return render_template("result.html", student_id=student_id, results=results)
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)

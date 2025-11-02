import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# Get absolute path to the project root (one level up from /webpage)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database path (located in project root)
DB_PATH = os.path.join(BASE_DIR, "seating_arrangement.db")

def get_student_entries(student_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT Date, time_slot, Room,
               SeatNoA, StudentIdA, NameA, BatchA,
               SeatNoB, StudentIdB, NameB, BatchB
        FROM arrangement
        WHERE StudentIdA = ? OR StudentIdB = ?
    """, (student_id, student_id))
    rows = cursor.fetchall()
    connection.close()
    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        student_id = request.form.get("student_id").strip()
        results = get_student_entries(student_id)
        return render_template("result.html", student_id=student_id, results=results)
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)

import sqlite3

db_path = "data.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# student data
cursor.execute("SELECT DISTINCT CourseCode FROM Enrollments;")
course_codes = [row[0] for row in cursor.fetchall()]
student_data = {code: [0] * 8 for code in course_codes}

print(student_data);

for CourseCode in student_data:
    cursor.execute("SELECT COUNT(*) CourseCode FROM Enrollments")
    student_data[CourseCode] = 
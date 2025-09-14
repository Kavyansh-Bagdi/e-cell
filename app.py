import sqlite3
from functions.room import Room
from functions.pdf_generator import generate_seating_pdf
from collections import deque

db_path = "data.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# student data
# CourseCode = no of student enroll
cursor.execute("SELECT DISTINCT CourseCode FROM Enrollments;")
course_codes = [row[0] for row in cursor.fetchall()]
student_data = {code: 0 for code in course_codes}

for course_code in student_data:
    cursor.execute("SELECT COUNT(*) FROM Enrollments WHERE CourseCode = ?", (course_code,))
    student_data[course_code] = cursor.fetchone()[0]

# time slot
cursor.execute("SELECT DISTINCT Time FROM ExamSchedule")
time_slots = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT DISTINCT Date FROM ExamSchedule")
days = [row[0] for row in cursor.fetchall()]

# classroom capacity
cursor.execute("SELECT Room, SeatA FROM Rooms");
classroom_capacity = {};
for tuple in cursor.fetchall():
    classroom_capacity['VLTC-'+tuple[0]] = tuple[1];

# print(days)
for day in days:

    # print("Day",day)

    for time_slot in time_slots:

        progress_tracker = {code: 0 for code in course_codes}

        # print("Time : ",time_slot)

        # fetch assign classroom for given day and time_slot
        cursor.execute(
            "SELECT Room1,Room2,Room3,Room4 FROM ExamSchedule WHERE Date = ? AND Time = ?",
            (day, time_slot)
        )
        classrooms = set()
        for row in cursor.fetchall():
            for room in row:
                if(room != None):
                    classrooms.add(room)
        classrooms = sorted(classrooms)

        # creating class object
        classroom_obj = {}
        for roomId in classrooms:
            classroom_obj[roomId] = Room(roomId,classroom_capacity[roomId])

        # fetching courses for corresponding classrooms
        courses_that_day = set()
        classrooms_course = {}
        for classroom in classrooms:
            cursor.execute('SELECT CourseCode FROM ExamSchedule WHERE Date = ? and Time = ? and ? in (Room1,Room2,Room3,Room4)',(day,time_slot,classroom))
            classrooms_course[classroom] = set()
            for course in cursor.fetchall():
                if(course != None):
                    classrooms_course[classroom].add(course[0])
                    courses_that_day.add(course[0])
            classrooms_course[classroom] = sorted(classrooms_course[classroom])
        classrooms_course = dict(sorted(classrooms_course.items()))

        # fetching all room coresponding to that course 
        course_room_that_day = {};
        for course in courses_that_day:
            cursor.execute('SELECT Room1,Room2,Room3,Room4 FROM ExamSchedule WHERE Date = ? AND Time = ? AND CourseCode = ?',(day,time_slot,course))

            course_room_that_day[course] = []
            for tuple in cursor.fetchall():
                for room in tuple:
                    if(room != None):
                        course_room_that_day[course].append(room)
                course_room_that_day[course] = sorted(course_room_that_day[course])

        course_room_that_day = dict(sorted(course_room_that_day.items()))
        # print(day,time_slot,course_room_that_day)

        # allocating seats | main
        for room in classrooms:
            print(classrooms_course[room])
            for courseId in (classrooms_course[room]):

                cursor = connection.cursor()
                cursor.execute("""
                    SELECT Students.ID FROM Students
                    JOIN Enrollments ON Students.ID = Enrollments.ID
                    WHERE Enrollments.CourseCode = ?
                    ORDER BY Students.ID
                """, (courseId,))

                all_students = deque([row[0] for row in cursor.fetchall()])

                seat_type = "SeatA" if list(classrooms_course[room]).index(courseId) % 2 == 0 else "SeatB"

                print(courseId," - ",course_room_that_day[courseId]);

                for courseId_room in (course_room_that_day[courseId]):
                    for seat in range(classroom_obj[courseId_room].left(seat_type)):
                        if(len(all_students) == 0):
                            break 
                        classroom_obj[courseId_room].allocate(all_students.popleft(),seat_type)

        generate_seating_pdf(classroom_obj,str(day+'_'+time_slot+'seating_arrangement'))

        # print(classrooms)

        # print("Classrooms : ",classrooms)

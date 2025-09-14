import sqlite3
from functions.room import Room
from functions.allocate_seat import allocate_course_sequentially

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
            "SELECT Room1,Room2,Room3 FROM ExamSchedule WHERE Date = ? AND Time = ?",
            (day, time_slot)
        )
        classrooms = set()
        for row in cursor.fetchall():
            for room in row:
                if(room != None):
                    classrooms.add(room)

        # creating class object
        print(classrooms)
        classroom_obj = {}
        for roomId in classrooms:
            classroom_obj[roomId] = Room(roomId,classroom_capacity[roomId])

        # fetching courses for corresponding classrooms
        courses_that_day = ()
        classrooms_course = {}
        for classroom in classrooms:
            cursor.execute('SELECT CourseCode FROM ExamSchedule WHERE Date = ? and Time = ? and ? in (Room1,Room2,Room3,Room4)',(day,time_slot,classroom))
            classrooms_course[classroom] = ()
            for course in cursor.fetchall():
                if(course != None):
                    classrooms_course[classroom].add(course[0])
                    courses_that_day.add(course[0])

        # fetching all room coresponding to that course 
        course_room_that_day = {};
        for course in courses_that_day:
            cursor.execute('SELECT Room1,Room2,Room3,Room4 FROM ExamSchedule WHERE Date = ? AND Time = ? AND CourseCode = ?',(day,time_slot,course))

            course_room_that_day[course] = ()
            for tuple in cursor.fetchall():
                for room in tuple:
                    if(room != None):
                        course_room_that_day[course].add(room)

        # allocating seats | main
        for room in classrooms:
            for courseId in classrooms_course[room]:
                for courseId_room in course_room_that_day[courseId]:
                    # decide seat type
                    seat_type = "SeatA";
                    if(classrooms_course[room].index(courseId) % 2 == 0){
                        seat_type = "SeatA"
                    }else{
                        seat_type = "SeatB"
                    }

                    allocate_course_sequentially(connection,classroom_obj[room],courseId,seat_type,progress_tracker)

        # print(classrooms)

        # print("Classrooms : ",classrooms)

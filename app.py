import sqlite3
from functions.room import Room
from functions.pdf_generator import generate_seating_pdf
from collections import deque
import os

def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")

db_path = "data.db"
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

semester = int(input("[ User Input ] Enter value for Semester: "))

print("""
[ Available Course Types ]
1. CORE
2. PROGRAM ELECTIVE
3. OPEN ELECTIVE
4. INSTITUTE CORE
5. HONORS
""")

course_type_options = {
    "1": "CORE",
    "2": "PROGRAM ELECTIVE",
    "3": "OPEN ELECTIVE",
    "4": "INSTITUTE CORE",
    "5": "HONORS"
}

choice = input("[ User Input ] Enter Course Type (1-5 or name): ").strip().upper()

if choice in course_type_options:
    course_type = course_type_options[choice]
else:
    course_type = choice.title()
    if course_type not in course_type_options.values():
        print("[ Warning ] Invalid course type entered. Defaulting to 'CORE'.")
        course_type = "CORE"


print("""
[ Available Degrees ]
1. B.Arch
2. M.Plan
3. B.Tech
4. M.Tech
5. M.Sc
6. Ph.D
7. MBA
""")

degree_options = {
    "1": "B.Arch",
    "2": "M.Plan",
    "3": "B.Tech",
    "4": "M.Tech",
    "5": "M.Sc",
    "6": "Ph.D",
    "7": "MBA"
}

deg_choice = input("[ User Input ] Enter Degree (1-7 or name): ").strip()

if deg_choice in degree_options:
    degree = degree_options[deg_choice]
else:
    degree = deg_choice.upper()
    if degree not in [d.upper() for d in degree_options.values()]:
        print("[ Warning ] Invalid degree entered. Defaulting to 'B.Tech'.")
        degree = "B.Tech"



# Allotment options
print("""
[ Allotment Type Options ]
1. Branch Wise
2. Course Wise
""")

allotment_options = {
    "1": "Branch Wise",
    "2": "Course Wise"
}

choice = input("[ User Input ] Enter Allotment Type (1-2 or name): ").strip().title()

if choice in allotment_options:
    allotment_type = allotment_options[choice]
else:
    # Normalize textual input
    if choice.lower() in ["branch wise", "branchwise"]:
        allotment_type = "Branch Wise"
    elif choice.lower() in ["course wise", "coursewise"]:
        allotment_type = "Course Wise"
    else:
        print("[ Warning ] Invalid choice. Defaulting to 'Branch Wise'.")
        allotment_type = "Branch Wise"

print(f"\n[ Selected ] Semester: {semester}, Course Type: {course_type}, Degree: {degree}")
print(f"[ Selected ] Allotment Type: {allotment_type}")

cursor.execute("SELECT RoomNo, SeatA FROM Rooms");
classroom_capacity = {};
for row in cursor.fetchall():
    classroom_capacity[row[0]] = row[1]


if allotment_type == "Branch Wise" :

    cursor.execute("SELECT CourseCode, CourseType, CoordinatorName, Semester FROM Courses WHERE Semester = ? AND Degree = ? AND CourseType = ?",(semester,degree,course_type))
    courses = [row for row in cursor.fetchall()]

    courses_student_dict = { (code, ctype, coord, sem): 0 for code, ctype, coord, sem in courses }


    for (code, ctype, coord, sem) in courses_student_dict.keys():
        cursor.execute("""
            SELECT Department 
            FROM CourseDept 
            WHERE CourseCode = ? 
            AND CourseType = ? 
            AND Semester = ? 
            AND CoordinatorName = ?;
        """, (code, ctype, sem, coord))

        dept_row = cursor.fetchone()
        department = dept_row[0] if dept_row else None

        if department:
            cursor.execute("""
                SELECT MAX(No_Student)
                FROM CourseDept
                WHERE Department = ? AND Semester = ?;
            """, (department, sem))
            max_row = cursor.fetchone()
            max_students = max_row[0] if max_row else 0
        else:
            max_students = 0

        courses_student_dict[(code, ctype, coord, sem)] = max_students

    # Dictionary to store (day, time) → list of courses
    schedule = {}

    for (code, ctype, coord, sem) in courses:
        cursor.execute("""
            SELECT Date, Time
            FROM ExamSchedule
            WHERE CourseCode = ? 
            AND CourseType = ? 
            AND Semester = ? 
            AND CoordinatorName = ?;
        """, (code, ctype, sem, coord))
        
        rows = cursor.fetchall()
        for (day, time_slot) in rows:
            key = (day, time_slot)
            if key not in schedule:
                schedule[key] = []
            schedule[key].append((code, ctype, coord, sem))

    day  = ""
    time_slot = ""
    no_course = 0

    for (_day,_time) in schedule:
        if no_course < len(schedule[_day,_time]) :
            no_course = len(schedule[(_day,_time)])
            day = _day
            time_slot = _time

    print("[DEBUG] No of Courses : ",no_course)
    print("[DEBUG] Courses : ",schedule[(day,time_slot)])
    room_to_courses = {}
    course_to_rooms = {}

    cursor.execute("""
        SELECT DISTINCT Room1, Room2, Room3, Room4
        FROM ExamSchedule
        WHERE Date = ? AND Time = ?;
    """, (day, time_slot))

    all_rooms = set()
    for row in cursor.fetchall():
        for room in row:
            if room:
                all_rooms.add(room)
    all_rooms = sorted(all_rooms)

    for room in all_rooms:
        room_to_courses[room] = set()  

        cursor.execute("""
            SELECT CourseCode, CourseType, CoordinatorName, Semester
            FROM ExamSchedule
            WHERE Date = ? AND Time = ? AND ? IN (Room1, Room2, Room3, Room4);
        """, (day, time_slot, room))

        for course in cursor.fetchall():
            if(course in courses):
                room_to_courses[room].add(course)
                if course not in course_to_rooms:
                    course_to_rooms[course] = []
                course_to_rooms[course].append(room)

    # re initializing room capacity for new day and time
    roomSeatAvailable = {}

    classroom_obj = {}
    for room in room_to_courses.keys():
        classroom_obj[room] = Room(room,classroom_capacity[room])

    for room in room_to_courses:
        roomSeatAvailable[room] = [classroom_capacity[room],classroom_capacity[room]]

    # visited Matrix
    isVisited = {}
    for course in course_to_rooms.keys():
        for room in course_to_rooms[course]:
            isVisited[(course,room)] = False

    for room in room_to_courses.keys():
        if len(room_to_courses[room]) == 0:
            continue

        for course_data in room_to_courses[room]:
            cursor.execute("""
                SELECT Students.ID
                FROM Students
                JOIN Enrollments ON Students.ID = Enrollments.ID
                WHERE Enrollments.CourseCode = ?
                AND Enrollments.CourseType = ?
                ORDER BY 
                    SUBSTR(Students.ID, 1, 4) DESC,   
                    SUBSTR(Students.ID, -4, 4) ASC;
            """, (course_data[0],course_data[1]))


            all_students = deque([row[0] for row in cursor.fetchall()])

            # occupy class fully : 1000
            # partially : -1000
            def calculateScore(seatType, classes):
                classCapacity = []
                for roomId in classes:
                    classCapacity.append(roomSeatAvailable[roomId][seatType])
                
                no_student = len(all_students)
                score = 0

                # if not enough seats in total → hard penalty
                if no_student > sum(classCapacity):
                    return -10000000000

                for capacity in classCapacity:
                    if no_student >= capacity:
                        score += 1000
                        no_student -= capacity
                    elif no_student > 0:
                        vacant = capacity - no_student
                        score -= vacant * 100
                        no_student = 0
                    else:
                        continue
                
                return score


            scoreA = calculateScore(0,course_to_rooms[course_data])
            scoreB = calculateScore(1,course_to_rooms[course_data])

            seatType = 0

            if(scoreA < scoreB):
                seatType = 1

            for room in course_to_rooms[course_data]:
                if isVisited[(course_data,room)]:
                    continue
                
                if not all_students:
                    break

                available = roomSeatAvailable[room][seatType]
                to_allocate = min(len(all_students), available)

                for _ in range(to_allocate):
                    studentId = all_students.popleft()
                    student_data = [studentId]
                    cursor.execute("SELECT Name, Section FROM STUDENTS WHERE ID = ?",(studentId,))
                    temp_data = list(cursor.fetchall()[0])
                    student_data.extend(temp_data)
                    classroom_obj[room].allocate(student_data, seatType)

                roomSeatAvailable[room][seatType] -= to_allocate

                isVisited[(course_data,room)] = True



    generate_seating_pdf(classroom_obj,str(day+'_'+time_slot+'seating_arrangement'),day,time_slot)




elif allotment_type == "Course Wise" :
    print("Course Wise")
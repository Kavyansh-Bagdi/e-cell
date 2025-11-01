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

# time slot
cursor.execute("SELECT DISTINCT Time FROM ExamSchedule")
time_slots = [row[0] for row in cursor.fetchall()]

# day
cursor.execute("SELECT DISTINCT Date FROM ExamSchedule")
days = [row[0] for row in cursor.fetchall()]

# room capacity
cursor.execute("SELECT RoomNo, SeatA FROM Rooms");
classroom_capacity = {};
for row in cursor.fetchall():
    classroom_capacity[row[0]] = row[1]


for day in days:
    for time_slot in time_slots:


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

        
        if len(classrooms) == 0:
            print("[WARNING] : No Classroom is assigned on ",day," & ",time_slot);
            continue

        # creating Rooms object
        print(classrooms)
        classroom_obj = {}
        for roomId in classrooms:
            if roomId.strip() != "":
                classroom_obj[roomId] = Room(roomId,classroom_capacity[roomId])

        # fetching courses for corresponding classrooms

        day_to_course_ids = set()
        room_to_course_ids = {}

        for room in classrooms:
            cursor.execute(
                '''
                SELECT CourseCode, CourseType, Semester, CoordinatorName
                FROM ExamSchedule
                WHERE Date = ? AND Time = ? AND ? IN (Room1, Room2, Room3, Room4)
                ''',
                (day, time_slot, room)
            )
            
            courses = cursor.fetchall()
            course_codes = {course[0] for course in courses}
            
            room_to_course_ids[room] = sorted(course_codes)
            day_to_course_ids.update(course_codes)

        room_to_course_ids = dict(sorted(room_to_course_ids.items()))

        for room in room_to_course_ids.keys():
            if len(room_to_course_ids[room]) == 0:
                print("[WARNING] : No Course Found for this RoomId : ",room," Day : ",day," Time : ",time_slot)
                continue
            
        # fetching all room coresponding to that course 
        course_ids_to_rooms = {};
        for course in day_to_course_ids:
            cursor.execute(
                """
                SELECT Room1,Room2,Room3,Room4 FROM ExamSchedule WHERE Date = ? AND Time = ? AND CourseCode = ?
                """,
                (day,time_slot,course))

            course_ids_to_rooms[course] = []
            for tuple in cursor.fetchall():
                for room in tuple:
                    if(room != None):
                        course_ids_to_rooms[course].append(room)
                course_ids_to_rooms[course] = sorted(course_ids_to_rooms[course])

        course_ids_to_rooms = dict(sorted(course_ids_to_rooms.items()))

        # initializing room seats
        roomSeatAvailable = {}
        for classroom in classrooms:
            if classroom.strip() != "" :
                roomSeatAvailable[classroom] = [classroom_capacity[classroom],classroom_capacity[classroom]]

        visited = {}
        for roomId in classrooms:
            visited[roomId] = {}
            for courseId in room_to_course_ids[roomId]:
                visited[roomId][courseId] = True

        # allocating seats
        for room in classrooms:

            for course in room_to_course_ids[room]:

                courseId = course[0]
                sem = course[2]
                ctype = course[1]
                coord = course[3]

                # fetch studentId
                cursor.execute("""
                    SELECT Students.ID
                    FROM Students
                    JOIN Enrollments ON Students.ID = Enrollments.ID
                    WHERE 
                    Enrollments.CourseCode = ? AND
                    Enrollments.CourseType = ? AND
                    Enrollments.Semester = ? AND
                    Enrollments.CoordinatorName = ?
                    ORDER BY 
                        SUBSTR(Students.ID, 1, 4) DESC,   
                        SUBSTR(Students.ID, -4, 4) ASC;
                """, (courseId,ctype,sem,coord))

                no_students = 0
                all_students = deque([row[0] for row in cursor.fetchall()])

                if ctype == "CORE":

                    cursor.execute("""
                        SELECT Department 
                        FROM CourseDept 
                        WHERE CourseCode = ? 
                        AND CourseType = ? 
                        AND Semester = ? 
                        AND CoordinatorName = ?;
                    """, (courseId, ctype, sem, coord))

                    dept_row = cursor.fetchone()
                    department = dept_row[0] if dept_row else None
                
                    cursor.execute("""
                        SELECT MAX(No_Student)
                        FROM CourseDept
                        WHERE Department = ? AND Semester = ?;
                    """, (department, sem))
                
                    max_row = cursor.fetchone()
                    no_students =  max_row[0] if max_row else 0
                    
                else:

                    no_students = len(all_students)

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


                scoreA = calculateScore(0,course_ids_to_rooms[course])
                scoreB = calculateScore(1,course_ids_to_rooms[course])

                seatType = 0

                if(scoreA < scoreB):
                    seatType = 1

                for roomId in course_ids_to_rooms[course]:
                    if not visited[roomId][course]:
                        continue
                    
                    if not all_students:
                        break

                    available = roomSeatAvailable[roomId][seatType]
                    to_allocate = min(len(all_students), available)

                    for _ in range(to_allocate):
                        studentId = all_students.popleft()
                        student_data = [studentId]
                        cursor.execute("SELECT Name, Section FROM STUDENTS WHERE ID = ?",(studentId,))
                        temp_data = list(cursor.fetchall()[0])
                        student_data.extend(temp_data)
                        classroom_obj[roomId].allocate(student_data, seatType)

                    roomSeatAvailable[roomId][seatType] -= to_allocate

                    visited[roomId][courseId] = False


        generate_seating_pdf(classroom_obj,str(day+'_'+time_slot+'seating_arrangement'),day,time_slot)
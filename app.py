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
        dayToCourseId = set()
        roomIdToCourseId = {}
        for classroom in classrooms:
            cursor.execute('SELECT CourseCode FROM ExamSchedule WHERE Date = ? and Time = ? and ? in (Room1,Room2,Room3,Room4)',(day,time_slot,classroom))
            roomIdToCourseId[classroom] = set()
            for course in cursor.fetchall():
                if(course != None):
                    roomIdToCourseId[classroom].add(course[0])
                    dayToCourseId.add(course[0])
            roomIdToCourseId[classroom] = sorted(roomIdToCourseId[classroom])
        roomIdToCourseId = dict(sorted(roomIdToCourseId.items()))

        # fetching all room coresponding to that course 
        courseToRoomId = {};
        for course in dayToCourseId:
            cursor.execute('SELECT Room1,Room2,Room3,Room4 FROM ExamSchedule WHERE Date = ? AND Time = ? AND CourseCode = ?',(day,time_slot,course))

            courseToRoomId[course] = []
            for tuple in cursor.fetchall():
                for room in tuple:
                    if(room != None):
                        courseToRoomId[course].append(room)
                courseToRoomId[course] = sorted(courseToRoomId[course])

        courseToRoomId = dict(sorted(courseToRoomId.items()))
        # print(day,time_slot,courseToRoomId)

        roomSeatAvailable = {}
        for classroom in classrooms:
            roomSeatAvailable[classroom] = [classroom_capacity[classroom],classroom_capacity[classroom]]

        # allocating seats | main
        for room in classrooms:
            print(roomIdToCourseId[room])  
            for courseId in (roomIdToCourseId[room]):

                cursor = connection.cursor()
                cursor.execute("""
                    SELECT Students.ID FROM Students
                    JOIN Enrollments ON Students.ID = Enrollments.ID
                    WHERE Enrollments.CourseCode = ?
                    ORDER BY Students.ID
                """, (courseId,))

                all_students = deque([row[0] for row in cursor.fetchall()])

                # occupy class fully : 1000
                # partially : -1000
                def calculateScore(courseId, seatType, classes):
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


                scoreA = calculateScore(courseId,0,courseToRoomId[courseId])
                scoreB = calculateScore(courseId,1,courseToRoomId[courseId])

                seatType = 0

                if(scoreA < scoreB):
                    seatType = 1

                for roomId in courseToRoomId[courseId]:
                    # First try current seatType
                    available = roomSeatAvailable[roomId][seatType]
                    to_allocate = min(len(all_students), available)

                    # Allocate to chosen seatType
                    for _ in range(to_allocate):
                        student = all_students.popleft()
                        classroom_obj[roomId].allocate(student, seatType)
                    roomSeatAvailable[roomId][seatType] -= to_allocate

                    # If still students left and other seatType has space, spill over
                    if len(all_students) > 0:
                        otherType = 1 if seatType == 0 else 0
                        available = roomSeatAvailable[roomId][otherType]
                        to_allocate = min(len(all_students), available)
                        for _ in range(to_allocate):
                            student = all_students.popleft()
                            classroom_obj[roomId].allocate(student, otherType)
                        roomSeatAvailable[roomId][otherType] -= to_allocate


                    

        generate_seating_pdf(classroom_obj,str(day+'_'+time_slot+'seating_arrangement'))

        # print(classrooms)

        # print("Classrooms : ",classrooms)

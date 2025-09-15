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
        print("-"*100)
        print("Day : ",day,'Time : ', time_slot)
        # progress_tracker = {code: 0 for code in course_codes}

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

        if len(classrooms) == 0:
            continue

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

        if len(roomIdToCourseId) == 0:
            continue

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
        
        # print(roomSeatAvailable)

        adjMatrix = {}
        for roomId in classrooms:
            adjMatrix[roomId] = {}
            for courseId in roomIdToCourseId[roomId]:
                adjMatrix[roomId][courseId] = True

        # allocating seats | main
        for room in classrooms:
            print("#"*100)
            print('Outer Loop RoomId : ',room)
            for courseId in roomIdToCourseId[room]:
                print('CourseId : ',courseId)
                # fetch studentId
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT Students.ID
                    FROM Students
                    JOIN Enrollments ON Students.ID = Enrollments.ID
                    WHERE Enrollments.CourseCode = ?
                    AND Enrollments.CourseType IN ('CORE','PROGRAM CORE','Major Core','Open Elective','Program Elective','Advance Elective')
                    ORDER BY 
                        SUBSTR(Students.ID, 1, 4) DESC,   
                        SUBSTR(Students.ID, -4, 4) ASC;
                """, (courseId,))


                all_students = deque([row[0] for row in cursor.fetchall()])
                print("Students : ",all_students)

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
                    print('InnerLoop RoomId : ',roomId)
                    if not adjMatrix[roomId][courseId]:
                        print('InnerLoop RoomId Breaked: ',roomId)
                        continue
                    
                    if not all_students:
                        break

                    available = roomSeatAvailable[roomId][seatType]
                    to_allocate = min(len(all_students), available)
                    print("Allocated : ",to_allocate)
                    print("Available : ",roomSeatAvailable[roomId][seatType])

                    for _ in range(to_allocate):
                        studentId = all_students.popleft()
                        student_data = [studentId]
                        cursor.execute("SELECT Name, Section FROM STUDENTS WHERE ID = ?",(studentId,))
                        temp_data = list(cursor.fetchall()[0])
                        student_data.extend(temp_data)
                        classroom_obj[roomId].allocate(student_data, seatType)

                    roomSeatAvailable[roomId][seatType] -= to_allocate

                    adjMatrix[roomId][courseId] = False

                    print('InnerLoop RoomId Completed: ',roomId)

                
                print(roomSeatAvailable)
                for roomId in classrooms:
                    print(roomId,':')
                    for courseId in roomIdToCourseId[roomId]:
                        print(courseId,':',adjMatrix[roomId][courseId],end=", ")
                    print()

        generate_seating_pdf(classroom_obj,str(day+'_'+time_slot+'seating_arrangement'),day,time_slot)

        # print(classrooms)

        # print("Classrooms : ",classrooms)

import sqlite3
from functions.room import Room
import argparse
from functions.pdf_generator import generate_seating_pdf
from functions.seating_arrangement_db_generate import generate_seating_db
from collections import deque
import os
from colorama import Fore, Style, init
init(autoreset=True)


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


parser = argparse.ArgumentParser(description="Seating Arrangement Generator")
parser.add_argument("--debug", action="store_true", help="Enable debug messages")
args = parser.parse_args()

DEBUG = args.debug

def debug_print(*msg):
    if DEBUG:
        print(Fore.CYAN + "[DEBUG]", *msg, Style.RESET_ALL)

def warn_print(*msg):
    print(Fore.YELLOW + "[WARNING]", *msg, Style.RESET_ALL)

def error_print(*msg):
    print(Fore.RED + "[ERROR]", *msg, Style.RESET_ALL)

def info_print(*msg):
    print(Fore.GREEN + "[INFO]", *msg, Style.RESET_ALL)


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
cursor.execute("SELECT RoomNo, SeatA FROM Rooms")
classroom_capacity = {}
for row in cursor.fetchall():
    room_no, seat_a = row
    classroom_capacity[room_no] = seat_a

for day in days:
    for time_slot in time_slots:
        # fetch assigned classrooms for given day and time_slot
        cursor.execute(
            "SELECT Room1, Room2, Room3, Room4 FROM ExamSchedule WHERE Date = ? AND Time = ?",
            (day, time_slot),
        )

        classrooms = set()
        for row in cursor.fetchall():
            for room in row:
                if room is not None and str(room).strip() != "":
                    classrooms.add(room)
        classrooms = sorted(classrooms)

        if not classrooms:
            warn_print("No Classroom is assigned on", day, "&", time_slot)
            continue

        classroom_obj = {}
        for room_id in classrooms:
            cap = classroom_capacity.get(room_id)
            if cap is None:
                print(f"[WARNING] : No capacity found for Room '{room_id}'. Skipping room.")
                continue
            classroom_obj[room_id] = Room(room_id, cap)

        if not classroom_obj:
            warn_print("No valid classrooms with capacity for", day, time_slot)
            continue

        # fetch courses for corresponding classrooms
        day_to_course_ids = set()  # set of tuples (CourseCode, CourseType, Semester, CoordinatorName)
        room_to_course_ids = {}

        for room in classrooms:
            cursor.execute(
                """
                SELECT CourseCode, CourseType, Semester, CoordinatorName
                FROM ExamSchedule
                WHERE Date = ? AND Time = ? AND ? IN (Room1, Room2, Room3, Room4)
                """,
                (day, time_slot, room),
            )
            courses = cursor.fetchall()  # list of 4-tuples
            # store full tuples so downstream code has all attributes
            room_to_course_ids[room] = sorted(courses)
            day_to_course_ids.update(courses)

        room_to_course_ids = dict(sorted(room_to_course_ids.items()))

        # warn about empty rooms (no course)
        for room, course_list in room_to_course_ids.items():
            if not course_list:
                warn_print("No Course Found for this RoomId :", room, " Day :", day, " Time :", time_slot)

        # fetching all rooms corresponding to each course tuple
        course_ids_to_rooms = {}
        for course_tuple in day_to_course_ids:  # each is (courseId, ctype, sem, coord)
            courseId, ctype, sem, coord = course_tuple
            cursor.execute(
                """
                SELECT Room1, Room2, Room3, Room4 FROM ExamSchedule
                WHERE Date = ? AND Time = ? AND CourseCode = ?
                    AND CourseType = ? AND Semester = ? AND CoordinatorName = ?
                """,
                (day, time_slot, courseId, ctype, sem, coord),
            )

            rooms_for_course = []
            for row in cursor.fetchall():
                for r in row:
                    if r is not None and str(r).strip() != "":
                        rooms_for_course.append(r)
            course_ids_to_rooms[course_tuple] = sorted(rooms_for_course)

        course_ids_to_rooms = dict(sorted(course_ids_to_rooms.items()))

        # initializing room seats [SeatA, SeatB] — using same capacity for both if only one is stored
        room_seat_available = {}
        for classroom in classrooms:
            cap = classroom_capacity.get(classroom)
            if cap is None:
                # already warned earlier, skip
                continue
            room_seat_available[classroom] = [cap, cap]

        # visited[roomId][course_tuple] = True indicates not yet allocated for that (room, course) pair
        visited = {}
        for room_id in classrooms:
            visited[room_id] = {}
            for course_tuple in room_to_course_ids.get(room_id, []):
                visited[room_id][course_tuple] = True

        # allocating seats
        for room in classrooms:
            if room not in room_to_course_ids:
                continue

            for course_tuple in room_to_course_ids[room]:
                courseId, ctype, sem, coord = course_tuple

                # fetch student IDs for this course
                cursor.execute(
                    """
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
                    """,
                    (courseId, ctype, sem, coord),
                )

                all_students = deque([row[0] for row in cursor.fetchall()])

                no_students = 0
                if ctype == "CORE":
                    cursor.execute(
                        """
                        SELECT Department 
                        FROM CourseDept 
                        WHERE CourseCode = ? 
                            AND CourseType = ? 
                            AND Semester = ? 
                            AND CoordinatorName = ?;
                        """,
                        (courseId, ctype, sem, coord),
                    )

                    dept_row = cursor.fetchone()
                    department = dept_row[0] if dept_row else None

                    cursor.execute(
                        """
                        SELECT MAX(No_Student)
                        FROM CourseDept
                        WHERE Department = ? AND Semester = ?;
                        """,
                        (department, sem),
                    )

                    max_row = cursor.fetchone()
                    no_students = max_row[0] if max_row and max_row[0] is not None else 0
                else:
                    no_students = len(all_students)

                if no_students == 0:
                    debug_print("No Student Found Course :", courseId)
                    # continue? your logic originally still tries to place zero students; we'll skip allocation
                    continue

                # helper: compute score of filling seat-index (0 or 1) across given rooms
                def calculate_score(seat_index, room_list):
                    class_capacity_list = [room_seat_available.get(r, [0, 0])[seat_index] for r in room_list]
                    needed = len(all_students)
                    score = 0

                    # impossible to fit
                    if needed > sum(class_capacity_list):
                        return float('-inf')

                    remaining = needed
                    for cap in class_capacity_list:
                        if remaining >= cap:
                            score += 1000
                            remaining -= cap
                        elif remaining > 0:
                            vacant = cap - remaining
                            score -= vacant * 100
                            remaining = 0
                        else:
                            # room unused
                            continue

                    return score

                rooms_for_this_course = course_ids_to_rooms.get(course_tuple, [])
                if not rooms_for_this_course:
                    warn_print("No rooms mapped for course", course_tuple, "on", day, time_slot)
                    continue

                scoreA = calculate_score(0, rooms_for_this_course)
                scoreB = calculate_score(1, rooms_for_this_course)
                seat_type = 1 if scoreB > scoreA else 0

                # allocate students across rooms in the order of rooms_for_this_course
                for dest_room in rooms_for_this_course:
                    if not visited.get(dest_room, {}).get(course_tuple, False):
                        continue

                    if not all_students:
                        break

                    available = room_seat_available.get(dest_room, [0, 0])[seat_type]
                    to_allocate = min(len(all_students), available)

                    if to_allocate <= 0:
                        continue

                    for _ in range(to_allocate):
                        studentId = all_students.popleft()
                        student_data = [studentId]
                        cursor.execute("SELECT Name, Section FROM Students WHERE ID = ?", (studentId,))
                        fetched = cursor.fetchone()
                        if fetched:
                            student_data.extend([fetched[0], fetched[1]])
                        else:
                            student_data.extend(["Unknown", "Unknown"])

                        # allocate in Room object (assumes Room.allocate handles seat_type)
                        if dest_room in classroom_obj:
                            classroom_obj[dest_room].allocate(student_data, seat_type)
                        else:
                            print(f"[WARNING] : Destination room {dest_room} not present in classroom_obj")

                    # decrement available seats
                    room_seat_available[dest_room][seat_type] -= to_allocate
                    visited[dest_room][course_tuple] = False

        # generate PDF for this day/time_slot (sanitize filename)
        filename = f"{str(day)}_{str(time_slot)}_seating_arrangement".replace(" ", "_")
        
        generate_seating_db(classroom_obj, day, time_slot)
        generate_seating_pdf(classroom_obj, filename, day, time_slot)

# close DB connection
connection.close()

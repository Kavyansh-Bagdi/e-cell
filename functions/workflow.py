# Schema
# CREATE TABLE Students (
#         ID TEXT PRIMARY KEY,
#         Name TEXT,
#         Degree TEXT,
#         Section TEXT,
#         Semester INTEGER,
#         Department TEXT
#     );

#     CREATE TABLE Rooms (
#         Room TEXT PRIMARY KEY,
#         SeatA TEXT,
#         SeatB TEXT, 
#         Floor TEXT
#     );

#     CREATE TABLE Courses (
#         CourseCode TEXT PRIMARY KEY,
#         CourseTitle TEXT,
#         CourseType TEXT,
#         ElectiveType TEXT,
#         CoordinatorID TEXT,
#         CoordinatorName TEXT,
#         CoordinatorEmailID TEXT,
#         Department TEXT
#     );

#     CREATE TABLE Enrollments (
#         ID TEXT,
#         CourseCode TEXT,
#         PRIMARY KEY (ID, CourseCode),
#         FOREIGN KEY (ID) REFERENCES Students(ID) ON DELETE CASCADE,
#         FOREIGN KEY (CourseCode) REFERENCES Courses(CourseCode) ON DELETE CASCADE
#     );
                         
#     CREATE TABLE ExamSchedule (
#         CourseCode TEXT,
#         DATE TEXT,
#         TIME TEXT,
#         Room1 TEXT,
#         Room2 TEXT,
#         Room3 TEXT,
#         Room4 TEXT,
#         PRIMARY KEY (CourseCode, Room1 ,Room2 ,Room3 ,Room4 , DATE),
#         FOREIGN KEY (CourseCode) REFERENCES Courses(CourseCode) ON DELETE CASCADE,
#         FOREIGN KEY (Room1) REFERENCES Rooms(Room) ON DELETE CASCADE,
#         FOREIGN KEY (Room2) REFERENCES Rooms(Room) ON DELETE CASCADE,
#         FOREIGN KEY (Room3) REFERENCES Rooms(Room) ON DELETE CASCADE,
#         FOREIGN KEY (Room4) REFERENCES Rooms(Room) ON DELETE CASCADE
#     );

# seat type = [seatA,seatB]

# gobal variable for storing index of student branch wise
#     CSE     ECE     AI      META
# 2nd  0        0       0       0
# 3rd  0        0       0       0
# 4th  0        0       0       0
 
# first select a time slot
# fetch all room in asc order
# iterate room in order
    # check wheater room is empty or not 
        # if empty
            # fetch all branch in that room
            # check in gobal dp to check wheather this branch arrangement is done or not
                # move to next branch
            # allocate seat to whole students present in that branch by a given seat type like A or B
        # else move to next room

# class Room:
#     ptrA = 1
#     ptrB = 1
#     capacity = None
#     roomId = None
#     arrangement = None 

#     def __init__(self,roomId : str, capacity : int):
#         self.roomId = roomId
#         self.capacity = capacity
#         self.arrangement = [[None,None] for _ in range(capacity)]

# def allocate_seat(course_id,seat_type)
# this funciton will take paramenter course_id and seat_type for a given time slot then this will allocate seat of seat type seat_type to all student of that course_id.

# def allocate_classroom()
# 1. fetch all course_id that are assigned to this classroom for given time slot
# 2. iterate to each course_id
# 3.    call allocate_seat() function with a appropiate seat_type
# <------ how you will decide seat type for a specific courseid/branch ------>
# <------ how we arrange courseid and branch                           ------>
# <------ should we will arrange by courseid or branch                 ------>

# def allocate_time_slot(time_slot)
# this function first fetch all classroom that are occupied during this type slot and then call allocate_classroom function for each classroom

#----------------------------------------------------------------------------------------------

# import sqlite3
# from collections import defaultdict

# # ---------------------------
# # Global Branch Pointer Table
# # ---------------------------
# # Keeps track of allocation progress per semester & department
# branch_dp = {
#     2: {"CSE": 0, "ECE": 0, "AI": 0, "META": 0},
#     3: {"CSE": 0, "ECE": 0, "AI": 0, "META": 0},
#     4: {"CSE": 0, "ECE": 0, "AI": 0, "META": 0},
# }

# # ---------------------------
# # Room Class
# # ---------------------------
# class Room:
#     def __init__(self, room_id: str, capacity: int):
#         self.room_id = room_id
#         self.capacity = capacity
#         self.arrangement = [[None, None] for _ in range(capacity)]
#         self.ptrA = 0
#         self.ptrB = 0

#     def allocate(self, student_id: str, seat_type: str) -> bool:
#         """Allocate a student into SeatA or SeatB, return False if full."""
#         if seat_type == "A":
#             while self.ptrA < self.capacity and self.arrangement[self.ptrA][0] is not None:
#                 self.ptrA += 1
#             if self.ptrA < self.capacity:
#                 self.arrangement[self.ptrA][0] = student_id
#                 return True
#         else:  # seat_type == "B"
#             while self.ptrB < self.capacity and self.arrangement[self.ptrB][1] is not None:
#                 self.ptrB += 1
#             if self.ptrB < self.capacity:
#                 self.arrangement[self.ptrB][1] = student_id
#                 return True
#         return False


# # ---------------------------
# # Allocation Functions
# # ---------------------------
# def allocate_seat(connection, room: Room, course_id: str, seat_type: str):
#     """Allocate all students of a course into the given room & seat type."""
#     cursor = connection.cursor()
#     cursor.execute("""
#         SELECT Students.ID, Students.Department, Students.Semester
#         FROM Students
#         JOIN Enrollments ON Students.ID = Enrollments.ID
#         WHERE Enrollments.CourseCode = ?
#         ORDER BY Students.Department, Students.ID
#     """, (course_id,))
#     students = cursor.fetchall()

#     for student_id, dept, sem in students:
#         # use branch_dp to ensure we don't reallocate
#         if branch_dp[sem][dept] == 1:
#             continue
#         allocated = room.allocate(student_id, seat_type)
#         if not allocated:
#             print(f"⚠️ Room {room.room_id} is full, cannot place {student_id}")
#         else:
#             branch_dp[sem][dept] = 1  # mark branch as done for this sem


# def allocate_classroom(connection, room: Room, time_slot: tuple):
#     """Allocate all courses scheduled in a classroom for a given time slot."""
#     date, time = time_slot
#     cursor = connection.cursor()
#     cursor.execute("""
#         SELECT CourseCode FROM ExamSchedule
#         WHERE DATE = ? AND TIME = ? 
#         AND (Room1 = ? OR Room2 = ? OR Room3 = ? OR Room4 = ?)
#     """, (date, time, room.room_id, room.room_id, room.room_id, room.room_id))
#     courses = [row[0] for row in cursor.fetchall()]

#     # Simple alternating seat type rule
#     seat_type = "A"
#     for course_id in courses:
#         allocate_seat(connection, room, course_id, seat_type)
#         seat_type = "B" if seat_type == "A" else "A"


# def allocate_time_slot(db_path, date: str, time: str):
#     """Main driver: allocate all rooms in a given time slot."""
#     connection = sqlite3.connect(db_path)
#     cursor = connection.cursor()

#     # Step 1: Fetch all rooms in this slot
#     cursor.execute("""
#         SELECT DISTINCT Room1, Room2, Room3, Room4
#         FROM ExamSchedule
#         WHERE DATE = ? AND TIME = ?
#     """, (date, time))
#     rooms = set()
#     for row in cursor.fetchall():
#         for r in row:
#             if r:
#                 rooms.add(r)

#     if not rooms:
#         print("No rooms scheduled in this slot.")
#         return

#     # Step 2: Build Room objects with capacity
#     room_objs = []
#     for r in sorted(rooms):
#         cursor.execute("SELECT SeatA, SeatB FROM Rooms WHERE Room = ?", (r,))
#         row = cursor.fetchone()
#         if row:
#             seatA, seatB = row
#             capacity = int(seatA) + int(seatB)
#             room_objs.append(Room(r, capacity))

#     # Step 3: Allocate per classroom
#     for room in room_objs:
#         allocate_classroom(connection, room, (date, time))

#     connection.close()
#     return {room.room_id: room.arrangement for room in room_objs}


# # ---------------------------
# # Example Run
# # ---------------------------
# if __name__ == "__main__":
#     allocations = allocate_time_slot("data.db", "2025-09-20", "09:00 AM")
#     for room, arrangement in allocations.items():
#         print(f"\nRoom {room}:")
#         for i, (a, b) in enumerate(arrangement[:10]):  # preview first 10 benches
#             print(f"Bench {i+1}: SeatA={a}, SeatB={b}")

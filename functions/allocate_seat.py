def allocate_seat(connection, room: Room, course_id: str, seat_type: str):
    """Allocate all students of a course into the given room & seat type."""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT Students.ID, Students.Department, Students.Semester
        FROM Students
        JOIN Enrollments ON Students.ID = Enrollments.ID
        WHERE Enrollments.CourseCode = ?
        ORDER BY Students.Department, Students.ID
    """, (course_id,))
    students = cursor.fetchall()

    for student_id, dept, sem in students:
        # use branch_dp to ensure we don't reallocate
        if branch_dp[sem][dept] == 1:
            continue
        allocated = room.allocate(student_id, seat_type)
        if not allocated:
            print(f"⚠️ Room {room.room_id} is full, cannot place {student_id}")
        else:
            branch_dp[sem][dept] = 1  # mark branch as done for this sem
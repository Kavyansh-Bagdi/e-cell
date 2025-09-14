course_allocation_progress = {}
def allocate_course_sequentially(
    connection,
    room: Room,
    course_id: str,
    seat_type: str,
    progress_tracker: dict
):
    
    print(f"--- Starting allocation for Course '{course_id}' in Room '{room.room_id}' ---")

    cursor = connection.cursor()
    cursor.execute("""
        SELECT Students.ID FROM Students
        JOIN Enrollments ON Students.ID = Enrollments.ID
        WHERE Enrollments.CourseCode = ?
        ORDER BY Students.ID
    """, (course_id,))
    all_students_in_course = [row[0] for row in cursor.fetchall()]

    if not all_students_in_course:
        print(f"⚠️ No students found for course '{course_id}'.")
        return

    start_index = progress_tracker.get(course_id, 0)
    print(f"Progress for '{course_id}': {start_index} students already allocated. Starting from student #{start_index + 1}.")

    if start_index >= len(all_students_in_course):
        print(f"ℹ️ All students for course '{course_id}' have already been seated.")
        return

    students_to_seat = all_students_in_course[start_index:]
    
    newly_allocated_count = 0
    for student_id in students_to_seat:
        was_allocated = room.allocate(student_id, seat_type)
        if was_allocated:
            newly_allocated_count += 1
        else:
            print(f"ℹ️ Room '{room.room_id}' is now full for Seat Type '{seat_type}'.")
            break

    new_progress_index = start_index + newly_allocated_count
    progress_tracker[course_id] = new_progress_index

    print(f"✅ Finished. Allocated {newly_allocated_count} new students from '{course_id}'.")
    print(f"   Tracker for '{course_id}' is now at: {new_progress_index}")
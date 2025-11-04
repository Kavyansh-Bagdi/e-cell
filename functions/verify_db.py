import sqlite3
import re

db_path = "data.db"

# ===== Colors =====
ORANGE = "\033[38;5;208m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# ===== Logger functions =====
def warning(message):
    print(f"{ORANGE}[WARNING]{RESET} : {message}")

def info(message):
    print(f"{YELLOW}[INFO]{RESET} : {message}")

def error(message):
    print(f"{RED}[ERROR]{RESET} : {message}")


# ===== Verify Enrolled Students =====
def verify_no_students(cId, ctype, sem, coord):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT ReviewStd FROM Courses 
            WHERE CourseCode = ? AND Semester = ? AND CourseType = ? AND CoordinatorName = ?
        """, (cId, sem, ctype, coord))
        review_student_cnt = cursor.fetchone()
        review_student_cnt = review_student_cnt[0] if review_student_cnt else 0

        cursor.execute("""
            SELECT COUNT(*) FROM Enrollments 
            WHERE CourseCode = ? AND Semester = ? AND CourseType = ? AND CoordinatorName = ?
        """, (cId, sem, ctype, coord))
        student_found = cursor.fetchone()
        student_found = student_found[0] if student_found else 0

        if review_student_cnt < student_found:
            error(f"Student count mismatch! (Expected (MTE PDF): {review_student_cnt}, Found (Enrollment): {student_found})")
            return False
        return True

    except Exception as e:
        error(f"{e}")
        return False
    finally:
        connection.close()


# ===== Verify Classrooms =====
def verify_no_classrooms(cId, ctype, sem, coord):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT Room1, Room2, Room3, Room4 FROM ExamSchedule 
            WHERE CourseCode = ? AND Semester = ? AND CourseType = ? AND CoordinatorName = ?
        """, (cId, sem, ctype, coord))
        result = cursor.fetchone()
        classrooms = [room for room in result if room] if result else []

        if len(classrooms) == 0:
            error(f"No classrooms assigned for course")
            return False
        return True

    except Exception as e:
        error(f"{e}")
        return False
    finally:
        connection.close()


# ===== Verify Course Key =====
def verify_course_key(cId, ctype, sem, coord):
    valid_types = [
        "CORE", "PROGRAM ELECTIVE", "OPEN ELECTIVE", "INSTITUTE CORE", "HONORS"
    ]

    valid = True

    if not re.fullmatch(r"\d{2}[A-Za-z]{3}\d{3}", cId):
        warning(f"Invalid Course ID format '{cId}'. Expected pattern: ddcccddd (e.g., 22CSE101)")
        valid = False

    if ctype.strip().upper() not in [t.upper() for t in valid_types]:
        warning(f"Invalid Course Type '{ctype}'. Must be one of: {', '.join(valid_types)}")
        valid = False

    if not isinstance(sem, int):
        warning(f"Invalid Semester '{sem}'. Must be an integer.")
        valid = False

    if not coord or not coord.strip():
        warning("Coordinator name cannot be empty.")
        valid = False

    return valid


# ===== Verify all Courses =====
def verify():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    error_count = 0 

    try:
        cursor.execute("""
            SELECT CourseCode, CourseType, Semester, CoordinatorName FROM Courses;
        """)
        courses = cursor.fetchall()
        info(f"Fetched {len(courses)} course records successfully.\n")

        for cId, ctype, sem, coord in courses:
            failed = False
            print_buffer = []

            # Capture log messages
            def capture_warning(msg): print_buffer.append((warning, msg))
            def capture_error(msg): print_buffer.append((error, msg))
            def capture_info(msg): print_buffer.append((info, msg))

            globals_backup = {
                "warning": warning,
                "error": error,
                "info": info
            }
            globals().update({
                "warning": capture_warning,
                "error": capture_error,
                "info": capture_info
            })

            # Run all verification checks
            if not verify_course_key(cId, ctype, sem, coord):
                failed = True
            if not verify_no_students(cId, ctype, sem, coord):
                failed = True
            if not verify_no_classrooms(cId, ctype, sem, coord):
                failed = True

            # Restore logging
            globals().update(globals_backup)

            # Print only failed courses
            if failed:
                error_count += 1
                print()
                print(f"Course: {cId} | Type: {ctype} | Semester: {sem} | Coordinator: {coord}")
                for func, msg in print_buffer:
                    func(msg)

        print("-" * 100)
        if error_count > 0:
            error(f"Verification completed with {error_count} issue(s) found.")
            return False
        else:
            info("All courses verified successfully. No issues found.")
            return True

    except Exception as e:
        error(f"{e}")
        return False

    finally:
        connection.close()


# ===== Entry Point =====
if __name__ == '__main__':
    verify()

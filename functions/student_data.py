import sqlite3
import pandas as pd

def create_and_populate_db(
    db_path = "data.db",
    enrollments = "data/enrollments.xlsx",
    mte = "data/mte.xlsx",
    room_capacity = "data/room_capacity.xlsx",
    students = "data/students.xlsx"
):
    students_df = pd.read_excel(students, engine="openpyxl")
    room_capacity_df = pd.read_excel(room_capacity, engine="openpyxl")   
    enrollments_df = pd.read_excel(enrollments, engine="openpyxl")   
    exam_schedule_df = pd.read_excel(mte, engine="openpyxl")

    # Formating Student Table
    required_columns = ["Student Id", "Student Name", "Degree", "Section", "Semester", "Department"]
    students_df = students_df[required_columns]

    students_df = students_df.rename(columns={
        "Student Id": "ID",
        "Student Name": "Name"
    })
    
    students_df["Semester"] = students_df["Semester"].astype(int)

    # Formating Rooms Table
    room_capacity_df = room_capacity_df.rename(columns={
        "Room No": "Room",
        "Seat A": "SeatA",
        "Seat B": "SeatB",
    })

    # Courses
    enrollments_df.columns = enrollments_df.columns.str.strip()

    courses_df = enrollments_df[["Course Code", "Course Title", "Course Type", "Elective Type","Course Coordinator ID", "Course Coordinator name", "Course Coordinator Email ID","Department"]].drop_duplicates(subset=["Course Code"]) 

    courses_df = courses_df.rename(columns={
        "Course Code": "CourseCode",
        "Course Title": "CourseTitle",
        "Course Type": "CourseType",
        "Elective Type": "ElectiveType",
        "Course Coordinator ID": "CoordinatorID",
        "Course Coordinator name": "CoordinatorName",
        "Course Coordinator Email ID": "CoordinatorEmailID",
        "Department": "Department"
    })
    # Exam Schedule
    exam_schedule_df = exam_schedule_df[["Course Code","Exam Date","Exam Time","Room 1","Room 2","Room 3","Room 4"]].rename(columns={
        "Course Code": "CourseCode",
        "Exam Date": "DATE",
        "Exam Time": "Time",
        "Room 1": "Room1",
        "Room 2": "Room2",
        "Room 3": "Room3",
        "Room 4": "Room4"
    })

    exam_schedule_df["DATE"] = pd.to_datetime(exam_schedule_df["DATE"], errors="coerce")

    # exam_schedule_df = exam_schedule_df[
    #     exam_schedule_df["CourseCode"].isin(courses_df["CourseCode"]) &
    #     exam_schedule_df["Room1"].isin(room_capacity_df["Room"]) &
    #     exam_schedule_df["Room2"].isin(room_capacity_df["Room"]) &
    #     exam_schedule_df["Room3"].isin(room_capacity_df["Room"]) &
    #     exam_schedule_df["Room4"].isin(room_capacity_df["Room"])
    # ]

    # Enrollment 
    enrollments_df = enrollments_df[["Student ID","Course Code"]]
    enrollments_table = enrollments_df.rename(columns={
        "Student ID" : "ID",
        "Course Code" : "CourseCode"
    })

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")  

    cursor.executescript("""
        DROP TABLE IF EXISTS Enrollments;
        DROP TABLE IF EXISTS Courses;
        DROP TABLE IF EXISTS Students;
        DROP TABLE IF EXISTS Rooms;
        DROP TABLE IF EXISTS ExamSchedule;
    """)

    cursor.execute("PRAGMA foreign_keys = ON;")  

    cursor.executescript("""
    CREATE TABLE Students (
        ID TEXT PRIMARY KEY,
        Name TEXT,
        Degree TEXT,
        Section TEXT,
        Semester INTEGER,
        Department TEXT
    );

    CREATE TABLE Rooms (
        Room TEXT PRIMARY KEY,
        SeatA TEXT,
        SeatB TEXT, 
        Floor TEXT
    );

    CREATE TABLE Courses (
        CourseCode TEXT PRIMARY KEY,
        CourseTitle TEXT,
        CourseType TEXT,
        ElectiveType TEXT,
        CoordinatorID TEXT,
        CoordinatorName TEXT,
        CoordinatorEmailID TEXT,
        Department TEXT
    );

    CREATE TABLE Enrollments (
        ID TEXT,
        CourseCode TEXT,
        PRIMARY KEY (ID, CourseCode),
        FOREIGN KEY (ID) REFERENCES Students(ID) ON DELETE CASCADE,
        FOREIGN KEY (CourseCode) REFERENCES Courses(CourseCode) ON DELETE CASCADE
    );
                         
    CREATE TABLE ExamSchedule (
        CourseCode TEXT,
        DATE TEXT,
        TIME TEXT,
        Room1 TEXT,
        Room2 TEXT,
        Room3 TEXT,
        Room4 TEXT,
        PRIMARY KEY (CourseCode, Room1 ,Room2 ,Room3 ,Room4 , DATE),
        FOREIGN KEY (CourseCode) REFERENCES Courses(CourseCode) ON DELETE CASCADE,
        FOREIGN KEY (Room1) REFERENCES Rooms(Room) ON DELETE CASCADE,
        FOREIGN KEY (Room2) REFERENCES Rooms(Room) ON DELETE CASCADE,
        FOREIGN KEY (Room3) REFERENCES Rooms(Room) ON DELETE CASCADE,
        FOREIGN KEY (Room4) REFERENCES Rooms(Room) ON DELETE CASCADE
    );
    """)

    students_df.to_sql("Students", connection, if_exists="append", index=False)
    room_capacity_df.to_sql("Rooms", connection, if_exists="replace", index=False)
    courses_df.to_sql("Courses", connection, if_exists="append", index=False)
    enrollments_table.to_sql("Enrollments", connection, if_exists="replace", index=False)
    exam_schedule_df.to_sql("ExamSchedule", connection, if_exists="replace", index=False)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_and_populate_db()

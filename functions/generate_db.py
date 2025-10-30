import sqlite3
import pandas as pd

def create_and_populate_db(
    db_path = "data.db",
    enrollments = "data/enrollments.xlsx",
    mte = "data/mte.xlsx",
    room_capacity = "data/room_capacity.xlsx",
    students = "data/students.xlsx"
):
    # Department Table
    department_df = pd.read_excel(students, engine="openpyxl")
    department_df = (
        department_df[['Department']]
        .rename(columns={'Department': 'Id'})
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Student Table
    students_df = pd.read_excel(students, engine="openpyxl")
    required_columns = ["Student Id", "Student Name", "Degree", "Section", "Semester", "Department","Batch","Specialization","Email"]
    students_df = students_df[required_columns]

    students_df = students_df.rename(columns={
        "Student Id": "Id",
        "Student Name": "Name"
    })
    students_df["Semester"] = students_df["Semester"].astype(int)

    
    # Rooms Table
    room_capacity_df = pd.read_excel(room_capacity, engine="openpyxl")   
    room_capacity_df = room_capacity_df.rename(columns={
        "Room No": "RoomNo",
        "Seat A": "SeatA",
        "Seat B": "SeatB",
        "Floor" : "Floor"
    })
    # Add VLTC- prefix and ensure string type
    room_capacity_df["RoomNo"] = "VLTC-" + room_capacity_df["RoomNo"].astype(str)
    # Courses
    courses_df = pd.read_excel(mte,engine="openpyxl")
    courses_df = courses_df[["Course Sem","Course Code", "Course Title", "Course Coordinator name","Elective Type", "Degree"]].rename(
        columns={
            "Course Sem" : "Semester",
            "Course Code": "CourseCode",
            "Elective Type" : "CourseType",
            "Course Coordinator name" : "CoordinatorName",
            "Course Title": "CourseName"
        }
    )
    # Replace "PROGRAM CORE" with "CORE"
    courses_df["CourseType"] = courses_df["CourseType"].replace("PROGRAM CORE", "CORE")
    courses_df["Degree"] = courses_df["Degree"].replace("M.Tech.", "M.Tech")


    courses_df = courses_df.drop_duplicates(
        subset=["CourseCode", "CourseType", "CoordinatorName", "Semester"]
    ).reset_index(drop=True)


    # Exam Schedule
    exam_schedule_df = pd.read_excel(mte,engine="openpyxl")
    exam_schedule_df = exam_schedule_df[["Course Code","Elective Type","Course Sem","Course Coordinator name","Exam Date","Exam Time","Room 1","Room 2","Room 3","Room 4"]].rename(columns={        
        "Course Code": "CourseCode",
        "Elective Type": "CourseType",
        "Course Sem": "Semester",
        "Course Coordinator name": "CoordinatorName",
        "Exam Date": "DATE",
        "Exam Time": "Time",
        "Room 1": "Room1",
        "Room 2": "Room2",
        "Room 3": "Room3",
        "Room 4": "Room4"
    })
    exam_schedule_df = exam_schedule_df.where(pd.notnull(exam_schedule_df), None)
    # Replace "PROGRAM CORE" with "CORE"
    exam_schedule_df["CourseType"] = exam_schedule_df["CourseType"].replace("PROGRAM CORE", "CORE")


    enrollments_df = pd.read_excel(enrollments,engine="openpyxl")
    enrollments_df = enrollments_df[["Student ID","Course Sem","Course Code","Elective Type","Course Coordinator name"]]
    enrollments_table = enrollments_df.rename(columns={
        "Student ID" : "Id",
        "Course Code" : "CourseCode",
        "Elective Type" : "CourseType",
        "Course Coordinator name": "CoordinatorName",
        "Course Sem" : "Semester"
    })

    # Replace "PROGRAM CORE" with "CORE"
    enrollments_table["CourseType"] = enrollments_table["CourseType"].replace("PROGRAM CORE", "CORE")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")  

    cursor.executescript("""
        DROP TABLE IF EXISTS Enrollments;
        DROP TABLE IF EXISTS ExamSchedule;
        DROP TABLE IF EXISTS Courses;
        DROP TABLE IF EXISTS Students;
        DROP TABLE IF EXISTS Rooms;
        DROP TABLE IF EXISTS Departments;
        DROP TABLE IF EXISTS CourseDept;
    """)

    cursor.execute("PRAGMA foreign_keys = ON;")  

    cursor.executescript("""
    CREATE TABLE Departments (
        Id TEXT PRIMARY KEY
    );
                         
    CREATE TABLE Students (
        Id TEXT PRIMARY KEY,
        Batch INTEGER,
        Degree TEXT,
        Department TEXT,
        Email TEXT,
        Name TEXT,
        Section TEXT,
        Semester INTEGER,
        Specialization TEXT,
        FOREIGN KEY (Department) REFERENCES Departments(Id) ON DELETE CASCADE
    );

    CREATE TABLE Rooms (
        RoomNo TEXT PRIMARY KEY,
        SeatA INTEGER,
        SeatB INTEGER, 
        Floor TEXT
    );
                         
    CREATE TABLE Courses (
        CoordinatorName TEXT,
        CourseCode TEXT,
        CourseName TEXT,
        CourseType TEXT,
        Degree TEXT,
        Semester INTEGER,
        RegularStd INTEGER DEFAULT 0,
        BackLogStd INTEGER DEFAULT 0,
        PRIMARY KEY (CourseCode,CourseType,CoordinatorName,Semester)
    );

    CREATE TABLE ExamSchedule (
        CourseCode TEXT,
        CourseType TEXT,
        CoordinatorName TEXT,
        Semester INTEGER,
        Date TEXT,
        Time TEXT,
        Room1 TEXT,
        Room2 TEXT,
        Room3 TEXT,
        Room4 TEXT,
        PRIMARY KEY (CourseCode,CourseType,CoordinatorName,Semester,Date,Time),
        FOREIGN KEY (CourseCode,CourseType,CoordinatorName,Semester) REFERENCES Courses(CourseCode,CourseType,CoordinatorName,Semester) ON DELETE CASCADE
    );
                         
    CREATE TABLE Enrollments (
        Id TEXT,
        CourseCode TEXT,
        CourseType TEXT,
        CoordinatorName TEXT,
        Semester INTEGER,
        PRIMARY KEY (Id, CourseCode,CourseType,CoordinatorName,Semester),
        FOREIGN KEY (Id) REFERENCES Students(Id) ON DELETE CASCADE,
        FOREIGN KEY (CourseCode,CourseType,CoordinatorName,Semester) REFERENCES Courses(CourseCode,CourseType,CoordinatorName,Semester) ON DELETE CASCADE
    );
                         
    CREATE TABLE CourseDept (
        Semester INTEGER,
        CourseCode TEXT,
        CourseType TEXT,
        CoordinatorName TEXT,
        Department TEXT,
        No_Student INTEGER,
        PRIMARY KEY (CourseCode, CourseType, CoordinatorName, Semester, Department),
        FOREIGN KEY (CourseCode, CourseType, CoordinatorName, Semester) 
            REFERENCES Courses(CourseCode, CourseType, CoordinatorName, Semester) 
            ON DELETE CASCADE,
        FOREIGN KEY (Department) 
            REFERENCES Departments(Id) 
            ON DELETE CASCADE
    );

    """)

    print("Department\n",department_df)
    print("Room Capacity\n",room_capacity_df)
    print("Students\n",students_df)
    print("Courses\n",courses_df)
    print("Exam Schedule\n",exam_schedule_df)
    print("Enrollments\n",enrollments_df)

    # Insert into correct tables
    department_df.to_sql('Departments', connection, if_exists="append", index=False)
    room_capacity_df.to_sql("Rooms", connection, if_exists="replace", index=False)
    students_df.to_sql("Students", connection, if_exists="append", index=False)
    courses_df.to_sql("Courses", connection, if_exists="append", index=False)
    exam_schedule_df.to_sql("ExamSchedule", connection, if_exists="append", index=False)
    enrollments_table.to_sql("Enrollments", connection, if_exists="replace", index=False)

    cursor.execute("""
        update enrollments set coordinatorname = 'DIPTI SHARMA' where (id,coursecode,coursetype) in (select s.id,e.coursecode,e.coursetype from enrollments e join students s on e.id = s.id and e.semester = s.semester where s.department = 'ARTIFICIAL INTELLIGENCE AND DATA ENGINEERING' and e.coursecode = '22HST241');
    """)

    cursor.execute("""
        INSERT INTO CourseDept (Semester, CourseCode, CourseType, CoordinatorName, Department, No_Student)
        SELECT 
            e.Semester, 
            e.CourseCode, 
            e.CourseType, 
            e.CoordinatorName, 
            s.Department,
            COUNT(*) AS No_Student
        FROM Courses c 
        JOIN Enrollments e
            ON  e.CourseCode = c.CourseCode
                AND e.CourseType = c.CourseType
                AND e.CoordinatorName = c.CoordinatorName
                AND e.Semester = c.Semester
        JOIN Students s 
            ON e.Id = s.Id
        JOIN Departments d
            ON s.Department = d.Id
        WHERE e.CourseType IN ('PROGRAM CORE', 'CORE')
        GROUP BY 
            e.CourseCode, 
            e.Semester, 
            e.CourseType, 
            s.Department,
            e.CoordinatorName
        ORDER BY e.Semester;
    """)


    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_and_populate_db()

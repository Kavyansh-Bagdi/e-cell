import sqlite3

def schema_generator():
    connection = sqlite3.connect("seating_arrangement.db")
    cursor = connection.cursor()

    cursor.execute("DELETE FROM arrangement")
    
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS arrangement (
            Date TEXT,
            time_slot TEXT,
            Room TEXT,
            SeatNoA TEXT,
            StudentIdA TEXT,
            NameA TEXT,
            BatchA TEXT,
            SeatNoB TEXT,
            StudentIdB TEXT,
            NameB TEXT,
            BatchB TEXT
        )
        """
    )

    connection.commit()
    connection.close()

def generate_seating_db(classrooms: dict, day: str, time_slot: str):
    """
    Stores seating data for multiple Room objects in the SQLite database without modifying seat numbers.
    """
    connection = sqlite3.connect("seating_arrangement.db")
    cursor = connection.cursor()

    for room_id, room in classrooms.items():
        for i, (seatA, seatB) in enumerate(room.arrangement, start=1):
            # --- Seat A ---
            if seatA:
                studentIdA, nameA, batchA = seatA
                seatNoA = str(i)+"A"
            else:
                studentIdA = nameA = batchA = seatNoA = None

            # --- Seat B ---
            if seatB:
                studentIdB, nameB, batchB = seatB
                seatNoB = str(i)+"B"
            else:
                studentIdB = nameB = batchB = seatNoB = None

            # Insert record
            cursor.execute("""
                INSERT INTO arrangement (
                    Date, time_slot, Room,
                    SeatNoA, StudentIdA, NameA, BatchA,
                    SeatNoB, StudentIdB, NameB, BatchB
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                day, time_slot, room_id,
                seatNoA, studentIdA, nameA, batchA,
                seatNoB, studentIdB, nameB, batchB
            ))

    connection.commit()
    connection.close()

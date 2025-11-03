import sqlite3

def generate_seating_db(classrooms: dict, day: str, time_slot: str):
    """
    Stores seating data for multiple Room objects in the SQLite database without modifying seat numbers.
    """
    connection = sqlite3.connect("data.db")
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
                INSERT INTO Arrangement (
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

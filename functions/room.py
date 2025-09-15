class Room:
    updated = 0
    ptrA = 0
    ptrB = 0
    capacity = None
    roomId = None
    arrangement = None

    def __init__(self,roomId : str, capacity : int):
        self.roomId = roomId
        self.capacity = capacity
        self.arrangement = [[None,None] for _ in range(capacity)]

    def allocate(self, student, seat_type: str) -> bool:
        if seat_type == 0:
            if(self.capacity == self.ptrA):
                return False
            while self.ptrA < self.capacity and self.arrangement[self.ptrA][0] is not None:
                self.ptrA += 1
            if self.ptrA < self.capacity:
                self.arrangement[self.ptrA][0] = student
                return True
        else:
            if(self.capacity == self.ptrB):
                return False
            while self.ptrB < self.capacity and self.arrangement[self.ptrB][1] is not None:
                self.ptrB += 1
            if self.ptrB < self.capacity:
                self.arrangement[self.ptrB][1] = student
                return True
        return False

    def left(self,seat_type):
        if(seat_type == 0):
            return self.capacity - self.ptrA 
        else:
            return self.capacity - self.ptrB
        
    def get_ptrA(self):
        return self.ptrA
    def get_ptrB(self):
        return self.ptrB
    
    def get_updated(self):
        return self.updated
    
    def set_updated(self):
        self.updated+=1;

    def print_details(self):
        print(f"\nRoom ID: {self.roomId}")
        print(f"Capacity: {self.capacity}")
        print(f"Pointer A (next SeatA): {self.ptrA}")
        print(f"Pointer B (next SeatB): {self.ptrB}")
        print(f"Updated count: {self.updated}")
        print("Arrangement:")
        for i, (seatA, seatB) in enumerate(self.arrangement, start=1):
            print(f"  Row {i:02d}: SeatA = {seatA}, SeatB = {seatB}")
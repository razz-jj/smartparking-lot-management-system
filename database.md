BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_FILE = os.path.join(DATA_DIR, "parking.db")


def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS parked_vehicles (
            slot INTEGER PRIMARY KEY,
            vehicle_no TEXT UNIQUE,
            vehicle_type TEXT,
            entry_time TEXT,
            vip INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_no TEXT,
            vehicle_type TEXT,
            entry_time TEXT,
            exit_time TEXT,
            duration_hours INTEGER,
            bill INTEGER,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()


def db_connect():
    return sqlite3.connect(DB_FILE, check_same_thread=False)



# -----------------------------
# PARKING LOGIC
# -----------------------------
def get_next_free_slot(slots, is_vip=False):
    if is_vip:
        for s in sorted(VIP_SLOTS):
            if slots[s] is None:
                return s
        return None

    for s in range(1, TOTAL_SLOTS + 1):
        if s not in VIP_SLOTS and slots[s] is None:
            return s

    for s in sorted(VIP_SLOTS):
        if slots[s] is None:
            return s

    return None


def calculate_bill(vehicle_type, entry_time, exit_time):
    duration_seconds = (exit_time - entry_time).total_seconds()
    duration_hours = math.ceil(duration_seconds / 3600)

    if duration_hours <= 2:
        return FIRST_2_HOURS_COST[vehicle_type], duration_hours

    extra_hours = duration_hours - 2
    bill = FIRST_2_HOURS_COST[vehicle_type] + extra_hours * VEHICLE_PRICING[vehicle_type]
    return bill, duration_hours

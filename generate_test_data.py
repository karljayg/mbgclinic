import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "clinic_data.db"

def generate_test_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Clear existing data
    cur.execute("DELETE FROM Followups")
    cur.execute("DELETE FROM Visits")
    cur.execute("DELETE FROM Patients")
    
    # Generate test patients
    test_patients = [
        ("12345", "John", "Doe", "25", "Spanish"),
        ("67890", "Jane", "Smith", "30", "None"),
        ("24680", "Bob", "Johnson", "45", "French"),
        ("13579", "Sarah", "Williams", "28", "Arabic"),
        ("86420", "Michael", "Brown", "35", "None"),
        ("97531", "Emily", "Davis", "22", "Spanish"),
        ("12346", "David", "Wilson", "40", "None"),
        ("67891", "Lisa", "Taylor", "33", "French"),
        ("24681", "James", "Anderson", "50", "None"),
        ("13580", "Jennifer", "Thomas", "27", "Spanish")
    ]
    
    cur.executemany("""
        INSERT INTO Patients (mrn, first_name, last_name, age, translator)
        VALUES (?, ?, ?, ?, ?)
    """, test_patients)
    
    # Generate test visits (3-5 visits per patient over the last 2 years)
    test_visits = []
    physicians = ["Dr. Smith", "Dr. Jones", "Dr. Brown", "Dr. White", "Dr. Green"]
    cx_results = ["Positive", "Negative"]
    ogtt_results = ["Normal", "Abnormal", "Borderline"]
    
    for mrn, _, _, _, _ in test_patients:
        num_visits = random.randint(3, 5)
        base_date = datetime.now() - timedelta(days=730)  # 2 years ago
        
        for _ in range(num_visits):
            visit_date = base_date + timedelta(days=random.randint(0, 730))
            physician = random.choice(physicians)
            last_cx = random.choice(cx_results)
            due_notes = f"Follow up in {random.randint(1, 12)} months"
            ogtt = random.choice(ogtt_results)
            
            test_visits.append((
                mrn,
                visit_date.strftime("%Y-%m-%d"),
                physician,
                last_cx,
                due_notes,
                ogtt
            ))
    
    cur.executemany("""
        INSERT INTO Visits (mrn, visit_date, physician, last_cx, due_notes, ogtt)
        VALUES (?, ?, ?, ?, ?, ?)
    """, test_visits)
    
    # Get visit IDs and add followups
    cur.execute("SELECT visit_id FROM Visits")
    visit_ids = [row[0] for row in cur.fetchall()]
    
    test_followups = []
    modulators = ["None", "Kalydeco", "Trikafta", "Symdeko", "Orkambi"]
    pft_results = ["Normal", "Abnormal", "Mild", "Moderate", "Severe"]
    
    for visit_id in visit_ids:
        test_followups.append((
            visit_id,
            random.choice(["Yes", "No"]),
            random.choice(modulators),
            random.choice(pft_results),
            random.choice(["Y", "N", "Pending"])
        ))
    
    cur.executemany("""
        INSERT INTO Followups (visit_id, opth, modulator, pft, registry)
        VALUES (?, ?, ?, ?, ?)
    """, test_followups)
    
    conn.commit()
    conn.close()
    print("Test data generated successfully!")

if __name__ == "__main__":
    generate_test_data() 
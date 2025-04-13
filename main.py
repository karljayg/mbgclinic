import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from datetime import datetime, timedelta
import pandas as pd
from tkcalendar import DateEntry
import random

DB_PATH = "clinic_data.db"

# Modern theme colors
BG_COLOR = "white"         # Pure white background
ACCENT_COLOR = "#1a237e"   # Deep blue
TEXT_COLOR = "black"       # Pure black text
BUTTON_COLOR = "#2196f3"   # Brighter blue for better visibility
BUTTON_HOVER = "#1976d2"   # Darker blue for hover
BUTTON_TEXT = "white"      # White text for buttons
TREE_HEADER_BG = "#1976d2" # Bright blue headers
TREE_HEADER_FG = "white"   # White header text
TREE_BG = "white"         # White tree background
TREE_FG = "black"         # Black tree text
TREE_SELECTED = "#bbdefb"  # Light blue selection

def create_styled_button(parent, text, command):
    btn = tk.Button(parent, text=text, command=command, 
                   bg=BUTTON_COLOR, fg=BUTTON_TEXT, 
                   font=("Arial", 11, "bold"),
                   padx=12, pady=6,
                   relief="raised",
                   bd=2,                      # Thicker border
                   highlightthickness=0)      # Remove highlight for macOS
    btn.bind("<Enter>", lambda e: btn.config(bg=BUTTON_HOVER))
    btn.bind("<Leave>", lambda e: btn.config(bg=BUTTON_COLOR))
    return btn

def create_styled_label(parent, text):
    return tk.Label(parent, text=text, bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 11))

def create_styled_entry(parent):
    return tk.Entry(parent, font=("Arial", 11), relief="solid", bg="white", bd=1)

def get_patients():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT mrn, first_name, last_name, age, translator FROM Patients")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_visits_for_patient(mrn):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT v.visit_date, v.physician, v.last_cx, v.due_notes, v.ogtt,
               f.opth, f.modulator, f.pft, f.registry
        FROM Visits v
        LEFT JOIN Followups f ON v.visit_id = f.visit_id
        WHERE v.mrn = ?
        ORDER BY v.visit_date DESC
    """, (mrn,))
    rows = cur.fetchall()
    conn.close()
    return rows

def open_visit_history(mrn, patient_name):
    win = tk.Toplevel()
    win.title(f"Visit History - {patient_name}")
    win.configure(bg=BG_COLOR)
    win.geometry("1200x600")

    # Create main frame
    main_frame = tk.Frame(win, bg=BG_COLOR)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Create tree frame
    tree_frame = tk.Frame(main_frame, bg=BG_COLOR)
    tree_frame.pack(fill=tk.BOTH, expand=True)

    # Create Treeview
    cols = ("Visit Date", "Physician", "Last CX", "Due Notes", "OGTT", 
            "Opth", "Modulator", "PFT", "Registry")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Custom.Treeview")
    
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    # Add scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_visits():
        for item in tree.get_children():
            tree.delete(item)
            
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT v.visit_date, v.physician, v.last_cx, v.due_notes, v.ogtt,
                   f.opth, f.modulator, f.pft, f.registry
            FROM Visits v
            LEFT JOIN Followups f ON v.visit_id = f.visit_id
            WHERE v.mrn = ?
            ORDER BY v.visit_date DESC
        """, (mrn,))
        
        for row in cur.fetchall():
            tree.insert("", tk.END, values=row)
            
        conn.close()

    def add_visit():
        def submit():
            visit_date = date_entry.get().strip()
            physician = physician_entry.get().strip()
            last_cx = last_cx_entry.get().strip()
            due_notes = due_notes_entry.get().strip()
            ogtt = ogtt_entry.get().strip()
            opth = opth_entry.get().strip()
            modulator = modulator_entry.get().strip()
            pft = pft_entry.get().strip()
            registry = registry_entry.get().strip()

            if not all([visit_date, physician]):
                messagebox.showerror("Error", "Visit Date and Physician are required")
                return

            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            try:
                # Insert visit
                cur.execute("""
                    INSERT INTO Visits (mrn, visit_date, physician, last_cx, due_notes, ogtt)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (mrn, visit_date, physician, last_cx, due_notes, ogtt))
                
                visit_id = cur.lastrowid
                
                # Insert followup
                cur.execute("""
                    INSERT INTO Followups (visit_id, opth, modulator, pft, registry)
                    VALUES (?, ?, ?, ?, ?)
                """, (visit_id, opth, modulator, pft, registry))
                
                conn.commit()
                add_win.destroy()
                refresh_visits()
                
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                conn.close()

        add_win = tk.Toplevel(win)
        add_win.title("Add Visit")
        add_win.configure(bg=BG_COLOR)

        # Create form frame
        form_frame = tk.Frame(add_win, bg=BG_COLOR)
        form_frame.pack(padx=20, pady=20)

        # Visit fields
        fields = [
            ("Visit Date (YYYY-MM-DD)", "date_entry"),
            ("Physician", "physician_entry"),
            ("Last CX", "last_cx_entry"),
            ("Due Notes", "due_notes_entry"),
            ("OGTT", "ogtt_entry"),
            ("Opth", "opth_entry"),
            ("Modulator", "modulator_entry"),
            ("PFT", "pft_entry"),
            ("Registry", "registry_entry")
        ]

        entries = {}
        for i, (label, varname) in enumerate(fields):
            create_styled_label(form_frame, label).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            entries[varname] = create_styled_entry(form_frame)
            entries[varname].grid(row=i, column=1, padx=10, pady=5)

        # Button frame
        btn_frame = tk.Frame(add_win, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        create_styled_button(btn_frame, "Save", submit).grid(row=0, column=0, padx=5)
        create_styled_button(btn_frame, "Cancel", add_win.destroy).grid(row=0, column=1, padx=5)

    # Button frame
    button_frame = tk.Frame(main_frame, bg=BG_COLOR)
    button_frame.pack(fill=tk.X, pady=(10, 0))

    create_styled_button(button_frame, "Add Visit", add_visit).pack(side=tk.LEFT, padx=5)
    create_styled_button(button_frame, "Close", win.destroy).pack(side=tk.LEFT, padx=5)

    refresh_visits()

def add_or_edit_patient(existing=None):
    def submit():
        mrn = mrn_entry.get().strip()
        first_name = first_name_entry.get().strip()
        last_name = last_name_entry.get().strip()
        age = age_entry.get().strip()
        translator = translator_entry.get().strip()

        if not all([mrn, first_name, last_name]):
            messagebox.showerror("Validation Error", "MRN, First Name, and Last Name are required.")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        try:
            if existing:
                cur.execute("""
                    UPDATE Patients 
                    SET first_name=?, last_name=?, age=?, translator=?
                    WHERE mrn=?
                """, (first_name, last_name, age, translator, existing["mrn"]))
            else:
                cur.execute("""
                    INSERT INTO Patients (mrn, first_name, last_name, age, translator)
                    VALUES (?, ?, ?, ?, ?)
                """, (mrn, first_name, last_name, age, translator))
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "MRN must be unique.")
        finally:
            conn.close()
            show_patients()
            win.destroy()

    win = tk.Toplevel()
    win.title("Edit Patient" if existing else "Add New Patient")
    win.configure(bg=BG_COLOR)

    # Form frame
    form_frame = tk.Frame(win, bg=BG_COLOR)
    form_frame.pack(padx=20, pady=20)

    fields = [
        ("MRN", "mrn_entry"),
        ("First Name", "first_name_entry"),
        ("Last Name", "last_name_entry"),
        ("Age", "age_entry"),
        ("Translator", "translator_entry")
    ]

    entries = {}
    for i, (label, varname) in enumerate(fields):
        create_styled_label(form_frame, label).grid(row=i, column=0, padx=10, pady=5, sticky="e")
        entries[varname] = create_styled_entry(form_frame)
        entries[varname].grid(row=i, column=1, padx=10, pady=5)

    if existing:
        entries["mrn_entry"].insert(0, existing["mrn"])
        entries["mrn_entry"].config(state="disabled")
        entries["first_name_entry"].insert(0, existing["first_name"])
        entries["last_name_entry"].insert(0, existing["last_name"])
        entries["age_entry"].insert(0, existing["age"])
        entries["translator_entry"].insert(0, existing["translator"])

    # Button frame
    btn_frame = tk.Frame(win, bg=BG_COLOR)
    btn_frame.pack(pady=10)

    create_styled_button(btn_frame, "Save", submit).grid(row=0, column=0, padx=5)
    create_styled_button(btn_frame, "Cancel", win.destroy).grid(row=0, column=1, padx=5)

    globals().update(entries)

def get_selected_patient():
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Select Patient", "Please select a patient.")
        return None
    item = tree.item(selected[0])
    values = item["values"]
    return {
        "mrn": values[0],
        "first_name": values[1],
        "last_name": values[2],
        "age": values[3],
        "translator": values[4]
    }

def open_selected_patient_history():
    patient = get_selected_patient()
    if patient:
        full_name = f"{patient['first_name']} {patient['last_name']}"
        open_visit_history(patient['mrn'], full_name)
    else:
        messagebox.showerror("Error", "Please select a patient first")

def on_edit_patient():
    patient = get_selected_patient()
    if patient:
        add_or_edit_patient(existing=patient)

def on_delete_patient():
    patient = get_selected_patient()
    if not patient:
        return
    confirm = messagebox.askyesno("Delete Patient", f"Are you sure you want to delete {patient['first_name']} {patient['last_name']}?")
    if not confirm:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM Patients WHERE mrn=?", (patient["mrn"],))
        conn.commit()
        conn.close()
        show_patients()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Cannot delete patient with visit history.")

def export_patients():
    filename = filedialog.asksaveasfilename(defaultextension=".csv", 
                                          filetypes=[("CSV files", "*.csv")])
    if not filename:
        return
    
    patients = get_patients()
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["MRN", "First Name", "Last Name", "Age", "Translator"])
        writer.writerows(patients)
    messagebox.showinfo("Success", "Patients exported successfully!")

def import_patients():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not filename:
        return
    
    try:
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            for row in reader:
                cur.execute("""
                    INSERT OR REPLACE INTO Patients (mrn, first_name, last_name, age, translator)
                    VALUES (?, ?, ?, ?, ?)
                """, row)
            conn.commit()
            conn.close()
        show_patients()
        messagebox.showinfo("Success", "Patients imported successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import: {str(e)}")

def generate_report():
    def generate():
        start_date = start_cal.get_date()
        end_date = end_cal.get_date()
        
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT p.first_name, p.last_name, p.mrn, v.visit_date, v.physician, 
                   f.opth, f.modulator, f.pft, f.registry
            FROM Patients p
            JOIN Visits v ON p.mrn = v.mrn
            LEFT JOIN Followups f ON v.visit_id = f.visit_id
            WHERE v.visit_date BETWEEN ? AND ?
            ORDER BY v.visit_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                              filetypes=[("Excel files", "*.xlsx")])
        if filename:
            df.to_excel(filename, index=False)
            messagebox.showinfo("Success", "Report generated successfully!")
    
    report_win = tk.Toplevel()
    report_win.title("Generate Report")
    report_win.configure(bg=BG_COLOR)
    
    create_styled_label(report_win, "Start Date:").grid(row=0, column=0, padx=10, pady=5)
    start_cal = DateEntry(report_win, width=12, background='darkblue',
                         foreground='white', borderwidth=2)
    start_cal.grid(row=0, column=1, padx=10, pady=5)
    
    create_styled_label(report_win, "End Date:").grid(row=1, column=0, padx=10, pady=5)
    end_cal = DateEntry(report_win, width=12, background='darkblue',
                       foreground='white', borderwidth=2)
    end_cal.grid(row=1, column=1, padx=10, pady=5)
    
    create_styled_button(report_win, "Generate", generate).grid(row=2, column=0, columnspan=2, pady=10)

def search_patients():
    search_term = search_var.get().lower()
    for item in tree.get_children():
        values = tree.item(item)["values"]
        if any(search_term in str(v).lower() for v in values):
            tree.selection_set(item)
            tree.see(item)
        else:
            tree.selection_remove(item)

def show_patients():
    for row in tree.get_children():
        tree.delete(row)
    for patient in get_patients():
        tree.insert("", tk.END, values=patient)

def check_and_generate_test_data():
    pass  # This function is kept for compatibility but does nothing

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create tables only if they don't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Patients (
            mrn TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            age TEXT NOT NULL,
            translator TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Visits (
            visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mrn TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            physician TEXT NOT NULL,
            last_cx TEXT,
            due_notes TEXT,
            ogtt TEXT,
            FOREIGN KEY (mrn) REFERENCES Patients(mrn)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Followups (
            followup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER NOT NULL,
            opth TEXT,
            modulator TEXT,
            pft TEXT,
            registry TEXT,
            FOREIGN KEY (visit_id) REFERENCES Visits(visit_id)
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize database and UI
init_database()

# Main UI
root = tk.Tk()
root.title("MBG Clinic - Patient Manager")
root.geometry("1000x600")
root.configure(bg=BG_COLOR)

# Search frame
search_frame = tk.Frame(root, bg=BG_COLOR)
search_frame.pack(fill=tk.X, padx=10, pady=5)

search_var = tk.StringVar()
search_var.trace("w", lambda *args: search_patients())

create_styled_label(search_frame, "Search:").pack(side=tk.LEFT, padx=5)
search_entry = create_styled_entry(search_frame)
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
search_entry.configure(textvariable=search_var, width=40)

# Main treeview frame
tree_frame = tk.Frame(root, bg=BG_COLOR)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

cols = ("MRN", "First Name", "Last Name", "Age", "Translator")
tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Custom.Treeview")
for col in cols:
    tree.heading(col, text=col)
    tree.column(col, width=150)

# Add scrollbar
scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Button frame
btn_frame = tk.Frame(root, bg=BG_COLOR)
btn_frame.pack(pady=10, fill=tk.X)  # Make frame fill width

# Create two rows of buttons for better layout
row1_buttons = [
    ("Refresh", lambda: show_patients()),
    ("Add Patient", lambda: add_or_edit_patient()),
    ("Edit Patient", on_edit_patient),
    ("Delete Patient", on_delete_patient),
    ("View Visits", open_selected_patient_history)
]

row2_buttons = [
    ("Import", import_patients),
    ("Export", export_patients),
    ("Reports", generate_report)
]

# Add first row of buttons
for i, (text, cmd) in enumerate(row1_buttons):
    btn = create_styled_button(btn_frame, text, cmd)
    btn.grid(row=0, column=i, padx=5, pady=2)
    btn.configure(width=12)

# Add second row of buttons
for i, (text, cmd) in enumerate(row2_buttons):
    btn = create_styled_button(btn_frame, text, cmd)
    btn.grid(row=1, column=i, padx=5, pady=2)
    btn.configure(width=12)

# Configure styles
style = ttk.Style()
style.theme_use('default')  # Reset to default theme first
style.configure("Custom.Treeview", 
                background=TREE_BG,
                foreground=TREE_FG,
                fieldbackground=TREE_BG,
                font=("Arial", 10))
style.configure("Custom.Treeview.Heading",
                background=TREE_HEADER_BG,
                foreground=TREE_HEADER_FG,
                font=("Arial", 10, "bold"))
style.map('Custom.Treeview',
          background=[('selected', TREE_SELECTED)],
          foreground=[('selected', 'black')])

# Show initial data
show_patients()

root.mainloop()

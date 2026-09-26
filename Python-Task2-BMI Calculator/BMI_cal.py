"""
BMI Calculator - Advanced Tier
GUI application (tkinter) with:
  - Weight/height input + Calculate button
  - Colour-coded result feedback
  - Multi-user support with named records
  - SQLite persistence
  - Matplotlib line chart of BMI trend over time
  - Error handling for DB read/write failures
"""

import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_FILE = "bmi_records.db"

CATEGORY_COLORS = {
    "Underweight": "#3498db",  # blue
    "Normal": "#2ecc71",       # green
    "Overweight": "#f39c12",   # orange
    "Obese": "#e74c3c",        # red
}


# --------------------------------------------------------------------------
# Database layer
# --------------------------------------------------------------------------
class BMIDatabase:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_file)

    def _init_db(self):
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_name TEXT NOT NULL,
                        weight_kg REAL NOT NULL,
                        height_m REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not initialise database:\n{e}")
            raise

    def add_record(self, user_name, weight, height, bmi, category):
        try:
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO records
                       (user_name, weight_kg, height_m, bmi, category, recorded_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_name, weight, height, bmi, category,
                     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                )
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not save record:\n{e}")
            return False

    def get_users(self):
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT DISTINCT user_name FROM records ORDER BY user_name"
                ).fetchall()
            return [r[0] for r in rows]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load users:\n{e}")
            return []

    def get_history(self, user_name):
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT bmi, recorded_at FROM records
                       WHERE user_name = ? ORDER BY recorded_at""",
                    (user_name,),
                ).fetchall()
            return rows
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load history:\n{e}")
            return []


# --------------------------------------------------------------------------
# BMI logic (shared with beginner tier)
# --------------------------------------------------------------------------
def calculate_bmi(weight_kg, height_m):
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


# --------------------------------------------------------------------------
# GUI Application
# --------------------------------------------------------------------------
class BMIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator")
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(bg="#f5f6fa")

        self.db = BMIDatabase()

        self._build_widgets()
        self._refresh_user_dropdown()

    # ---------------- UI construction ----------------
    def _build_widgets(self):
        title = tk.Label(self, text="BMI Calculator", font=("Segoe UI", 18, "bold"),
                          bg="#f5f6fa")
        title.pack(pady=(15, 10))

        form = tk.Frame(self, bg="#f5f6fa")
        form.pack(pady=5)

        # Name
        tk.Label(form, text="Name:", bg="#f5f6fa", anchor="w", width=10)\
            .grid(row=0, column=0, sticky="w", pady=6)
        self.name_var = tk.StringVar()
        tk.Entry(form, textvariable=self.name_var, width=22).grid(row=0, column=1, pady=6)

        # Weight
        tk.Label(form, text="Weight (kg):", bg="#f5f6fa", anchor="w", width=10)\
            .grid(row=1, column=0, sticky="w", pady=6)
        self.weight_var = tk.StringVar()
        tk.Entry(form, textvariable=self.weight_var, width=22).grid(row=1, column=1, pady=6)

        # Height
        tk.Label(form, text="Height (m):", bg="#f5f6fa", anchor="w", width=10)\
            .grid(row=2, column=0, sticky="w", pady=6)
        self.height_var = tk.StringVar()
        tk.Entry(form, textvariable=self.height_var, width=22).grid(row=2, column=1, pady=6)

        calc_btn = tk.Button(self, text="Calculate", command=self.on_calculate,
                              bg="#4a69bd", fg="white", font=("Segoe UI", 11, "bold"),
                              width=18, cursor="hand2")
        calc_btn.pack(pady=15)

        # Result display
        self.result_frame = tk.Frame(self, bg="#dfe4ea", width=380, height=80)
        self.result_frame.pack(pady=5)
        self.result_frame.pack_propagate(False)
        self.result_label = tk.Label(self.result_frame, text="Enter details and calculate",
                                      bg="#dfe4ea", font=("Segoe UI", 12, "bold"))
        self.result_label.pack(expand=True)

        # User history / graph section
        hist_frame = tk.Frame(self, bg="#f5f6fa")
        hist_frame.pack(pady=15)

        tk.Label(hist_frame, text="View trend for:", bg="#f5f6fa")\
            .grid(row=0, column=0, padx=5)
        self.user_dropdown = ttk.Combobox(hist_frame, state="readonly", width=15)
        self.user_dropdown.grid(row=0, column=1, padx=5)

        graph_btn = tk.Button(hist_frame, text="Show Graph", command=self.on_show_graph,
                               bg="#6a89cc", fg="white", cursor="hand2")
        graph_btn.grid(row=0, column=2, padx=5)

    # ---------------- Actions ----------------
    def on_calculate(self):
        name = self.name_var.get().strip()
        weight_raw = self.weight_var.get().strip()
        height_raw = self.height_var.get().strip()

        if not name:
            messagebox.showwarning("Missing Name", "Please enter a name to save the record.")
            return

        try:
            weight = float(weight_raw)
            height = float(height_raw)
        except ValueError:
            messagebox.showerror("Invalid Input", "Weight and height must be numeric.")
            return

        if weight <= 0 or height <= 0:
            messagebox.showerror("Invalid Input", "Weight and height must be positive numbers.")
            return

        bmi = calculate_bmi(weight, height)
        category = classify_bmi(bmi)
        color = CATEGORY_COLORS[category]

        self.result_frame.configure(bg=color)
        self.result_label.configure(
            bg=color, fg="white",
            text=f"BMI: {bmi:.2f}\nCategory: {category}"
        )

        saved = self.db.add_record(name, weight, height, bmi, category)
        if saved:
            self._refresh_user_dropdown(select=name)

    def on_show_graph(self):
        user = self.user_dropdown.get()
        if not user:
            messagebox.showinfo("No User Selected", "Please select a user to view their trend.")
            return

        history = self.db.get_history(user)
        if len(history) < 1:
            messagebox.showinfo("No Data", f"No BMI records found for {user}.")
            return

        bmis = [row[0] for row in history]
        dates = [row[1] for row in history]

        win = tk.Toplevel(self)
        win.title(f"BMI Trend — {user}")
        win.geometry("560x420")

        fig, ax = plt.subplots(figsize=(5.5, 4))
        ax.plot(range(len(bmis)), bmis, marker="o", color="#4a69bd", linewidth=2)
        ax.set_title(f"BMI Trend for {user}")
        ax.set_xlabel("Record #")
        ax.set_ylabel("BMI")
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels([d.split(" ")[0] for d in dates], rotation=45, ha="right", fontsize=7)
        ax.axhspan(18.5, 25, color="#2ecc71", alpha=0.1)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _refresh_user_dropdown(self, select=None):
        users = self.db.get_users()
        self.user_dropdown["values"] = users
        if select and select in users:
            self.user_dropdown.set(select)
        elif users:
            self.user_dropdown.set(users[0])


if __name__ == "__main__":
    app = BMIApp()
    app.mainloop()


#BMI Calculator 
<img width="1207" height="585" alt="image" src="https://github.com/user-attachments/assets/c3bf0086-2e53-4f6f-be9b-ad2c03c80ea4" />

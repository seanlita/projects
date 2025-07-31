import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv
import mysql.connector
from datetime import date, datetime, timedelta
import sys

# Global MySQL connection and cursor
conn = None
cursor = None

def main_app():
    global entry_date, combo_day, entry_income, entry_food, entry_drinks, entry_airtime
    global entry_motorcycle, entry_fuel, entry_others, entry_if_others, entry_university
    global entries, tree, root, conn, cursor

    dark_mode = [False]

    def set_theme():
        theme_bg = "#121212" if dark_mode[0] else "#e6f0ff"
        theme_fg = "#ffffff" if dark_mode[0] else "#000000"
        entry_bg = "#1e1e1e" if dark_mode[0] else "#ffffff"
        entry_fg = "#ffffff" if dark_mode[0] else "#000000"
        
        root.configure(bg=theme_bg)
        frame_input.configure(bg=theme_bg, fg=theme_fg)
        frame_list.configure(bg=theme_bg, fg=theme_fg)
        for child in frame_input.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=theme_bg)
                for widget in child.winfo_children():
                    if isinstance(widget, tk.Label):
                        widget.configure(bg=theme_bg, fg=theme_fg)
                    elif isinstance(widget, ttk.Entry):
                        widget.configure(style="Dark.TEntry" if dark_mode[0] else "TEntry")
            elif isinstance(child, ttk.Button):
                child.configure(style="Dark.TButton" if dark_mode[0] else "TButton")
        tree.configure(style="Dark.Treeview" if dark_mode[0] else "Treeview")

    def update_day_from_date(event=None):
        d = entry_date.get().strip()
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            day_name = dt.strftime("%A")
            combo_day.set(day_name)
        except ValueError:
            combo_day.set("")

    def add_user():
        global combo_day, entry_date, entry_income, entry_food, entry_drinks, entry_airtime
        global entry_motorcycle, entry_fuel, entry_others, entry_if_others, entry_university

        try:
            def parse_number(value, field_name):
                if value.strip() == '':
                    return 0.0
                try:
                    num = float(value)
                    if num < 0:
                        raise ValueError(f"{field_name} must be >= 0.")
                    return num
                except ValueError:
                    raise ValueError(f"{field_name} must be a number and >= 0.")

            reg_date_str = entry_date.get().strip()
            if not reg_date_str:
                messagebox.showwarning("Input Error", "Date is required.")
                return
            try:
                reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showwarning("Input Error", "Date format must be YYYY-MM-DD.")
                return

            day = combo_day.get().strip()
            if not day:
                messagebox.showwarning("Input Error", "Day is not valid.")
                return

            income = parse_number(entry_income.get(), "Income")
            food = parse_number(entry_food.get(), "Food")
            drinks = parse_number(entry_drinks.get(), "Drinks")
            airtime = parse_number(entry_airtime.get(), "Airtime")
            motorcycle = parse_number(entry_motorcycle.get(), "Motorcycle")
            fuel = parse_number(entry_fuel.get(), "Fuel")
            others = parse_number(entry_others.get(), "Others")
            if_others = entry_if_others.get().strip() or None
            university = parse_number(entry_university.get(), "University")

            total_expense = food + drinks + airtime + motorcycle + fuel + others + university
            total = income - total_expense

            cursor.execute("""
                UPDATE data
                SET day=%s, income=income + %s, food=food + %s, drinks=drinks + %s, airtime=airtime + %s,
                    motorcycle=motorcycle + %s, fuel=fuel + %s, others=others + %s, if_others=%s, university=university + %s,
                    total_expense=food + drinks + airtime + motorcycle + fuel + others + university,
                    total=income - (food + drinks + airtime + motorcycle + fuel + others + university)
                WHERE reg_date = %s
            """, (day, income, food, drinks, airtime, motorcycle, fuel, others, if_others, university, reg_date))
            conn.commit()

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO data 
                    (reg_date, day, income, food, drinks, airtime, motorcycle, fuel, others, if_others, university, total_expense, total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (reg_date, day, income, food, drinks, airtime, motorcycle, fuel, others, if_others, university, total_expense, total))
                conn.commit()
                messagebox.showinfo("Success", "✅ New record added successfully.")
            else:
                messagebox.showinfo("Updated", "✅ Existing record updated successfully.")

            refresh_users()

            entry_date.delete(0, tk.END)
            entry_date.insert(0, str(date.today()))
            update_day_from_date()
            entry_income.delete(0, tk.END)
            entry_food.delete(0, tk.END)
            entry_drinks.delete(0, tk.END)
            entry_airtime.delete(0, tk.END)
            entry_motorcycle.delete(0, tk.END)
            entry_fuel.delete(0, tk.END)
            entry_others.delete(0, tk.END)
            entry_if_others.delete(0, tk.END)
            entry_university.delete(0, tk.END)
            entry_income.focus_set()

        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to insert/update record:\n{err}")

    def refresh_users():
        for i in tree.get_children():
            tree.delete(i)
        try:
            cursor.execute("SELECT id, reg_date, day, income, food, drinks, airtime, motorcycle, fuel, others, if_others, university, total_expense, total FROM data ORDER BY reg_date")
            for row in cursor.fetchall():
                tree.insert("", tk.END, values=row)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch records:\n{err}")

    def save_dataset():
        try:
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            cursor.execute("""
                SELECT id, reg_date, day, income, food, drinks, airtime, motorcycle, fuel, others, if_others, university, total_expense, total
                FROM data
                WHERE reg_date BETWEEN %s AND %s
                ORDER BY reg_date
            """, (start_of_week, end_of_week))
            records = cursor.fetchall()

            if not records:
                messagebox.showinfo("No Data", "No records found for the current week.")
                return

            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], title="Save Weekly Dataset As")
            if not file_path:
                return

            with open(file_path, mode="w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                headers = ["ID", "Date", "Day", "Income", "Food", "Drinks", "Airtime", "Motorcycle", "Fuel", "Others", "If_Others", "University", "Total_Expenses", "Total"]
                writer.writerow(headers)
                writer.writerows(records)

            messagebox.showinfo("Success", f"Weekly dataset saved to:\n{file_path}")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching records:\n{err}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV:\n{e}")

    def delete_selected():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a row to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected record?")
        if not confirm:
            return

        try:
            item = tree.item(selected_item)
            record_id = item["values"][0]

            cursor.execute("DELETE FROM data WHERE id = %s", (record_id,))
            conn.commit()
            tree.delete(selected_item)
            messagebox.showinfo("Deleted", "Record deleted successfully.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to delete record:\n{err}")

    def on_closing():
        try:
            cursor.close()
            conn.close()
        except:
            pass
        root.destroy()

    root = tk.Tk()
    root.title("🏠 MY HOME ACCOUNT")
    root.geometry("1350x780")
    root.configure(bg="#e6f0ff")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#5a8dee", foreground="white")
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=28, background="#ffffff", fieldbackground="#ffffff")
    style.configure("TEntry", foreground="black", fieldbackground="white")
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)

    style.configure("Dark.Treeview", font=("Segoe UI", 10), rowheight=28, background="#1e1e1e", fieldbackground="#1e1e1e", foreground="white")
    style.configure("Dark.TEntry", foreground="white", fieldbackground="#1e1e1e")
    style.configure("Dark.TButton", font=("Segoe UI", 10, "bold"), padding=8, background="#333", foreground="white")

    style.map("TButton", background=[("active", "#4a69bd")], foreground=[("active", "white")])
    style.map("Dark.TButton", background=[("active", "#555")], foreground=[("active", "#fff")])

    frame_input = tk.LabelFrame(root, text="➕ Add Expense Record", bg="#e6f0ff", font=("Segoe UI", 14, "bold"), padx=10, pady=10, fg="#333")
    frame_input.pack(padx=20, pady=10, fill="x")

    entries = []

    def add_labeled_entry(label_text):
        row = tk.Frame(frame_input, bg="#e6f0ff")
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label_text, width=15, anchor="w", font=("Segoe UI", 10, "bold"), bg="#e6f0ff", fg="#333").pack(side="left")
        entry = ttk.Entry(row, width=50, cursor="xterm")
        entry.pack(side="left", expand=True, fill="x")
        entries.append(entry)
        return entry

    entry_date = add_labeled_entry("📅 Date (YYYY-MM-DD)")
    entry_date.insert(0, str(date.today()))
    entry_date.bind("<FocusOut>", update_day_from_date)
    entry_date.bind("<Return>", lambda e: [update_day_from_date(), entry_income.focus_set()])

    row_day = tk.Frame(frame_input, bg="#e6f0ff")
    row_day.pack(fill="x", pady=3)
    tk.Label(row_day, text="📅 Day", width=15, anchor="w", font=("Segoe UI", 10, "bold"), bg="#e6f0ff", fg="#333").pack(side="left")
    combo_day = ttk.Combobox(row_day, width=50, state="readonly", cursor="arrow", font=("Segoe UI", 10))
    combo_day['values'] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    combo_day.pack(side="left", fill="x", expand=True)
    update_day_from_date()

    entry_income = add_labeled_entry("💰 Income")
    entry_food = add_labeled_entry("🍔 Food")
    entry_drinks = add_labeled_entry("🥤 Drinks")
    entry_airtime = add_labeled_entry("📞 Airtime")
    entry_motorcycle = add_labeled_entry("🛵 Motorcycle")
    entry_fuel = add_labeled_entry("⛽ Fuel")
    entry_others = add_labeled_entry("📦 Others")
    entry_if_others = add_labeled_entry("📝 If_Others")
    entry_university = add_labeled_entry("🎓 University")

    for idx, entry in enumerate(entries):
        entry.bind("<Return>", lambda e, i=idx: (add_user() if (e.state & 0x0001) else entries[i + 1].focus_set()) if i + 1 < len(entries) else add_user())

    button_row = tk.Frame(frame_input, bg="#e6f0ff")
    button_row.pack(pady=12)

    ttk.Button(button_row, text="🌙 Toggle Dark Mode", command=lambda: [dark_mode.__setitem__(0, not dark_mode[0]), set_theme()], cursor="hand2").pack(side="left", padx=10)
    ttk.Button(button_row, text="🗑️ Delete Record", command=delete_selected, cursor="hand2").pack(side="left", padx=10)
    ttk.Button(button_row, text="➕ Add Record", command=add_user, cursor="hand2").pack(side="left", padx=10)
    ttk.Button(button_row, text="💾 Save Dataset", command=save_dataset, cursor="hand2").pack(side="left", padx=10)
    ttk.Button(button_row, text="🚪 Exit App", command=on_closing, cursor="hand2").pack(side="left", padx=10)

    frame_list = tk.LabelFrame(root, text="📊 Expense Records", bg="#e6f0ff", font=("Segoe UI", 14, "bold"), fg="#222")
    frame_list.pack(padx=20, pady=10, fill="both", expand=True)

    columns = ("ID", "Date", "Day", "Income", "Food", "Drinks", "Airtime", "Motorcycle", "Fuel", "Others", "If_Others", "University", "Total_Expenses", "Total")
    tree = ttk.Treeview(frame_list, columns=columns, show="headings", height=14, cursor="hand2")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=100)

    tree.pack(fill="both", expand=True)

    root.after(100, refresh_users)
    set_theme()
    root.mainloop()


def show_login():
    login_root = tk.Tk()
    login_root.title("🔐 Secure Login")
    login_root.geometry("400x320")
    login_root.configure(bg="#f0f5ff")

    tk.Label(login_root, text="🔑 Username", font=("Segoe UI", 12, "bold"), bg="#f0f5ff").pack(pady=(30, 5))
    entry_user = ttk.Entry(login_root, font=("Segoe UI", 12), width=30, cursor="xterm")
    entry_user.pack()

    tk.Label(login_root, text="🔒 Password", font=("Segoe UI", 12, "bold"), bg="#f0f5ff").pack(pady=(20, 5))
    entry_pass = ttk.Entry(login_root, show="*", font=("Segoe UI", 12), width=30, cursor="xterm")
    entry_pass.pack()

    login_attempts = [0]
    attempts_label = tk.Label(login_root, text="You have 5 attempts remaining.", font=("Segoe UI", 10), fg="blue", bg="#f0f5ff")
    attempts_label.pack(pady=10)

    def update_attempts_label():
        remaining = 5 - login_attempts[0]
        text, color = (f"You have {remaining} attempts remaining.", "orange") if remaining > 0 else ("No attempts remaining. Exiting...", "red")
        attempts_label.config(text=text, fg=color)

    def try_login(event=None):
        global conn, cursor
        username = entry_user.get().strip()
        password = entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Username and Password are required.")
            return

        try:
            conn = mysql.connector.connect(host="localhost", user=username, password=password, database="Ghost")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login_users WHERE username = %s AND password = %s", (username, password))
            if cursor.fetchone():
                login_root.destroy()
                main_app()
            else:
                login_attempts[0] += 1
                update_attempts_label()
                if login_attempts[0] >= 5:
                    messagebox.showerror("Login Failed", "Too many failed attempts.")
                    login_root.destroy()
                    sys.exit()
                messagebox.showerror("Login Failed", "Invalid credentials.")
                entry_pass.delete(0, tk.END)

        except mysql.connector.Error:
            login_attempts[0] += 1
            update_attempts_label()
            if login_attempts[0] >= 5:
                messagebox.showerror("Connection Error", "Too many failed attempts. Exiting...")
                login_root.destroy()
                sys.exit()
            messagebox.showerror("Connection Error", "Could not connect.")
            entry_pass.delete(0, tk.END)

    entry_user.bind("<Return>", lambda e: entry_pass.focus_set())
    entry_pass.bind("<Return>", try_login)

    ttk.Button(login_root, text="Login", command=try_login, cursor="hand2").pack(pady=20)

    login_root.mainloop()


# Start the app
show_login()

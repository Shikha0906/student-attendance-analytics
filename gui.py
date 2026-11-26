"""Tkinter GUI for Student Attendance Analytics. Run: python gui.py"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from typing import Optional

from storage import Storage
from attendance_service import AttendanceService
from analytics_service import AnalyticsService
from export import AttendanceExporter


class AttendanceApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Student Attendance Analytics")
        self.root.geometry("1000x700")
        self.storage = Storage(data_dir="data")
        self.attendance = AttendanceService(self.storage)
        self.analytics = AnalyticsService(self.storage)
        self.exporter = AttendanceExporter(self.storage)
        self._build_ui()
    def _build_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_dashboard = ttk.Frame(nb)
        self.tab_record = ttk.Frame(nb)
        self.tab_manage = ttk.Frame(nb)
        self.tab_analytics = ttk.Frame(nb)
        self.tab_export = ttk.Frame(nb)
        nb.add(self.tab_dashboard, text="Dashboard")
        nb.add(self.tab_record, text="Record Attendance")
        nb.add(self.tab_manage, text="Manage")
        nb.add(self.tab_analytics, text="Analytics")
        nb.add(self.tab_export, text="Export")
        self._build_dashboard()
        self._build_record_tab()
        self._build_manage_tab()
        self._build_analytics_tab()
        self._build_export_tab()

    def _build_dashboard(self):
        f = self.tab_dashboard
        sf = ttk.Frame(f)
        sf.pack(fill="x", padx=20, pady=20)
        self.lbl_students = self._card(sf, "Total Students", "0", 0)
        self.lbl_courses = self._card(sf, "Total Courses", "0", 1)
        self.lbl_records = self._card(sf, "Attendance Records", "0", 2)
        self.lbl_rate = self._card(sf, "Overall Attendance Rate", "0%", 3)
        ttk.Button(f, text="Refresh Dashboard", command=self._refresh_dashboard).pack(pady=10)
        ttk.Label(f, text="Recent Attendance Records", font=("Segoe UI", 12, "bold")).pack(pady=(20, 5))
        self.tree = ttk.Treeview(f, columns=("date", "student", "course", "status"), show="headings", height=12)
        for c, w in [("date", 100), ("student", 200), ("course", 200), ("status", 100)]:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def _card(self, parent, title, value, column):
        card = ttk.Frame(parent, padding=15)
        card.grid(row=0, column=column, padx=10, sticky="nsew")
        parent.grid_columnconfigure(column, weight=1)
        ttk.Label(card, text=title, font=("Segoe UI", 10, "bold")).pack()
        lbl = ttk.Label(card, text=value, font=("Segoe UI", 20, "bold"), foreground="#0d6efd")
        lbl.pack()
        return lbl

    def _build_record_tab(self):
        f = self.tab_record
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text="Student:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.cmb_student = ttk.Combobox(f, state="readonly", width=40)
        self.cmb_student.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ttk.Label(f, text="Course:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.cmb_course = ttk.Combobox(f, state="readonly", width=40)
        self.cmb_course.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ttk.Label(f, text="Date:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_date = ttk.Entry(f, width=40)
        self.entry_date.insert(0, date.today().isoformat())
        self.entry_date.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        ttk.Label(f, text="Status:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.cmb_status = ttk.Combobox(f, state="readonly", width=40, values=["present", "absent", "late"])
        self.cmb_status.set("present")
        self.cmb_status.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        ttk.Button(f, text="Record Attendance", command=self._on_record).grid(row=4, column=0, columnspan=2, pady=20)
        self.lbl_msg = ttk.Label(f, text="", foreground="green")
        self.lbl_msg.grid(row=5, column=0, columnspan=2, pady=5)
        self._refresh_students()
        self._refresh_courses()
        self._refresh_records()

    def _build_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_dashboard = ttk.Frame(nb)
        self.tab_record = ttk.Frame(nb)
        self.tab_manage = ttk.Frame(nb)
        self.tab_analytics = ttk.Frame(nb)
        self.tab_export = ttk.Frame(nb)
        nb.add(self.tab_dashboard, text="Dashboard")
        nb.add(self.tab_record, text="Record Attendance")
    def _build_manage_tab(self):
        f = self.tab_manage
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text="Add New Student", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 5))
        ttk.Label(f, text="Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.e_s_name = ttk.Entry(f, width=40)
        self.e_s_name.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(f, text="Email:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.e_s_email = ttk.Entry(f, width=40)
        self.e_s_email.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ttk.Button(f, text="Add Student", command=self._on_add_student).grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Separator(f, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=20)
        ttk.Label(f, text="Add New Course", font=("Segoe UI", 11, "bold")).grid(row=5, column=0, columnspan=2, pady=(0, 5))
        ttk.Label(f, text="Name:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.e_c_name = ttk.Entry(f, width=40)
        self.e_c_name.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        ttk.Label(f, text="Code (e.g., CS101):").grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.e_c_code = ttk.Entry(f, width=40)
        self.e_c_code.grid(row=7, column=1, padx=10, pady=5, sticky="ew")
        ttk.Button(f, text="Add Course", command=self._on_add_course).grid(row=8, column=0, columnspan=2, pady=10)
        self.lbl_mmsg = ttk.Label(f, text="", foreground="green")
        self.lbl_mmsg.grid(row=9, column=0, columnspan=2, pady=5)

    def _build_analytics_tab(self):
        f = self.tab_analytics
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        ttk.Label(f, text="Daily Totals", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, pady=(10, 5))
        ttk.Label(f, text="Date:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.e_a_date = ttk.Entry(f, width=20)
        self.e_a_date.insert(0, date.today().isoformat())
        self.e_a_date.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        ttk.Button(f, text="Get Daily Totals", command=self._on_daily).grid(row=2, column=0, pady=10)
        self.lbl_daily = ttk.Label(f, text="", wraplength=400)
        self.lbl_daily.grid(row=3, column=0, padx=10, pady=5)
        ttk.Label(f, text="Course-wise Totals", font=("Segoe UI", 11, "bold")).grid(row=0, column=1, pady=(10, 5))
        ttk.Label(f, text="Course:").grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.cmb_a_course = ttk.Combobox(f, state="readonly", width=25)
        self.cmb_a_course.grid(row=1, column=1, padx=10, pady=5, sticky="e")
        ttk.Button(f, text="Get Course Totals", command=self._on_course).grid(row=2, column=1, pady=10)
        self.lbl_course = ttk.Label(f, text="", wraplength=400)
        self.lbl_course.grid(row=3, column=1, padx=10, pady=5)
        ttk.Button(f, text="Show Full Summary", command=self._on_summary).grid(row=4, column=0, columnspan=2, pady=20)
        self.lbl_summary = ttk.Label(f, text="", wraplength=900, justify="left")
        self.lbl_summary.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

    def _build_export_tab(self):
        f = self.tab_export
        ttk.Label(f, text="Export Reports to CSV", font=("Segoe UI", 12, "bold")).pack(pady=20)
        bf = ttk.Frame(f)
        bf.pack(pady=10)
        ttk.Button(bf, text="Export All Records", command=self._exp_all).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(bf, text="Export Daily Summary", command=self._exp_daily).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(bf, text="Export Course Summary", command=self._exp_course).grid(row=0, column=2, padx=5, pady=5)
        self.lbl_exp = ttk.Label(f, text="", foreground="green", wraplength=600)
        self.lbl_exp.pack(pady=20)
        nb.add(self.tab_manage, text="Manage")
        nb.add(self.tab_analytics, text="Analytics")
        nb.add(self.tab_export, text="Export")
        self._build_dashboard()
        self._build_record_tab()
    def _refresh_students(self):
        self.cmb_student["values"] = [f"{s.student_id} | {s.name} | {s.email}" for s in self.storage.get_students()]

    def _refresh_courses(self):
        vals = [f"{c.course_id} | {c.code} | {c.name}" for c in self.storage.get_courses()]
        self.cmb_course["values"] = vals
        self.cmb_a_course["values"] = vals

    def _refresh_records(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in self.storage.get_all_records()[:20]:
            s = self.storage.get_student_by_id(r.student_id)
            c = self.storage.get_course_by_id(r.course_id)
            self.tree.insert("", "end", values=(r.date, s.name if s else "?", c.code if c else "?", r.status))

    def _refresh_dashboard(self):
        st = self.storage.get_students()
        cr = self.storage.get_courses()
        rc = self.storage.get_all_records()
        self.lbl_students.config(text=str(len(st)))
        self.lbl_courses.config(text=str(len(cr)))
        self.lbl_records.config(text=str(len(rc)))
        if rc:
            p = sum(1 for r in rc if r.status == "present")
            self.lbl_rate.config(text=f"{round(p / len(rc) * 100, 2)}%")
        else:
            self.lbl_rate.config(text="0%")
        self._refresh_records()

    def _sid(self, v):
        return v.split(" | ")[0] if v and " | " in v else None

    def _on_record(self):
        try:
            sid = self._sid(self.cmb_student.get())
            cid = self._sid(self.cmb_course.get())
            d = date.fromisoformat(self.entry_date.get())
            st = self.cmb_status.get()
            if not sid or not cid:
                messagebox.showerror("Error", "Select a student and course.")
                return
            self.attendance.record_attendance(sid, cid, d, st)
            self.lbl_msg.config(text=f"Recorded: {st}", foreground="green")
            self._refresh_records()
            self._refresh_dashboard()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _on_add_student(self):
        n = self.e_s_name.get().strip()
        e = self.e_s_email.get().strip()
        if not n or not e:
            messagebox.showerror("Error", "Fill name and email.")
            return
        try:
            s = self.attendance.register_student(n, e)
            self.lbl_mmsg.config(text=f"Added: {s.name}", foreground="green")
            self.e_s_name.delete(0, tk.END)
            self.e_s_email.delete(0, tk.END)
            self._refresh_students()
            self._refresh_dashboard()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _on_add_course(self):
        n = self.e_c_name.get().strip()
        c = self.e_c_code.get().strip()
        if not n or not c:
            messagebox.showerror("Error", "Fill name and code.")
            return
        try:
            cr = self.attendance.register_course(n, c)
            self.lbl_mmsg.config(text=f"Added: {cr.code}", foreground="green")
            self.e_c_name.delete(0, tk.END)
            self.e_c_code.delete(0, tk.END)
            self._refresh_courses()
            self._refresh_dashboard()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _on_daily(self):
        try:
            d = date.fromisoformat(self.e_a_date.get())
            s = self.analytics.daily_totals(d, use_mapreduce=True)
            self.lbl_daily.config(text=f"{s['date']}: {s['present']}P/{s['absent']}A/{s['late']}L | Rate: {s['attendance_rate_percent']}%", foreground="#0d6efd")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _on_course(self):
        try:
            cid = self._sid(self.cmb_a_course.get())
            if not cid:
                messagebox.showerror("Error", "Select a course.")
                return
            s = self.analytics.course_wise_totals(cid, use_mapreduce=True)
            cr = self.storage.get_course_by_id(cid)
            self.lbl_course.config(text=f"{cr.code}: {s['present']}P/{s['absent']}A/{s['late']}L | Rate: {s['attendance_rate_percent']}%", foreground="#0d6efd")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _on_summary(self):
        cs = self.analytics.all_courses_summary(use_mapreduce=True)
        ds = self.analytics.all_dates_summary()
        ov = self.analytics.average_attendance_rate()
        lines = [f"Overall: {ov}%", "", "Courses:"]
        for c in cs:
            lines.append(f"  {c['code']}: {c['attendance_rate_percent']}% ({c['present']}/{c['total_records']})")
        lines.append("")
        lines.append("Dates:")
        for d in ds:
            lines.append(f"  {d['date']}: {d['attendance_rate_percent']}% ({d['present']}/{d['total_records']})")
        self.lbl_summary.config(text="\n".join(lines), foreground="#0d6efd")

    def _exp_all(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if p:
            self.exporter.export_all_records(p)
            self.lbl_exp.config(text=f"Saved: {p}", foreground="green")

    def _exp_daily(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if p:
            self.exporter.export_daily_summary(p)
            self.lbl_exp.config(text=f"Saved: {p}", foreground="green")

    def _exp_course(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if p:
            self.exporter.export_course_summary(p)
            self.lbl_exp.config(text=f"Saved: {p}", foreground="green")


def main():
    root = tk.Tk()
    AttendanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
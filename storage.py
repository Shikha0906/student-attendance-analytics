"""Simple JSON-based file storage for attendance records."""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import date

from models import Student, Course, AttendanceRecord


class Storage:
    """Handles persistence of students, courses, and attendance records."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.students_file = os.path.join(data_dir, "students.json")
        self.courses_file = os.path.join(data_dir, "courses.json")
        self.attendance_file = os.path.join(data_dir, "attendance.json")
        self.faculty_file = os.path.join(data_dir, "faculty.json")
        os.makedirs(data_dir, exist_ok=True)
        self._initialize_files()

    def _initialize_files(self) -> None:
        """Create empty JSON files if they don't exist."""
        for path in (self.students_file, self.courses_file, self.attendance_file):
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)

        if not os.path.exists(self.faculty_file):
            default_faculty = [{
                "faculty_id": "FAC-001",
                "name": "Prof. Administrator",
                "username": "faculty",
                "mobile": "9876543210",
                "email": "faculty@college.edu",
                "password": "admin123",
                "role": "Faculty Administrator"
            }]
            with open(self.faculty_file, "w", encoding="utf-8") as f:
                json.dump(default_faculty, f, indent=2)

    def _read_json(self, path: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: str, data: List[Dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # --- Students ---
    def add_student(self, student: Student) -> None:
        students = self._read_json(self.students_file)
        students.append(student.to_dict())
        self._write_json(self.students_file, students)

    def get_students(self) -> List[Student]:
        return [Student(**s) for s in self._read_json(self.students_file)]

    def get_student_by_id(self, student_id: str) -> Optional[Student]:
        for s in self.get_students():
            if s.student_id == student_id:
                return s
        return None

    # --- Courses ---
    def add_course(self, course: Course) -> None:
        courses = self._read_json(self.courses_file)
        courses.append(course.to_dict())
        self._write_json(self.courses_file, courses)

    def get_courses(self) -> List[Course]:
        return [Course(**c) for c in self._read_json(self.courses_file)]

    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        for c in self.get_courses():
            if c.course_id == course_id:
                return c
        return None

    # --- Attendance ---
    def add_record(self, record: AttendanceRecord) -> None:
        records = self._read_json(self.attendance_file)
        records.append(record.to_dict())
        self._write_json(self.attendance_file, records)

    def get_all_records(self) -> List[AttendanceRecord]:
        return [AttendanceRecord(**r) for r in self._read_json(self.attendance_file)]

    def get_records_by_date(self, att_date: date) -> List[AttendanceRecord]:
        target = att_date.isoformat()
        return [r for r in self.get_all_records() if r.date == target]

    def get_records_by_course(self, course_id: str) -> List[AttendanceRecord]:
        return [r for r in self.get_all_records() if r.course_id == course_id]

    def get_records_by_student(self, student_id: str) -> List[AttendanceRecord]:
        return [r for r in self.get_all_records() if r.student_id == student_id]

    # --- Faculty / Admin ---
    def get_all_faculty(self) -> List[Dict[str, Any]]:
        return self._read_json(self.faculty_file)

    def add_faculty(self, faculty: Dict[str, Any]) -> None:
        faculties = self._read_json(self.faculty_file)
        updated = False
        for idx, f in enumerate(faculties):
            if f.get("username", "").lower() == faculty.get("username", "").lower() or f.get("mobile", "").strip() == faculty.get("mobile", "").strip():
                faculties[idx] = faculty
                updated = True
                break
        if not updated:
            faculties.append(faculty)
        self._write_json(self.faculty_file, faculties)

    def get_faculty_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        for f in self.get_all_faculty():
            if f.get("username", "").lower() == username.lower():
                return f
        return None

    def get_faculty_by_mobile(self, mobile: str) -> Optional[Dict[str, Any]]:
        for f in self.get_all_faculty():
            if f.get("mobile", "").strip() == mobile.strip():
                return f
        return None
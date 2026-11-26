"""Service layer for recording and managing student attendance."""

from typing import List, Optional, Dict, Any
from datetime import date

from models import Student, Course, AttendanceRecord
from storage import Storage


class AttendanceService:
    """Business logic for recording attendance."""

    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()

    def register_student(self, name: str, email: str) -> Student:
        student = Student(student_id=self._generate_id("STU"), name=name, email=email)
        self.storage.add_student(student)
        return student

    def register_course(self, name: str, code: str) -> Course:
        course = Course(course_id=self._generate_id("CRS"), name=name, code=code)
        self.storage.add_course(course)
        return course

    def record_attendance(self, student_id: str, course_id: str,
                          att_date: date, status: str) -> AttendanceRecord:
        """Record attendance for a student in a course on a given date."""
        # Validate references exist
        if not self.storage.get_student_by_id(student_id):
            raise ValueError(f"Student with id {student_id} does not exist.")
        if not self.storage.get_course_by_id(course_id):
            raise ValueError(f"Course with id {course_id} does not exist.")

        record = AttendanceRecord.create(student_id, course_id, att_date, status)
        self.storage.add_record(record)
        return record

    def record_bulk_attendance(self, entries: List[Dict[str, Any]]) -> List[AttendanceRecord]:
        """Record multiple attendance entries at once.

        Each entry dict must contain: student_id, course_id, date, status.
        """
        records: List[AttendanceRecord] = []
        for entry in entries:
            att_date = entry["date"] if isinstance(entry["date"], date) else date.fromisoformat(entry["date"])
            record = self.record_attendance(
                student_id=entry["student_id"],
                course_id=entry["course_id"],
                att_date=att_date,
                status=entry["status"],
            )
            records.append(record)
        return records

    def get_all_records(self) -> List[AttendanceRecord]:
        return self.storage.get_all_records()

    @staticmethod
    def _generate_id(prefix: str) -> str:
        import uuid
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
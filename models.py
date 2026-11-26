"""Data models for the Student Attendance Analytics system."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, List
import uuid


@dataclass
class Student:
    """Represents a student."""
    student_id: str
    name: str
    email: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Course:
    """Represents a course."""
    course_id: str
    name: str
    code: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AttendanceRecord:
    """Represents a single attendance record."""
    record_id: str
    student_id: str
    course_id: str
    date: str  # ISO format YYYY-MM-DD
    status: str  # "present", "absent", "late"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def create(cls, student_id: str, course_id: str, att_date: date,
               status: str) -> "AttendanceRecord":
        """Factory method to create a new attendance record."""
        if status not in ("present", "absent", "late"):
            raise ValueError(f"Invalid status: {status}. Must be 'present', 'absent', or 'late'.")
        return cls(
            record_id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=course_id,
            date=att_date.isoformat(),
            status=status,
        )
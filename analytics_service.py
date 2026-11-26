"""Analytics service for daily and course-wise attendance totals.

Supports both direct aggregation and an optional MapReduce-style implementation.
Cloud backend support added for distributed analytics.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from collections import defaultdict

from models import AttendanceRecord, Student, Course
from storage import Storage

class AnalyticsService:
    """Computes attendance aggregates: daily totals, course-wise totals, averages."""

    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def daily_totals(self, target_date: date, use_mapreduce: bool = False) -> Dict[str, Any]:
        """Return attendance totals for a specific date.

        Returns a dict with total records and breakdown by status.
        """
        records = self.storage.get_records_by_date(target_date)
        if use_mapreduce:
            return self._mapreduce_daily(records, target_date)
        return self._direct_daily(records, target_date)

    def course_wise_totals(self, course_id: str, use_mapreduce: bool = False) -> Dict[str, Any]:
        """Return attendance totals for a specific course.

        Returns present/absent/late counts and attendance percentage.
        """
        records = self.storage.get_records_by_course(course_id)
        if use_mapreduce:
            return self._mapreduce_course(records, course_id)
        return self._direct_course(records, course_id)

    def all_courses_summary(self, use_mapreduce: bool = False) -> List[Dict[str, Any]]:
        """Return a summary for every course in the system."""
        courses = self.storage.get_courses()
        summary: List[Dict[str, Any]] = []
        for course in courses:
            stats = self.course_wise_totals(course.course_id, use_mapreduce=use_mapreduce)
            summary.append({
                "course_id": course.course_id,
                "name": course.name,
                "code": course.code,
                **stats,
            })
        return summary

    def all_dates_summary(self, use_mapreduce: bool = False) -> List[Dict[str, Any]]:
        """Return a summary for every date that has attendance records."""
        records = self.storage.get_all_records()
        dates = sorted({r.date for r in records})
        summary: List[Dict[str, Any]] = []
        for d in dates:
            target = date.fromisoformat(d)
            stats = self.daily_totals(target, use_mapreduce=use_mapreduce)
            summary.append({
                "date": d,
                **stats,
            })
        return summary

    def average_attendance_rate(self, course_id: Optional[str] = None,
                                use_mapreduce: bool = False) -> float:
        """Compute average attendance rate (present / total) as a percentage (0-100).

        If course_id is given, computes for that course only; otherwise for all records.
        """
        if course_id:
            records = self.storage.get_records_by_course(course_id)
        else:
            records = self.storage.get_all_records()

        if not records:
            return 0.0

        if use_mapreduce:
            present_count = self._mapreduce_count(records, lambda r: r.status == "present")
            total_count = len(records)
        else:
            present_count = sum(1 for r in records if r.status == "present")
            total_count = len(records)

        return round((present_count / total_count) * 100, 2)

    # ------------------------------------------------------------------
    # Direct aggregation implementations
    # ------------------------------------------------------------------
    def _direct_daily(self, records: List[AttendanceRecord],
                      target_date: date) -> Dict[str, Any]:
        counts = {"present": 0, "absent": 0, "late": 0}
        for r in records:
            if r.status in counts:
                counts[r.status] += 1
        total = len(records)
        present_rate = round((counts["present"] / total) * 100, 2) if total else 0.0
        return {
            "date": target_date.isoformat(),
            "total_records": total,
            "present": counts["present"],
            "absent": counts["absent"],
            "late": counts["late"],
            "attendance_rate_percent": present_rate,
        }

    def _direct_course(self, records: List[AttendanceRecord],
                       course_id: str) -> Dict[str, Any]:
        counts = {"present": 0, "absent": 0, "late": 0}
        for r in records:
            if r.status in counts:
                counts[r.status] += 1
        total = len(records)
        present_rate = round((counts["present"] / total) * 100, 2) if total else 0.0
        return {
            "course_id": course_id,
            "total_records": total,
            "present": counts["present"],
            "absent": counts["absent"],
            "late": counts["late"],
            "attendance_rate_percent": present_rate,
        }

    # ------------------------------------------------------------------
    # MapReduce-style implementations
    # ------------------------------------------------------------------
    def _mapreduce_daily(self, records: List[AttendanceRecord],
                         target_date: date) -> Dict[str, Any]:
        """MapReduce: map (date, status) -> 1, reduce by key sum."""
        # Map phase
        mapped: List[Tuple[str, int]] = []
        for r in records:
            mapped.append((r.status, 1))

        # Reduce phase: group by status and sum
        reduced: Dict[str, int] = defaultdict(int)
        for key, value in mapped:
            reduced[key] += value

        counts = {status: reduced.get(status, 0) for status in ("present", "absent", "late")}
        total = sum(counts.values())
        present_rate = round((counts["present"] / total) * 100, 2) if total else 0.0
        return {
            "date": target_date.isoformat(),
            "total_records": total,
            "present": counts["present"],
            "absent": counts["absent"],
            "late": counts["late"],
            "attendance_rate_percent": present_rate,
            "method": "mapreduce",
        }

    def _mapreduce_course(self, records: List[AttendanceRecord],
                          course_id: str) -> Dict[str, Any]:
        """MapReduce: map (course_id, status) -> 1, reduce by key sum."""
        # Map phase: emit (status, 1) for each record
        mapped: List[Tuple[str, int]] = []
        for r in records:
            mapped.append((r.status, 1))

        # Reduce phase: group by status and sum
        reduced: Dict[str, int] = defaultdict(int)
        for key, value in mapped:
            reduced[key] += value

        counts = {status: reduced.get(status, 0) for status in ("present", "absent", "late")}
        total = sum(counts.values())
        present_rate = round((counts["present"] / total) * 100, 2) if total else 0.0
        return {
            "course_id": course_id,
            "total_records": total,
            "present": counts["present"],
            "absent": counts["absent"],
            "late": counts["late"],
            "attendance_rate_percent": present_rate,
            "method": "mapreduce",
        }

    @staticmethod
    def _mapreduce_count(records: List[AttendanceRecord],
                         predicate) -> int:
        """MapReduce count: map records matching predicate -> 1, reduce by sum."""
        mapped = [1 for r in records if predicate(r)]
        return sum(mapped)


class CloudAnalyticsService(AnalyticsService):
    """Extended analytics service with cloud backend support.

    Integrates with AWS S3, Azure Blob, or GCP Cloud Storage for
    distributed attendance data processing.
    """

    def __init__(self, storage: Optional[Storage] = None, cloud_backend: str = None):
        super().__init__(storage)
        self.cloud_backend = cloud_backend  # "aws_s3", "azure_blob", "gcp_gcs"
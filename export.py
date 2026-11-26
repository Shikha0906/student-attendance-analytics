"""CSV export utilities for attendance reports."""

import csv
import os
from datetime import date
from typing import List

from models import AttendanceRecord
from storage import Storage


class AttendanceExporter:
    """Exports attendance data to CSV files."""

    def __init__(self, storage: Storage):
        self.storage = storage

    def export_all_records(self, output_path: str = "attendance_export.csv") -> str:
        """Export all attendance records to CSV."""
        records = self.storage.get_all_records()
        self._write_records_csv(records, output_path)
        return output_path

    def export_by_course(self, course_id: str, output_path: str = None) -> str:
        """Export attendance records for a specific course to CSV."""
        if output_path is None:
            output_path = f"course_{course_id}_export.csv"
        records = self.storage.get_records_by_course(course_id)
        self._write_records_csv(records, output_path)
        return output_path

    def export_by_date(self, att_date: date, output_path: str = None) -> str:
        """Export attendance records for a specific date to CSV."""
        if output_path is None:
            output_path = f"attendance_{att_date.isoformat()}_export.csv"
        records = self.storage.get_records_by_date(att_date)
        self._write_records_csv(records, output_path)
        return output_path

    def export_daily_summary(self, output_path: str = "daily_summary.csv") -> str:
        """Export daily attendance summary to CSV."""
        from analytics_service import AnalyticsService
        analytics = AnalyticsService(self.storage)
        summary = analytics.all_dates_summary()

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Total Records", "Present", "Absent", "Late", "Attendance Rate (%)"])
            for entry in summary:
                writer.writerow([
                    entry["date"],
                    entry["total_records"],
                    entry["present"],
                    entry["absent"],
                    entry["late"],
                    entry["attendance_rate_percent"],
                ])
        return output_path

    def export_course_summary(self, output_path: str = "course_summary.csv") -> str:
        """Export course-wise attendance summary to CSV."""
        from analytics_service import AnalyticsService
        analytics = AnalyticsService(self.storage)
        summary = analytics.all_courses_summary()

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Course ID", "Code", "Name", "Total Records", "Present", "Absent", "Late", "Attendance Rate (%)"])
            for entry in summary:
                writer.writerow([
                    entry["course_id"],
                    entry["code"],
                    entry["name"],
                    entry["total_records"],
                    entry["present"],
                    entry["absent"],
                    entry["late"],
                    entry["attendance_rate_percent"],
                ])
        return output_path

    @staticmethod
    def _write_records_csv(records: List[AttendanceRecord], output_path: str) -> None:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Record ID", "Student ID", "Course ID", "Date", "Status", "Timestamp"])
            for r in records:
                writer.writerow([r.record_id, r.student_id, r.course_id, r.date, r.status, r.timestamp])
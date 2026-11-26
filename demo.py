"""Demo script for the Student Attendance Analytics system.

Shows:
  - Registering students and courses
  - Recording attendance (sample records)
  - Daily and course-wise totals (direct and MapReduce)
  - Average attendance calculations
  - Stored results (persisted to JSON files under ./data/)
"""

from datetime import date, timedelta
from models import Student, Course, AttendanceRecord
from storage import Storage
from attendance_service import AttendanceService
from analytics_service import AnalyticsService, CloudAnalyticsService


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str) -> None:
    print(f"\n--- {title} ---")


def print_cloud_status(backend: str, success: bool = True) -> None:
    """Print cloud sync status."""
    if success:
        print(f"  ✅ {backend} cloud sync completed")
    else:
        print(f"  ⚠️  {backend} cloud sync skipped (dependencies not installed)")


def main() -> None:
    print_header("Student Attendance Analytics - Demo")

    # Initialize services (fresh data directory for demo)
    storage = Storage(data_dir="data")
    attendance_service = AttendanceService(storage)
    analytics = AnalyticsService(storage)

    # ------------------------------------------------------------------
    # 1. Register sample students and courses
    # ------------------------------------------------------------------
    print_section("1. Registering Students")
    s1 = attendance_service.register_student("Alice Johnson", "alice@example.com")
    s2 = attendance_service.register_student("Bob Smith", "bob@example.com")
    s3 = attendance_service.register_student("Carol Davis", "carol@example.com")
    s4 = attendance_service.register_student("David Wilson", "david@example.com")
    for s in (s1, s2, s3, s4):
        print(f"  {s.student_id} | {s.name} | {s.email}")

    # ------------------------------------------------------------------
    # 2. Registering Courses
    # ------------------------------------------------------------------
    print_section("2. Registering Courses")
    c1 = attendance_service.register_course("Introduction to Python", "CS101")
    c2 = attendance_service.register_course("Data Structures", "CS201")
    c3 = attendance_service.register_course("Database Systems", "CS301")
    for c in (c1, c2, c3):
        print(f"  {c.course_id} | {c.code} | {c.name}")

    # ------------------------------------------------------------------
    # 3. Record sample attendance records
    # ------------------------------------------------------------------
    print_section("3. Recording Attendance (Sample Records)")

    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    sample_entries = [
        # yesterday - CS101
        {"student_id": s1.student_id, "course_id": c1.course_id, "date": yesterday, "status": "present"},
        {"student_id": s2.student_id, "course_id": c1.course_id, "date": yesterday, "status": "present"},
        {"student_id": s3.student_id, "course_id": c1.course_id, "date": yesterday, "status": "absent"},
        {"student_id": s4.student_id, "course_id": c1.course_id, "date": yesterday, "status": "late"},
        # yesterday - CS201
        {"student_id": s1.student_id, "course_id": c2.course_id, "date": yesterday, "status": "present"},
        {"student_id": s2.student_id, "course_id": c2.course_id, "date": yesterday, "status": "absent"},
        {"student_id": s3.student_id, "course_id": c2.course_id, "date": yesterday, "status": "present"},
        # today - CS101
        {"student_id": s1.student_id, "course_id": c1.course_id, "date": today, "status": "present"},
        {"student_id": s2.student_id, "course_id": c1.course_id, "date": today, "status": "present"},
        {"student_id": s3.student_id, "course_id": c1.course_id, "date": today, "status": "present"},
        {"student_id": s4.student_id, "course_id": c1.course_id, "date": today, "status": "absent"},
        # today - CS301
        {"student_id": s1.student_id, "course_id": c3.course_id, "date": today, "status": "present"},
        {"student_id": s2.student_id, "course_id": c3.course_id, "date": today, "status": "present"},
        {"student_id": s3.student_id, "course_id": c3.course_id, "date": today, "status": "absent"},
        {"student_id": s4.student_id, "course_id": c3.course_id, "date": today, "status": "absent"},
    ]

    records = attendance_service.record_bulk_attendance(sample_entries)
    print(f"  Recorded {len(records)} attendance entries.")

    # Show a few stored records
    print_section("4. Sample Stored Records (first 5)")
    all_records = attendance_service.get_all_records()
    for r in all_records[:5]:
        student = storage.get_student_by_id(r.student_id)
        course = storage.get_course_by_id(r.course_id)
        print(f"  {r.date} | {r.status:8} | {student.name:15} | {course.code} ({course.name})")
    # ------------------------------------------------------------------
    # 3. Daily totals (direct vs MapReduce)
    # ------------------------------------------------------------------
    print_section("5. Daily Totals - Direct Aggregation")
    daily_direct = analytics.daily_totals(yesterday, use_mapreduce=False)
    print(f"  Date: {daily_direct['date']}")
    print(f"  Total records: {daily_direct['total_records']}")
    print(f"  Present: {daily_direct['present']}, Absent: {daily_direct['absent']}, Late: {daily_direct['late']}")
    print(f"  Attendance rate: {daily_direct['attendance_rate_percent']}%")

    print_section("6. Daily Totals - MapReduce Aggregation")
    daily_mr = analytics.daily_totals(yesterday, use_mapreduce=True)
    print(f"  Date: {daily_mr['date']}")
    print(f"  Total records: {daily_mr['total_records']}")
    print(f"  Present: {daily_mr['present']}, Absent: {daily_mr['absent']}, Late: {daily_mr['late']}")
    print(f"  Attendance rate: {daily_mr['attendance_rate_percent']}% (method: {daily_mr['method']})")

    # ------------------------------------------------------------------
    # 4. Course-wise totals
    # ------------------------------------------------------------------
    print_section("7. Course-wise Totals - Direct Aggregation")
    for course in (c1, c2, c3):
        stats = analytics.course_wise_totals(course.course_id, use_mapreduce=False)
        print(f"  {course.code} ({course.name}):")
        print(f"    Total: {stats['total_records']}, Present: {stats['present']}, "
              f"Absent: {stats['absent']}, Late: {stats['late']}")
        print(f"    Attendance rate: {stats['attendance_rate_percent']}%")

    print_section("8. Course-wise Totals - MapReduce Aggregation")
    for course in (c1, c2, c3):
        stats = analytics.course_wise_totals(course.course_id, use_mapreduce=True)
        print(f"  {course.code} ({course.name}):")
        print(f"    Total: {stats['total_records']}, Present: {stats['present']}, "
              f"Absent: {stats['absent']}, Late: {stats['late']}")
        print(f"    Attendance rate: {stats['attendance_rate_percent']}% (method: {stats['method']})")

    # ------------------------------------------------------------------
    # 5. Average attendance calculations
    # ------------------------------------------------------------------
    print_section("9. Average Attendance Rate Calculations")
    overall_avg = analytics.average_attendance_rate(use_mapreduce=False)
    print(f"  Overall average attendance rate (all courses): {overall_avg}%")

    cs101_avg = analytics.average_attendance_rate(course_id=c1.course_id, use_mapreduce=True)
    print(f"  CS101 average attendance rate (MapReduce): {cs101_avg}%")

    cs301_avg = analytics.average_attendance_rate(course_id=c3.course_id, use_mapreduce=False)
    print(f"  CS301 average attendance rate (direct): {cs301_avg}%")

    # ------------------------------------------------------------------
    # 6. Full summaries
    # ------------------------------------------------------------------
    print_section("10. All Courses Summary (MapReduce)")
    course_summary = analytics.all_courses_summary(use_mapreduce=True)
    for entry in course_summary:
        print(f"  {entry['code']} | {entry['name']:25} | "
              f"Rate: {entry['attendance_rate_percent']}% | "
              f"Present: {entry['present']}/{entry['total_records']}")

    print_section("11. All Dates Summary (Direct)")
    date_summary = analytics.all_dates_summary(use_mapreduce=False)
    for entry in date_summary:
        print(f"  {entry['date']} | Total: {entry['total_records']} | "
              f"Present: {entry['present']} | Absent: {entry['absent']} | "
              f"Late: {entry['late']} | Rate: {entry['attendance_rate_percent']}%")

    # ------------------------------------------------------------------
    # 7. Stored results
    # ------------------------------------------------------------------
    print_section("12. Stored Results (JSON files under ./data/)")
    import os
    data_dir = os.path.abspath("data")
    print(f"  Data directory: {data_dir}")
    for fname in ("students.json", "courses.json", "attendance.json"):
        fpath = os.path.join(data_dir, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            print(f"  {fname}: {size} bytes")

    print_header("Demo Complete")


if __name__ == "__main__":
    main()
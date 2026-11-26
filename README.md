# Student Attendance Analytics with Distributed MapReduce Engine

A modern cloud-aligned Python web application to record student attendance, compute daily and course-wise analytics, and simulate distributed MapReduce pipeline processing.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-orange.svg)](https://www.chartjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start (Web Application)

### 1. Run Locally
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/student-attendance-analytics.git
cd student-attendance-analytics

# Install dependencies
pip install -r requirements.txt

# Start the web server
python web_app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

- **Stage 1 (Front Page):** Click **"🚀 Open Web Application"**
- **Stage 2 (Login/Register):** Use default credentials (`faculty` / `admin123`) or register with simulated **Mobile SMS OTP verification**.
- **Stage 3 (Dashboard):** View interactive **Chart.js status doughnut**, **course attendance bar charts**, **quick filter chips**, and the **animated MapReduce simulation**.

---

## ☁️ 1-Click Cloud Deployment

### Deploy to Render (Free Tier)
1. Push this repository to your GitHub account.
2. Sign in to **[Render.com](https://render.com/)** and click **New + $\rightarrow$ Web Service**.
3. Select your repository `student-attendance-analytics`.
4. Configure:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python web_app.py` (or `gunicorn web_app:app`)
5. Click **Create Web Service** — Render will automatically build and host your app on a public URL (`https://your-app.onrender.com`)!

---

## 🌟 Key Features

- **3-Stage User Experience:** Clean Front Landing Page $\rightarrow$ Codehal Glassmorphism sliding auth portal with 2FA OTP $\rightarrow$ Interactive Dashboard.
- **Visual Charts (Chart.js):** Status distribution doughnut chart, course performance bar chart with risk threshold bands ($\ge 75\%$ optimal, $50-74\%$ moderate, $<50\%$ at risk).
- **Quick Filter Chips:** Instant client-side filtering (`All`, `✓ Present`, `✕ Absent`, `⏰ Late`) with live record count badges.
- **Distributed MapReduce Simulation:** Step-by-step visual execution flow tracing Mapper splits, Shuffle/Sort hash partitioner, and Reducer counts.
- **Detail Privacy Enforcement:** Complete credential and DOM table wipe on sign-out for shared university workstations.
- **Full Academic Report:** Read [`PROJECT_REPORT.md`](PROJECT_REPORT.md) for the 8-page academic dossier and rubric compliance.

## Enhancements

- **Cloud storage backends** — AWS S3, Azure Blob, GCP Cloud Storage
- **Docker containerization** — run as a containerized application
- **Terraform IaC** — provision cloud resources automatically
- **GitHub Actions CI/CD** — automated testing, building, and deployment

## Project Structure

```
student-attendance-analytics/
├── models.py          # Data models (Student, Course, AttendanceRecord)
├── storage.py         # JSON file-based storage
├── attendance_service.py  # Attendance recording business logic
├── analytics_service.py   # Aggregation (direct + MapReduce)
├── export.py           # CSV export utilities
├── demo.py             # CLI demo with sample records
├── gui.py              # Tkinter GUI application
├── requirements.txt    # (none required — stdlib only)
└── README.md           # This file
```

## Requirements

- Python 3.8+ (uses only the standard library — `dataclasses`, `json`, `uuid`, `datetime`, `collections`)

No `pip install` is needed.

## Usage

### Run the demo

```bash
cd student-attendance-analytics
python demo.py
```

### Use programmatically

```python
from datetime import date
from storage import Storage
from attendance_service import AttendanceService
from analytics_service import AnalyticsService

storage = Storage(data_dir="data")
attendance = AttendanceService(storage)
analytics = AnalyticsService(storage)

# Register
student = attendance.register_student("Alice", "alice@example.com")
course = attendance.register_course("Python 101", "CS101")

# Record attendance
attendance.record_attendance(
    student_id=student.student_id,
    course_id=course.course_id,
    att_date=date.today(),
    status="present",
)

# Daily totals (direct)
daily = analytics.daily_totals(date.today(), use_mapreduce=False)
print(daily)

# Course-wise totals (MapReduce)
course_stats = analytics.course_wise_totals(course.course_id, use_mapreduce=True)
print(course_stats)

# Average attendance rate
avg = analytics.average_attendance_rate(course_id=course.course_id)
print(f"{avg}%")
```

### Launch the Web Dashboard (Browser)

```bash
cd student-attendance-analytics
python web_app.py
```
*Or double-click `run_web.bat` or `open_local.html`!*
The web server will start on `http://localhost:5000` and automatically open your default browser.

The web application includes 5 tabs:
- **Dashboard**: Real-time stats cards (Total Students, Courses, Records, Overall Attendance Rate) and recent logs
- **Record Attendance**: Form to record new student attendance with instant updates
- **Manage**: Register new students and courses with live list tables
- **Analytics & MapReduce**: Daily and course-wise totals with toggleable MapReduce engine
- **Export**: One-click download of attendance logs and summaries as CSV files

### Run the GUI (Desktop Application)

```bash
cd student-attendance-analytics
python gui.py
```
*Or double-click `run_gui.bat`!*


**Suggested demo for your teacher:**
1. Run `python gui.py`
2. **Dashboard tab** — Show real-time stats cards (total students, courses, records, attendance rate)
3. **Record Attendance tab** — Record a new attendance entry
4. **Manage tab** — Add a new student and course
5. **Analytics tab** — View daily totals, course-wise totals, and full summary
6. **Export tab** — Export data to CSV
7. Run `python demo.py` to show the CLI output with all calculations

## MapReduce

The MapReduce-style path follows the classic pattern:

1. **Map** — each attendance record emits a `(status, 1)` pair.
2. **Shuffle/Group** — pairs are grouped by status.
3. **Reduce** — values for each status are summed.

Enable it by passing `use_mapreduce=True` to any analytics method. Both
implementations produce identical results; the MapReduce version is included
for demonstration purposes.

## Output Example

```
============================================================
  Student Attendance Analytics - Demo
============================================================

--- 1. Registering Students ---
  STU-xxxxx | Alice Johnson | alice@example.com
  STU-xxxxx | Bob Smith     | bob@example.com
  STU-xxxxx | Carol Davis   | carol@example.com
  STU-xxxxx | David Wilson  | david@example.com

--- 2. Registering Courses ---
  CRS-xxxxx | CS101 | Introduction to Python
  CRS-xxxxx | CS201 | Data Structures
  CRS-xxxxx | CS301 | Database Systems

--- 3. Recording Attendance ---
  Recorded 15 attendance entries.

--- 5. Daily Totals (Direct) ---
  Date: 2026-11-17 | Total: 7 | Present: 4 | Absent: 2 | Late: 1 | Rate: 57.14%

--- 6. Daily Totals (MapReduce) ---
  Date: 2026-11-17 | Total: 7 | Present: 4 | Absent: 2 | Late: 1 | Rate: 57.14% (method: mapreduce)

--- 7-8. Course-wise Totals ---
  CS101: Total: 8 | Present: 5 | Absent: 2 | Late: 1 | Rate: 62.5%
  CS201: Total: 3 | Present: 2 | Absent: 1 | Late: 0 | Rate: 66.67%
  CS301: Total: 4 | Present: 2 | Absent: 2 | Late: 0 | Rate: 50.0%

--- 9. Average Attendance ---
  Overall: 60.0% | CS101 (MapReduce): 62.5% | CS301 (direct): 50.0%

--- 12. Stored Results ---
  students.json: 630 bytes
  courses.json: 452 bytes
  attendance.json: 3565 bytes
============================================================
  Demo Complete
============================================================
```

## License

MIT
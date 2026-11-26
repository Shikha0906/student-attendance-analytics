"""Flask web application for Student Attendance Analytics.

Run with: python app.py
Access via: http://localhost:5000
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import date, timedelta
import os
import json
from typing import Optional, List, Dict, Any

from models import Student, Course, AttendanceRecord
from storage import Storage
from attendance_service import AttendanceService
from analytics_service import AnalyticsService

app = Flask(__name__)
storage = Storage(data_dir="data")
attendance_service = AttendanceService(storage)
analytics = AnalyticsService(storage)
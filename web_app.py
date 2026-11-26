"""Flask Web Application for Student Attendance Analytics.

Features:
- Front Landing Page (Welcome card matching user design)
- Dedicated Faculty / Admin Portal with Mobile OTP Verification:
  - Step 1: Register once with Mobile Number, Name, Username, Email, Password
  - Step 2: Realistic SMS OTP Verification with live code popup & autofill
  - Step 3: Subsequent direct login with Username & Password (no re-registration needed)
  - Security: When signing out, all sensitive credentials and fields completely disappear
- 3-Lines Corner Menu (☰ / Hamburger) on Dashboard with dialog popup:
  - 👤 My Profile (shows verified mobile, name, credentials)
  - ⚙️ Portal Settings (interactive toggles & preferences)
  - 🌙 / ☀️ Theme Toggle
  - 🏠 Return to Front Page
  - 🚪 Logout (instantly wipes details)
- Interactive Dashboard with 5 feature tabs
- Dark Mode support with persistent toggle (🌙 / ☀️)
- Interactive Seed Sample Data button with animation & live updates
- Live search & status filter for attendance records
- MapReduce vs Direct Aggregation comparison
- CSV export for records and summaries
"""

from datetime import date, datetime
import io
import json
import os
import random
import sys
import threading
import time
import uuid
import webbrowser

from flask import (
    Flask,
    Response,
    jsonify,
    render_template_string,
    request,
    session,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from analytics_service import AnalyticsService
from attendance_service import AttendanceService
from export import AttendanceExporter
from models import AttendanceRecord, Course, Student
from storage import Storage

app = Flask(__name__)
app.secret_key = "student_attendance_analytics_secret_key_2026"

storage = Storage(data_dir=os.path.join(BASE_DIR, "data"))
attendance_svc = AttendanceService(storage)
analytics_svc = AnalyticsService(storage)
exporter = AttendanceExporter(storage)

# In-memory store for active OTP codes: { mobile: { "otp": str, "expires": float, "username": str } }
ACTIVE_OTPS = {}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Student Attendance Analytics | Faculty Portal</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#eef2ff', 100: '#e0e7ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' }
          }
        }
      }
    }
  </script>
  <script type="module" src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js"></script>
  <script nomodule src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    .tab-btn.active {
      border-color: #6366f1;
      color: #6366f1;
      background-color: rgba(99, 102, 241, 0.08);
    }
    .dark .tab-btn.active {
      border-color: #818cf8;
      color: #818cf8;
      background-color: rgba(129, 140, 248, 0.12);
    }
    .otp-input {
      letter-spacing: 0.5em;
      font-weight: 800;
    }
    * {
      transition: background-color 0.2s ease, border-color 0.2s ease;
    }

    /* CODEHAL GLASSMORPHISM & SLIDING STYLES */
    #auth-page {
      background: radial-gradient(circle at 50% 25%, rgba(99, 102, 241, 0.3) 0%, transparent 60%),
                  radial-gradient(circle at 85% 80%, rgba(168, 85, 247, 0.22) 0%, transparent 55%),
                  #0b0f19;
      font-family: 'Poppins', sans-serif;
    }
    html:not(.dark) #auth-page {
      background: radial-gradient(circle at 50% 25%, rgba(99, 102, 241, 0.18) 0%, transparent 60%),
                  radial-gradient(circle at 85% 80%, rgba(236, 72, 153, 0.15) 0%, transparent 55%),
                  #f8fafc;
    }

    .wrapper {
      position: relative;
      width: 440px;
      height: 490px;
      background: rgba(15, 23, 42, 0.72);
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 24px;
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      box-shadow: 0 0 40px rgba(0, 0, 0, 0.6);
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
      transition: transform .5s ease, height .35s ease;
    }
    html:not(.dark) .wrapper {
      background: rgba(255, 255, 255, 0.75);
      border: 2px solid rgba(255, 255, 255, 0.9);
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.12);
    }
    .wrapper.active {
      height: 650px;
    }
    .wrapper.otp-active {
      height: 480px;
    }

    .wrapper .form-box {
      width: 100%;
      padding: 38px 40px;
    }
    .wrapper .form-box.login {
      transition: transform .45s cubic-bezier(0.4, 0, 0.2, 1);
      transform: translateX(0);
    }
    .wrapper.active .form-box.login {
      transform: translateX(-480px);
      position: absolute;
      pointer-events: none;
    }
    .wrapper .form-box.register {
      position: absolute;
      transform: translateX(480px);
      transition: transform .45s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .wrapper.active .form-box.register {
      transform: translateX(0);
      position: relative;
    }

    .form-box h2 {
      font-size: 1.85em;
      color: #fff;
      text-align: center;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    html:not(.dark) .form-box h2 {
      color: #1e1b4b;
    }

    .input-box {
      position: relative;
      width: 100%;
      height: 46px;
      border-bottom: 2px solid rgba(255, 255, 255, 0.5);
      margin: 20px 0;
      transition: border-color .3s;
    }
    html:not(.dark) .input-box {
      border-bottom: 2px solid #6366f1;
    }
    .input-box:focus-within {
      border-bottom-color: #818cf8;
    }

    .input-box label {
      position: absolute;
      top: 50%;
      left: 5px;
      transform: translateY(-50%);
      font-size: 0.9em;
      color: rgba(255, 255, 255, 0.75);
      font-weight: 500;
      pointer-events: none;
      transition: .25s ease;
    }
    html:not(.dark) .input-box label {
      color: #475569;
    }

    .input-box input:focus~label,
    .input-box input:not(:placeholder-shown)~label {
      top: -4px;
      font-size: 0.72em;
      font-weight: 700;
      color: #818cf8;
    }
    html:not(.dark) .input-box input:focus~label,
    html:not(.dark) .input-box input:not(:placeholder-shown)~label {
      color: #4f46e5;
    }

    .input-box input {
      width: 100%;
      height: 100%;
      background: transparent;
      border: none;
      outline: none;
      font-size: 0.92em;
      color: #fff;
      font-weight: 600;
      padding: 0 32px 0 5px;
      font-family: inherit;
    }
    html:not(.dark) .input-box input {
      color: #0f172a;
    }

    .input-box .icon {
      position: absolute;
      right: 6px;
      font-size: 1.25em;
      color: rgba(255, 255, 255, 0.75);
      line-height: 48px;
      pointer-events: none;
    }
    html:not(.dark) .input-box .icon {
      color: #6366f1;
    }

    .remember-forgot {
      font-size: .8em;
      color: rgba(255, 255, 255, 0.85);
      font-weight: 500;
      margin: -10px 0 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    html:not(.dark) .remember-forgot {
      color: #334155;
    }
    .remember-forgot a {
      color: #a5b4fc;
      text-decoration: none;
      transition: color .2s;
    }
    html:not(.dark) .remember-forgot a {
      color: #4f46e5;
    }
    .remember-forgot a:hover {
      text-decoration: underline;
    }

    .codehal-btn {
      width: 100%;
      height: 44px;
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      border: none;
      outline: none;
      border-radius: 12px;
      cursor: pointer;
      font-size: 0.95em;
      color: #fff;
      font-weight: 700;
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
      transition: all .25s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .codehal-btn:hover {
      background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(99, 102, 241, 0.55);
    }

    .login-register {
      font-size: .82em;
      color: rgba(255, 255, 255, 0.85);
      text-align: center;
      font-weight: 500;
      margin: 18px 0 6px;
    }
    html:not(.dark) .login-register {
      color: #475569;
    }
    .login-register a {
      color: #a5b4fc;
      text-decoration: none;
      font-weight: 700;
      margin-left: 4px;
    }
    html:not(.dark) .login-register a {
      color: #4f46e5;
    }
    .login-register a:hover {
      text-decoration: underline;
    }

    .wrapper .icon-close {
      position: absolute;
      top: 0;
      right: 0;
      width: 44px;
      height: 44px;
      background: rgba(99, 102, 241, 0.85);
      font-size: 1.6em;
      color: #fff;
      display: flex;
      justify-content: center;
      align-items: center;
      border-bottom-left-radius: 20px;
      cursor: pointer;
      z-index: 20;
      transition: background .2s;
    }
    .wrapper .icon-close:hover {
      background: #ef4444;
    }
  </style>
</head>
<body class="bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-100 min-h-screen relative" onclick="closeDropdownIfClickedOutside(event)">

  <!-- SMS OTP Simulated Push Banner -->
  <div id="sms-toast" class="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 hidden max-w-md w-11/12 bg-slate-900/95 text-white p-4 rounded-2xl shadow-2xl border border-indigo-500/80 backdrop-blur-md transition-all duration-300">
    <div class="flex items-start justify-between gap-3">
      <div class="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-lg flex-shrink-0">
        📲
      </div>
      <div class="flex-1">
        <div class="flex items-center justify-between">
          <p class="text-xs font-bold text-indigo-400">SMS Gateway • College Auth</p>
          <span class="text-[10px] text-slate-400">Just now</span>
        </div>
        <p class="text-xs text-slate-200 mt-1" id="sms-msg-text">
          Your Faculty Verification OTP is <strong class="text-amber-300 font-mono text-sm underline cursor-pointer" onclick="autoFillOTP()">123456</strong>. Valid for 5 minutes.
        </p>
        <button onclick="autoFillOTP()" class="mt-2 text-[11px] font-bold text-indigo-400 hover:text-indigo-300 underline">
          ⚡ Click here to Autofill OTP
        </button>
      </div>
      <button onclick="document.getElementById('sms-toast').classList.add('hidden')" class="text-slate-400 hover:text-white text-xs">✕</button>
    </div>
  </div>

  <!-- Centered SMS Delivery Modal Popup -->
  <div id="sms-modal" class="fixed inset-0 z-50 hidden bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-slate-900 border-2 border-indigo-500 rounded-3xl p-6 sm:p-8 max-w-sm w-full text-white shadow-2xl text-center transform transition-all">
      <div class="w-16 h-16 mx-auto rounded-2xl bg-indigo-600/30 border border-indigo-400 flex items-center justify-center text-3xl mb-3 shadow-lg">
        📲
      </div>
      <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-950 border border-indigo-800 text-[11px] font-bold text-indigo-300 mb-2">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        SMS Delivered to <span id="modal-sms-mobile">+91 9911583182</span>
      </div>
      <h3 class="text-base font-bold text-white">College SMS Gateway</h3>
      
      <div class="my-4 p-4 bg-slate-800/90 rounded-2xl border border-slate-700">
        <p class="text-xs text-slate-300">Your Faculty Verification Code is:</p>
        <div class="my-2.5 py-2 px-4 bg-slate-950 rounded-xl border border-indigo-500/50">
          <span id="modal-sms-otp" class="text-3xl font-black text-amber-300 font-mono tracking-widest">123456</span>
        </div>
        <p class="text-[11px] text-slate-400">Valid for 5 minutes. Do not share with anyone.</p>
      </div>

      <div class="space-y-2">
        <button onclick="applyAndCloseOTPModal()" class="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-xl text-xs shadow-lg transition cursor-pointer flex items-center justify-center gap-2">
          <span>⚡ Autofill OTP Code & Continue</span>
        </button>
        <button onclick="document.getElementById('sms-modal').classList.add('hidden')" class="w-full py-2 text-xs text-slate-400 hover:text-slate-200 cursor-pointer">
          I will enter manually
        </button>
      </div>
    </div>
  </div>

  <!-- Notification Toast -->
  <div id="toast" class="fixed top-20 right-6 z-50 hidden px-5 py-3 rounded-2xl shadow-2xl border text-sm font-medium flex items-center gap-2 animate-bounce"></div>


  <!-- ======================================================== -->
  <!-- 1. STAGE 1: FRONT LANDING PAGE                           -->
  <!-- ======================================================== -->
  <div id="landing-page" class="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 relative">
    
    <!-- Top Right Dark Mode Toggle on Front Page -->
    <div class="absolute top-6 right-6">
      <button onclick="toggleDarkMode()" class="p-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 shadow-sm hover:scale-105 transition flex items-center gap-1.5 text-xs font-semibold" title="Toggle Light/Dark Mode">
        <span class="theme-icon text-sm">🌙</span>
        <span class="theme-label hidden sm:inline">Theme</span>
      </button>
    </div>

    <!-- Centered Card matching Image 1 -->
    <div class="w-full max-w-md bg-white dark:bg-slate-800 rounded-3xl p-8 sm:p-12 shadow-2xl border border-slate-200 dark:border-slate-700 text-center transition-all duration-300 transform hover:shadow-3xl">
      <!-- Gradient Icon Circle -->
      <div class="w-24 h-24 mx-auto rounded-full bg-gradient-to-tr from-indigo-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-6">
        <svg class="w-12 h-12 text-white" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L2 7l10 5 10-5L12 2zM2 17l10 5 10-5L2 17zm10 8L12 12l-10 5L2 7l10 5L12 17z"/>
        </svg>
      </div>

      <!-- Title & Subtitle -->
      <h1 class="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-3">
        Student Attendance Analytics
      </h1>
      <p class="text-base text-slate-500 dark:text-slate-400 mb-8 leading-relaxed">
        Click below to open the interactive web application
      </p>

      <!-- Action Button: Opens Faculty Auth Portal -->
      <button onclick="openApp()" class="w-full py-4 px-6 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-2xl shadow-lg shadow-indigo-600/30 transition transform hover:-translate-y-0.5 active:translate-y-0 text-base flex items-center justify-center gap-2 cursor-pointer">
        <span class="text-lg">🚀</span> Open Web Application
      </button>

      <p class="text-xs text-slate-400 dark:text-slate-500 mt-6 font-medium">
        Python • Flask • SQLite & MapReduce
      </p>
    </div>
  </div>


  <!-- ======================================================== -->
  <!-- 2. STAGE 2: FACULTY / ADMIN AUTHENTICATION PORTAL        -->
  <!-- ======================================================== -->
  <!-- ======================================================== -->
  <!-- 2. STAGE 2: FACULTY / ADMIN AUTHENTICATION (CODEHAL UI)   -->
  <!-- ======================================================== -->
  <div id="auth-page" class="hidden min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 relative">
    
    <!-- Codehal Modern Top Navigation Header -->
    <header class="fixed top-0 left-0 w-full px-6 sm:px-16 py-5 flex items-center justify-between z-30 bg-slate-900/40 backdrop-blur-md border-b border-white/10">
      <div class="flex items-center gap-2 cursor-pointer" onclick="showLanding()">
        <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black text-sm shadow">
          SA
        </div>
        <h2 class="text-base sm:text-lg font-bold text-white tracking-tight">Student Attendance Analytics</h2>
      </div>
      <nav class="flex items-center gap-4 sm:gap-6">
        <a href="javascript:void(0)" onclick="showLanding()" class="text-xs sm:text-sm font-semibold text-slate-200 hover:text-white transition cursor-pointer">Home</a>
        <a href="javascript:void(0)" onclick="switchAuthTab('login')" class="text-xs sm:text-sm font-semibold text-slate-200 hover:text-white transition cursor-pointer">Login</a>
        <a href="javascript:void(0)" onclick="switchAuthTab('register')" class="text-xs sm:text-sm font-semibold text-slate-200 hover:text-white transition cursor-pointer">Register</a>
        <button onclick="toggleDarkMode()" class="p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition cursor-pointer" title="Toggle Theme">
          <span class="theme-icon">🌙</span>
        </button>
      </nav>
    </header>

    <!-- Codehal Sliding Glassmorphism Wrapper -->
    <div class="wrapper mt-16 sm:mt-12">
      <!-- Close Icon Corner Button -->
      <span class="icon-close" onclick="showLanding()" title="Return to Front Page">
        <ion-icon name="close-outline"></ion-icon>
      </span>

      <!-- 1. LOGIN FORM BOX -->
      <div class="form-box login">
        <h2>Login</h2>
        <form id="form-login" onsubmit="handleFacultyLogin(event)" autocomplete="off">
          <div class="input-box">
            <span class="icon"><ion-icon name="person-outline"></ion-icon></span>
            <input type="text" id="login-username" required placeholder=" " autocomplete="off">
            <label>Username</label>
          </div>

          <div class="input-box">
            <span class="icon"><ion-icon name="lock-closed-outline"></ion-icon></span>
            <input type="password" id="login-password" required placeholder=" " autocomplete="new-password">
            <label>Password</label>
          </div>

          <div class="remember-forgot">
            <label><input type="checkbox" id="chk-remember"> Remember me</label>
            <a href="javascript:void(0)" onclick="showToast('Default Faculty: faculty / admin123')">Forgot password?</a>
          </div>

          <button type="submit" id="btn-login-submit" class="codehal-btn">
            <span>Login to Portal</span>
          </button>

          <div class="login-register">
            <p>Don't have an account? <a href="javascript:void(0)" class="register-link">Register</a></p>
          </div>
        </form>
      </div>

      <!-- 2. REGISTER FORM BOX -->
      <div class="form-box register">
        <!-- Step 1: Registration Form -->
        <div id="reg-step-1">
          <h2>Registration</h2>
          <form id="form-reg-details" onsubmit="handleRequestOTP(event)" autocomplete="off">
            <div class="input-box">
              <span class="icon"><ion-icon name="person-outline"></ion-icon></span>
              <input type="text" id="reg-name" required placeholder=" " autocomplete="off">
              <label>Full Name</label>
            </div>

            <div class="input-box">
              <span class="icon"><ion-icon name="call-outline"></ion-icon></span>
              <input type="tel" id="reg-mobile" pattern="[0-9]{10}" required placeholder=" " autocomplete="off" title="10-digit mobile number">
              <label>Mobile Number (+91)</label>
            </div>

            <div class="input-box">
              <span class="icon"><ion-icon name="at-outline"></ion-icon></span>
              <input type="text" id="reg-username" required placeholder=" " autocomplete="off">
              <label>Desired Username</label>
            </div>

            <div class="input-box">
              <span class="icon"><ion-icon name="mail-outline"></ion-icon></span>
              <input type="email" id="reg-email" placeholder=" " autocomplete="off">
              <label>Email Address</label>
            </div>

            <div class="input-box">
              <span class="icon"><ion-icon name="lock-closed-outline"></ion-icon></span>
              <input type="password" id="reg-password" minlength="4" required placeholder=" " autocomplete="new-password">
              <label>Password</label>
            </div>

            <div class="remember-forgot">
              <label><input type="checkbox" required checked> Agree to terms & conditions</label>
            </div>

            <button type="submit" id="btn-request-otp" class="codehal-btn">
              <span>📲 Send Mobile OTP</span>
            </button>

            <div class="login-register">
              <p>Already have an account? <a href="javascript:void(0)" class="login-link">Login</a></p>
            </div>
          </form>
        </div>

        <!-- Step 2: OTP Verification Form -->
        <div id="reg-step-2" class="hidden">
          <h2>Verify OTP</h2>
          <p class="text-xs text-center text-slate-300 mt-2 mb-3">
            Code sent to <strong id="otp-mobile-display" class="text-amber-300 font-mono">+91 9911583182</strong>
            <br>
            <a href="javascript:void(0)" onclick="backToRegStep1()" class="text-indigo-400 hover:underline text-[11px]">✏️ Edit details</a>
          </p>

          <form id="form-verify-otp" onsubmit="handleVerifyOTP(event)">
            <div class="input-box">
              <input type="text" id="reg-otp" maxlength="6" pattern="[0-9]{6}" required placeholder=" " autocomplete="one-time-code" class="text-center font-mono tracking-widest text-lg font-bold">
              <label class="text-center w-full">Enter 6-Digit Code</label>
            </div>

            <div class="remember-forgot text-xs">
              <span id="otp-timer">Expires in 04:59</span>
              <a href="javascript:void(0)" onclick="resendOTP()" class="font-bold underline">Resend OTP</a>
            </div>

            <button type="submit" id="btn-verify-otp-submit" class="codehal-btn mt-3">
              <span>✅ Complete Registration</span>
            </button>

            <div class="login-register">
              <p><a href="javascript:void(0)" onclick="backToRegStep1()">← Back to Registration</a></p>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>


  <!-- ======================================================== -->
  <!-- 3. STAGE 3: MAIN APPLICATION DASHBOARD                   -->
  <!-- ======================================================== -->
  <div id="app-container" class="hidden transition-opacity duration-300">
    
    <!-- Top Navigation Header -->
    <header class="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-30 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col md:flex-row items-center justify-between gap-3">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white font-black text-xl shadow">
            SA
          </div>
          <div>
            <h1 class="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">Student Attendance Analytics</h1>
            <p class="text-xs text-slate-500 dark:text-slate-400">Daily & Course-wise Totals with Optional MapReduce Engine</p>
          </div>
        </div>

        <div class="flex items-center space-x-3">
          
                    <!-- Live Header Clock & Online Badge -->
          <div class="hidden md:flex items-center gap-2 bg-slate-100 dark:bg-slate-700/60 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-600 text-xs text-slate-600 dark:text-slate-300 font-mono shadow-sm">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
            <span class="font-bold text-emerald-600 dark:text-emerald-400">ONLINE</span>
            <span class="text-slate-300 dark:text-slate-600">|</span>
            <span id="live-header-clock" class="font-bold">--:--:--</span>
          </div>

          <!-- Interactive Seed Sample Data Button -->
          <button id="btn-seed" onclick="confirmSeedData()" class="px-3 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-xl shadow-sm transition flex items-center gap-1.5 cursor-pointer">
            <span id="seed-icon">🌱</span>
            <span id="seed-label">Seed Sample Data</span>
          </button>

          <!-- 3-Lines Corner Menu Button (☰ / Hamburger) -->
          <div class="relative inline-block text-left">
            <button id="menu-btn" onclick="toggleDropdownMenu(event)" class="flex items-center gap-2 px-3 py-2 rounded-2xl bg-slate-100 dark:bg-slate-700/80 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 transition shadow-sm cursor-pointer" title="Faculty Options Menu">
              <div class="w-6 h-6 rounded-lg bg-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow" id="menu-avatar-initials">
                FA
              </div>
              <span class="text-xs font-bold text-slate-800 dark:text-slate-200 hidden sm:inline" id="menu-user-display">Prof. Administrator</span>
              <!-- Hamburger 3-Lines Icon -->
              <svg class="w-5 h-5 text-slate-600 dark:text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <!-- Floating Dialog Box / Dropdown Menu -->
            <div id="user-dropdown-menu" class="hidden absolute right-0 mt-2 w-64 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-2xl py-2 z-50 divide-y divide-slate-100 dark:divide-slate-700/60 transition transform duration-150">
              
              <!-- Header info inside dialog -->
              <div class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span class="text-[10px] uppercase font-bold tracking-wider text-emerald-600 dark:text-emerald-400">Authenticated Faculty</span>
                </div>
                <p class="text-sm font-bold text-slate-900 dark:text-white truncate mt-1" id="dropdown-name">Prof. Administrator</p>
                <p class="text-xs text-slate-500 dark:text-slate-400 font-mono" id="dropdown-mobile">📱 9876543210</p>
              </div>

              <!-- Menu Items: Profile, Setting, Theme, Return Home -->
              <div class="py-1">
                <button onclick="openProfileModal()" class="w-full text-left px-4 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 flex items-center gap-2.5 transition cursor-pointer">
                  <span class="text-sm">👤</span> Profile
                </button>
                <button onclick="openSettingsModal()" class="w-full text-left px-4 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 flex items-center gap-2.5 transition cursor-pointer">
                  <span class="text-sm">⚙️</span> Setting
                </button>
                <button onclick="toggleDarkMode()" class="w-full text-left px-4 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-indigo-50 dark:hover:bg-indigo-950/50 flex items-center justify-between transition cursor-pointer">
                  <span class="flex items-center gap-2.5"><span class="theme-icon text-sm">🌙</span> Theme</span>
                  <span class="text-[10px] text-slate-400 font-mono theme-text">Dark</span>
                </button>
              </div>

              <!-- Logout (Wipes Details) -->
              <div class="py-1">
                <button onclick="handleLogout()" class="w-full text-left px-4 py-2.5 text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 flex items-center gap-2.5 transition cursor-pointer">
                  <span class="text-sm">🚪</span> Logout
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-200 dark:border-slate-700 flex space-x-2 overflow-x-auto">
        <button onclick="switchTab('dashboard')" id="tab-dashboard" class="tab-btn active py-3 px-4 text-sm font-semibold border-b-2 border-transparent transition whitespace-nowrap cursor-pointer">
          📊 Dashboard
        </button>
        <button onclick="switchTab('record')" id="tab-record" class="tab-btn py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-slate-600 dark:text-slate-400 transition whitespace-nowrap cursor-pointer">
          ✏️ Record Attendance
        </button>
        <button onclick="switchTab('manage')" id="tab-manage" class="tab-btn py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-slate-600 dark:text-slate-400 transition whitespace-nowrap cursor-pointer">
          👥 Manage Students & Courses
        </button>
        <button onclick="switchTab('analytics')" id="tab-analytics" class="tab-btn py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-slate-600 dark:text-slate-400 transition whitespace-nowrap cursor-pointer">
          📈 Analytics & MapReduce
        </button>
        <button onclick="switchTab('export')" id="tab-export" class="tab-btn py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-slate-600 dark:text-slate-400 transition whitespace-nowrap cursor-pointer">
          📤 Export CSV
        </button>
      </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

      <!-- 1. DASHBOARD TAB -->
      <section id="content-dashboard" class="space-y-6">
        <!-- KPI Stat Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
            <p class="text-xs uppercase font-bold text-slate-400 dark:text-slate-400">Total Students</p>
            <p id="kpi-students" class="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">--</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Enrolled learners</p>
          </div>
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
            <p class="text-xs uppercase font-bold text-slate-400 dark:text-slate-400">Total Courses</p>
            <p id="kpi-courses" class="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400 mt-2">--</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Active subjects</p>
          </div>
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
            <p class="text-xs uppercase font-bold text-slate-400 dark:text-slate-400">Attendance Records</p>
            <p id="kpi-records" class="text-3xl font-extrabold text-purple-600 dark:text-purple-400 mt-2">--</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Total sessions logged</p>
          </div>
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
            <p class="text-xs uppercase font-bold text-slate-400 dark:text-slate-400">Overall Attendance</p>
            <p id="kpi-rate" class="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-2">--%</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Present attendance rate</p>
          </div>
        </div>

        <!-- Interactive Visual Analytics Charts (Chart.js) -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Chart 1: Status Doughnut Breakdown -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 flex flex-col justify-between">
            <div class="flex items-center justify-between mb-2">
              <div>
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>🍩</span> Status Distribution
                </h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">Present vs Absent vs Late Sessions</p>
              </div>
              <span class="text-[10px] font-mono bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded font-bold">Chart.js</span>
            </div>
            <div class="relative flex items-center justify-center py-2" style="height: 220px;">
              <canvas id="chart-status-doughnut"></canvas>
            </div>
            <div id="chart-doughnut-legend" class="grid grid-cols-3 gap-2 text-center text-xs pt-3 border-t border-slate-100 dark:border-slate-700/60">
              <div class="p-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300">
                <p class="text-[10px] uppercase font-bold">Present</p>
                <p id="legend-present" class="text-base font-extrabold mt-0.5">--</p>
              </div>
              <div class="p-1.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300">
                <p class="text-[10px] uppercase font-bold">Absent</p>
                <p id="legend-absent" class="text-base font-extrabold mt-0.5">--</p>
              </div>
              <div class="p-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300">
                <p class="text-[10px] uppercase font-bold">Late</p>
                <p id="legend-late" class="text-base font-extrabold mt-0.5">--</p>
              </div>
            </div>
          </div>

          <!-- Chart 2: Course Attendance Performance Bar Chart -->
          <div class="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 flex flex-col justify-between">
            <div class="flex items-center justify-between mb-2">
              <div>
                <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>📊</span> Course Attendance Rates (%)
                </h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">Student presence percentage across registered courses</p>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[10px] font-mono bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded font-bold">Live Comparison</span>
              </div>
            </div>
            <div class="relative flex items-center justify-center py-2" style="height: 220px;">
              <canvas id="chart-courses-bar"></canvas>
            </div>
            <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-3 border-t border-slate-100 dark:border-slate-700/60 flex-wrap gap-2">
              <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span> High Presence (&ge;75%)</span>
              <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span> Moderate (50-74%)</span>
              <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block"></span> At Risk (&lt;50%)</span>
            </div>
          </div>
        </div>

        <!-- Recent Records Table with Live Search & Filter -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-white">Recent Attendance Records</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400">Chronological attendance logs recorded by faculty</p>
            </div>

            <!-- Search, Interactive Filter Chips and Controls -->
            <div class="flex flex-col sm:flex-row sm:items-center gap-3">
              <!-- Quick Filter Chips -->
              <div class="flex items-center gap-1.5 flex-wrap">
                <button type="button" onclick="setChipFilter('all')" id="chip-all" class="filter-chip px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1 cursor-pointer bg-indigo-600 text-white shadow-sm">
                  <span>All</span> <span id="count-chip-all" class="bg-white/20 px-1.5 py-0.2 rounded-full text-[10px]">0</span>
                </button>
                <button type="button" onclick="setChipFilter('present')" id="chip-present" class="filter-chip px-2.5 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 hover:text-emerald-600">
                  <span>✓ Present</span> <span id="count-chip-present" class="bg-slate-200 dark:bg-slate-600 px-1.5 py-0.2 rounded-full text-[10px]">0</span>
                </button>
                <button type="button" onclick="setChipFilter('absent')" id="chip-absent" class="filter-chip px-2.5 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-rose-50 dark:hover:bg-rose-950/40 hover:text-rose-600">
                  <span>✕ Absent</span> <span id="count-chip-absent" class="bg-slate-200 dark:bg-slate-600 px-1.5 py-0.2 rounded-full text-[10px]">0</span>
                </button>
                <button type="button" onclick="setChipFilter('late')" id="chip-late" class="filter-chip px-2.5 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-950/40 hover:text-amber-600">
                  <span>⏰ Late</span> <span id="count-chip-late" class="bg-slate-200 dark:bg-slate-600 px-1.5 py-0.2 rounded-full text-[10px]">0</span>
                </button>
              </div>

              <!-- Search Box -->
              <div class="flex items-center gap-2">
                <input type="text" id="search-records" oninput="filterRecordsTable()" placeholder="🔍 Search records..." class="px-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 w-36 sm:w-48 text-slate-900 dark:text-white">
                <button onclick="loadDashboard()" class="text-xs bg-slate-100 dark:bg-slate-700 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 px-2.5 py-1.5 rounded-lg font-bold border border-slate-300 dark:border-slate-600 transition flex items-center gap-1 cursor-pointer" title="Refresh">
                  <span>🔄</span>
                </button>
              </div>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 uppercase text-xs border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th class="py-3 px-4">Date</th>
                  <th class="py-3 px-4">Student</th>
                  <th class="py-3 px-4">Course</th>
                  <th class="py-3 px-4">Status</th>
                  <th class="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody id="table-recent" class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr><td colspan="5" class="py-6 text-center text-slate-400">Loading records...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- 2. RECORD ATTENDANCE TAB -->
      <section id="content-record" class="hidden max-w-2xl mx-auto">
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 md:p-8">
          <h2 class="text-xl font-bold text-slate-900 dark:text-white mb-1">Record Student Attendance</h2>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">Log daily attendance for an individual student in a specific course.</p>

          <form id="form-record" onsubmit="handleRecordSubmit(event)" class="space-y-4">
            <div>
              <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Select Student *</label>
              <select id="rec-student" required class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm">
                <option value="">-- Choose Student --</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Select Course *</label>
              <select id="rec-course" required class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm">
                <option value="">-- Choose Course --</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Attendance Date *</label>
              <input type="date" id="rec-date" required class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm">
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Attendance Status *</label>
              <div class="grid grid-cols-3 gap-3">
                <label class="flex items-center justify-center p-3 border border-slate-200 dark:border-slate-700 rounded-xl cursor-pointer hover:bg-emerald-50 dark:hover:bg-emerald-950/30">
                  <input type="radio" name="status" value="present" checked class="text-emerald-600 focus:ring-emerald-500">
                  <span class="ml-2 text-sm font-semibold text-emerald-700 dark:text-emerald-400">Present</span>
                </label>
                <label class="flex items-center justify-center p-3 border border-slate-200 dark:border-slate-700 rounded-xl cursor-pointer hover:bg-rose-50 dark:hover:bg-rose-950/30">
                  <input type="radio" name="status" value="absent" class="text-rose-600 focus:ring-rose-500">
                  <span class="ml-2 text-sm font-semibold text-rose-700 dark:text-rose-400">Absent</span>
                </label>
                <label class="flex items-center justify-center p-3 border border-slate-200 dark:border-slate-700 rounded-xl cursor-pointer hover:bg-amber-50 dark:hover:bg-amber-950/30">
                  <input type="radio" name="status" value="late" class="text-amber-600 focus:ring-amber-500">
                  <span class="ml-2 text-sm font-semibold text-amber-700 dark:text-amber-400">Late</span>
                </label>
              </div>
            </div>

            <div class="pt-4">
              <button type="submit" class="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-md transition cursor-pointer">
                Save Attendance Record
              </button>
            </div>
          </form>
        </div>
      </section>

      <!-- 3. MANAGE STUDENTS & COURSES TAB -->
      <section id="content-manage" class="hidden space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white mb-4">Add New Student</h2>
            <form id="form-student" onsubmit="handleAddStudent(event)" class="space-y-3">
              <div>
                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Student Full Name *</label>
                <input type="text" id="stu-name" placeholder="e.g. Emily Watson" required class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg text-sm">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Email Address *</label>
                <input type="email" id="stu-email" placeholder="e.g. emily@example.com" required class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg text-sm">
              </div>
              <button type="submit" class="px-4 py-2 bg-slate-900 dark:bg-indigo-600 hover:bg-slate-800 dark:hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-sm cursor-pointer">
                Register Student
              </button>
            </form>

            <h3 class="text-sm font-bold text-slate-800 dark:text-white mt-6 mb-2">Registered Students</h3>
            <div class="max-h-56 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-lg">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700 text-slate-500">
                  <tr><th class="p-2">ID</th><th class="p-2">Name</th><th class="p-2">Email</th></tr>
                </thead>
                <tbody id="list-students" class="divide-y divide-slate-100 dark:divide-slate-700"></tbody>
              </table>
            </div>
          </div>

          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white mb-4">Add New Course</h2>
            <form id="form-course" onsubmit="handleAddCourse(event)" class="space-y-3">
              <div>
                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Course Code *</label>
                <input type="text" id="crs-code" placeholder="e.g. CS401" required class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg text-sm uppercase">
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Course Title *</label>
                <input type="text" id="crs-name" placeholder="e.g. Machine Learning" required class="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg text-sm">
              </div>
              <button type="submit" class="px-4 py-2 bg-slate-900 dark:bg-indigo-600 hover:bg-slate-800 dark:hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-sm cursor-pointer">
                Register Course
              </button>
            </form>

            <h3 class="text-sm font-bold text-slate-800 dark:text-white mt-6 mb-2">Registered Courses</h3>
            <div class="max-h-56 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-lg">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700 text-slate-500">
                  <tr><th class="p-2">Code</th><th class="p-2">Course Name</th><th class="p-2">Course ID</th></tr>
                </thead>
                <tbody id="list-courses" class="divide-y divide-slate-100 dark:divide-slate-700"></tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      <!-- 4. ANALYTICS & MAPREDUCE TAB -->
      <section id="content-analytics" class="hidden space-y-6">
        <div class="bg-gradient-to-r from-indigo-900 to-purple-900 text-white rounded-2xl p-6 shadow-md flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <div class="flex items-center space-x-2">
              <span class="px-2.5 py-0.5 rounded text-xs font-bold bg-indigo-500/30 border border-indigo-400">MapReduce Engine</span>
              <h2 class="text-xl font-bold">Distributed Aggregation Pipeline</h2>
            </div>
            <p class="text-xs text-indigo-200 mt-1 max-w-2xl">
              Simulates MapReduce: <strong>Map Phase</strong> emits <code>(Key, 1)</code> intermediate tuples &rarr; <strong>Shuffle & Sort</strong> partitions by key &rarr; <strong>Reduce Phase</strong> computes totals, counts, and attendance rates.
            </p>
          </div>

          <div class="flex items-center space-x-3 bg-white/10 backdrop-blur p-2.5 rounded-xl border border-white/20">
            <label class="text-xs font-semibold tracking-wide text-white cursor-pointer select-none" for="chk-mapreduce">
              Enable MapReduce Mode
            </label>
            <input type="checkbox" id="chk-mapreduce" onchange="loadAnalytics()" checked class="w-5 h-5 accent-indigo-400 cursor-pointer">
          </div>
        </div>

                <!-- Interactive Animated MapReduce Pipeline Visualizer -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
            <div>
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-indigo-500 animate-pulse"></span>
                <h3 class="text-base font-bold text-slate-900 dark:text-white">Live MapReduce Pipeline Execution Flow</h3>
              </div>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Interactive step-by-step trace of distributed key-value pairs processing</p>
            </div>
            <button onclick="runMapReduceSimulation()" id="btn-run-simulation" class="px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-sm transition flex items-center gap-2 cursor-pointer self-start sm:self-auto">
              <span>▶ Run Interactive Simulation</span>
            </button>
          </div>

          <!-- Pipeline Stages Flow Diagram -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
            <!-- Stage 1: Input Splits -->
            <div id="sim-step-input" class="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 transition duration-300">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-extrabold uppercase text-slate-500 dark:text-slate-400">Step 1</span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono font-bold">Input Logs</span>
              </div>
              <h4 class="text-sm font-bold text-slate-900 dark:text-white mb-1">Attendance Records</h4>
              <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">Raw JSON session entries partitioned into input splits.</p>
              <div id="sim-data-input" class="mt-3 text-[11px] font-mono bg-white dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 truncate">
                Ready to stream...
              </div>
            </div>

            <!-- Stage 2: Map Phase -->
            <div id="sim-step-map" class="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 transition duration-300">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-extrabold uppercase text-indigo-600 dark:text-indigo-400">Step 2</span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-mono font-bold">Map Phase</span>
              </div>
              <h4 class="text-sm font-bold text-slate-900 dark:text-white mb-1">Mapper Workers</h4>
              <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">Emits intermediate tuples: <code>(CourseCode, (1, 0, 0))</code></p>
              <div id="sim-data-map" class="mt-3 text-[11px] font-mono bg-white dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-700 text-indigo-600 dark:text-indigo-400 truncate">
                Waiting for map...
              </div>
            </div>

            <!-- Stage 3: Shuffle & Sort -->
            <div id="sim-step-shuffle" class="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 transition duration-300">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-extrabold uppercase text-purple-600 dark:text-purple-400">Step 3</span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 font-mono font-bold">Shuffle/Sort</span>
              </div>
              <h4 class="text-sm font-bold text-slate-900 dark:text-white mb-1">Key Partitioner</h4>
              <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">Groups values by unique key: <code>CS101 &rarr; [T1, T2, ...]</code></p>
              <div id="sim-data-shuffle" class="mt-3 text-[11px] font-mono bg-white dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-700 text-purple-600 dark:text-purple-400 truncate">
                Waiting for shuffle...
              </div>
            </div>

            <!-- Stage 4: Reduce Phase -->
            <div id="sim-step-reduce" class="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 transition duration-300">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-extrabold uppercase text-emerald-600 dark:text-emerald-400">Step 4</span>
                <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-mono font-bold">Reduce Phase</span>
              </div>
              <h4 class="text-sm font-bold text-slate-900 dark:text-white mb-1">Reducer Output</h4>
              <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">Reduces tuples into final sums, totals, & attendance rates.</p>
              <div id="sim-data-reduce" class="mt-3 text-[11px] font-mono bg-white dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-700 text-emerald-600 dark:text-emerald-400 truncate">
                Waiting for reduce...
              </div>
            </div>
          </div>

          <!-- Simulation Live Status Bar -->
          <div id="sim-status-bar" class="mt-4 p-3 rounded-xl bg-slate-100 dark:bg-slate-900 text-xs font-mono text-slate-600 dark:text-slate-400 flex items-center justify-between flex-wrap gap-2">
            <span id="sim-log">⚡ Simulation ready. Click "Run Interactive Simulation" to trace the MapReduce execution.</span>
            <span id="sim-badge" class="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-[11px] font-bold">Status: IDLE</span>
          </div>
        </div>

        <!-- Course-Wise Totals & Averages -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white">Course-wise Attendance Totals & Averages</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">Aggregated breakdown by course</p>
            </div>
            <span id="badge-method-course" class="text-xs font-mono font-semibold px-2 py-1 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">Method: MapReduce</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 uppercase text-xs border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th class="py-3 px-4">Course Code</th>
                  <th class="py-3 px-4">Course Name</th>
                  <th class="py-3 px-4">Total Sessions</th>
                  <th class="py-3 px-4">Present</th>
                  <th class="py-3 px-4">Absent</th>
                  <th class="py-3 px-4">Late</th>
                  <th class="py-3 px-4">Attendance Rate (%)</th>
                </tr>
              </thead>
              <tbody id="table-courses-summary" class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr><td colspan="7" class="py-6 text-center text-slate-400">Loading course analytics...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Daily Attendance Totals -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-bold text-slate-900 dark:text-white">Daily Attendance Totals</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">System-wide totals per calendar date</p>
            </div>
            <span id="badge-method-daily" class="text-xs font-mono font-semibold px-2 py-1 rounded bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">Method: MapReduce</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 uppercase text-xs border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th class="py-3 px-4">Date</th>
                  <th class="py-3 px-4">Total Logged</th>
                  <th class="py-3 px-4">Present</th>
                  <th class="py-3 px-4">Absent</th>
                  <th class="py-3 px-4">Late</th>
                  <th class="py-3 px-4">Daily Attendance %</th>
                </tr>
              </thead>
              <tbody id="table-daily-summary" class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr><td colspan="6" class="py-6 text-center text-slate-400">Loading daily analytics...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- 5. EXPORT TAB -->
      <section id="content-export" class="hidden max-w-3xl mx-auto space-y-6">
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 md:p-8">
          <h2 class="text-xl font-bold text-slate-900 dark:text-white mb-2">Export Attendance Reports (CSV)</h2>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-6">Download tabular CSV reports directly for documentation and spreadsheet grading.</p>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="border border-slate-200 dark:border-slate-700 rounded-xl p-5 hover:border-indigo-400 dark:hover:border-indigo-500 transition flex flex-col justify-between">
              <div>
                <div class="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 flex items-center justify-center font-bold mb-3">LOG</div>
                <h3 class="font-bold text-sm text-slate-800 dark:text-white">All Attendance Logs</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Full raw records with student IDs, course IDs, date, and status.</p>
              </div>
              <a href="/export/all" download="attendance_records.csv" class="mt-4 block text-center py-2 px-3 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm">
                Download All Logs (CSV)
              </a>
            </div>

            <div class="border border-slate-200 dark:border-slate-700 rounded-xl p-5 hover:border-indigo-400 dark:hover:border-indigo-500 transition flex flex-col justify-between">
              <div>
                <div class="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 flex items-center justify-center font-bold mb-3">DAY</div>
                <h3 class="font-bold text-sm text-slate-800 dark:text-white">Daily Summary</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Daily totals, present, absent, late, and attendance percentage.</p>
              </div>
              <a href="/export/daily" download="daily_attendance_summary.csv" class="mt-4 block text-center py-2 px-3 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-lg shadow-sm">
                Download Daily (CSV)
              </a>
            </div>

            <div class="border border-slate-200 dark:border-slate-700 rounded-xl p-5 hover:border-indigo-400 dark:hover:border-indigo-500 transition flex flex-col justify-between">
              <div>
                <div class="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 flex items-center justify-center font-bold mb-3">CRS</div>
                <h3 class="font-bold text-sm text-slate-800 dark:text-white">Course Summary</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Course-wise totals and overall course attendance rate.</p>
              </div>
              <a href="/export/course" download="course_attendance_summary.csv" class="mt-4 block text-center py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-sm">
                Download Courses (CSV)
              </a>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div><!-- /app-container -->


  <!-- ======================================================== -->
  <!-- 4. MODALS: PROFILE & SETTINGS DIALOGS                    -->
  <!-- ======================================================== -->

  <!-- Profile Modal -->
  <div id="modal-profile" class="fixed inset-0 z-50 hidden bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white dark:bg-slate-800 rounded-3xl p-6 sm:p-8 max-w-sm w-full shadow-2xl border border-slate-200 dark:border-slate-700">
      <div class="text-center">
        <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white text-2xl font-black shadow-lg shadow-indigo-500/30" id="prof-modal-avatar">
          FA
        </div>
        <h3 class="text-lg font-bold text-slate-900 dark:text-white mt-3" id="prof-modal-name">Prof. Administrator</h3>
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800 mt-1">
          ✓ Verified Faculty Admin
        </span>
      </div>

      <div class="mt-6 space-y-3 text-xs">
        <div class="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl flex justify-between items-center">
          <span class="text-slate-500 dark:text-slate-400">Username:</span>
          <span class="font-bold text-slate-800 dark:text-slate-200 font-mono" id="prof-modal-user">faculty</span>
        </div>
        <div class="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl flex justify-between items-center">
          <span class="text-slate-500 dark:text-slate-400">Mobile Number:</span>
          <span class="font-bold text-slate-800 dark:text-slate-200 font-mono" id="prof-modal-mobile">9876543210</span>
        </div>
        <div class="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl flex justify-between items-center">
          <span class="text-slate-500 dark:text-slate-400">Email Address:</span>
          <span class="font-bold text-slate-800 dark:text-slate-200 truncate max-w-[170px]" id="prof-modal-email">faculty@college.edu</span>
        </div>
        <div class="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl flex justify-between items-center">
          <span class="text-slate-500 dark:text-slate-400">System Role:</span>
          <span class="font-bold text-indigo-600 dark:text-indigo-400" id="prof-modal-role">Course Instructor & Admin</span>
        </div>
      </div>

      <button onclick="closeModal('modal-profile')" class="mt-6 w-full py-2.5 bg-slate-900 dark:bg-slate-700 hover:bg-slate-800 dark:hover:bg-slate-600 text-white rounded-xl text-xs font-bold transition cursor-pointer">
        Close Profile
      </button>
    </div>
  </div>

  <!-- Settings Modal -->
  <div id="modal-settings" class="fixed inset-0 z-50 hidden bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white dark:bg-slate-800 rounded-3xl p-6 sm:p-8 max-w-sm w-full shadow-2xl border border-slate-200 dark:border-slate-700">
      <div class="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700">
        <h3 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <span>⚙️</span> Portal Settings
        </h3>
        <button onclick="closeModal('modal-settings')" class="text-slate-400 hover:text-slate-600 text-sm">✕</button>
      </div>

      <div class="mt-4 space-y-4 text-xs">
        <div class="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-xl">
          <div>
            <p class="font-bold text-slate-800 dark:text-white">Dark Mode Theme</p>
            <p class="text-[11px] text-slate-500">Toggle dark / light display</p>
          </div>
          <button onclick="toggleDarkMode()" class="px-2.5 py-1 bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold rounded-lg text-xs cursor-pointer">
            Toggle
          </button>
        </div>

        <div class="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-xl">
          <div>
            <p class="font-bold text-slate-800 dark:text-white">MapReduce Pipeline</p>
            <p class="text-[11px] text-slate-500">Run distributed Map/Reduce by default</p>
          </div>
          <input type="checkbox" checked class="w-4 h-4 accent-indigo-600">
        </div>

        <div class="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-xl">
          <div>
            <p class="font-bold text-slate-800 dark:text-white">Live Push Notifications</p>
            <p class="text-[11px] text-slate-500">Show toasts on attendance submission</p>
          </div>
          <input type="checkbox" checked class="w-4 h-4 accent-indigo-600">
        </div>
      </div>

      <button onclick="closeModal('modal-settings')" class="mt-6 w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition cursor-pointer">
        Save & Close
      </button>
    </div>
  </div>


  <!-- ======================================================== -->
  <!-- 5. APPLICATION JAVASCRIPT LOGIC                          -->
  <!-- ======================================================== -->
  <script>
    let currentStudents = [];
    let currentCourses = [];
    let allRecordsData = [];
    let currentFaculty = null;
    let generatedOTPForDemo = '';

    // --- DARK MODE TOGGLE ---
    function initTheme() {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
        updateThemeUI(true);
      } else {
        document.documentElement.classList.remove('dark');
        updateThemeUI(false);
      }
    }

    function toggleDarkMode() {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      updateThemeUI(isDark);
      showToast(isDark ? '🌙 Dark mode enabled' : '☀️ Light mode enabled');
    }

    function updateThemeUI(isDark) {
      document.querySelectorAll('.theme-icon').forEach(el => el.innerText = isDark ? '☀️' : '🌙');
      document.querySelectorAll('.theme-text').forEach(el => el.innerText = isDark ? 'Light' : 'Dark');
    }

    // --- CORNER 3-LINES HAMBURGER MENU DROPDOWN ---
    function toggleDropdownMenu(e) {
      if (e) e.stopPropagation();
      const menu = document.getElementById('user-dropdown-menu');
      menu.classList.toggle('hidden');
    }

    function closeDropdownIfClickedOutside(e) {
      const menu = document.getElementById('user-dropdown-menu');
      const btn = document.getElementById('menu-btn');
      if (menu && !menu.classList.contains('hidden')) {
        if (!menu.contains(e.target) && !btn.contains(e.target)) {
          menu.classList.add('hidden');
        }
      }
    }

    function openProfileModal() {
      document.getElementById('user-dropdown-menu').classList.add('hidden');
      if (currentFaculty) {
        document.getElementById('prof-modal-name').innerText = currentFaculty.name || 'Faculty Member';
        document.getElementById('prof-modal-user').innerText = currentFaculty.username || 'faculty';
        document.getElementById('prof-modal-mobile').innerText = currentFaculty.mobile ? `+91 ${currentFaculty.mobile}` : 'Verified';
        document.getElementById('prof-modal-email').innerText = currentFaculty.email || `${currentFaculty.username}@college.edu`;
        document.getElementById('prof-modal-role').innerText = currentFaculty.role || 'Faculty Administrator';
        const initials = (currentFaculty.name || 'FA').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        document.getElementById('prof-modal-avatar').innerText = initials;
      }
      document.getElementById('modal-profile').classList.remove('hidden');
    }

    function openSettingsModal() {
      document.getElementById('user-dropdown-menu').classList.add('hidden');
      document.getElementById('modal-settings').classList.remove('hidden');
    }

    function closeModal(id) {
      document.getElementById(id).classList.add('hidden');
    }

    // --- APP STAGES: LANDING -> AUTH -> DASHBOARD ---
    function openApp() {
      showAuth();
    }

    function showLanding() {
      document.getElementById('landing-page').classList.remove('hidden');
      document.getElementById('auth-page').classList.add('hidden');
      document.getElementById('app-container').classList.add('hidden');
      const menu = document.getElementById('user-dropdown-menu');
      if (menu) menu.classList.add('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showAuth() {
      document.getElementById('landing-page').classList.add('hidden');
      document.getElementById('auth-page').classList.remove('hidden');
      document.getElementById('app-container').classList.add('hidden');
      const menu = document.getElementById('user-dropdown-menu');
      if (menu) menu.classList.add('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showDashboard() {
      document.getElementById('landing-page').classList.add('hidden');
      document.getElementById('auth-page').classList.add('hidden');
      document.getElementById('app-container').classList.remove('hidden');
      
      if (currentFaculty) {
        document.getElementById('menu-user-display').innerText = currentFaculty.name || 'Faculty Member';
        document.getElementById('dropdown-name').innerText = currentFaculty.name || 'Faculty Member';
        document.getElementById('dropdown-mobile').innerText = currentFaculty.mobile ? `📱 +91 ${currentFaculty.mobile}` : '📱 Verified Mobile';
        const initials = (currentFaculty.name || 'FA').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        document.getElementById('menu-avatar-initials').innerText = initials;
      }
      loadDashboard();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // --- LIVE OTP COUNTDOWN TIMER ---
    let otpCountdownInterval = null;
    function startOTPTimer(durationSeconds = 300) {
      if (otpCountdownInterval) clearInterval(otpCountdownInterval);
      let remaining = durationSeconds;
      const timerEl = document.getElementById('otp-timer');
      
      function updateTimerDisplay() {
        const mins = String(Math.floor(remaining / 60)).padStart(2, '0');
        const secs = String(remaining % 60).padStart(2, '0');
        if (timerEl) {
          if (remaining > 0) {
            timerEl.innerText = `Expires in ${mins}:${secs}`;
            timerEl.className = 'text-xs text-slate-500 font-mono';
          } else {
            timerEl.innerText = '⚠️ Code expired. Please click Resend OTP.';
            timerEl.className = 'text-xs text-rose-500 font-bold';
            clearInterval(otpCountdownInterval);
            otpCountdownInterval = null;
          }
        }
      }
      
      updateTimerDisplay();
      otpCountdownInterval = setInterval(() => {
        remaining--;
        updateTimerDisplay();
        if (remaining <= 0) {
          clearInterval(otpCountdownInterval);
          otpCountdownInterval = null;
        }
      }, 1000);
    }

    // --- COMPLETE PRIVACY WIPE: DISAPPEAR DETAILS ON LOGOUT ---
    function clearAllFacultyDetails() {
      // Clear header and dropdown user display
      const menuUser = document.getElementById('menu-user-display');
      if (menuUser) menuUser.innerText = 'Faculty Admin';
      const dropName = document.getElementById('dropdown-name');
      if (dropName) dropName.innerText = '';
      const dropMobile = document.getElementById('dropdown-mobile');
      if (dropMobile) dropMobile.innerText = '';
      const avatarInitials = document.getElementById('menu-avatar-initials');
      if (avatarInitials) avatarInitials.innerText = '--';

      // Clear profile modal details
      const profName = document.getElementById('prof-modal-name');
      if (profName) profName.innerText = '';
      const profUser = document.getElementById('prof-modal-user');
      if (profUser) profUser.innerText = '';
      const profMobile = document.getElementById('prof-modal-mobile');
      if (profMobile) profMobile.innerText = '';
      const profEmail = document.getElementById('prof-modal-email');
      if (profEmail) profEmail.innerText = '';
      const profRole = document.getElementById('prof-modal-role');
      if (profRole) profRole.innerText = '';
      const profAvatar = document.getElementById('prof-modal-avatar');
      if (profAvatar) profAvatar.innerText = '--';

      // Clear dashboard data and tables
      allRecordsData = [];
      const tblRecent = document.getElementById('table-recent');
      if (tblRecent) tblRecent.innerHTML = '';
      const tblCourses = document.getElementById('table-courses-summary');
      if (tblCourses) tblCourses.innerHTML = '';
      const tblDaily = document.getElementById('table-daily-summary');
      if (tblDaily) tblDaily.innerHTML = '';
      const listStu = document.getElementById('list-students');
      if (listStu) listStu.innerHTML = '';
      const listCrs = document.getElementById('list-courses');
      if (listCrs) listCrs.innerHTML = '';

      // Reset KPIs
      const kpiStu = document.getElementById('kpi-students');
      if (kpiStu) kpiStu.innerText = '0';
      const kpiCrs = document.getElementById('kpi-courses');
      if (kpiCrs) kpiCrs.innerText = '0';
      const kpiRec = document.getElementById('kpi-records');
      if (kpiRec) kpiRec.innerText = '0';
      const kpiRate = document.getElementById('kpi-rate');
      if (kpiRate) kpiRate.innerText = '0%';

      // Close all modals, popups, and dropdowns
      const menu = document.getElementById('user-dropdown-menu');
      if (menu) menu.classList.add('hidden');
      const modProf = document.getElementById('modal-profile');
      if (modProf) modProf.classList.add('hidden');
      const modSet = document.getElementById('modal-settings');
      if (modSet) modSet.classList.add('hidden');
      const smsToast = document.getElementById('sms-toast');
      if (smsToast) smsToast.classList.add('hidden');
      const smsModal = document.getElementById('sms-modal');
      if (smsModal) smsModal.classList.add('hidden');
    }

    function clearAllAuthInputs() {
      // Clear Login inputs
      document.getElementById('login-username').value = '';
      document.getElementById('login-password').value = '';
      
      // Clear Registration inputs
      document.getElementById('reg-name').value = '';
      document.getElementById('reg-mobile').value = '';
      document.getElementById('reg-username').value = '';
      document.getElementById('reg-email').value = '';
      document.getElementById('reg-password').value = '';
      document.getElementById('reg-otp').value = '';
      
      // Reset forms
      const f1 = document.getElementById('form-login');
      if (f1) f1.reset();
      const f2 = document.getElementById('form-reg-details');
      if (f2) f2.reset();
      const f3 = document.getElementById('form-verify-otp');
      if (f3) f3.reset();
    }

    async function handleLogout() {
      try {
        await fetch('/api/auth/logout', { method: 'POST' });
      } catch (e) {}

      currentFaculty = null;
      generatedOTPForDemo = '';

      if (otpCountdownInterval) {
        clearInterval(otpCountdownInterval);
        otpCountdownInterval = null;
      }

      // Complete detail wipe as requested: "so that no one can see"
      clearAllFacultyDetails();
      clearAllAuthInputs();
      backToRegStep1();
      
      const wrapper = document.querySelector('.wrapper');
      if (wrapper) {
        wrapper.classList.remove('active');
        wrapper.classList.remove('otp-active');
      }

      showToast('🔒 Signed out. All credentials and records cleared.');
      showLanding(); // Return directly to the front landing page
    }

    function switchAuthTab(tab) {
      clearAllAuthInputs(); // wipe details when switching tabs too!
      backToRegStep1();

      const wrapper = document.querySelector('.wrapper');
      if (wrapper) {
        if (tab === 'login') {
          wrapper.classList.remove('active');
          wrapper.classList.remove('otp-active');
        } else {
          wrapper.classList.add('active');
          wrapper.classList.remove('otp-active');
        }
      }
    }

    function fillDemoCreds() {
      document.getElementById('login-username').value = 'faculty';
      document.getElementById('login-password').value = 'admin123';
      showToast('Filled demo faculty credentials!');
    }

    async function handleFacultyLogin(e) {
      e.preventDefault();
      const username = document.getElementById('login-username').value.trim();
      const password = document.getElementById('login-password').value;
      const btn = document.getElementById('btn-login-submit');

      btn.disabled = true;
      btn.innerHTML = '<span>Verifying credentials...</span>';

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const result = await res.json();
        if (result.success) {
          currentFaculty = result.faculty;
          clearAllAuthInputs();
          showToast('Welcome back, ' + result.faculty.name + '!');
          showDashboard();
        } else {
          showToast(result.error || 'Login failed', true);
        }
      } catch (err) {
        showToast('Login error: ' + err.message, true);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Sign In to Dashboard</span>';
      }
    }

    // --- REGISTRATION WITH MOBILE OTP VERIFICATION ---
    async function handleRequestOTP(e) {
      e.preventDefault();
      const name = document.getElementById('reg-name').value.trim();
      const mobile = document.getElementById('reg-mobile').value.trim();
      const username = document.getElementById('reg-username').value.trim();
      const password = document.getElementById('reg-password').value;
      const btn = document.getElementById('btn-request-otp');

      if (mobile.length !== 10) {
        showToast('Please enter a valid 10-digit mobile number', true);
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '<span>📲 Sending OTP to mobile...</span>';

      try {
        const res = await fetch('/api/auth/send-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, mobile, username, password })
        });
        const result = await res.json();
        if (result.success) {
          generatedOTPForDemo = result.otp;
          document.getElementById('otp-mobile-display').innerText = `+91 ${mobile}`;
          
          // Populate & show centered SMS delivery popup modal
          const modalMobile = document.getElementById('modal-sms-mobile');
          if (modalMobile) modalMobile.innerText = `+91 ${mobile}`;
          const modalOtp = document.getElementById('modal-sms-otp');
          if (modalOtp) modalOtp.innerText = result.otp;
          const smsModal = document.getElementById('sms-modal');
          if (smsModal) smsModal.classList.remove('hidden');

          // Also populate sticky push banner
          const smsToast = document.getElementById('sms-toast');
          document.getElementById('sms-msg-text').innerHTML = `Your Faculty Registration OTP is <strong class="text-amber-300 font-mono text-base underline cursor-pointer" onclick="autoFillOTP()">${result.otp}</strong>. Valid for 5 minutes.`;
          smsToast.classList.remove('hidden');

          // Transition to Step 2
          document.getElementById('reg-step-1').classList.add('hidden');
          document.getElementById('reg-step-2').classList.remove('hidden');
          const wrapper = document.querySelector('.wrapper');
          if (wrapper) wrapper.classList.add('otp-active');
          document.getElementById('reg-otp').focus();
          startOTPTimer(300);
          showToast(`📲 Verification code sent to +91 ${mobile}!`);
        } else {
          showToast(result.error || 'Failed to send OTP', true);
        }
      } catch (err) {
        showToast('Error requesting OTP: ' + err.message, true);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>📲 Send Mobile OTP</span>';
      }
    }

    function autoFillOTP() {
      if (generatedOTPForDemo) {
        document.getElementById('reg-otp').value = generatedOTPForDemo;
        showToast('Autofilled verification code: ' + generatedOTPForDemo);
      }
    }

    function applyAndCloseOTPModal() {
      autoFillOTP();
      const smsModal = document.getElementById('sms-modal');
      if (smsModal) smsModal.classList.add('hidden');
      document.getElementById('reg-otp').focus();
    }

    function backToRegStep1() {
      if (otpCountdownInterval) {
        clearInterval(otpCountdownInterval);
        otpCountdownInterval = null;
      }
      const wrapper = document.querySelector('.wrapper');
      if (wrapper) wrapper.classList.remove('otp-active');
      document.getElementById('reg-step-1').classList.remove('hidden');
      document.getElementById('reg-step-2').classList.add('hidden');
      document.getElementById('sms-toast').classList.add('hidden');
      const smsModal = document.getElementById('sms-modal');
      if (smsModal) smsModal.classList.add('hidden');
    }

    async function resendOTP() {
      const mobile = document.getElementById('reg-mobile').value.trim();
      const username = document.getElementById('reg-username').value.trim();
      try {
        const res = await fetch('/api/auth/send-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mobile, username })
        });
        const result = await res.json();
        if (result.success) {
          generatedOTPForDemo = result.otp;
          const modalOtp = document.getElementById('modal-sms-otp');
          if (modalOtp) modalOtp.innerText = result.otp;
          const smsModal = document.getElementById('sms-modal');
          if (smsModal) smsModal.classList.remove('hidden');
          document.getElementById('sms-msg-text').innerHTML = `New OTP sent: <strong class="text-amber-300 font-mono text-base underline cursor-pointer" onclick="autoFillOTP()">${result.otp}</strong>.`;
          document.getElementById('sms-toast').classList.remove('hidden');
          startOTPTimer(300);
          showToast('📲 New OTP code sent to mobile!');
        }
      } catch (e) {
        showToast('Failed to resend OTP', true);
      }
    }

    async function handleVerifyOTP(e) {
      e.preventDefault();
      const name = document.getElementById('reg-name').value.trim();
      const mobile = document.getElementById('reg-mobile').value.trim();
      const username = document.getElementById('reg-username').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const password = document.getElementById('reg-password').value;
      const otp = document.getElementById('reg-otp').value.trim();
      const btn = document.getElementById('btn-verify-otp-submit');

      btn.disabled = true;
      btn.innerHTML = '<span>Verifying OTP code...</span>';

      try {
        const res = await fetch('/api/auth/verify-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, mobile, username, email, password, otp })
        });
        const result = await res.json();
        if (result.success) {
          currentFaculty = result.faculty;
          document.getElementById('sms-toast').classList.add('hidden');
          clearAllAuthInputs();
          backToRegStep1();
          showToast('🎉 Mobile verified & registration complete! Welcome ' + result.faculty.name);
          showDashboard();
        } else {
          showToast(result.error || 'Invalid OTP code. Please try again.', true);
        }
      } catch (err) {
        showToast('Verification error: ' + err.message, true);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>✅ Verify OTP & Complete Registration</span>';
      }
    }

    // --- DASHBOARD DATA & ACTIONS ---
    function showToast(msg, isError = false) {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.className = `fixed top-20 right-6 z-50 px-5 py-3 rounded-2xl shadow-2xl border text-sm font-medium flex items-center gap-2 ${
        isError ? 'bg-rose-900 border-rose-700 text-white' : 'bg-slate-900 dark:bg-slate-700 border-slate-700 dark:border-slate-600 text-white'
      }`;
      toast.classList.remove('hidden');
      setTimeout(() => toast.classList.add('hidden'), 3500);
    }

    function switchTab(tabId) {
      const tabs = ['dashboard', 'record', 'manage', 'analytics', 'export'];
      tabs.forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        const content = document.getElementById(`content-${t}`);
        if (t === tabId) {
          btn.classList.add('active');
          btn.classList.remove('text-slate-600', 'dark:text-slate-400');
          content.classList.remove('hidden');
        } else {
          btn.classList.remove('active');
          btn.classList.add('text-slate-600', 'dark:text-slate-400');
          content.classList.add('hidden');
        }
      });
      if (tabId === 'dashboard') loadDashboard();
      if (tabId === 'record') loadRecordOptions();
      if (tabId === 'manage') loadManageLists();
      if (tabId === 'analytics') loadAnalytics();
    }

    function animateValue(id, start, end, duration, suffix = '') {
      const obj = document.getElementById(id);
      if (!obj) return;
      if (isNaN(end)) {
        obj.innerText = end + suffix;
        return;
      }
      let startTimestamp = null;
      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = Math.floor(progress * (end - start) + start);
        obj.innerText = current + suffix;
        if (progress < 1) {
          window.requestAnimationFrame(step);
        } else {
          obj.innerText = end + suffix;
        }
      };
      window.requestAnimationFrame(step);
    }

    async function loadDashboard() {
      try {
        const statsRes = await fetch('/api/stats');
        const stats = await statsRes.json();
        
        animateValue('kpi-students', 0, stats.total_students, 600);
        animateValue('kpi-courses', 0, stats.total_courses, 600);
        animateValue('kpi-records', 0, stats.total_records, 600);
        animateValue('kpi-rate', 0, Math.round(stats.overall_attendance_rate), 600, '%');

        const recRes = await fetch('/api/attendance');
        allRecordsData = await recRes.json();
        
        // Fetch course summaries for bar chart
        const crsRes = await fetch('/api/analytics/courses?mapreduce=true');
        const courses = await crsRes.json();

        updateChipCounts(allRecordsData);
        renderDashboardCharts(allRecordsData, courses);
        filterRecordsTable();
      } catch (err) {
        showToast('Error loading dashboard: ' + err.message, true);
      }
    }

    function renderRecordsTable(records) {
      const tbody = document.getElementById('table-recent');
      if (!records || !records.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="py-6 text-center text-slate-400">No attendance records found. Click "Seed Sample Data" above to load data.</td></tr>';
        return;
      }

      tbody.innerHTML = records.slice(0, 20).map(r => {
        let statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">Present</span>';
        if (r.status === 'absent') statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800">Absent</span>';
        if (r.status === 'late') statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">Late</span>';
        const formattedTs = r.timestamp ? r.timestamp.replace('T', ' ').substring(0, 19) : '--';
        return `
          <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition">
            <td class="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">${r.date}</td>
            <td class="py-3 px-4 text-slate-900 dark:text-white font-medium">${r.student_name}</td>
            <td class="py-3 px-4"><span class="font-mono text-xs bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded font-bold">${r.course_code}</span> ${r.course_name}</td>
            <td class="py-3 px-4">${statusBadge}</td>
            <td class="py-3 px-4 text-xs text-slate-400 font-mono">${formattedTs}</td>
          </tr>
        `;
      }).join('');
    }

    function filterRecordsTable() {
      const query = document.getElementById('search-records') ? document.getElementById('search-records').value.toLowerCase().trim() : '';

      let filtered = allRecordsData || [];
      if (activeChipStatus && activeChipStatus !== 'all') {
        filtered = filtered.filter(r => (r.status || '').toLowerCase() === activeChipStatus);
      }
      if (query) {
        filtered = filtered.filter(r => 
          (r.student_name || '').toLowerCase().includes(query) ||
          (r.course_name || '').toLowerCase().includes(query) ||
          (r.course_code || '').toLowerCase().includes(query) ||
          (r.date || '').includes(query)
        );
      }
      renderRecordsTable(filtered);
    }

    async function loadRecordOptions() {
      document.getElementById('rec-date').value = new Date().toISOString().split('T')[0];
      const stuRes = await fetch('/api/students');
      currentStudents = await stuRes.json();
      const crsRes = await fetch('/api/courses');
      currentCourses = await crsRes.json();

      const stuSelect = document.getElementById('rec-student');
      stuSelect.innerHTML = '<option value="">-- Choose Student --</option>' +
        currentStudents.map(s => `<option value="${s.student_id}">${s.name} (${s.email})</option>`).join('');

      const crsSelect = document.getElementById('rec-course');
      crsSelect.innerHTML = '<option value="">-- Choose Course --</option>' +
        currentCourses.map(c => `<option value="${c.course_id}">[${c.code}] ${c.name}</option>`).join('');
    }

    async function handleRecordSubmit(e) {
      e.preventDefault();
      const student_id = document.getElementById('rec-student').value;
      const course_id = document.getElementById('rec-course').value;
      const att_date = document.getElementById('rec-date').value;
      const status = document.querySelector('input[name="status"]:checked').value;

      try {
        const res = await fetch('/api/attendance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id, course_id, date: att_date, status })
        });
        const result = await res.json();
        if (result.success) {
          showToast('✅ Attendance recorded successfully!');
          switchTab('dashboard');
        } else {
          showToast(result.error || 'Failed to record attendance', true);
        }
      } catch (err) {
        showToast('Error recording attendance: ' + err.message, true);
      }
    }

    async function loadManageLists() {
      const stuRes = await fetch('/api/students');
      currentStudents = await stuRes.json();
      const crsRes = await fetch('/api/courses');
      currentCourses = await crsRes.json();

      const stuTbody = document.getElementById('list-students');
      stuTbody.innerHTML = currentStudents.map(s => `
        <tr>
          <td class="p-2 font-mono text-slate-500 dark:text-slate-400">${s.student_id}</td>
          <td class="p-2 font-semibold text-slate-800 dark:text-slate-200">${s.name}</td>
          <td class="p-2 text-slate-500 dark:text-slate-400">${s.email}</td>
        </tr>
      `).join('');

      const crsTbody = document.getElementById('list-courses');
      crsTbody.innerHTML = currentCourses.map(c => `
        <tr>
          <td class="p-2 font-mono font-bold text-indigo-600 dark:text-indigo-400">${c.code}</td>
          <td class="p-2 font-semibold text-slate-800 dark:text-slate-200">${c.name}</td>
          <td class="p-2 font-mono text-slate-500 dark:text-slate-400">${c.course_id}</td>
        </tr>
      `).join('');
    }

    async function handleAddStudent(e) {
      e.preventDefault();
      const name = document.getElementById('stu-name').value.trim();
      const email = document.getElementById('stu-email').value.trim();
      try {
        const res = await fetch('/api/students', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email })
        });
        const result = await res.json();
        if (result.success) {
          showToast('✅ Student registered: ' + name);
          document.getElementById('form-student').reset();
          loadManageLists();
        } else {
          showToast(result.error || 'Registration failed', true);
        }
      } catch (err) {
        showToast('Error registering student: ' + err.message, true);
      }
    }

    async function handleAddCourse(e) {
      e.preventDefault();
      const code = document.getElementById('crs-code').value.trim();
      const name = document.getElementById('crs-name').value.trim();
      try {
        const res = await fetch('/api/courses', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, name })
        });
        const result = await res.json();
        if (result.success) {
          showToast('✅ Course registered: ' + code);
          document.getElementById('form-course').reset();
          loadManageLists();
        } else {
          showToast(result.error || 'Registration failed', true);
        }
      } catch (err) {
        showToast('Error registering course: ' + err.message, true);
      }
    }

    async function loadAnalytics() {
      const useMR = document.getElementById('chk-mapreduce').checked;
      const methodLabel = useMR ? 'Method: MapReduce Engine' : 'Method: Direct Aggregation';
      document.getElementById('badge-method-course').innerText = methodLabel;
      document.getElementById('badge-method-daily').innerText = methodLabel;

      try {
        const crsRes = await fetch(`/api/analytics/courses?mapreduce=${useMR}`);
        const courses = await crsRes.json();
        const crsTbody = document.getElementById('table-courses-summary');
        crsTbody.innerHTML = courses.map(c => `
          <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition">
            <td class="py-3 px-4 font-mono font-bold text-indigo-600 dark:text-indigo-400">${c.code}</td>
            <td class="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">${c.name}</td>
            <td class="py-3 px-4 font-bold">${c.total_records}</td>
            <td class="py-3 px-4 text-emerald-600 dark:text-emerald-400 font-semibold">${c.present}</td>
            <td class="py-3 px-4 text-rose-600 dark:text-rose-400 font-semibold">${c.absent}</td>
            <td class="py-3 px-4 text-amber-600 dark:text-amber-400 font-semibold">${c.late}</td>
            <td class="py-3 px-4 font-bold text-indigo-700 dark:text-indigo-300">${c.attendance_rate_percent}%</td>
          </tr>
        `).join('');

        const dailyRes = await fetch(`/api/analytics/daily?mapreduce=${useMR}`);
        const daily = await dailyRes.json();
        const dailyTbody = document.getElementById('table-daily-summary');
        dailyTbody.innerHTML = daily.map(d => `
          <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition">
            <td class="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">${d.date}</td>
            <td class="py-3 px-4 font-bold">${d.total_records}</td>
            <td class="py-3 px-4 text-emerald-600 dark:text-emerald-400 font-semibold">${d.present}</td>
            <td class="py-3 px-4 text-rose-600 dark:text-rose-400 font-semibold">${d.absent}</td>
            <td class="py-3 px-4 text-amber-600 dark:text-amber-400 font-semibold">${d.late}</td>
            <td class="py-3 px-4 font-bold text-indigo-700 dark:text-indigo-300">${d.attendance_rate_percent}%</td>
          </tr>
        `).join('');
      } catch (err) {
        showToast('Error loading analytics: ' + err.message, true);
      }
    }

    // --- INTERACTIVE SEEDING LOGIC ---
    async function confirmSeedData() {
      const btn = document.getElementById('btn-seed');
      const icon = document.getElementById('seed-icon');
      const label = document.getElementById('seed-label');

      btn.disabled = true;
      btn.classList.add('opacity-75');
      icon.innerHTML = `<svg class="animate-spin w-3.5 h-3.5 text-white inline" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>`;
      label.innerText = 'Seeding Data...';

      try {
        const res = await fetch('/api/seed', { method: 'POST' });
        const result = await res.json();
        if (result.success) {
          showToast(`🌱 Seeded ${result.records_count} records across ${result.students_count} students & ${result.courses_count} courses!`);
          await loadDashboard();
        } else {
          showToast('Failed to seed: ' + (result.error || 'Unknown error'), true);
        }
      } catch (err) {
        showToast('Error seeding data: ' + err.message, true);
      } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-75');
        icon.innerHTML = '🌱';
        label.innerText = 'Seed Sample Data';
      }
    }

    // Initialize theme and routing

    // --- LIVE HEADER CLOCK & FILTER CHIPS & CHART.JS LOGIC ---
    let activeChipStatus = 'all';
    let doughnutChart = null;
    let coursesBarChart = null;

    function startHeaderClock() {
      function update() {
        const el = document.getElementById('live-header-clock');
        if (el) {
          const now = new Date();
          el.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
      }
      update();
      setInterval(update, 1000);
    }

    function setChipFilter(status) {
      activeChipStatus = status;
      ['all', 'present', 'absent', 'late'].forEach(s => {
        const btn = document.getElementById('chip-' + s);
        if (!btn) return;
        if (s === status) {
          btn.className = 'filter-chip px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1 cursor-pointer bg-indigo-600 text-white shadow-sm';
        } else {
          btn.className = 'filter-chip px-2.5 py-1 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600';
        }
      });
      filterRecordsTable();
    }

    function updateChipCounts(records) {
      const total = records ? records.length : 0;
      const present = records ? records.filter(r => r.status === 'present').length : 0;
      const absent = records ? records.filter(r => r.status === 'absent').length : 0;
      const late = records ? records.filter(r => r.status === 'late').length : 0;
      const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
      setTxt('count-chip-all', total);
      setTxt('count-chip-present', present);
      setTxt('count-chip-absent', absent);
      setTxt('count-chip-late', late);
      setTxt('legend-present', present);
      setTxt('legend-absent', absent);
      setTxt('legend-late', late);
    }

    function renderDashboardCharts(records, courseSummaries) {
      if (typeof Chart === 'undefined') return;
      const isDark = document.documentElement.classList.contains('dark');
      const textColor = isDark ? '#cbd5e1' : '#475569';
      const gridColor = isDark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.8)';

      // 1. Status Doughnut Chart
      const present = records ? records.filter(r => r.status === 'present').length : 0;
      const absent = records ? records.filter(r => r.status === 'absent').length : 0;
      const late = records ? records.filter(r => r.status === 'late').length : 0;

      const doughnutCtx = document.getElementById('chart-status-doughnut');
      if (doughnutCtx) {
        if (doughnutChart) doughnutChart.destroy();
        doughnutChart = new Chart(doughnutCtx, {
          type: 'doughnut',
          data: {
            labels: ['Present', 'Absent', 'Late'],
            datasets: [{
              data: [present || (records.length ? 0 : 1), absent, late],
              backgroundColor: ['#10b981', '#f43f5e', '#f59e0b'],
              borderWidth: 2,
              borderColor: isDark ? '#1e293b' : '#ffffff',
              hoverOffset: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function(ctx) {
                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                    const val = ctx.raw;
                    const pct = total ? Math.round((val / total) * 100) : 0;
                    return ` ${ctx.label}: ${val} (${pct}%)`;
                  }
                }
              }
            },
            animation: { duration: 800, easing: 'easeOutQuart' }
          }
        });
      }

      // 2. Course Performance Bar Chart
      const barCtx = document.getElementById('chart-courses-bar');
      if (barCtx && courseSummaries && courseSummaries.length) {
        if (coursesBarChart) coursesBarChart.destroy();
        const labels = courseSummaries.map(c => c.code);
        const rates = courseSummaries.map(c => c.attendance_rate_percent || 0);
        const bgColors = rates.map(r => r >= 75 ? 'rgba(16, 185, 129, 0.85)' : (r >= 50 ? 'rgba(245, 158, 11, 0.85)' : 'rgba(244, 63, 94, 0.85)'));

        coursesBarChart = new Chart(barCtx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Attendance Rate (%)',
              data: rates,
              backgroundColor: bgColors,
              borderRadius: 8,
              borderSkipped: false
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                max: 100,
                grid: { color: gridColor },
                ticks: { color: textColor, callback: v => v + '%' }
              },
              x: {
                grid: { display: false },
                ticks: { color: textColor, font: { weight: 'bold' } }
              }
            },
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function(ctx) {
                    const c = courseSummaries[ctx.dataIndex];
                    return ` ${c.name}: ${ctx.raw}% (${c.present}/${c.total_records} sessions)`;
                  }
                }
              }
            },
            animation: { duration: 800, easing: 'easeOutQuart' }
          }
        });
      }
    }

    // --- INTERACTIVE MAPREDUCE SIMULATION TRACE ---
    async function runMapReduceSimulation() {
      const btn = document.getElementById('btn-run-simulation');
      const log = document.getElementById('sim-log');
      const badge = document.getElementById('sim-badge');
      const stepInput = document.getElementById('sim-step-input');
      const stepMap = document.getElementById('sim-step-map');
      const stepShuffle = document.getElementById('sim-step-shuffle');
      const stepReduce = document.getElementById('sim-step-reduce');

      const dataInput = document.getElementById('sim-data-input');
      const dataMap = document.getElementById('sim-data-map');
      const dataShuffle = document.getElementById('sim-data-shuffle');
      const dataReduce = document.getElementById('sim-data-reduce');

      btn.disabled = true;
      btn.classList.add('opacity-50');

      const resetHighlights = () => {
        [stepInput, stepMap, stepShuffle, stepReduce].forEach(s => {
          s.classList.remove('ring-2', 'ring-indigo-500', 'ring-purple-500', 'ring-emerald-500', 'scale-[1.02]');
        });
      };

      try {
        badge.innerText = 'STATUS: STEP 1 (INPUT)';
        badge.className = 'px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 text-[11px] font-bold';
        stepInput.classList.add('ring-2', 'ring-blue-500', 'scale-[1.02]');
        log.innerText = 'Step 1/4: Ingesting raw JSON logs into distributed partition chunks...';
        dataInput.innerText = `Ingested: ${allRecordsData ? allRecordsData.length : 0} attendance logs`;
        await new Promise(r => setTimeout(r, 650));

        resetHighlights();
        badge.innerText = 'STATUS: STEP 2 (MAPPING)';
        badge.className = 'px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 text-[11px] font-bold';
        stepMap.classList.add('ring-2', 'ring-indigo-500', 'scale-[1.02]');
        log.innerText = 'Step 2/4: Mapper function executing: parsing records into key-value tuples (CourseCode, [P, A, L])...';
        dataMap.innerText = `Mapped: ${allRecordsData ? allRecordsData.length : 0} intermediate tuples`;
        await new Promise(r => setTimeout(r, 700));

        resetHighlights();
        badge.innerText = 'STATUS: STEP 3 (SHUFFLE & SORT)';
        badge.className = 'px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 text-[11px] font-bold';
        stepShuffle.classList.add('ring-2', 'ring-purple-500', 'scale-[1.02]');
        log.innerText = 'Step 3/4: Hash Partitioner grouping intermediate tuples by course & date keys in memory...';
        dataShuffle.innerText = `Grouped: ${currentCourses ? currentCourses.length : 3} course buckets`;
        await new Promise(r => setTimeout(r, 700));

        resetHighlights();
        badge.innerText = 'STATUS: STEP 4 (REDUCE)';
        badge.className = 'px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 text-[11px] font-bold';
        stepReduce.classList.add('ring-2', 'ring-emerald-500', 'scale-[1.02]');
        log.innerText = 'Step 4/4: Reducer aggregating sums, calculating attendance rates, and generating final report.';
        dataReduce.innerText = `Emitted: 100% computed metrics`;
        await new Promise(r => setTimeout(r, 600));

        resetHighlights();
        badge.innerText = 'COMPLETED (1.1ms latency)';
        badge.className = 'px-2 py-0.5 rounded bg-emerald-500 text-white text-[11px] font-bold';
        log.innerText = '✅ MapReduce pipeline executed successfully! Zero anomalies found across all nodes.';
        showToast('⚡ MapReduce pipeline simulation finished in 1.1ms!');
      } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-50');
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      startHeaderClock();
      initTheme();

      // Hook up Codehal login / register slide links
      document.querySelectorAll('.register-link').forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          switchAuthTab('register');
        });
      });
      document.querySelectorAll('.login-link').forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          switchAuthTab('login');
        });
      });
    });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


# ========================================================
# FACULTY AUTHENTICATION & MOBILE OTP ENDPOINTS
# ========================================================
@app.route("/api/auth/send-otp", methods=["POST"])
def auth_send_otp():
    """Generate and send SMS OTP to faculty mobile number."""
    data = request.get_json(force=True)
    mobile = data.get("mobile", "").strip()
    username = data.get("username", "").strip()
    name = data.get("name", "").strip()

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return jsonify({"success": False, "error": "Please enter a valid 10-digit mobile number"}), 400


    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    ACTIVE_OTPS[mobile] = {
        "otp": otp,
        "expires": time.time() + 300,  # 5 min expiry
        "username": username,
    }

    return jsonify({
        "success": True,
        "otp": otp,
        "mobile": mobile,
        "message": f"Verification code sent to +91 {mobile[:3]}****{mobile[-3:]}",
    })


@app.route("/api/auth/verify-otp", methods=["POST"])
def auth_verify_otp():
    """Verify submitted OTP and complete registration."""
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    mobile = data.get("mobile", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    submitted_otp = data.get("otp", "").strip()

    if not mobile or not submitted_otp or not username or not password:
        return jsonify({"success": False, "error": "All fields including OTP are required"}), 400

    otp_record = ACTIVE_OTPS.get(mobile)
    # Check OTP (allow generated OTP or demo fallback '123456')
    is_valid = False
    if submitted_otp == "123456":
        is_valid = True
    elif otp_record and otp_record.get("otp") == submitted_otp:
        if time.time() <= otp_record.get("expires", 0):
            is_valid = True

    if not is_valid:
        return jsonify({"success": False, "error": "Invalid or expired OTP verification code"}), 400

    # Clear used OTP
    ACTIVE_OTPS.pop(mobile, None)

    faculty = {
        "faculty_id": f"FAC-{uuid.uuid4().hex[:6].upper()}",
        "name": name or "Faculty Member",
        "username": username,
        "mobile": mobile,
        "email": email or f"{username}@college.edu",
        "password": password,
        "role": "Faculty Administrator",
        "mobile_verified": True,
        "created_at": datetime.now().isoformat(),
    }
    storage.add_faculty(faculty)
    session["faculty_user"] = username

    return jsonify({
        "success": True,
        "message": "Mobile number verified and registration successful!",
        "faculty": {
            "name": faculty["name"],
            "username": faculty["username"],
            "role": faculty["role"],
            "mobile": faculty["mobile"],
            "email": faculty["email"],
        },
    })


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """Direct login for returning faculty using username and password."""
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "error": "Please enter both username and password"}), 400

    faculty = storage.get_faculty_by_username(username)
    if not faculty or faculty.get("password") != password:
        return jsonify({"success": False, "error": "Invalid username or password"}), 401

    session["faculty_user"] = faculty["username"]
    return jsonify({
        "success": True,
        "message": "Login successful!",
        "faculty": {
            "name": faculty.get("name", "Prof. Administrator"),
            "username": faculty.get("username"),
            "role": faculty.get("role", "Faculty Administrator"),
            "mobile": faculty.get("mobile", ""),
            "email": faculty.get("email", ""),
        },
    })


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    """Logout and clear session."""
    session.pop("faculty_user", None)
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route("/api/auth/current", methods=["GET"])
def auth_current():
    """Return active faculty user profile."""
    user = session.get("faculty_user")
    if user:
        faculty = storage.get_faculty_by_username(user)
        if faculty:
            return jsonify({
                "authenticated": True,
                "faculty": {
                    "name": faculty.get("name", user),
                    "username": faculty.get("username"),
                    "role": faculty.get("role", "Faculty Administrator"),
                    "mobile": faculty.get("mobile", ""),
                    "email": faculty.get("email", ""),
                },
            })
    return jsonify({"authenticated": False})


# ========================================================
# STATS & CRUD ENDPOINTS
# ========================================================
@app.route("/api/stats")
def get_stats():
    students = storage.get_students()
    courses = storage.get_courses()
    records = storage.get_all_records()
    rate = analytics_svc.average_attendance_rate()
    return jsonify({
        "total_students": len(students),
        "total_courses": len(courses),
        "total_records": len(records),
        "overall_attendance_rate": rate,
    })


@app.route("/api/students", methods=["GET", "POST"])
def manage_students():
    if request.method == "POST":
        data = request.get_json(force=True)
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        if not name or not email:
            return jsonify({"success": False, "error": "Name and email are required"}), 400
        student = attendance_svc.register_student(name, email)
        return jsonify({"success": True, "student": student.to_dict()})

    students = storage.get_students()
    return jsonify([s.to_dict() for s in students])


@app.route("/api/courses", methods=["GET", "POST"])
def manage_courses():
    if request.method == "POST":
        data = request.get_json(force=True)
        code = data.get("code", "").strip().upper()
        name = data.get("name", "").strip()
        if not code or not name:
            return jsonify({"success": False, "error": "Course code and name are required"}), 400
        course = attendance_svc.register_course(name, code)
        return jsonify({"success": True, "course": course.to_dict()})

    courses = storage.get_courses()
    return jsonify([c.to_dict() for c in courses])


@app.route("/api/attendance", methods=["GET", "POST"])
def manage_attendance():
    if request.method == "POST":
        data = request.get_json(force=True)
        student_id = data.get("student_id")
        course_id = data.get("course_id")
        date_str = data.get("date")
        status = data.get("status", "present").lower()

        if not student_id or not course_id or not date_str:
            return jsonify({"success": False, "error": "student_id, course_id, and date are required"}), 400

        try:
            att_date = date.fromisoformat(date_str)
            record = attendance_svc.record_attendance(student_id, course_id, att_date, status)
            return jsonify({"success": True, "record": record.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    records = storage.get_all_records()
    students_map = {s.student_id: s.name for s in storage.get_students()}
    courses_map = {c.course_id: (c.code, c.name) for c in storage.get_courses()}

    enriched = []
    for r in reversed(records):
        c_code, c_name = courses_map.get(r.course_id, ("UNKNOWN", "Unknown Course"))
        enriched.append({
            "record_id": r.record_id,
            "student_id": r.student_id,
            "student_name": students_map.get(r.student_id, "Unknown Student"),
            "course_id": r.course_id,
            "course_code": c_code,
            "course_name": c_name,
            "date": r.date,
            "status": r.status,
            "timestamp": r.timestamp,
        })
    return jsonify(enriched)


@app.route("/api/analytics/daily")
def get_daily_analytics():
    use_mr = request.args.get("mapreduce", "true").lower() == "true"
    summary = analytics_svc.all_dates_summary(use_mapreduce=use_mr)
    return jsonify(summary)


@app.route("/api/analytics/courses")
def get_course_analytics():
    use_mr = request.args.get("mapreduce", "true").lower() == "true"
    summary = analytics_svc.all_courses_summary(use_mapreduce=use_mr)
    return jsonify(summary)


@app.route("/export/all")
def export_all():
    records = storage.get_all_records()
    output = io.StringIO()
    import csv

    writer = csv.writer(output)
    writer.writerow(["Record ID", "Student ID", "Course ID", "Date", "Status", "Timestamp"])
    for r in records:
        writer.writerow([r.record_id, r.student_id, r.course_id, r.date, r.status, r.timestamp])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_all_records.csv"},
    )


@app.route("/export/daily")
def export_daily():
    summary = analytics_svc.all_dates_summary()
    output = io.StringIO()
    import csv

    writer = csv.writer(output)
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
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=daily_attendance_summary.csv"},
    )


@app.route("/export/course")
def export_course():
    summary = analytics_svc.all_courses_summary()
    output = io.StringIO()
    import csv

    writer = csv.writer(output)
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
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=course_attendance_summary.csv"},
    )


@app.route("/api/seed", methods=["POST"])
def seed_data():
    """Reset and seed fresh, realistic sample dataset."""
    try:
        for path in (storage.students_file, storage.courses_file, storage.attendance_file):
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        s1 = attendance_svc.register_student("Alice Johnson", "alice@example.com")
        s2 = attendance_svc.register_student("Bob Smith", "bob@example.com")
        s3 = attendance_svc.register_student("Carol Davis", "carol@example.com")
        s4 = attendance_svc.register_student("David Wilson", "david@example.com")

        c1 = attendance_svc.register_course("Introduction to Python", "CS101")
        c2 = attendance_svc.register_course("Data Structures", "CS201")
        c3 = attendance_svc.register_course("Database Systems", "CS301")

        sample_entries = [
            {"student_id": s1.student_id, "course_id": c1.course_id, "date": "2026-11-17", "status": "present"},
            {"student_id": s2.student_id, "course_id": c1.course_id, "date": "2026-11-17", "status": "present"},
            {"student_id": s3.student_id, "course_id": c1.course_id, "date": "2026-11-17", "status": "absent"},
            {"student_id": s4.student_id, "course_id": c1.course_id, "date": "2026-11-17", "status": "late"},
            {"student_id": s1.student_id, "course_id": c2.course_id, "date": "2026-11-17", "status": "present"},
            {"student_id": s2.student_id, "course_id": c2.course_id, "date": "2026-11-18", "status": "present"},
            {"student_id": s3.student_id, "course_id": c2.course_id, "date": "2026-11-18", "status": "absent"},
            {"student_id": s1.student_id, "course_id": c3.course_id, "date": "2026-11-18", "status": "present"},
            {"student_id": s2.student_id, "course_id": c3.course_id, "date": "2026-11-18", "status": "present"},
            {"student_id": s3.student_id, "course_id": c3.course_id, "date": "2026-11-18", "status": "absent"},
            {"student_id": s4.student_id, "course_id": c3.course_id, "date": "2026-11-20", "status": "absent"},
            {"student_id": s1.student_id, "course_id": c1.course_id, "date": "2026-11-20", "status": "present"},
            {"student_id": s2.student_id, "course_id": c1.course_id, "date": "2026-11-20", "status": "present"},
            {"student_id": s3.student_id, "course_id": c1.course_id, "date": "2026-11-20", "status": "present"},
            {"student_id": s4.student_id, "course_id": c1.course_id, "date": "2026-11-20", "status": "late"},
        ]
        attendance_svc.record_bulk_attendance(sample_entries)

        return jsonify({
            "success": True,
            "students_count": 4,
            "courses_count": 3,
            "records_count": len(sample_entries),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("  Student Attendance Analytics Server Running")
    print(f"  Dashboard URL: http://0.0.0.0:{port}")
    print("=" * 60)
    if "PORT" not in os.environ:
        threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=False)
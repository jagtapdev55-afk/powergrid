# ⚡ PowerGrid — Electricity Distribution Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.14.2-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0.1-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.x-red?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Enabled-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)

**A full-stack web application simulating a real-world electricity distribution management system — modelled on how electricity boards like MSEDCL and BESCOM operate.**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [API Docs](#-rest-api) • [Screenshots](#-project-structure)

</div>

---

## 📌 About The Project

PowerGrid is an **interdisciplinary project** combining software engineering, electrical infrastructure, IoT architecture, and public administration. It provides a unified platform for consumers to manage all electricity-related services and for administrators to handle operations efficiently.

The system is **future-ready** — the REST API is designed to accept readings from real smart meters without any code changes. When a smart meter is installed, it calls the existing endpoint and the system auto-verifies the reading instantly.

---

## ✨ Features

### 👤 Consumer Portal
| Feature | Description |
|--------|-------------|
| 🔐 Register & Login | Email OTP verification on registration, CAPTCHA on login |
| 🔑 Forgot Password | Username → OTP to email → Set new password (3-step secure flow) |
| 📋 New Connection | Apply for residential, commercial, or industrial electricity connection with document upload |
| 💳 Bill Payment | Pay bills via UPI, Card, Net Banking, Cash, or Cheque |
| 📄 PDF Receipt | Download payment receipt as a branded PDF |
| 📢 Complaints | Register complaints with photo attachments across 8 categories |
| ⚡ Outage Report | Report power outages with location and affected household count |
| 📊 Meter Reading | Submit meter readings with photo upload — smart meter ready |
| 🎫 Support Tickets | Raise tickets with threaded admin replies |
| 📈 Status Timeline | Visual step-by-step progress tracker on every application |
| 🔔 Notifications | Real-time bell notifications for every status change |
| 📧 Email Alerts | HTML email notifications on every status update |
| 📱 PWA | Installable on mobile like a native app |
| ⚙️ Preferences | Toggle which emails to receive, manage multiple consumer numbers |

### 🛠️ Admin Panel
| Feature | Description |
|--------|-------------|
| ⚡ Quick Actions | Approve / Reject / Resolve per row without opening the record |
| 📦 Bulk Operations | Approve all, reject all, export CSV with one click |
| 🎨 Status Badges | Color-coded status badges on all list views |
| 📣 Announcements | Broadcast planned outage alerts to all users |
| 📬 Reminder Emails | Send reminder emails to selected consumers |
| 📊 Full Management | Manage all 14 models from one unified admin panel |

### 🌐 REST API (Smart Meter Ready)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/` | GET | API status check — public |
| `/api/meter-reading/submit/` | POST | Smart meter / device submits reading |
| `/api/meter-readings/` | GET | List meter readings |
| `/api/status/` | GET | Check any application status by reference |
| `/api/summary/` | GET | Full consumer data in one call |
| `/api/docs/` | GET | Human-readable API documentation |

---

## 🧰 Tech Stack

### Backend
- **Django 6.0.1** — Web framework (MVT pattern)
- **Python 3.14.2** — Latest stable Python
- **Django REST Framework** — REST API with serializers, throttling, authentication
- **Django Signals** — Event-driven auto email + notification on status changes
- **ReportLab** — PDF receipt generation
- **Pillow** — Image handling for meter photo upload
- **django-simple-captcha** — CAPTCHA protection on login
- **django-pwa** — Progressive Web App support
- **python-decouple** — Environment variable management

### Frontend
- Vanilla HTML5, CSS3, JavaScript
- Google Fonts (Nunito Sans, Bebas Neue, Share Tech Mono, Plus Jakarta Sans, Inter)
- Font Awesome 6.4 icons
- Custom CSS animations — green + white PowerGrid theme

### Admin
- **django-unfold** — Premium Unfold admin theme with green branding

### Authentication & Security
- Custom User Model extending `AbstractUser`
- Email OTP verification (6-digit, 10-minute expiry)
- OTP-based password reset (3-step flow)
- CAPTCHA on login/register
- API Key authentication for smart meter endpoints
- Login activity tracking (IP, user agent, timestamp)
- CSRF protection on all forms
- Passwords hashed with PBKDF2 + SHA256

### Email
- Gmail SMTP (TLS, port 587)
- 6 HTML email templates
- Async email sending (background threading — non-blocking)
- Per-user email preferences

---

## 🗄️ Database Models

```
accounts app (6 models)
├── CustomUser         — Extended user with phone, department, verification
├── EmailOTP           — OTP storage with expiry and IP tracking
├── LoginActivity      — Login history per user
├── Notification       — In-app bell notifications
├── ConsumerNumber     — Multiple consumer numbers per user
└── EmailPreference    — Per-user email toggle preferences

myapp (8 models)
├── ConnectionRequest  — New connection applications (CONN0000001)
├── BillPayment        — Bill payments (PAY0000001)
├── Complaint          — Complaints (COMP0000001)
├── PowerOutage        — Outage reports (OUT0000001)
├── MeterReading       — Meter readings (READ0000001) — smart meter ready
├── SupportTicket      — Support tickets (TICK0000001)
├── TicketReply        — Threaded replies on tickets
└── OutageAnnouncement — Admin broadcast announcements
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- pip
- Git

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/powergrid.git
cd powergrid
```

**2. Create virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements..txt
pip install djangorestframework django-simple-captcha pillow
```

**4. Create `.env` file**

Create a `.env` file in the project root (same folder as `manage.py`):
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=PowerGrid <your-email@gmail.com>
SMART_METER_API_KEY=powergrid-smart-meter-secret-2026
```

> **Gmail Setup:** Go to Google Account → Security → 2-Step Verification → App Passwords → Generate password for "Mail"

**5. Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**6. Create admin superuser**
```bash
python manage.py createsuperuser
```

**7. Collect static files**
```bash
python manage.py collectstatic
```

**8. Run the server**
```bash
python manage.py runserver
```

**9. Open in browser**
```
http://127.0.0.1:8000/          → Home page
http://127.0.0.1:8000/admin/    → Admin panel
http://127.0.0.1:8000/api/docs/ → API documentation
```

---

## 🌐 REST API

### Smart Meter Integration

The API is designed so that when a real smart meter is installed, it just calls one endpoint — no code changes needed:

```json
POST /api/meter-reading/submit/
{
  "consumer_number": "CON0000001",
  "current_reading": 1456.7,
  "previous_reading": 1411.4,
  "reading_date": "2026-04-07",
  "api_key": "powergrid-smart-meter-secret-2026",
  "source": "smart_meter",
  "device_id": "SM-MH-00123",
  "voltage": 231.4,
  "current_amp": 4.2,
  "power_factor": 0.92,
  "signal_strength": 87,
  "tamper_alert": false
}
```

**Response:**
```json
{
  "success": true,
  "reading_id": "READ0000042",
  "units_consumed": "45.30",
  "auto_verified": true,
  "message": "Reading received and auto-verified."
}
```

Smart meter readings → **auto-verified** (no admin approval needed)  
Manual readings → **pending admin verification**

---

## 📁 Project Structure

```
myproject/
├── accounts/                  # Auth app
│   ├── models.py              # CustomUser, EmailOTP, Notification, etc.
│   ├── views.py               # Register, Login, OTP, Profile, etc.
│   ├── forms.py               # RegisterForm, LoginForm
│   ├── urls.py                # accounts/* routes
│   └── templates/accounts/    # 12 HTML templates
│       ├── login.html
│       ├── register.html
│       ├── verify_otp.html
│       ├── forgot_step1.html  # Enter username
│       ├── forgot_step2.html  # Enter OTP
│       ├── forgot_step3.html  # Set new password
│       └── ...
│
├── myapp/                     # Main app
│   ├── models.py              # 8 core models
│   ├── views.py               # All service views + PDF receipt
│   ├── admin.py               # Unfold admin with quick actions
│   ├── signals.py             # Auto email + notification on status change
│   ├── forms.py               # All service forms
│   └── utils.py               # Email utilities
│
├── api/                       # REST API app
│   ├── serializers.py         # DRF serializers for all models
│   ├── views.py               # API endpoints
│   └── urls.py                # /api/* routes
│
├── templates/
│   ├── home.html              # Landing page
│   ├── dashboard/
│   │   ├── user_dashboard.html
│   │   └── my_applications.html
│   ├── services/              # 9 service page templates
│   ├── emails/                # 6 HTML email templates
│   └── api/
│       └── docs.html          # API documentation page
│
├── static/                    # CSS, JS, images
├── manage.py
└── requirements..txt
```

---

## 🔄 Application Status Flows

```
Connection Request:
  Pending → Under Review → Site Inspection → Approved → Completed
                                           ↘ Rejected

Bill Payment:
  Pending → Processing → Completed
                       ↘ Failed → Refunded

Complaint:
  Registered → Acknowledged → In Progress → Resolved → Closed
                                                      ↗ Reopened

Power Outage:
  Reported → Acknowledged → Investigating → Repairing → Resolved

Meter Reading:
  Submitted → Verified → Billed
            ↘ Rejected

Support Ticket:
  Open → In Progress → Awaiting Response → Resolved → Closed
```

---

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | True for development, False for production |
| `EMAIL_HOST_USER` | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (not your login password) |
| `DEFAULT_FROM_EMAIL` | Display name and email for outgoing mail |
| `SMART_METER_API_KEY` | API key for smart meter device authentication |

---

## 🏗️ Interdisciplinary Domains

This project integrates knowledge from **7 different fields:**

| Domain | Application |
|--------|-------------|
| 🖥️ Software Engineering | Django, REST API, database design, signals |
| ⚡ Electrical Engineering | Meter readings, voltage, power factor, smart meters |
| 🏙️ Urban Infrastructure | Power grid, outage management, area mapping |
| 💼 Business/Management | Billing workflows, complaint escalation, SLA |
| 📊 Data Science | Consumption tracking, anomaly detection potential |
| 🏛️ Public Administration | MSEDCL/BESCOM-style workflows, grievance system |
| 🌐 IoT | Smart meter architecture, MQTT awareness, API-first design |

---

## 📈 Future Scope

- [ ] Deploy on Railway / Render with PostgreSQL
- [ ] WhatsApp Bot for bill status enquiry
- [ ] WebSocket real-time admin dashboard
- [ ] Smart Meter Simulator (auto-sends readings every 15 minutes)
- [ ] Carbon Footprint Tracker per consumer
- [ ] Electricity Bill Slab Calculator
- [ ] Consumer Credit Score system
- [ ] Grievance Escalation (auto-escalate unresolved complaints after 7 days)

---

## 👨‍💻 Author

**Your Name**  
B.Tech / BCA / MCA — [Your College Name]  
[your.email@example.com]  
[LinkedIn Profile URL]  
[GitHub Profile URL]

---

## 📄 License

This project is built for educational purposes as part of a college/university project.

---

<div align="center">

**⭐ Star this repository if you found it useful!**

Made with ❤️ using Django 6.0 + Python 3.14

</div>

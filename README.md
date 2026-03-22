# Integrated Campus Management System

A Django-based web application for managing students, faculty, and administrative operations in a college or university. The system provides role-based dashboards, document management (DigiLocker), data export to Excel, and dynamic field customization.

---

## Table of Contents

- [Key Technologies](#key-technologies)
- [Directory Structure](#directory-structure)
- [Database Models](#database-models)
- [URL Routes](#url-routes)
- [Authentication & Authorization](#authentication--authorization)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)

---

## Key Technologies

| Layer | Technology |
|---|---|
| Web Framework | [Django 6.0.3](https://docs.djangoproject.com/en/6.0/) |
| Database | SQLite3 (development) |
| Frontend | Django Templates + Bootstrap |
| Excel Export | [openpyxl](https://openpyxl.readthedocs.io/) |
| Authentication | Django built-in auth (`django.contrib.auth`) |

---

## Directory Structure

```
Integrated-Campus-Management-System/
├── manage.py                          # Django CLI entry point
├── db.sqlite3                         # SQLite development database
├── static/
│   └── logo.gif                       # Application logo
├── media/
│   └── student_documents/             # Uploaded student documents
├── college_erp_final/                 # Django project configuration
│   ├── settings.py                    # Project settings
│   ├── urls.py                        # Root URL dispatcher
│   ├── asgi.py                        # ASGI server config
│   └── wsgi.py                        # WSGI server config
└── core/                              # Main Django application
    ├── models.py                      # 7 database models
    ├── views.py                       # 20+ view functions (~495 lines)
    ├── urls.py                        # Application URL patterns
    ├── admin.py                       # Django admin site registration
    ├── middleware.py                  # No-cache middleware for authenticated users
    ├── apps.py                        # App configuration
    ├── migrations/                    # Database migration files
    ├── templates/                     # 21 HTML templates
    │   ├── base.html                  # Base layout (navigation, styles)
    │   ├── login.html
    │   ├── admin_dashboard.html
    │   ├── student_dashboard.html
    │   ├── faculty_dashboard.html
    │   ├── non_teaching_dashboard.html
    │   ├── student_list.html
    │   ├── student_detail.html
    │   ├── student_full_details.html
    │   ├── student_edit.html
    │   ├── add_student.html
    │   ├── faculty_list.html
    │   ├── faculty_view.html
    │   ├── faculty_edit.html
    │   ├── add_faculty.html
    │   ├── digilocker.html
    │   ├── student_locker.html
    │   ├── export.html
    │   ├── advanced_settings.html
    │   ├── change_password.html
    │   └── programmes.html
    └── templatetags/
        └── custom_filters.py          # `clean` and `get_item` template filters
```

---

## Database Models

All models live in `core/models.py`. The schema uses Django's built-in `User` model for authentication and extends it with application-specific profiles.

```
django.contrib.auth.User
├── Student  (OneToOne)
│   ├── StudentCustomData  (ForeignKey)  ─── AppField (ForeignKey)
│   └── StudentDocument   (ForeignKey)  ─── DocumentType (ForeignKey)
└── Faculty  (OneToOne)
    └── FacultyCustomData  (ForeignKey) ─── AppField (ForeignKey)
```

### Model Reference

| Model | Purpose | Key Fields |
|---|---|---|
| `Student` | Student profile linked to a `User` | `roll_no`, `department`, `course` (UG/PG/Research), `batch`, `dob`, `aadhaar`, parent details, academic percentages, `hosteller` |
| `Faculty` | Staff profile linked to a `User` | `name`, `department`, `designation`, `staff_type` (teaching / non_teaching) |
| `AppField` | Defines a configurable display field for students or faculty | `model_type`, `internal_name`, `display_name`, `is_static` |
| `StudentCustomData` | Stores values for custom student fields | `student` (FK), `field` (FK → AppField), `value` |
| `FacultyCustomData` | Stores values for custom faculty fields | `faculty` (FK), `field` (FK → AppField), `value` |
| `DocumentType` | Names a category of student document | `name`, `is_static` |
| `StudentDocument` | An uploaded file for a student | `student` (FK), `document_type` (FK), `file`, `uploaded_at`; unique on `(student, document_type)` |

---

## URL Routes

Root dispatcher (`college_erp_final/urls.py`) sends `/admin/` to Django's built-in admin site and everything else to `core/urls.py`.

| URL | View | Description |
|---|---|---|
| `/` | `login_view` | Login page |
| `/logout/` | `logout_view` | Log out and redirect |
| `/admin-dashboard/` | `admin_dashboard` | Admin overview with system statistics |
| `/student/` | `student_dashboard` | Logged-in student's personal dashboard |
| `/faculty-dashboard/` | `faculty_dashboard` | Teaching / non-teaching staff dashboard |
| `/students/` | `student_list` | Searchable, filterable list of all students |
| `/add-student/` | `add_student` | Create a new student record |
| `/student/<id>/` | `student_detail` | Quick view of a single student |
| `/student/full/<id>/` | `student_full_details` | Complete student profile |
| `/student/<id>/edit/` | `student_edit` | Edit student information |
| `/student/<id>/delete/` | `delete_student` | Delete a student |
| `/faculty/` | `faculty_list` | List of all faculty members |
| `/faculty/add/` | `add_faculty` | Create a new faculty record |
| `/faculty/view/<id>/` | `faculty_view` | View faculty details |
| `/faculty/edit/<id>/` | `faculty_edit` | Edit faculty information |
| `/faculty/<id>/delete/` | `delete_faculty` | Delete a faculty member |
| `/departments/` | `programmes` | Department-wise student statistics |
| `/change-password/` | `change_password` | Change the current user's password |
| `/export/` | `export_view` | Configure an Excel export |
| `/export-excel/` | `export_excel` | Download the generated Excel file |
| `/digilocker/` | `digilocker` | Search for a student's document locker |
| `/digilocker/<id>/` | `student_locker` | Upload / download documents for a student |
| `/advanced/` | `advanced_settings` | Manage visible fields and document types |

---

## Authentication & Authorization

### Login Flow

`login_view` uses `django.contrib.auth.authenticate`. After a successful login the user is redirected based on their role:

```
superuser  OR  member of "Admin" group  →  admin_dashboard
hasattr(user, 'faculty')                →  faculty_dashboard
hasattr(user, 'student')               →  student_dashboard
```

### Roles and Permissions

| Role | How Detected | What They Can Access |
|---|---|---|
| **Admin / Superuser** | `user.is_superuser` or `user.groups` contains "Admin" | Everything — all students, all faculty, settings, export |
| **Teaching Faculty** | `user.faculty` exists and `staff_type == 'teaching'` | Own dashboard; students filtered to their department |
| **Non-Teaching Staff** | `user.faculty` exists and `staff_type == 'non_teaching'` | All students; DigiLocker; data export |
| **Student** | `user.student` exists | Own dashboard and own document locker only |

All views are protected with `@login_required`. Unauthorized access to admin-only pages returns `HttpResponseForbidden`.

### Default Credentials (development seed)

| Account type | Username | Password |
|---|---|---|
| Student | `<roll_no>` | `1234` |
| Faculty | auto-generated (e.g. `name123`) | `faculty123` |

### No-Cache Middleware

`core/middleware.NoCacheAuthenticatedMiddleware` adds `Cache-Control: no-cache, no-store` headers to every response for authenticated users to prevent browsers from caching sensitive pages.

---

## Key Features

### 1. Multi-Role Dashboards
Each user role sees a different dashboard on login. Admins see institution-wide statistics; teaching faculty see only their department's students; students see their own profile summary.

### 2. Student & Faculty Management
Full CRUD operations on both students and faculty with department-based filtering, a full-text search bar, and filters for gender, course type, and batch year.

### 3. DigiLocker (Document Management)
Every student has a secure document locker. Admins and non-teaching staff can upload and download files against predefined document types (marksheets, Aadhaar, PAN, Community Certificate, etc.). The `(student, document_type)` unique constraint prevents duplicate uploads.

### 4. Dynamic Field Management (`/advanced/`)
Admins can add custom fields to the student or faculty schema at runtime without database migrations. Custom values are stored in `StudentCustomData` / `FacultyCustomData` tables and are shown alongside built-in fields in all detail and edit views.

### 5. Excel Export
Administrators and non-teaching staff can download a filtered student list as an `.xlsx` file. The export page lets them choose which fields to include and filter by department or batch.

### 6. Department Statistics (`/departments/`)
Shows a breakdown of enrolled students per department, helping administrators monitor enrolment trends.

---

## Getting Started

### Prerequisites

```bash
pip install django openpyxl
```

### Setup

```bash
# Apply database migrations
python manage.py migrate

# Create a superuser (admin account)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser. Log in with the superuser credentials you just created.

> **Note:** The default settings use `DEBUG = True` and SQLite, which is suitable for local development only. For production deployment, set a strong `SECRET_KEY`, set `DEBUG = False`, configure `ALLOWED_HOSTS`, and switch to a production database.

---

## Running Tests

```bash
python manage.py test core --verbosity=2
```

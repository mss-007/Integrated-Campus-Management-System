# Integrated Campus Management System

A web-based **College ERP (Enterprise Resource Planning)** system built with Django. It provides administrators, faculty members, and students with a unified platform for managing campus data, documents, and operations.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Technologies](#key-technologies)
- [Directory Structure](#directory-structure)
- [Data Models](#data-models)
- [User Roles & Access Control](#user-roles--access-control)
- [Key Features](#key-features)
- [Setup & Installation](#setup--installation)
- [URL Reference](#url-reference)

---

## Project Overview

The system is branded as **NGMC ERP** and supports three types of users:

| Role | How they log in | What they can do |
|---|---|---|
| **Admin / Superuser** | Django `is_superuser` flag or `Admin` group | Full access to all modules |
| **Faculty** | Linked `Faculty` record | View own department's students, export data |
| **Student** | Linked `Student` record | View own profile, manage DigiLocker documents |

All users authenticate through a single login page. After login, each user is redirected to the appropriate dashboard.

---

## Key Technologies

| Technology | Purpose |
|---|---|
| **Python / Django 6.x** | Backend web framework (views, ORM, authentication) |
| **SQLite** | Default development database (`db.sqlite3`) |
| **Django Auth** | Built-in user model, sessions, password management |
| **Bootstrap 5.3** | Responsive UI components (loaded from CDN) |
| **Bootstrap Icons** | Icon set used across all templates |
| **Animate.css** | Entrance animations on cards and tables |
| **openpyxl** | Excel (`.xlsx`) file generation for data exports |
| **Django Template Language** | Server-side HTML rendering with custom template tags |

---

## Directory Structure

```
Integrated-Campus-Management-System/
├── manage.py                        # Django management entry point
├── db.sqlite3                       # SQLite database (generated after migrations)
│
├── college_erp_final/               # Django project configuration
│   ├── settings.py                  # App settings (database, installed apps, media/static)
│   ├── urls.py                      # Root URL dispatcher (includes core.urls)
│   ├── wsgi.py                      # WSGI deployment entry point
│   └── asgi.py                      # ASGI deployment entry point
│
├── core/                            # Main Django application
│   ├── models.py                    # All database models
│   ├── views.py                     # All view functions (business logic)
│   ├── urls.py                      # URL patterns for the core app
│   ├── admin.py                     # Django admin registrations
│   ├── apps.py                      # App configuration
│   ├── tests.py                     # Test file (scaffold only)
│   │
│   ├── templates/                   # HTML templates (Django Template Language)
│   │   ├── base.html                # Base layout: sidebar, dark mode, JS helpers
│   │   ├── login.html               # Login page
│   │   ├── admin_dashboard.html     # Admin home with summary stats
│   │   ├── faculty_dashboard.html   # Faculty home
│   │   ├── student_dashboard.html   # Student home
│   │   ├── student_list.html        # Searchable/filterable student table
│   │   ├── add_student.html         # Add student form
│   │   ├── student_detail.html      # Student brief profile view
│   │   ├── student_full_details.html# Student complete profile view
│   │   ├── student_edit.html        # Edit student data
│   │   ├── faculty_list.html        # Faculty table
│   │   ├── add_faculty.html         # Add faculty form
│   │   ├── faculty_view.html        # Faculty profile view
│   │   ├── faculty_edit.html        # Edit faculty data
│   │   ├── programmes.html          # Department-level statistics
│   │   ├── digilocker.html          # Admin/student document hub
│   │   ├── student_locker.html      # Per-student document upload/view
│   │   ├── export.html              # Export configuration form
│   │   ├── advanced_settings.html   # Manage field labels and custom fields
│   │   └── change_password.html     # Password change form
│   │
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── custom_filters.py        # `clean` and `get_item` template filters
│   │
│   └── migrations/                  # Auto-generated database migrations
│       ├── 0001_initial.py
│       ├── 0002_documenttype_studentdocument.py
│       └── 0003_faculty_user.py
│
└── static/
    └── logo.gif                     # Application logo shown in the sidebar
```

---

## Data Models

All models are defined in `core/models.py`.

### `Student`
Represents a student record, linked one-to-one with Django's built-in `User`.

Key fields: `roll_no`, `name`, `department`, `admission_year`, `course` (UG / PG / Research), `batch`, `dob`, `gender`, `blood_group`, `phone`, `email`, `aadhaar`, parent details, academic history (`tenth_percentage`, `twelfth_percentage`), `hosteller`, `physically_challenged`.

### `Faculty`
Represents a staff member, optionally linked one-to-one with a `User`.

Key fields: `name`, `department`, `designation`, `staff_type` (teaching / non-teaching).

### `AppField`
Stores metadata for every field visible in the UI, enabling admins to rename labels or add custom fields.

Key fields: `model_type` (student / faculty), `internal_name`, `display_name`, `is_static`.

### `StudentCustomData` / `FacultyCustomData`
Key-value stores that hold values for dynamically added (non-static) fields.

Key fields: `student` / `faculty` (FK), `field` (FK → `AppField`), `value`.

### `DocumentType`
Defines the categories of documents available in DigiLocker (e.g., "10th Marksheet", "Aadhaar Card").

Key fields: `name`, `is_static`.

### `StudentDocument`
Stores the actual uploaded files for a student's DigiLocker.

Key fields: `student` (FK), `document_type` (FK), `file` (stored under `media/student_documents/`), `uploaded_at`.

---

## User Roles & Access Control

Access is enforced at the view level using Django's `@login_required` decorator plus explicit role checks.

| View / Feature | Admin | Faculty | Student |
|---|:---:|:---:|:---:|
| Admin dashboard | ✅ | ❌ | ❌ |
| Student list & search | ✅ | ✅ (own dept only) | ❌ |
| Add / edit / delete student | ✅ | ❌ | ❌ |
| Student full profile | ✅ | ✅ (own dept) | ✅ (own profile) |
| Faculty list & search | ✅ | ❌ | ❌ |
| Add / edit / delete faculty | ✅ | ❌ | ❌ |
| Departments overview | ✅ | ❌ | ❌ |
| Advanced field settings | ✅ | ❌ | ❌ |
| Export to Excel | ✅ | ✅ (own dept students) | ❌ |
| DigiLocker admin hub | ✅ | ❌ (redirected) | ❌ |
| Student DigiLocker | ✅ | ✅ (view only) | ✅ (own, upload/delete) |
| Change password | ✅ | ✅ | ✅ |

---

## Key Features

### 1. Role-Based Dashboards
Each role sees a tailored dashboard after login:
- **Admin**: Summary statistics (total students, gender breakdown, department count, teaching vs. non-teaching faculty).
- **Faculty**: Department info, count of students in the faculty's department, and any custom field values.
- **Student**: Personal profile overview.

### 2. Student & Faculty Management
Full CRUD (Create, Read, Update, Delete) for both entities. Student records use `roll_no` as the Django username with a default password of `1234`. Faculty usernames are auto-generated from the name with a random suffix.

### 3. Dynamic Field System (Advanced Settings)
Admins can rename display labels for any standard field or create new custom fields for students or faculty. Custom field values are stored in `StudentCustomData` / `FacultyCustomData`.

### 4. DigiLocker
A per-student document vault. Students can upload and delete files in named categories (10th Marksheet, Aadhaar Card, etc.). Admins can view all documents; faculty can view (not modify) documents for students in their department.

### 5. Excel Export
Admins and faculty can select any combination of student (or, for admins, faculty) fields and export the filtered result as a downloadable `.xlsx` file powered by `openpyxl`.

### 6. Programmes / Departments
A department-level summary page showing total enrolment, gender breakdown, and faculty count per department.

### 7. Dark Mode
A client-side dark mode toggle is available across all pages. The preference is persisted in `localStorage`.

### 8. Responsive Sidebar
The sidebar collapses on mobile screens and can be manually toggled on all screen sizes.

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/mss-007/Integrated-Campus-Management-System.git
cd Integrated-Campus-Management-System

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install django openpyxl

# 4. Apply database migrations
python manage.py migrate

# 5. Create an admin superuser
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Then open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser and log in with the superuser credentials.

> **Note:** The default student password is `1234` and the default faculty password is `faculty123`. These should be changed after first login.

---

## URL Reference

All URLs are defined in `core/urls.py` and mounted at the site root in `college_erp_final/urls.py`.

| URL | View Function | Description |
|---|---|---|
| `/` | `login_view` | Login page |
| `/admin-dashboard/` | `admin_dashboard` | Admin home |
| `/student/` | `student_dashboard` | Student home |
| `/faculty-dashboard/` | `faculty_dashboard` | Faculty home |
| `/students/` | `student_list` | Searchable student list |
| `/add-student/` | `add_student` | Add a new student |
| `/student/<id>/` | `student_detail` | Brief student profile |
| `/student/full/<id>/` | `student_full_details` | Full student profile |
| `/student/<id>/edit/` | `student_edit` | Edit student data |
| `/student/<id>/delete/` | `delete_student` | Delete a student |
| `/faculty/` | `faculty_list` | Faculty list |
| `/faculty/add/` | `add_faculty` | Add a new faculty member |
| `/faculty/view/<id>/` | `faculty_view` | Faculty profile |
| `/faculty/edit/<id>/` | `faculty_edit` | Edit faculty data |
| `/faculty/<id>/delete/` | `delete_faculty` | Delete a faculty member |
| `/departments/` | `programmes` | Department statistics |
| `/advanced/` | `advanced_settings` | Field & document type configuration |
| `/export/` | `export_view` | Export configuration form |
| `/export-excel/` | `export_excel` | Trigger Excel download |
| `/digilocker/` | `digilocker` | DigiLocker hub (admin) |
| `/digilocker/<id>/` | `student_locker` | Per-student DigiLocker |
| `/change-password/` | `change_password` | Change password |
| `/logout/` | `logout_view` | Log out |
| `/admin/` | Django admin | Built-in Django admin panel |

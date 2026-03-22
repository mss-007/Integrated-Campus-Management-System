# Integrated Campus Management System

A Django-based campus ERP (Enterprise Resource Planning) system for managing students, faculty, departments, and documents in a college environment.

---

## Table of Contents

- [Key Technologies](#key-technologies)
- [Project Structure](#project-structure)
- [Data Models](#data-models)
- [URL Routes & Views](#url-routes--views)
- [Role-Based Access Control](#role-based-access-control)
- [Features](#features)
- [Templates](#templates)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)

---

## Key Technologies

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 6.0.3 |
| Database | SQLite (development default) |
| Frontend CSS | Bootstrap 5.3.3 |
| Icons | Bootstrap Icons |
| Animations | Animate.css 4.1.1 |
| Excel Export | openpyxl |
| Auth | Django built-in (`django.contrib.auth`) |

---

## Project Structure

```
Integrated-Campus-Management-System/
├── manage.py                      # Django management entry point
├── college_erp_final/             # Project configuration package
│   ├── settings.py                # Django settings (DB, installed apps, middleware, static/media)
│   ├── urls.py                    # Root URL configuration (delegates to core.urls)
│   ├── wsgi.py                    # WSGI deployment entry point
│   └── asgi.py                    # ASGI deployment entry point
├── core/                          # Single Django application (all business logic lives here)
│   ├── models.py                  # 7 data models (Student, Faculty, etc.)
│   ├── views.py                   # ~20 view functions
│   ├── urls.py                    # URL patterns for the core app
│   ├── admin.py                   # Django admin registrations
│   ├── middleware.py              # Custom no-cache middleware
│   ├── apps.py                    # App configuration
│   ├── tests.py                   # Test module
│   ├── migrations/                # Database migration files
│   │   ├── 0001_initial.py
│   │   ├── 0002_documenttype_studentdocument.py
│   │   └── 0003_faculty_user.py
│   ├── templates/                 # 21 HTML templates (Django template language)
│   │   ├── base.html              # Base layout with sidebar, dark mode, navigation
│   │   ├── login.html
│   │   ├── admin_dashboard.html
│   │   ├── faculty_dashboard.html
│   │   ├── non_teaching_dashboard.html
│   │   ├── student_dashboard.html
│   │   ├── student_list.html
│   │   ├── student_detail.html
│   │   ├── student_full_details.html
│   │   ├── student_edit.html
│   │   ├── add_student.html
│   │   ├── faculty_list.html
│   │   ├── faculty_view.html
│   │   ├── faculty_edit.html
│   │   ├── add_faculty.html
│   │   ├── digilocker.html
│   │   ├── student_locker.html
│   │   ├── programmes.html
│   │   ├── export.html
│   │   ├── advanced_settings.html
│   │   └── change_password.html
│   └── templatetags/
│       └── custom_filters.py      # `clean` and `get_item` template filters
└── static/
    └── logo.gif                   # Application logo
```

---

## Data Models

All models are defined in `core/models.py`. The application uses Django's built-in `User` model for authentication and links custom profiles to it.

### `Student`
Represents a student record. Linked one-to-one to a `User` account (username = roll number, default password = `1234`).

Key fields: `name`, `roll_no`, `department`, `admission_year`, `course` (UG/PG/Research), `batch`, `gender`, `dob`, `blood_group`, `aadhaar`, contact details, parent/guardian info, academic percentages (10th, 12th), `hosteller`, `physically_challenged`.

### `Faculty`
Represents a faculty or staff member. Linked one-to-one to a `User` account (default password = `faculty123`).

Key fields: `name`, `department`, `designation`, `staff_type` (`teaching` or `non_teaching`).

### `AppField`
Stores field configuration for Student and Faculty models. Supports two purposes:
1. **Label customization** (`is_static=True`): Admin can rename the display labels of existing fields (e.g., rename "Roll No" to "Enrollment Number").
2. **Custom fields** (`is_static=False`): Admin can add entirely new data fields beyond the built-in model fields.

### `StudentCustomData`
Stores values for custom (non-static) `AppField` entries for a specific student. Acts as a key-value extension to the `Student` model.

### `FacultyCustomData`
Same pattern as `StudentCustomData`, but for faculty members.

### `DocumentType`
Defines categories of documents (e.g., "10th Marksheet", "Aadhaar Card"). Static types are pre-seeded and cannot be deleted. Admins can add custom types.

### `StudentDocument`
Stores file uploads for a student per document type. Each `(student, document_type)` pair is unique — uploading a new file for the same type replaces the previous one. Files are saved to `media/student_documents/`.

---

## URL Routes & Views

All routes are defined in `core/urls.py`. Below is a summary:

| URL Pattern | View | Description |
|-------------|------|-------------|
| `/` | `login_view` | Login page; redirects based on role after login |
| `/logout/` | `logout_view` | Logs out and redirects to login |
| `/admin-dashboard/` | `admin_dashboard` | Admin home with statistics |
| `/student/` | `student_dashboard` | Student's own profile page |
| `/faculty-dashboard/` | `faculty_dashboard` | Teaching/non-teaching staff home |
| `/students/` | `student_list` | Searchable and filterable list of students |
| `/add-student/` | `add_student` | Form to create a new student |
| `/student/<id>/` | `student_detail` | Summary view of a student's details |
| `/student/full/<id>/` | `student_full_details` | Full detail view including custom fields |
| `/student/<id>/edit/` | `student_edit` | Edit student details |
| `/student/<id>/delete/` | `delete_student` | Delete a student and their user account |
| `/faculty/` | `faculty_list` | Searchable list of faculty members |
| `/faculty/add/` | `add_faculty` | Form to create a new faculty member |
| `/faculty/view/<id>/` | `faculty_view` | View faculty details |
| `/faculty/edit/<id>/` | `faculty_edit` | Edit faculty details |
| `/faculty/<id>/delete/` | `delete_faculty` | Delete a faculty member and their user account |
| `/departments/` | `programmes` | Department-wise student/faculty statistics |
| `/digilocker/` | `digilocker` | Search students to access their document locker |
| `/digilocker/<id>/` | `student_locker` | Upload/view/delete documents for a student |
| `/export/` | `export_view` | Configure data export options |
| `/export-excel/` | `export_excel` | Download selected fields as an `.xlsx` file |
| `/advanced/` | `advanced_settings` | Manage field labels, custom fields, document types |
| `/change-password/` | `change_password` | Password change form for any logged-in user |

### Helper Functions in `views.py`

- **`ensure_static_fields()`** — Seeds `AppField` and `DocumentType` tables with default entries on first use.
- **`get_app_fields(model_type)`** — Returns a label map and list of custom fields for a given model type, used by edit/add views.

---

## Role-Based Access Control

Access is enforced inside each view function using Django's `@login_required` decorator and manual group/profile checks.

| Role | How Identified | Access Level |
|------|---------------|-------------|
| **Admin** | `user.is_superuser` or member of `"Admin"` group | Full access to all features |
| **Teaching Faculty** | `user.faculty` exists and `staff_type == "teaching"` | Student list/details scoped to their department; can export their department's data |
| **Non-Teaching Staff** | `user.faculty` exists and `staff_type == "non_teaching"` | Read-only access to all students across departments, DigiLocker search, export |
| **Student** | `user.student` exists | Own profile and document locker only; cannot access student list or other students |

Login routing logic (in `login_view`):
1. Admin → `/admin-dashboard/`
2. Faculty (any type) → `/faculty-dashboard/`
3. Student → `/student/`

---

## Features

### Dynamic Field Labels & Custom Fields (`/advanced/`)
Admins can rename the display labels of any built-in student or faculty field. They can also add entirely new custom fields. Custom field values are stored in `StudentCustomData` / `FacultyCustomData`.

### DigiLocker (`/digilocker/`)
A document management system per student. Pre-configured document types (marksheets, ID proofs, certificates) are shown as a checklist. Students and admins can upload, view, and delete documents. Non-teaching staff can view but not upload/delete.

### Excel Export (`/export-excel/`)
Any faculty or admin can export student or faculty data to an `.xlsx` file. Users select which fields to include and can filter by department. Built using `openpyxl`.

### Dark Mode
A dark/light mode toggle is available on all pages. The preference is saved in `localStorage` and applied via a CSS class swap on `<body>`.

### No-Cache Middleware
`core/middleware.py` defines `NoCacheAuthenticatedMiddleware`, which adds `no-cache` headers to all responses for authenticated users, preventing the browser back-button from displaying stale authenticated pages.

---

## Templates

All templates extend `base.html`, which provides:
- A fixed sidebar with role-aware navigation links
- A top navbar with the college logo, page title, dark mode toggle, and logout button
- Bootstrap 5 layout and responsive grid
- Global CSS for sidebar, cards, buttons, and dark mode overrides

Custom template filters are available via `{% load custom_filters %}`:
- `{{ value|clean }}` — Returns `"-"` for `None` or empty string values
- `{{ dict|get_item:key }}` — Dictionary key lookup in templates

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

# Create a superuser (Admin account)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

Then open `http://127.0.0.1:8000/` in your browser.

### Default Credentials for Seeded Accounts

- **Students**: Username = roll number, Password = `1234`
- **Faculty**: Username = auto-generated (shown on creation), Password = `faculty123`
- All users should change their password after first login via `/change-password/`

---

## Running Tests

```bash
python manage.py test core --verbosity=2
```

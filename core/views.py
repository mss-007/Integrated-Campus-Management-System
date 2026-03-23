from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.db import models
from django.db.models import Count, Q
from openpyxl import Workbook
import random
from django.contrib.auth import logout
from .models import Student, Faculty, AppField, StudentCustomData, FacultyCustomData, DocumentType, StudentDocument

def ensure_static_fields():
    if AppField.objects.count() == 0:
        # 🔥 UPDATED: Added new split fields and removed old 'name' field
        student_static = [
            'first_name', 'last_name', 'roll_no', 'department', 'admission_year', 'dob', 
            'gender', 'blood_group', 'religion', 'category', 'physically_challenged', 
            'aadhaar', 'permanent_address', 'email', 'phone', 
            'father_first_name', 'father_last_name', 'mother_first_name', 'mother_last_name', 
            'father_occupation', 'mother_occupation', 'father_phone', 'mother_phone', 
            'guardian_name', 'guardian_phone', 'tenth_year', 'tenth_percentage', 
            'twelfth_year', 'twelfth_percentage', 'course', 'batch', 'hosteller'
        ]
        faculty_static = ['name', 'department', 'designation', 'staff_type']
        
        for f in student_static: AppField.objects.get_or_create(model_type='student', internal_name=f, is_static=True, defaults={'display_name': f.replace('_', ' ').title()})
        for f in faculty_static: AppField.objects.get_or_create(model_type='faculty', internal_name=f, is_static=True, defaults={'display_name': f.replace('_', ' ').title()})

    if DocumentType.objects.count() == 0:
        core_docs = ['10th Marksheet', '12th Marksheet', 'Semester 1 Marksheet', 'Semester 2 Marksheet', 'Semester 3 Marksheet', 'Semester 4 Marksheet', 'Semester 5 Marksheet', 'Semester 6 Marksheet', 'Aadhaar Card', 'PAN Card', 'Community Certificate']
        for d in core_docs: DocumentType.objects.get_or_create(name=d, is_static=True)

def get_app_fields(model_type):
    fields = AppField.objects.filter(model_type=model_type)
    labels = {f.internal_name: f.display_name for f in fields if f.is_static}
    custom_fields = [f for f in fields if not f.is_static]
    return labels, custom_fields

@login_required
def advanced_settings(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    ensure_static_fields()

    if request.method == "POST":
        action = request.POST.get('action')
        if action == "update_label": AppField.objects.filter(id=request.POST.get('field_id')).update(display_name=request.POST.get('display_name'))
        elif action == "add_field": AppField.objects.create(model_type=request.POST.get('model_type'), internal_name=f"custom_{AppField.objects.count() + 1}", display_name=request.POST.get('display_name'), is_static=False)
        elif action == "delete_field": AppField.objects.filter(id=request.POST.get('field_id')).delete()
        elif action == "add_doc_type": DocumentType.objects.create(name=request.POST.get('display_name'), is_static=False)
        elif action == "update_doc_label": DocumentType.objects.filter(id=request.POST.get('field_id')).update(name=request.POST.get('display_name'))
        elif action == "delete_doc_type": DocumentType.objects.filter(id=request.POST.get('field_id'), is_static=False).delete()
        messages.success(request, "Settings updated successfully.")
        return redirect('advanced_settings')

    return render(request, 'advanced_settings.html', {
        'student_fields': AppField.objects.filter(model_type='student'),
        'faculty_fields': AppField.objects.filter(model_type='faculty'),
        'doc_types': DocumentType.objects.all()
    })

from django.contrib.auth import login # Make sure this is imported at the top!

def login_view(request):
    if request.method == "POST":
        raw_username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # 1. Use .filter().first() instead of .get() so it NEVER crashes, even if there are ghosts
        db_user = User.objects.filter(username__iexact=raw_username).first()
        
        if db_user:
            is_student = hasattr(db_user, 'student')
            
            # 2. Strict case-checking for Admins and Faculty only
            if not is_student and db_user.username != raw_username:
                messages.error(request, "Invalid username or password")
                return render(request, 'login.html')
            
            # 3. 🔥 THE MANUAL BYPASS 🔥 Check the password directly!
            if db_user.check_password(password):
                # We have to tell Django which backend to use since we skipped authenticate()
                db_user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, db_user)
                
                # Route them correctly
                if db_user.is_superuser or db_user.groups.filter(name="Admin").exists(): 
                    return redirect('admin_dashboard')
                elif hasattr(db_user, 'faculty'): 
                    return redirect('faculty_dashboard')
                elif hasattr(db_user, 'student'): 
                    return redirect('student_dashboard')
                    
        # If we reach here, either the user wasn't found or the password was wrong
        messages.error(request, "Invalid username or password")
        
    return render(request, 'login.html')

@login_required
def admin_dashboard(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    
    teaching_count = Faculty.objects.filter(staff_type__iexact="teaching").count()
    non_teaching_count = Faculty.objects.filter(staff_type__iexact="non_teaching").count()
    
    student_depts = Student.objects.values_list('department', flat=True)
    teaching_depts = Faculty.objects.filter(staff_type__iexact="teaching").values_list('department', flat=True)
    total_depts = len(set(d for d in list(student_depts) + list(teaching_depts) if d))

    return render(request, 'admin_dashboard.html', {
        'total_students': Student.objects.count(), 
        'total_boys': Student.objects.filter(gender__iexact="male").count(),
        'total_girls': Student.objects.filter(gender__iexact="female").count(), 
        'total_departments': total_depts,
        'teaching_faculty': teaching_count, 
        'non_teaching': non_teaching_count
    })

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student'): return HttpResponseForbidden()
    return render(request, 'student_dashboard.html', {'student': request.user.student})

@login_required
def faculty_dashboard(request):
    if not hasattr(request.user, 'faculty'): return HttpResponseForbidden()
    
    faculty = request.user.faculty
    ensure_static_fields()
    extra_data = FacultyCustomData.objects.filter(faculty=faculty)
    
    if faculty.staff_type.lower() == 'non_teaching':
        student_depts = Student.objects.values_list('department', flat=True)
        teaching_depts = Faculty.objects.filter(staff_type__iexact="teaching").values_list('department', flat=True)
        total_depts = len(set(d for d in list(student_depts) + list(teaching_depts) if d))
        
        return render(request, 'non_teaching_dashboard.html', {
            'faculty': faculty, 
            'total_students': Student.objects.count(),
            'total_departments': total_depts,
            'extra_data': extra_data
        })
    
    my_students = Student.objects.filter(department__iexact=faculty.department).count()
    return render(request, 'faculty_dashboard.html', {
        'faculty': faculty, 
        'my_students_count': my_students,
        'extra_data': extra_data
    })

import datetime  # Make sure this is at the top of your views.py!

@login_required
def add_student(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): 
        return HttpResponseForbidden()
        
    ensure_static_fields()
    labels, _ = get_app_fields('student')
    
    if request.method == "POST":
        roll_no = request.POST.get('roll_no', '').strip()
        
        # 1. Check if the exact Roll No exists in the Student table
        existing_student = Student.objects.filter(roll_no__iexact=roll_no).first()
        if existing_student:
            name_display = f"{existing_student.first_name} {existing_student.last_name}".strip() or "An older student record"
            messages.error(request, f"Blocked! {name_display} already has Roll No '{roll_no}' in the {existing_student.department} department!")
            return redirect('add_student')

        # 2. Check if the Login Username is already taken in the User table
        existing_users = User.objects.filter(username__iexact=roll_no)
        for user in existing_users:
            if hasattr(user, 'student'):
                # The username is taken, but their Student.roll_no is different (trailing space trap!)
                name_display = f"{user.student.first_name} {user.student.last_name}".strip() or "A student"
                messages.error(request, f"Blocked! The login ID '{roll_no}' is already being used by {name_display} (Their actual listed Roll No is '{user.student.roll_no}'). Go edit their profile to fix it!")
                return redirect('add_student')
            elif hasattr(user, 'faculty'):
                messages.error(request, f"Blocked! A Faculty member is using '{roll_no}' as their login username!")
                return redirect('add_student')
            else:
                # It's a true ghost (no student, no faculty attached). Nuke it.
                user.delete()
                
        # 3. The coast is clear! Grab the split names.
        f_name = request.POST.get('first_name', '').strip()
        l_name = request.POST.get('last_name', '').strip()
        
        user = User.objects.create_user(username=roll_no, password="1234", first_name=f_name, last_name=l_name)
        
        # 4. Safely grab the admission year or default to the current year
        adm_year = request.POST.get('admission_year')
        if not adm_year:
            adm_year = datetime.date.today().year
        else:
            try:
                adm_year = int(adm_year)
            except ValueError:
                adm_year = datetime.date.today().year
        
        # 5. Build the dictionary and create the student
        student_data = {
            'user': user, 
            'roll_no': roll_no,
            'first_name': f_name,
            'last_name': l_name,
            'department': request.POST.get('department', ''),
            'gender': request.POST.get('gender', ''),
            'course': request.POST.get('course', ''),
            'admission_year': adm_year
        }
        
        Student.objects.create(**student_data)
        messages.success(request, f"Student added successfully! Login: {roll_no} | Password: 1234")
        return redirect('student_list')
        
    return render(request, 'add_student.html', {'labels': labels})

@login_required
def student_edit(request, id):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): 
        return HttpResponseForbidden()
    
    student = get_object_or_404(Student, id=id)
    ensure_static_fields()
    labels, custom_fields = get_app_fields('student')
    
    if request.method == "POST":
        # 1. Standard Fields (Note: 'department' and 'religion' removed for custom processing below)
        standard_fields = [
            'first_name', 'last_name', 'roll_no', 'course', 
            'gender', 'blood_group', 'category', 'aadhaar', 'phone', 'email', 
            'permanent_address', 'father_first_name', 'father_last_name', 
            'mother_first_name', 'mother_last_name', 'father_occupation', 
            'mother_occupation', 'father_phone', 'mother_phone', 
            'guardian_name', 'guardian_phone', 'batch'
        ]
        
        for field in standard_fields:
            if field in labels: 
                setattr(student, field, request.POST.get(field))
                
        # 2. 🔥 Custom Department Logic (Handling 'Other')
        if 'department' in labels:
            selected_dept = request.POST.get('department', '')
            if selected_dept == 'Other':
                student.department = request.POST.get('department_other', 'Other').strip()
            else:
                student.department = selected_dept.strip()
        
        # 3. 🔥 Custom Religion Logic (Handling 'Other')
        if 'religion' in labels:
            selected_religion = request.POST.get('religion', '')
            if selected_religion == 'Other':
                student.religion = request.POST.get('religion_other', 'Other').strip()
            else:
                student.religion = selected_religion.strip()

        # 4. Boolean and Date Fields
        if 'dob' in labels: 
            student.dob = request.POST.get('dob') if request.POST.get('dob') else None
        if 'physically_challenged' in labels: 
            student.physically_challenged = request.POST.get('physically_challenged') == "True"
        if 'hosteller' in labels: 
            student.hosteller = request.POST.get('hosteller') == "True"
            
        # 5. Integer Fields
        for field in ['tenth_year', 'twelfth_year']:
            if field in labels and request.POST.get(field):
                try: setattr(student, field, int(request.POST.get(field)))
                except ValueError: pass
                    
        # 6. Float Fields
        for field in ['tenth_percentage', 'twelfth_percentage']:
            if field in labels and request.POST.get(field):
                try: setattr(student, field, float(request.POST.get(field)))
                except ValueError: pass
                    
        student.save()
        
        # 7. Custom App Fields (Dynamic Settings Data)
        for cf in custom_fields:
            obj, _ = StudentCustomData.objects.get_or_create(student=student, field=cf)
            obj.value = request.POST.get(f'custom_{cf.id}', '')
            obj.save()
            
        messages.success(request, "Details updated successfully")
        return redirect('student_full_details', id=student.id)
        
    # GET request handling
    for cf in custom_fields:
        data = StudentCustomData.objects.filter(student=student, field=cf).first()
        cf.current_value = data.value if data else ""
        
    return render(request, 'student_edit.html', {'student': student, 'labels': labels, 'custom_fields': custom_fields})


@login_required
def student_detail(request, id):
    student = get_object_or_404(Student, id=id)
    is_admin = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    is_faculty = hasattr(request.user, 'faculty') and request.user.faculty.department.lower() == student.department.lower()
    is_self = hasattr(request.user, 'student') and request.user.student == student

    if not (is_admin or is_self or is_faculty or is_non_teaching): return HttpResponseForbidden()

    ensure_static_fields()
    labels, _ = get_app_fields('student')
    fields = []
    for f in student._meta.fields:
        if f.name not in ['id', 'user'] and f.name in labels and getattr(student, f.name):
            val = getattr(student, f.name)
            if f.name in ['hosteller', 'physically_challenged']: val = "Yes" if val is True else ("No" if val is False else val)
            fields.append({'label': labels[f.name], 'value': val})
            
    return render(request, 'student_detail.html', {'student': student, 'fields': fields, 'is_admin': is_admin, 'is_faculty': (is_faculty or is_non_teaching)})

@login_required
def student_full_details(request, id):
    student = get_object_or_404(Student, id=id)
    is_admin = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    is_self = hasattr(request.user, 'student') and request.user.student == student
    is_faculty = hasattr(request.user, 'faculty') and request.user.faculty.department.lower() == student.department.lower()
    
    if not (is_admin or is_self or is_faculty or is_non_teaching): return HttpResponseForbidden()

    ensure_static_fields()
    labels, _ = get_app_fields('student')
    extra_data = StudentCustomData.objects.filter(student=student)
    return render(request, 'student_full_details.html', {'student': student, 'labels': labels, 'extra_data': extra_data, 'is_faculty': (is_faculty or is_non_teaching), 'is_admin': is_admin})

@login_required
def student_list(request):
    if hasattr(request.user, 'student'): return HttpResponseForbidden()
    q, dept, gender, course_type = request.GET.get('q', '').strip(), request.GET.get('dept', '').strip(), request.GET.get('gender', '').strip(), request.GET.get('type', '').strip()
    
    students = Student.objects.all()
    
    # Determine roles
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    is_actual_admin = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    
    # 🔥 FIXED: If they are Teaching Faculty AND NOT an Admin, restrict them to their department.
    # (Admins will now bypass this and see everyone!)
    if hasattr(request.user, 'faculty') and not is_non_teaching and not is_actual_admin:
        students = students.filter(department__iexact=request.user.faculty.department)

    if q:
        q_objs = Q()
        for field in Student._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)): q_objs |= Q(**{f"{field.name}__icontains": q})
            elif isinstance(field, (models.IntegerField, models.FloatField)) and q.isdigit(): q_objs |= Q(**{f"{field.name}": int(q)})
        custom_matches = StudentCustomData.objects.filter(value__icontains=q).values_list('student_id', flat=True)
        q_objs |= Q(id__in=custom_matches) | Q(user__email__icontains=q)
        students = students.filter(q_objs).distinct()

    if dept: students = students.filter(department__iexact=dept)
    if gender: students = students.filter(gender__iexact=gender)
    if course_type: students = students.filter(course__iexact=course_type)
    
    return render(request, 'student_list.html', {'students': students, 'is_admin': is_actual_admin})

@login_required
def delete_student(request, id):
    # Security check
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): 
        return HttpResponseForbidden()
        
    student = get_object_or_404(Student, id=id)
    
    # 🔥 FIX: Just delete the student! 
    # Our models.py signal will automatically hunt down and delete the attached User.
    student.delete() 
    
    messages.success(request, "Student and login account deleted successfully!")
    return redirect('student_list')

from django.db.models import Q # Make sure you have this import at the top!

@login_required
def faculty_list(request):
    # Security check (Admins and Faculty can view)
    if hasattr(request.user, 'student'): return HttpResponseForbidden()
    
    q = request.GET.get('q', '').strip()
    faculty = Faculty.objects.all()

    # 1. 🔥 UPGRADED SEARCH: Now searches core fields AND Custom Data (like Designation)
    if q:
        q_objs = Q(name__icontains=q) | Q(department__icontains=q)
        
        # Search the custom fields table for the query
        custom_matches = FacultyCustomData.objects.filter(value__icontains=q).values_list('faculty_id', flat=True)
        q_objs |= Q(id__in=custom_matches)
        
        faculty = faculty.filter(q_objs).distinct()

    # 2. 🔥 FETCH CUSTOM DESIGNATION: Find the custom field for Designation
    # We look for an AppField where the display name contains "Designation"
    desig_field = AppField.objects.filter(model_type='faculty', display_name__icontains='designation').first()

    # Attach the custom designation to each faculty member for the template
    for f in faculty:
        f.custom_designation = None # Default
        if desig_field:
            data = FacultyCustomData.objects.filter(faculty=f, field=desig_field).first()
            if data and data.value:
                f.custom_designation = data.value

    return render(request, 'faculty_list.html', {'faculty': faculty})

@login_required
def add_faculty(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    ensure_static_fields()
    labels, custom_fields = get_app_fields('faculty')
    if request.method == "POST":
        name = request.POST.get('name')
        base_user = name.replace(" ", "").lower()
        username = f"{base_user}{random.randint(100,999)}"
        while User.objects.filter(username=username).exists():
            username = f"{base_user}{random.randint(100,999)}"
            
        user = User.objects.create_user(username=username, password="faculty123", first_name=name)

        faculty_data = {'user': user}
        for field in ['name', 'department', 'designation', 'staff_type']:
            if field in labels: faculty_data[field] = request.POST.get(field)
        faculty = Faculty.objects.create(**faculty_data)
        for cf in custom_fields:
            val = request.POST.get(f'custom_{cf.id}', '')
            if val: FacultyCustomData.objects.create(faculty=faculty, field=cf, value=val)
            
        messages.success(request, f"Faculty added successfully! Username: {username} | Password: faculty123")
        return redirect('faculty_list')
    return render(request, 'add_faculty.html', {'labels': labels, 'custom_fields': custom_fields})

@login_required
def faculty_edit(request, id):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): 
        return HttpResponseForbidden()
        
    faculty = get_object_or_404(Faculty, id=id)
    ensure_static_fields()
    labels, custom_fields = get_app_fields('faculty')
    
    if request.method == "POST":
        for field in ['name', 'department', 'designation', 'staff_type']:
            if field in labels: setattr(faculty, field, request.POST.get(field))
        faculty.save()
        
        for cf in custom_fields:
            obj, _ = FacultyCustomData.objects.get_or_create(faculty=faculty, field=cf)
            obj.value = request.POST.get(f'custom_{cf.id}', '')
            obj.save()
            
        messages.success(request, "Faculty updated successfully")
        return redirect('faculty_list')
        
    for cf in custom_fields:
        data = FacultyCustomData.objects.filter(faculty=faculty, field=cf).first()
        cf.current_value = data.value if data else ""
        
    return render(request, 'faculty_edit.html', {'faculty': faculty, 'labels': labels, 'custom_fields': custom_fields})

@login_required
def faculty_view(request, id):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    faculty = get_object_or_404(Faculty, id=id)
    ensure_static_fields()
    labels, _ = get_app_fields('faculty')
    extra_data = FacultyCustomData.objects.filter(faculty=faculty)
    return render(request, 'faculty_view.html', {'faculty': faculty, 'labels': labels, 'extra_data': extra_data})

@login_required
def delete_faculty(request, id):
    # Security check
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): 
        return HttpResponseForbidden()
        
    faculty = get_object_or_404(Faculty, id=id)
    
    # 🔥 FIX: Just delete the faculty! 
    # The models.py signal handles the User account automatically.
    faculty.delete()
    
    messages.success(request, "Faculty member and login account deleted successfully!")
    return redirect('faculty_list') # Replace 'faculty_list' with your actual URL name if different

@login_required
def digilocker(request):
    if hasattr(request.user, 'student'): return redirect('student_locker', id=request.user.student.id)
    
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    
    if hasattr(request.user, 'faculty') and not is_non_teaching: 
        return redirect('student_list')
    
    q = request.GET.get('q', '').strip()
    students = Student.objects.all()

    if q:
        q_objs = Q()
        for field in Student._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)): q_objs |= Q(**{f"{field.name}__icontains": q})
            elif isinstance(field, (models.IntegerField, models.FloatField)) and q.isdigit(): q_objs |= Q(**{f"{field.name}": int(q)})
        custom_matches = StudentCustomData.objects.filter(value__icontains=q).values_list('student_id', flat=True)
        q_objs |= Q(id__in=custom_matches) | Q(user__email__icontains=q)
        students = students.filter(q_objs).distinct()

    return render(request, 'digilocker.html', {'students': students})

@login_required
def student_locker(request, id):
    student = get_object_or_404(Student, id=id)
    is_admin = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    is_faculty = hasattr(request.user, 'faculty')
    
    if request.method == "POST":
        action = request.POST.get('action')
        doc_type_id = request.POST.get('doc_type_id')
        doc_type = get_object_or_404(DocumentType, id=doc_type_id)
        
        # 1. Handle Uploading (Auto-Locks immediately after upload)
        if action == 'upload':
            file = request.FILES.get('file')
            if file:
                doc, created = StudentDocument.objects.get_or_create(student=student, document_type=doc_type)
                doc.file = file
                doc.status = 'Locked' # Automatically locks!
                doc.save()
                messages.success(request, f"{doc_type.name} uploaded successfully and locked for review.")
                
        # 2. Handle Deleting (Only if Unlocked or if Admin)
        elif action == 'delete':
            doc = StudentDocument.objects.filter(student=student, document_type=doc_type).first()
            if doc:
                doc.delete()
                messages.success(request, "Document deleted.")
                
        # 3. Handle Student Requesting an Edit
        elif action == 'request_edit':
            doc = StudentDocument.objects.filter(student=student, document_type=doc_type).first()
            if doc:
                doc.status = 'Requested'
                doc.save()
                messages.success(request, "Edit request sent! Please wait for Admin approval.")
                
        # 4. Handle Admin Approving the Edit
        elif action == 'approve_edit' and is_admin:
            doc = StudentDocument.objects.filter(student=student, document_type=doc_type).first()
            if doc:
                doc.status = 'Unlocked'
                doc.save()
                messages.success(request, "Edit access granted. The student can now delete and replace this document.")
                
        return redirect('student_locker', id=student.id)

    # Build the locker grid
    doc_types = DocumentType.objects.all()
    locker_items = []
    for dt in doc_types:
        doc = StudentDocument.objects.filter(student=student, document_type=dt).first()
        locker_items.append({'type': dt, 'document': doc})
        
    return render(request, 'student_locker.html', {
        'student': student, 
        'locker_items': locker_items,
        'is_admin': is_admin,
        'is_faculty': is_faculty
    })

    doc_types = DocumentType.objects.all()
    existing_docs = {doc.document_type_id: doc for doc in StudentDocument.objects.filter(student=student)}
    locker_items = [{'type': dt, 'document': existing_docs.get(dt.id)} for dt in doc_types]
    
    return render(request, 'student_locker.html', {'student': student, 'locker_items': locker_items, 'is_faculty': (is_faculty_dept or is_non_teaching), 'is_admin': (is_admin_user or is_non_teaching)})

@login_required
def export_view(request):
    is_admin_user = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    is_teaching = hasattr(request.user, 'faculty') and not is_non_teaching
    
    if not (is_admin_user or is_teaching or is_non_teaching): 
        return HttpResponseForbidden()
        
    ensure_static_fields()
    
    is_acting_admin = is_admin_user or is_non_teaching
    
    context = {
        'student_fields': AppField.objects.filter(model_type='student'),
        'is_admin': is_acting_admin,
        'is_faculty': is_teaching
    }
    
    if is_acting_admin:
        context['faculty_fields'] = AppField.objects.filter(model_type='faculty')
        context['departments'] = Student.objects.exclude(department__isnull=True).exclude(department__exact='').values_list('department', flat=True).distinct()
        
    return render(request, 'export.html', context)
 
@login_required
def export_excel(request):
    is_admin_user = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    is_teaching = hasattr(request.user, 'faculty') and not is_non_teaching
    
    if not (is_admin_user or is_teaching or is_non_teaching): 
        return HttpResponseForbidden()
        
    if request.method == "POST":
        selected_fields = request.POST.getlist('fields')
        
        if is_teaching:
            data_type = 'student'
            department = request.user.faculty.department
        else:
            data_type = request.POST.get('type')
            department = request.POST.get('department')
            
        wb = Workbook()
        ws = wb.active
        
        fields_objs = AppField.objects.filter(internal_name__in=selected_fields, model_type=data_type)
        header_map = {f.internal_name: f.display_name for f in fields_objs}
        ws.append([header_map.get(f, f) for f in selected_fields])
        
        queryset = Faculty.objects.all() if data_type == "faculty" else Student.objects.all()
        
        if department and department != "All": 
            queryset = queryset.filter(department__iexact=department)
            
        for obj in queryset:
            row = []
            for f in selected_fields:
                if f.startswith('custom_'):
                    cd = StudentCustomData.objects.filter(student=obj, field__internal_name=f).first() if data_type == 'student' else FacultyCustomData.objects.filter(faculty=obj, field__internal_name=f).first()
                    row.append(cd.value if cd else "")
                else:
                    val = getattr(obj, f, "")
                    if f in ['hosteller', 'physically_challenged']: val = "Yes" if val is True else ("No" if val is False else val)
                    row.append(val)
            ws.append(row)
            
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=data_export.xlsx'
        wb.save(response)
        return response

@login_required
def programmes(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    
    departments = Student.objects.values('department').annotate(
        total_students=Count('id'), 
        boys=Count('id', filter=Q(gender__iexact='male')), 
        girls=Count('id', filter=Q(gender__iexact='female'))
    )
    
    dept_data = [
        {
            'name': d['department'], 
            'total_students': d['total_students'], 
            'boys': d['boys'], 
            'girls': d['girls'], 
            'faculty': Faculty.objects.filter(department=d['department'], staff_type__iexact='teaching').count()
        } 
        for d in departments
    ]
    
    return render(request, 'programmes.html', {'departments': dept_data})

@login_required
def change_password(request):
    if request.method == "POST":
        new_pw, conf_pw = request.POST.get('new_password'), request.POST.get('confirm_password')
        if new_pw != conf_pw: messages.error(request, "Passwords do not match"); return redirect('change_password')
        if len(new_pw) < 6: messages.error(request, "Password must be at least 6 characters"); return redirect('change_password')
        request.user.set_password(new_pw); request.user.save(); update_session_auth_hash(request, request.user)
        messages.success(request, "Password updated successfully")
        return redirect('admin_dashboard' if request.user.is_superuser else ('faculty_dashboard' if hasattr(request.user, 'faculty') else 'student_dashboard'))
    return render(request, 'change_password.html')

def logout_view(request): 
    logout(request)
    return redirect('login')
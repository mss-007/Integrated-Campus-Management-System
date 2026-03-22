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
        student_static = ['name', 'roll_no', 'department', 'admission_year', 'dob', 'gender', 'blood_group', 'religion', 'category', 'physically_challenged', 'aadhaar', 'permanent_address', 'email', 'phone', 'father_name', 'mother_name', 'father_occupation', 'mother_occupation', 'father_phone', 'mother_phone', 'guardian_name', 'tenth_year', 'tenth_percentage', 'twelfth_year', 'twelfth_percentage', 'course', 'batch', 'hosteller']
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

def login_view(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            if user.is_superuser or user.groups.filter(name="Admin").exists(): return redirect('admin_dashboard')
            elif hasattr(user, 'faculty'): return redirect('faculty_dashboard')
            elif hasattr(user, 'student'): return redirect('student_dashboard')
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
    
    # 🔥 ROUTE NON-TEACHING STAFF TO THEIR NEW DASHBOARD
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
    
    # Normal Teaching Dashboard
    my_students = Student.objects.filter(department__iexact=faculty.department).count()
    return render(request, 'faculty_dashboard.html', {
        'faculty': faculty, 
        'my_students_count': my_students,
        'extra_data': extra_data
    })

@login_required
def add_student(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    ensure_static_fields()
    labels, _ = get_app_fields('student')
    if request.method == "POST":
        roll_no = request.POST.get('roll_no')
        if User.objects.filter(username=roll_no).exists(): messages.error(request, "Student already exists"); return redirect('add_student')
        user = User.objects.create_user(username=roll_no, password="1234", first_name=request.POST.get('name'))
        student_data = {'user': user, 'roll_no': roll_no}
        for field in ['name', 'department', 'admission_year', 'course', 'gender']:
            if field in labels: student_data[field] = request.POST.get(field).strip().title() if field == 'department' else request.POST.get(field)
        Student.objects.create(**student_data)
        messages.success(request, "Student added successfully")
        return redirect('student_list')
    return render(request, 'add_student.html', {'labels': labels})

@login_required
def student_edit(request, id):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    student = get_object_or_404(Student, id=id)
    ensure_static_fields()
    labels, custom_fields = get_app_fields('student')
    if request.method == "POST":
        for field in ['name', 'roll_no', 'department', 'course', 'gender', 'blood_group', 'religion', 'category', 'aadhaar', 'phone', 'email', 'permanent_address', 'father_name', 'mother_name', 'father_occupation', 'mother_occupation', 'father_phone', 'mother_phone', 'batch']:
            if field in labels: setattr(student, field, request.POST.get(field))
        if 'dob' in labels: student.dob = request.POST.get('dob') if request.POST.get('dob') else None
        if 'physically_challenged' in labels: student.physically_challenged = request.POST.get('physically_challenged') == "True"
        if 'hosteller' in labels: student.hosteller = request.POST.get('hosteller') == "True"
        for field in ['tenth_year', 'twelfth_year']:
            if field in labels:
                try: setattr(student, field, int(request.POST.get(field)))
                except: pass
        for field in ['tenth_percentage', 'twelfth_percentage']:
            if field in labels:
                try: setattr(student, field, float(request.POST.get(field)))
                except: pass
        student.save()
        for cf in custom_fields:
            obj, _ = StudentCustomData.objects.get_or_create(student=student, field=cf)
            obj.value = request.POST.get(f'custom_{cf.id}', '')
            obj.save()
        messages.success(request, "Details updated successfully")
        return redirect('student_full_details', id=student.id)
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

    # 🔥 Non-Teaching added to allowed viewers
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
    
    # 🔥 Non-Teaching added to allowed viewers
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
    
    # 🔥 Determine if user is Non-Teaching
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    
    # If standard teaching faculty, restrict to their specific department
    if hasattr(request.user, 'faculty') and not is_non_teaching:
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
    
    # Send actual admin status to ensure Non-Teaching staff don't get 'Edit/Delete' buttons in the HTML
    is_actual_admin = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    return render(request, 'student_list.html', {'students': students, 'is_admin': is_actual_admin})

def delete_student(request, id):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    student = Student.objects.get(id=id)
    if student.user: student.user.delete()
    student.delete()
    return redirect('student_list')

@login_required
def faculty_list(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    faculty = Faculty.objects.all()
    q, dept = request.GET.get('q', '').strip(), request.GET.get('dept', '').strip()
    if q:
        q_objs = Q()
        for field in Faculty._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)): q_objs |= Q(**{f"{field.name}__icontains": q})
        custom_matches = FacultyCustomData.objects.filter(value__icontains=q).values_list('faculty_id', flat=True)
        q_objs |= Q(id__in=custom_matches)
        faculty = faculty.filter(q_objs).distinct()
    if dept: faculty = faculty.filter(department=dept)
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

def delete_faculty(request, id):
    if not (request.user.is_superuser or request.user.groups.filter(name="Admin").exists()): return HttpResponseForbidden()
    faculty = Faculty.objects.get(id=id)
    if faculty.user: faculty.user.delete()
    faculty.delete()
    return redirect('faculty_list')

@login_required
def digilocker(request):
    if hasattr(request.user, 'student'): return redirect('student_locker', id=request.user.student.id)
    
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    
    # 🔥 Only lock out TEACHING Faculty. Non-Teaching can access the Search page.
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
    
    is_admin_user = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    is_faculty_dept = hasattr(request.user, 'faculty') and request.user.faculty.department.lower() == student.department.lower()
    is_self = hasattr(request.user, 'student') and request.user.student == student
    
    if not (is_admin_user or is_self or is_faculty_dept or is_non_teaching): return HttpResponseForbidden()
    ensure_static_fields()
    
    # 🔥 SECURITY LOCK: Prevent Non-Teaching from uploading or deleting via direct POST requests
    if request.method == 'POST':
        if not (is_admin_user or is_self): return HttpResponseForbidden()
        
        action = request.POST.get('action')
        doc_type = get_object_or_404(DocumentType, id=request.POST.get('doc_type_id'))
        if action == 'upload' and request.FILES.get('file'):
            StudentDocument.objects.filter(student=student, document_type=doc_type).delete()
            StudentDocument.objects.create(student=student, document_type=doc_type, file=request.FILES.get('file'))
            messages.success(request, f"{doc_type.name} uploaded securely.")
        elif action == 'delete':
            StudentDocument.objects.filter(student=student, document_type=doc_type).delete()
            messages.success(request, f"{doc_type.name} removed.")
        return redirect('student_locker', id=student.id)

    doc_types = DocumentType.objects.all()
    existing_docs = {doc.document_type_id: doc for doc in StudentDocument.objects.filter(student=student)}
    locker_items = [{'type': dt, 'document': existing_docs.get(dt.id)} for dt in doc_types]
    
    # 🔥 HACK FOR HTML: By telling the HTML that Non-Teaching is "Faculty", the template automatically hides the upload/delete buttons!
    return render(request, 'student_locker.html', {'student': student, 'locker_items': locker_items, 'is_faculty': (is_faculty_dept or is_non_teaching), 'is_admin': (is_admin_user or is_non_teaching)})

@login_required
def export_view(request):
    is_admin_user = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    is_non_teaching = hasattr(request.user, 'faculty') and request.user.faculty.staff_type.lower() == 'non_teaching'
    is_teaching = hasattr(request.user, 'faculty') and not is_non_teaching
    
    if not (is_admin_user or is_teaching or is_non_teaching): 
        return HttpResponseForbidden()
        
    ensure_static_fields()
    
    # Treat Non-Teaching as Admin so they get the full Department dropdown options
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
        
        # 🔥 Force regular teaching faculty to ONLY export their department
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

def logout_view(request): logout(request); return redirect('login')
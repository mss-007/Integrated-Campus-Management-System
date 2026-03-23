from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ==========================================
    # 🔐 AUTHENTICATION & CORE SETTINGS
    # ==========================================
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('advanced/', views.advanced_settings, name='advanced_settings'),

    # ==========================================
    # 📊 ROLE-BASED DASHBOARDS
    # ==========================================
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('faculty-dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),

    # ==========================================
    # 🎓 STUDENT MANAGEMENT
    # ==========================================
    path('students/', views.student_list, name='student_list'),
    path('add-student/', views.add_student, name='add_student'),
    path('student/<int:id>/', views.student_detail, name='student_detail'),
    
    # 🔥 FIXED: Pointed the redundant URL straight to the unified view!
    path('student/full/<int:id>/', views.student_detail, name='student_full_details'),
    
    path('student/<int:id>/edit/', views.student_edit, name='student_edit'),
    path('student/<int:id>/delete/', views.delete_student, name='delete_student'),

    # ==========================================
    # 👨‍🏫 FACULTY & STAFF MANAGEMENT
    # ==========================================
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/add/', views.add_faculty, name='add_faculty'),
    path('faculty/view/<int:id>/', views.faculty_view, name='faculty_view'),
    path('faculty/edit/<int:id>/', views.faculty_edit, name='faculty_edit'),
    path('faculty/<int:id>/delete/', views.delete_faculty, name='delete_faculty'),

    # ==========================================
    # 📁 ACADEMICS & DIGILOCKER
    # ==========================================
    path('departments/', views.programmes, name='departments'),
    path('digilocker/', views.digilocker, name='digilocker'),
    path('digilocker/<int:id>/', views.student_locker, name='student_locker'),

    # ==========================================
    # 📈 DATA EXPORT
    # ==========================================
    path('export/', views.export_view, name='export'),
    path('export-excel/', views.export_excel, name='export_excel'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    #website-url
    path('', views.welcome_page, name='welcome'),
    path('get-started', views.get_started_page, name='get-started'),
    path('features', views.features_page, name='features'),
    path('about', views.about_page, name='about'),
    path('pricing', views.pricing_page, name='pricing'),
    path('contact', views.contact_page, name='contact'),


    path('logout/', views.user_logout, name='logout'),
    path('login/', views.login_view, name='login'),
    # Registration URLs
    path('company-registration/', views.company_registration, name='company_registration'),
    path('student-registration/', views.student_registration, name='student_registration'),
    path('upload-students/', views.upload_students, name='upload_students'),
    path('university-registration/', views.university_registration, name='university_registration'),

    # Dashboard URLs
    path('system-admin-dashboard/', views.system_admin_dashboard, name='system_admin_dashboard'),
    #company dashboard
    path('company-dashboard/', views.company_dashboard, name='company_dashboard'),
    path('post-vacancy/', views.post_vacancy, name='post_vacancy'),
    path('vacancy-list/', views.vacancy_list, name='vacancy_list'),
    path('update-vacancy/<int:id>/', views.update_vacancy, name='update_vacancy'),
    path('view-applicants/<int:id>/', views.view_applicants, name='view_applicants'),
    path('remove-vacancy/<int:id>/', views.remove_vacancy, name='remove_vacancy'),
    path('all-applications/', views.all_applications, name='all_applications'),
    path('company/profile/', views.company_profile, name='company_profile'),
    path('company/profile/edit/', views.edit_company_profile, name='edit_company_profile'),
    path('company/students/', views.company_students, name='company_students'),
    path('invite/<int:student_id>/<int:vacancy_id>/', views.invite_for_interview, name='invite_for_interview'),
    path('company/waitlist/', views.company_waitlist, name='company_waitlist'),
    path('manage-departments/', views.manage_departments, name='manage_departments'),
    path('department/<int:department_id>/students/', views.view_department_students, name='view_department_students'),
    
    #university dashboard
    path('university-dashboard/', views.university_dashboard, name='university_dashboard'),
    path('add_student/', views.add_student, name='add_student'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('bulk_upload_students/', views.bulk_upload_students, name='bulk_upload_students'),
    path('instutution/students/', views.student_list, name='student_list'),
    # URL for viewing enrolled students
    path('students/enrolled/', views.view_enrolled_students, name='view_enrolled_students'),
    path('results/', views.result_list, name='result_list'),
    path('results/upload-single/', views.upload_single_result, name='upload_single_result'),
    path('results/upload-bulk/', views.upload_bulk_results, name='upload_bulk_results'),
    path('analytics/enrollment-report/', views.enrollment_report, name='enrollment_report'),
    path('analytics/performance-analytics/', views.performance_analytics, name='performance_analytics'),
    path('university/edit/', views.UniversityUpdateView.as_view(), name='edit_university_profile'),
    path('university/profile/', views.university_profile, name='university_profile'),
    path('messages/', views.all_messages_view, name='university_messages'),


    
    #student dashboard urls
    path('apply/<int:vacancy_id>/', views.apply_for_vacancy, name='apply_for_vacancy'),
    path('create-resume/', views.create_resume, name='create_resume'),
    path('create-cover-letter/', views.create_cover_letter, name='create_cover_letter'),
    path('application-status/', views.application_status, name='application_status'),
    path('internship_opportunities/',views.internship_opportunities, name='internship_opportunities'),
    path('internship-preparation/', views.internship_preparation_view, name='internship_preparation'),
    path('profile/', views.profile_view, name='profile'),

    
    path('student/notifications/', views.student_notifications, name='student_notifications'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


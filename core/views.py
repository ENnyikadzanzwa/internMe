from django.shortcuts import render, redirect
from .forms import * 
import csv
from django.contrib.auth.models import User
from .models import Student,Company,University
from django.shortcuts import render
from .models import Vacancy, Application
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
import pandas as pd
from django.utils.timezone import now
from django.db.models import Q
from django.db import IntegrityError
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Avg, FloatField,Count
from django.db.models.functions import Cast
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.utils.decorators import method_decorator
from django.utils import timezone
import sweetify

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Add success message
                messages.success(request, "Login successful! Welcome back.")
                # Redirect after the page reloads
                return render(request, 'core/auth/index.html', {'form': form, 'redirect_url': get_redirect_url(user)})
            else:
                # Authentication failed
                messages.error(request, "Invalid username or password.")
                return render(request, 'core/auth/index.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'core/auth/index.html', {'form': form})

def get_redirect_url(user):
    # Logic to decide which dashboard to redirect to after login
    if user.extendeduser.role == 'System Admin':
        return 'system_admin_dashboard'
    elif user.extendeduser.role == 'Company Representative':
        return 'company_dashboard'
    elif user.extendeduser.role == 'University Admin':
        return 'university_dashboard'
    elif user.extendeduser.role == 'Student':
        return 'student_dashboard'
    else:
        return 'welcome_page'


def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logging out



def company_registration(request):
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Company registered successfully!")
                return redirect('company_registration')
            except IntegrityError as e:
                messages.error(request, "Integrity error occurred: " + str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CompanyRegistrationForm()
    
    return render(request, 'core/company/company_registration.html', {'form': form})




def student_registration(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()  # Create the User and link it to the existing Student
                messages.success(request, "Your account has been created successfully!")
                return redirect('student_registration')  # Redirect to the login page
            except IntegrityError:
                # Handle IntegrityError (e.g., if the student registration number already exists)
                messages.error(request, title="Error", message="This registration number already has an associated user account.", icon="error")
        else:
            messages.error(request, "There was an error in your registration form. Please correct it.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'core/student/student_registration.html', {'form': form})



def upload_students(request):
    if request.method == 'POST':
        form = StudentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            for row in reader:
                user = User.objects.create_user(username=row['username'], password=row['password'])
                student = Student.objects.create(
                    user=user,
                    registration_number=row['registration_number'],
                    university=request.user.extendeduser.university,
                    program_of_study=row['program_of_study'],
                    year_of_study=row['year_of_study']
                )
            return redirect('university_dashboard')
    else:
        form = StudentUploadForm()
    return render(request, 'core/student/upload_students.html', {'form': form})





def university_registration(request):
    if request.method == 'POST':
        form = UniversityRegistrationForm(request.POST)
        if form.is_valid():
            try:
                form.save()  # Attempt to save the form
                messages.success(request, "Institution registered successfully! Redirecting to the dashboard...")
                return redirect('university_registration')  # Redirect to reload the page with the message
            except IntegrityError as e:
                # Handle integrity errors (e.g., duplicate entries)
                if 'unique constraint' in str(e).lower():
                    messages.error(request, "Institution with this name or email already exists. Please use different details.")
                else:
                    messages.error(request, "An error occurred during registration. Please try again.")
        else:
            # Handle general form validation errors
            messages.error(request, "Failed to register institution. Please correct the errors and try again.")
    else:
        form = UniversityRegistrationForm()
    return render(request, 'core/university/index-reg.html', {'form': form})



#dashboards  and asociated logic
#system adminstrators
def system_admin_dashboard(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'System Admin':
        return redirect('login')  # Ensure only system admins can access this view

    users = ExtendedUser.objects.all()

    return render(request, 'core/adminstrators/system_admin_dashboard.html', {
        'users': users
    })



def company_dashboard(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Company Representative':
        return redirect('login')

    # Get the company associated with the authenticated user
    company = get_object_or_404(Company, company_rep=request.user)

    # Get all vacancies for the company
    vacancies = company.vacancy_set.all()

    # Get applications for the company's vacancies
    applications = Application.objects.filter(vacancy__in=vacancies)

    # You can also fetch students or other related data here
    students = Student.objects.filter(application__in=applications).distinct()

    return render(request, 'core/company/company_dashboard.html', {
        'company': company,
        'vacancies': vacancies,
        'applications': applications,
        'students': students,
        'user': request.user,
    })

def company_waitlist(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Company Representative':
        return redirect('login')

    try:
        # Get the company associated with the current user
        company = Company.objects.get(company_rep=request.user)
    except Company.DoesNotExist:
        # Handle the case where no company is associated with the user
        return redirect('login')

    # Fetch waitlisted students for the company
    waitlisted_students = Waitlist.objects.filter(company=company, is_enrolled=False)

    if request.method == 'POST':
        waitlist_id = request.POST.get('waitlist_id')
        try:
            waitlist_entry = Waitlist.objects.get(id=waitlist_id, company=company)
            # Enroll student
            waitlist_entry.is_enrolled = True
            waitlist_entry.save()
        except Waitlist.DoesNotExist:
            # Handle the case where the waitlist entry does not exist
            return redirect('company_waitlist')

        return redirect('company_waitlist')

    return render(request, 'core/company/waitlist.html', {'waitlisted_students': waitlisted_students})


@login_required
def company_students(request):
    # Ensure the logged-in user is a company representative
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Company Representative':
        return redirect('login')

    # Get the company associated with the logged-in user
    company = Company.objects.get(company_rep=request.user)

    # Get students who have applied to this company's vacancies
    applications = Application.objects.filter(vacancy__company=company)
    students = Student.objects.filter(id__in=applications.values_list('student_id', flat=True))

    return render(request, 'core/company/company_students.html', {
        'company': company,
        'students': students,
    })


def invite_for_interview(request, student_id, vacancy_id):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Company Representative':
        return redirect('login')

    student = get_object_or_404(Student, id=student_id)
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)

    # Create a notification for the student
    Notification.objects.create(
        student=student,
        vacancy=vacancy,
        message=f"You have been invited for an interview for {vacancy.title}."
    )
    
    return redirect('company_waitlist') 

@login_required
def company_profile(request):
    # Ensure the logged-in user is a Company Representative
    if not request.user.extendeduser.role == 'Company Representative':
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get the company associated with the logged-in user
    company = get_object_or_404(Company, company_rep=request.user)

    context = {
        'company': company,
    }
    return render(request, 'core/company/company_profile.html', context)


@login_required
def edit_company_profile(request):
    # Ensure the logged-in user is a Company Representative
    if not request.user.extendeduser.role == 'Company Representative':
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get the company associated with the logged-in user
    company = get_object_or_404(Company, company_rep=request.user)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_profile')  # Redirect to the profile page after saving changes
    else:
        form = CompanyForm(instance=company)

    context = {
        'form': form,
        'company': company,
    }
    return render(request, 'core/company/edit_company_profile.html', context)

@login_required
def post_vacancy(request):
    # Check if the logged-in user is a company representative
    try:
        
        if request.user.extendeduser.role != 'Company Representative':
            messages.error(request, "You are not authorized to post vacancies.")
            return redirect('company_dashboard')  # Redirect to home page or appropriate page
    except ExtendedUser.DoesNotExist:
        messages.error(request, "User role not found.")
        return redirect('company_dashboard')

    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            # Get the company of the current user (assuming a company is associated with the user)
            company = Company.objects.get(company_rep=request.user)

            # Create and save the vacancy
            vacancy = form.save(commit=False)
            vacancy.company = company
            vacancy.save()

            messages.success(request, "Internship vacancy posted successfully!")
            return redirect('vacancy_list')  # Redirect to a page that lists vacancies
        else:
            messages.error(request, "There was an error in posting the vacancy. Please correct it.")
    else:
        form = VacancyForm()

    return render(request, 'core/company/post_vacancy.html', {'form': form})


@login_required
def vacancy_list(request):
    # Ensure the user is a company representative
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Company Representative':
        return redirect('login')

    # Get the company associated with the logged-in user
    try:
        company = Company.objects.get(company_rep=request.user)
    except Company.DoesNotExist:
        # Handle case where the logged-in user is not associated with a company
        return render(request, 'core/company/vacancy_list.html', {'vacancies': [], 'error': "You are not associated with any company."})

    # Retrieve vacancies associated with the company
    vacancies = Vacancy.objects.filter(company=company)

    return render(request, 'core/company/vacancy_list.html', {'vacancies': vacancies})


# Update Vacancy
def update_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    
    # If the request is a POST, process the form submission
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()  # Save the updated vacancy details
            messages.success(request, 'Vacancy updated successfully!')
            return redirect('vacancy_list')  # Redirect to the list of vacancies
    else:
        # For GET request, display the form with current vacancy data
        form = VacancyForm(instance=vacancy)
    
    return render(request, 'core/company/update_vacancy.html', {'form': form, 'vacancy': vacancy})


# View Applicants
def view_applicants(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    applicants = Application.objects.filter(vacancy=vacancy)
    return render(request, 'core/company/view_applicants.html', {'vacancy': vacancy, 'applicants': applicants})

# Remove Vacancy
def remove_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    vacancy.delete()
    messages.success(request, "Vacancy removed successfully.")
    return redirect('vacancy_list')





@login_required
def all_applications(request):
    company_rep = request.user
    try:
        company = Company.objects.get(company_rep=company_rep)
    except Company.DoesNotExist:
        company = None

    applications = []

    if company:
        vacancies = Vacancy.objects.filter(company=company)
        applications = Application.objects.filter(vacancy__in=vacancies)

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        applications = applications.filter(
            Q(student__registration_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__university__name__icontains=search_query)
        )

    # Sorting functionality
    sort_by = request.GET.get('sort_by', '')
    order = request.GET.get('order', 'asc')
    
    if sort_by:
        if order == 'asc':
            applications = applications.order_by(sort_by)
        else:
            applications = applications.order_by(f'-{sort_by}')
    
    return render(request, 'core/company/all_applications.html', {'applications': applications, 'company': company})




def university_dashboard(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'University Admin':
        return redirect('login')

    try:
        university = University.objects.get(university_admin=request.user)
    except University.DoesNotExist:
        return redirect('login')

    students = Student.objects.filter(university=university)

    total_students = students.count()
    enrolled_students = students.filter(year_of_study__gt=0).count()
    students_due_for_attachment = students.filter(year_of_study__gte=3).count()

    # For reports, we will use dummy data for now or logic based on time periods like 'Today', 'This Month', and 'This Year'
    # Here, for simplicity, I’m generating some example data that you can later replace with actual dynamic data.

    today = datetime.today()
    last_7_days = [today - timedelta(days=i) for i in range(7)]
    total_students_data = [total_students for _ in range(7)]  # Dummy data for the last 7 days
    enrolled_students_data = [enrolled_students for _ in range(7)]  # Dummy data for the last 7 days
    attachment_due_data = [students_due_for_attachment for _ in range(7)]  # Dummy data for the last 7 days

    return render(request, 'core/university/main.html', {
        'university': university,
        'students': students,
        'total_students': total_students,
        'enrolled_students': enrolled_students,
        'students_due_for_attachment': students_due_for_attachment,
        'last_7_days': last_7_days,
        'total_students_data': total_students_data,
        'enrolled_students_data': enrolled_students_data,
        'attachment_due_data': attachment_due_data,
    })



@login_required
def university_profile(request):
    # Ensure the logged-in user is a University Admin
    if not request.user.extendeduser.role == 'University Admin':
        return HttpResponseForbidden("You do not have permission to access this page.")

    # Get the university associated with the logged-in user
    university = get_object_or_404(University, university_admin=request.user)

    if request.method == 'POST':
        form = UniversityForm(request.POST, instance=university)
        if form.is_valid():
            form.save()
            return redirect('university_profile')  # Replace with the correct profile page URL name
    else:
        form = UniversityForm(instance=university)

    context = {
        'form': form,
        'university': university,
    }
    return render(request, 'core/university/profile.html', context)


@method_decorator(login_required, name='dispatch')
class UniversityUpdateView(UpdateView):
    model = University
    form_class = UniversityForm
    template_name = 'core/university/edit_profile.html'

    def get_object(self, queryset=None):
        # Ensure only the university associated with the current user is editable
        return get_object_or_404(University, university_admin=self.request.user)

    def get_success_url(self):
        # Redirect to the profile page or analytics after successful update
        return reverse_lazy('university_profile')  # Replace with the actual profile page URL name

@login_required
def add_student(request):
    # Check if the user is a University Admin
    try:
        if request.user.extendeduser.role != 'University Admin':
            messages.error(request, "You do not have permission to add students.")
            return redirect('home')  # Redirect to some home page or dashboard
    except ExtendedUser.DoesNotExist:
        messages.error(request, "User role not found.")
        return redirect('home')

    # Get the university associated with the university admin
    university = University.objects.get(university_admin=request.user)

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            # Save the student without assigning a user yet
            student = form.save(commit=False)
            student.university = university
            student.save()
            messages.success(request, "Student added successfully. The student will register their own account later.")

            # Clear the form and redirect to the same page
            return redirect('add_student')  # Redirect to the same page for adding another student
    else:
        form = StudentForm()

    return render(request, 'core/university/add_student.html', {'form': form})


@login_required
def bulk_upload_students(request):
    # Check if the user is a University Admin
    try:
        if request.user.extendeduser.role != 'University Admin':
            messages.error(request, "You do not have permission to upload students.")
            return redirect('home')
    except User.DoesNotExist:
        messages.error(request, "User role not found.")
        return redirect('home')

    university = University.objects.get(university_admin=request.user)

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, "Please upload a file.")
            return redirect('bulk_upload_students')

        try:
            # Read CSV or Excel file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                messages.error(request, "Invalid file type. Please upload a CSV or Excel file.")
                return redirect('bulk_upload_students')

            # Expected columns: registration_number, program_of_study, year_of_study
            required_columns = ['registration_number', 'program_of_study', 'year_of_study']
            if not all(column in df.columns for column in required_columns):
                messages.error(request, f"File must contain the following columns: {', '.join(required_columns)}")
                return redirect('bulk_upload_students')

            # Process and save each row
            for _, row in df.iterrows():
                Student.objects.create(
                    registration_number=row['registration_number'],
                    program_of_study=row['program_of_study'],
                    year_of_study=row['year_of_study'],
                    university=university
                )

            messages.success(request, "Students uploaded successfully.")
            return redirect('bulk_upload_students')

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('bulk_upload_students')

    return render(request, 'core/university/bulk_upload_students.html')


# Helper function to check if the user is a university admin
def is_university_admin(user):
    return hasattr(user, 'extendeduser') and user.extendeduser.role == 'University Admin'

@login_required
@user_passes_test(is_university_admin)
def result_list(request):
    university = request.user.university_admin.first()  # Fetch the admin's university
    results = Result.objects.filter(student__university=university)
    return render(request, 'core/university/result_list.html', {'results': results})

@login_required
@user_passes_test(is_university_admin)
def upload_single_result(request):
    if request.method == 'POST':
        form = SingleResultForm(request.POST, user=request.user)  # Pass user to form via kwargs
        if form.is_valid():
            result = form.save(commit=False)
            # Ensure the student belongs to the university of the logged-in admin
            if result.student.university == request.user.university_admin.first():
                result.save()
                return redirect('result_list')
            else:
                form.add_error(None, "Student does not belong to your university.")
    else:
        form = SingleResultForm(initial={'user': request.user})  # Pass user via initial
    return render(request, 'core/university/upload_single.html', {'form': form})


@login_required
@user_passes_test(is_university_admin)
def upload_bulk_results(request):
    if request.method == 'POST':
        form = BulkResultUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            university = request.user.university_admin.first()
            try:
                csv_file = file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(csv_file)
                for row in reader:
                    student = Student.objects.get(registration_number=row['registration_number'], university=university)
                    Result.objects.create(
                        student=student,
                        course_name=row['course_name'],
                        grade=row['grade'],
                        semester=row['semester'],
                        year=row['year']
                    )
                return redirect('result_list')
            except Exception as e:
                form.add_error(None, f"Error processing file: {e}")
    else:
        form = BulkResultUploadForm()
    return render(request, 'core/university/upload_bulk.html', {'form': form})



@login_required
def student_list(request):
    # Check if the user is a University Admin
    try:
        if request.user.extendeduser.role != 'University Admin':
            messages.error(request, "You do not have permission to this page")
            return redirect('home')
    except User.DoesNotExist:
        messages.error(request, "User role not found.")
        return redirect('home')

    university = University.objects.get(university_admin=request.user)

    # Fetch students associated with this university
    students = Student.objects.filter(university=university)

    return render(request, 'core/university/student_list.html', {'students': students})




@login_required
@user_passes_test(is_university_admin)  # Reuse the helper function
def enrollment_report(request):
    university = request.user.university_admin.first()  # Get the admin's university
    students = Student.objects.filter(university=university)

    # Aggregations for the enrollment report
    by_year = students.values('year_of_study').annotate(total=Count('id')).order_by('year_of_study')
    by_program = students.values('program_of_study').annotate(total=Count('id')).order_by('program_of_study')
    total_students = students.count()

    context = {
        'by_year': by_year,
        'by_program': by_program,
        'total_students': total_students,
    }
    return render(request, 'core/university/enrollment_report.html', context)



def performance_analytics(request):
    # Fetch the university the current user is associated with
    university = University.objects.get(university_admin=request.user)

    # Filter results for students in the selected university
    results = Result.objects.filter(student__university=university)

    # Define a mapping for letter grades to numeric equivalents
    grade_mapping = {
        "A": 4.0,
        "B": 3.0,
        "C": 2.0,
        "D": 1.0,
        "F": 0.0
    }

    # Annotate a new field for numeric grades
    results = results.annotate(
        numeric_grade=Cast('grade', FloatField())
    )

    # Replace non-numeric grades with mapped numeric equivalents
    results_with_numeric_grades = []
    for result in results:
        try:
            numeric_grade = float(result.grade)
        except ValueError:
            numeric_grade = grade_mapping.get(result.grade.upper(), None)  # Default to None if unmapped
        if numeric_grade is not None:
            results_with_numeric_grades.append(numeric_grade)

    # Calculate overall average grade if there are valid numeric grades
    overall_avg_grade = (
        sum(results_with_numeric_grades) / len(results_with_numeric_grades)
        if results_with_numeric_grades else None
    )

    # Prepare context for rendering
    context = {
        'university': university,
        'overall_avg_grade': overall_avg_grade,
        'results': results,
    }

    return render(request, 'core/university/performance_analytics.html', context)




def view_enrolled_students(request):
    # Logic to filter and display only enrolled students
    enrolled_students = Student.objects.filter(status='Enrolled')
    return render(request, 'core/university/student_list.html', {'students': enrolled_students})

#student dashboard
def student_dashboard(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Student':
        return redirect('login')  # Ensure only students can access this view

    student = request.user.student

    # Applications QuerySet
    applications = Application.objects.filter(student=student)
    applied_vacancy_ids = set(applications.values_list('vacancy_id', flat=True))  # Get IDs of applied vacancies

    # Vacancies
    available_vacancies = Vacancy.objects.all()  # Add filtering logic if needed

    return render(request, 'core/student/student_dashboard.html', {
        'student': student,
        'applications': applications,
        'available_vacancies': available_vacancies,
        'applied_vacancy_ids': applied_vacancy_ids,  # Pass applied vacancy IDs
    })

def student_notifications(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Student':
        return redirect('login')

    student = request.user.student
    notifications = Notification.objects.filter(student=student, is_confirmed=False)

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = Notification.objects.get(id=notification_id, student=student)

        # Confirm the invitation
        if 'confirm' in request.POST:
            notification.is_confirmed = True
            notification.save()

            # Add student to the company waitlist
            Waitlist.objects.create(
                company=notification.vacancy.company,
                student=student,
                vacancy=notification.vacancy
            )
        elif 'decline' in request.POST:
            notification.delete()

        return redirect('student_notifications')

    return render(request, 'core/student/notifications.html', {'notifications': notifications})


from .forms import CustomPasswordChangeForm

@login_required
def profile_view(request):
    student = request.user.student
    
    if request.method == "POST":
        profile_form = StudentProfileForm(request.POST, instance=student)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        
        if profile_form.is_valid():
            profile_form.save()
            return redirect('profile')
        
        elif password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            return redirect('profile')
    else:
        profile_form = StudentProfileForm(instance=student)
        password_form = CustomPasswordChangeForm(user=request.user)
    
    return render(
        request, 
        'core/student/profile.html', 
        {
            'profile_form': profile_form, 
            'password_form': password_form, 
            'student': student
        }
    )

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Resume, CoverLetter

@login_required
def internship_preparation_view(request):
    # Get the logged-in student's resume and cover letter
    student = request.user.student
    resume = get_object_or_404(Resume, student=student)
    cover_letter = get_object_or_404(CoverLetter, student=student)

    context = {
        'resume': resume.file.url if resume else None,
        'cover_letter': cover_letter.file.url if cover_letter else None,
    }
    return render(request, 'core/student/internship_preparation.html', context)



def application_status(request):
    # Ensure the user is authenticated and is a student
    if not request.user.is_authenticated or not hasattr(request.user, 'student'):
        return redirect('login')  # Redirect to login if not authenticated
    
    # Fetch all applications made by the logged-in student
    student = request.user.student
    applications = Application.objects.filter(student=student).select_related('vacancy', 'vacancy__company')

    # Get a list of applied vacancy IDs to check if the student has applied
    applied_vacancy_ids = applications.values_list('vacancy_id', flat=True)

    context = {
        'applications': applications,
        'applied_vacancy_ids': applied_vacancy_ids,
    }
    return render(request, 'core/student/application_status.html', context)




def internship_opportunities(request):
    # Fetch all active vacancies
    active_vacancies = Vacancy.objects.filter(application_deadline__gte=timezone.now())

    # Check if the student is logged in and a valid student
    if request.user.is_authenticated and hasattr(request.user, 'student'):
        student = request.user.student
    else:
        return redirect('login')  # Redirect to login if not authenticated

    context = {
        'active_vacancies': active_vacancies,
        'current_time': timezone.now(),  # Pass the current time to the template
    }
    return render(request, 'core/student/internship_opportunities.html', context)



@login_required
def apply_for_vacancy(request, vacancy_id):
    # Get the logged-in student's profile
    student = Student.objects.get(user=request.user)

    # Check if the student has a resume and cover letter
    if not Resume.objects.filter(student=student).exists():
        return redirect('create_resume')  # Redirect to the resume creation page

    if not CoverLetter.objects.filter(student=student).exists():
        return redirect('create_cover_letter')  # Redirect to the cover letter creation page

    vacancy = Vacancy.objects.get(id=vacancy_id)
    
    # Check if the student has already applied
    if Application.objects.filter(student=student, vacancy=vacancy).exists():
        messages.error(request, "You have already applied for this internship.")
        return redirect('application_status')  # Redirect back to the vacancy list

    # Create an application
    application = Application.objects.create(
        vacancy=vacancy,
        student=student,
        status='Applied'
    )
    messages.success(request, "Your application has been submitted successfully!")
    return redirect('application_status')

@login_required
def create_resume(request):
    # Ensure the student has access to create a resume
    student = Student.objects.get(user=request.user)

    if request.method == 'POST':
        resume_file = request.FILES.get('resume_file')
        if resume_file:
            resume = Resume.objects.create(student=student, file=resume_file)
            messages.success(request, "Resume created successfully!")
            return redirect('create_cover_letter')  # Redirect to cover letter creation
        else:
            messages.error(request, "Please upload a valid resume file.")

    return render(request, 'core/student/create_resume.html')

@login_required
def create_cover_letter(request):
    student = Student.objects.get(user=request.user)

    if request.method == 'POST':
        cover_letter_file = request.FILES.get('cover_letter_file')
        if cover_letter_file:
            cover_letter = CoverLetter.objects.create(student=student, file=cover_letter_file)
            messages.success(request, "Cover letter created successfully!")
            return redirect('application_status')  # Redirect to the vacancy list
        else:
            messages.error(request, "Please upload a valid cover letter file.")

    return render(request, 'core/student/create_cover_letter.html')


#website
def welcome_page(request):
    return render(request,'core/website/index.html')
def get_started_page(request):
    return render(request,'core/website/courses.html')
def features_page(request):
    return render(request,'core/website/feature-page.html')
def about_page(request):
    return render(request,'core/website/about.html')
def pricing_page(request):
    return render(request,'core/website/pricing.html')
def contact_page(request):
    return render(request,'core/website/contact.html')    
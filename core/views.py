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
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.utils.timezone import now
from django.db.models import Q

#login view
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to the dashboard based on user role
                if user.extendeduser.role == 'System Admin':
                    return redirect('system_admin_dashboard')
                elif user.extendeduser.role == 'Company Representative':
                    return redirect('company_dashboard')
                elif user.extendeduser.role == 'University Admin':
                    return redirect('university_dashboard')
                elif user.extendeduser.role == 'Student':
                    return redirect('student_dashboard')
                else:
                    return redirect('welcome_page')
            else:
                # Authentication failed, add error message
                messages.error(request, "Invalid username or password.")
                return render(request, 'core/auth/index.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'core/auth/index.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logging out

#registration views
def company_registration(request):
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_dashboard')  # Redirect to the company dashboard after registration
    else:
        form = CompanyRegistrationForm()
    return render(request, 'core/company/company_registration.html', {'form': form})

def student_registration(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Create the User and link it to the existing Student
            messages.success(request, "Your account has been created successfully!")
            return redirect('login')  # Redirect to the login page
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
            form.save()
            return redirect('university_dashboard')  # Redirect after successful registration
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


#company
def company_dashboard(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Company Representative':
        return redirect('login')

    # Get the company associated with the authenticated user
    company = Company.objects.get(company_rep=request.user)
    user = request.user
    # Get all vacancies for the company
    vacancies = company.vacancy_set.all()

    return render(request, 'core/company/company_dashboard.html', {
        'company': company,
        'vacancies': vacancies,
        'user':user
    })


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
def vacancy_list(request):
    vacancies = Vacancy.objects.all()  # Optionally filter by other criteria (e.g., active, deadline passed)
    return render(request, 'core/company/vacancy_list.html', {'vacancies': vacancies})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Vacancy, Application

# Update Vacancy
# Update Vacancy View
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


#university
def university_dashboard(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'University Admin':
        return redirect('login')  # Ensure only university admins can access this view

    
    university = University.objects.get(university_admin=request.user)
    students = university.student_set.all()  # Assuming one-to-many relation between university and students

    return render(request, 'core/university/main.html', {
        'university': university,
        'students': students
    })
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


#student dashboard
def student_dashboard(request):
    if not request.user.is_authenticated or request.user.extendeduser.role != 'Student':
        return redirect('login')  # Ensure only students can access this view

    student = request.user.student
    applications = Application.objects.filter(student=student)
    available_vacancies = Vacancy.objects.all()  # You can add filtering logic if needed

    return render(request, 'core/student/student_dashboard.html', {
        'student': student,
        'applications': applications,
        'available_vacancies': available_vacancies
    })


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

    context = {
        'applications': applications,
    }
    return render(request, 'core/student/application_status.html', context)


def internship_opportunities(request):
    # Fetch all active vacancies
    active_vacancies = Vacancy.objects.filter(application_deadline__gte=now())

    # Check if the student is logged in and a valid student
    if request.user.is_authenticated and hasattr(request.user, 'student'):
        student = request.user.student
    else:
        return redirect('login')  # Redirect to login if not authenticated

    context = {
        'active_vacancies': active_vacancies,
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
    
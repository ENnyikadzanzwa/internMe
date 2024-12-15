from django import forms
from .models import *
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

class UniversityRegistrationForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'address', 'contact_email']
    
    admin_username = forms.CharField(max_length=150, required=True)
    admin_email = forms.EmailField(required=True)
    admin_password = forms.CharField(widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if University.objects.filter(name=name).exists():
            raise forms.ValidationError("An institution with this name already exists.")
        return name

    def clean_contact_email(self):
        contact_email = self.cleaned_data.get('contact_email')
        if University.objects.filter(contact_email=contact_email).exists():
            raise forms.ValidationError("This contact email is already in use.")
        return contact_email

    def clean_admin_email(self):
        admin_email = self.cleaned_data.get('admin_email')
        if User.objects.filter(email=admin_email).exists():
            raise forms.ValidationError("This admin email is already registered.")
        return admin_email

    def save(self, commit=True):
        university = super().save(commit=False)
        if commit:
            user = ExtendedUser.objects.create(
                user=User.objects.create_user(
                    username=self.cleaned_data['admin_username'],
                    email=self.cleaned_data['admin_email'],
                    password=self.cleaned_data['admin_password']
                ),
                role='University Admin'
            )
            university.university_admin = user.user
            university.save()
        return university

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['registration_number', 'program_of_study', 'year_of_study']
class StudentUploadForm(forms.Form):
    file = forms.FileField()



class StudentRegistrationForm(forms.Form):
    registration_number = forms.CharField(max_length=50, required=True)
    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=True,
        empty_label="Select University",
    )
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned_data = super().clean()
        reg_number = cleaned_data.get('registration_number')
        university = cleaned_data.get('university')

        # Check if the student exists
        if not Student.objects.filter(registration_number=reg_number, university=university).exists():
            raise forms.ValidationError("No student found with this registration number and university.")

        # Check if the student already has a user account
        student = Student.objects.get(registration_number=reg_number, university=university)
        if student.user:
            raise forms.ValidationError("This student already has an account.")

        return cleaned_data

    def save(self):
        # Get cleaned data
        reg_number = self.cleaned_data['registration_number']
        university = self.cleaned_data['university']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        # Retrieve the existing student
        student = Student.objects.get(registration_number=reg_number, university=university)

        # Create the User
        user = User.objects.create_user(
            username=reg_number,  # Set username to registration number
            email=email,
            password=password
        )

        # Create ExtendedUser with role 'student'
        extended_user = ExtendedUser.objects.create(user=user, role='Student')

        # Link the User to the Student
        student.user = user
        student.save()






class CompanyRegistrationForm(forms.ModelForm):
    # Add fields for the representative's details
    rep_username = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Representative Username'}),
    )
    rep_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Representative Email'}),
    )
    rep_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Representative Password'}),
    )

    class Meta:
        model = Company
        fields = ['name', 'address', 'contact_email', 'industry']  # Fields from the Company model
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Company Name'}),
            'address': forms.TextInput(attrs={'placeholder': 'Institution Address'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'Contact Email'}),
            'industry': forms.TextInput(attrs={'placeholder': 'Industry'}),
        }

    def clean_rep_username(self):
        username = self.cleaned_data['rep_username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_rep_email(self):
        email = self.cleaned_data['rep_email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        # Save the company and its representative user
        company = super().save(commit=False)
        rep_username = self.cleaned_data['rep_username']
        rep_email = self.cleaned_data['rep_email']
        rep_password = self.cleaned_data['rep_password']

        if commit:
            # Create the representative user
            user = User.objects.create_user(
                username=rep_username,
                email=rep_email,
                password=rep_password,
            )

            # Assign additional details for the representative if required (e.g., roles)
            # Assuming you have an ExtendedUser model
            from core.models import ExtendedUser  # Replace with your app path
            ExtendedUser.objects.create(
                user=user,
                role='Company Representative'  # Role specific to your app logic
            )

            # Link the representative user to the company
            company.company_rep = user
            company.save()

        return company

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )



class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ['title', 'description', 'requirements', 'location', 'application_deadline']
        
    application_deadline = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'program_of_study', 'year_of_study', 'address', 
            'phone', 'about', 'twitter', 'facebook', 
            'instagram', 'linkedin'
        ]

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize fields
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter your old password'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter new password'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm new password'})


class SingleResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'course_name', 'grade', 'semester', 'year']

class BulkResultUploadForm(forms.Form):
    file = forms.FileField(help_text="Upload a CSV file with columns: registration_number, course_name, grade, semester, year")

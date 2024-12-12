from django import forms
from .models import *
from django.contrib.auth.forms import PasswordChangeForm

class UniversityRegistrationForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'address', 'contact_email']
    
    # Additional admin fields
    admin_username = forms.CharField(max_length=150, required=True)
    admin_email = forms.EmailField(required=True)
    admin_password = forms.CharField(widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Automatically add the 'form-control' class to all form fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

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
    class Meta:
        model = Company
        fields = ['name', 'address', 'contact_email', 'industry']

    rep_username = forms.CharField(max_length=150, required=True)
    rep_email = forms.EmailField(required=True)
    rep_password = forms.CharField(widget=forms.PasswordInput, required=True)

    def save(self, commit=True):
        company = super().save(commit=False)
        if commit:
            user = User.objects.create_user(
                username=self.cleaned_data['rep_username'],
                email=self.cleaned_data['rep_email'],
                password=self.cleaned_data['rep_password']
            )
            
            # Create ExtendedUser instance
            ExtendedUser.objects.create(
                user=user,
                role='Company Representative'
            )
            
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

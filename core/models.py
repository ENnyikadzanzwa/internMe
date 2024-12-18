from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# User extension model for adding the 'role' field
class ExtendedUser(models.Model):
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('University Admin', 'University Admin'),
        ('Company Representative', 'Company Representative'),
        ('System Admin', 'System Admin')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# University model
class University(models.Model):
    name = models.CharField(max_length=255)
    mission = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    address = models.TextField()
    contact_email = models.EmailField()
    university_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='university_admin')

    def __str__(self):
        return self.name

# Student model
class Student(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    registration_number = models.CharField(max_length=50, unique=True)
    university = models.ForeignKey('University', on_delete=models.CASCADE)
    program_of_study = models.CharField(max_length=255)
    year_of_study = models.IntegerField()
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.registration_number} - {self.program_of_study}"

# Adding Resume and CoverLetter models
class Resume(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume of {self.student.user.username}"

class CoverLetter(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    file = models.FileField(upload_to='cover_letters/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cover Letter of {self.student.user.username}"

# Company model
class Company(models.Model):
    name = models.CharField(max_length=255)
    mission = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    address = models.TextField()
    contact_email = models.EmailField()
    company_rep = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_rep')
    industry = models.CharField(max_length=255)

    def __str__(self):
        return self.name
class CompanyDepartment(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.company.name})"
class CompanyStudent(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    department = models.ForeignKey('CompanyDepartment', on_delete=models.CASCADE)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.department.name}"

# Vacancy model
class Vacancy(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    application_deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# Application model
class Application(models.Model):
    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Under Review', 'Under Review')
    ]
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application by {self.student.user.username} for {self.vacancy.title}"

class Notification(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    vacancy = models.ForeignKey('Vacancy', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_confirmed = models.BooleanField(default=False)
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.student.user.username}"

class Message(models.Model):
    recipient = models.ForeignKey('University', on_delete=models.CASCADE)
    sender = models.ForeignKey('Company', on_delete=models.CASCADE)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.name} to {self.recipient.name}"

class Waitlist(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    vacancy = models.ForeignKey('Vacancy', on_delete=models.CASCADE)
    is_enrolled = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Waitlist: {self.student.user.username} for {self.company.name}"


# Result model
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.CharField(max_length=255)
    grade = models.FloatField()
    semester = models.CharField(max_length=50)
    year = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for {self.student.user.username}: {self.course} - {self.grade}"

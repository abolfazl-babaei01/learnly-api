from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.validators import phone_regex
from .managers import UserManager
from django.utils.timezone import now, timedelta
import random
import string


# Create your models here.

def generate_random_otp_code():
    return ''.join(random.choices(string.digits, k=6))


class Otp(models.Model):
    phone_number = models.CharField(max_length=11, validators=(phone_regex,))
    otp_code = models.CharField(max_length=6, default=generate_random_otp_code())
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Otp for {self.phone_number}'

    def regenerate_otp(self):
        """
        Generate new OTP code and save it to database.
        """
        self.otp_code = generate_random_otp_code()
        self.save()

    def valid_delay(self):
        """
        Checks if at least 3 minutes have passed since the last OTP generation.
        """
        if self.created_at and now() <= self.created_at + timedelta(minutes=3):
            return False

        self.created_at = now()
        self.save()
        return True

    def is_otp_valid(self, otp):
        """
        Verifies if the provided OTP matches the generated code and
        ensures it has not expired (valid for up to 5 minutes).
        """
        if self.otp_code == str(otp) and now() <= self.created_at + timedelta(minutes=5):
            return True
        return False

    def send_sms_otp(self):
        """
        send sms to user phone number
        """
        print(f"Otp code {self.otp_code} To {self.phone_number}")


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.

    This model uses phone number as the primary identifier for authentication
    instead of the default username. It also includes additional fields such as:

    - `role`: Defines whether the user is a student or a teacher.
    - `avatar`: Optional profile image.
    - `bio`: Optional short biography.

    Fields:
        phone_number (str): A unique 11-digit phone number used for login.
        role (str): User role, either 'student' or 'teacher'.
        avatar (Image): User profile picture (optional).
        bio (Text): Short user bio (optional).

    Methods:
        is_teacher(): Returns True if the user is a teacher.
        is_student(): Returns True if the user is a student.
    """

    class RoleChoices(models.TextChoices):
        student = ('student', 'Student')
        teacher = ('teacher', 'Teacher')

    phone_number = models.CharField(max_length=11, unique=True, validators=(phone_regex,))
    role = models.CharField(max_length=7, choices=RoleChoices.choices, default=RoleChoices.student)

    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.phone_number

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.validators import phone_regex
from .managers import UserManager


# Create your models here.


class CustomUser(AbstractUser):
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

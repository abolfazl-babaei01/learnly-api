from django.contrib import admin
from .models import CustomUser, Otp

# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    pass


@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    pass
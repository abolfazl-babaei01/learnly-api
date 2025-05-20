from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # auth - otp
    path('auth/otp/request/', views.OtpRequestView.as_view(), name='otp-request'),
    path('auth/otp/verify/', views.VerifyUserOtpView.as_view(), name='otp-verify'),
    path('auth/password/login/', views.PasswordLoginView.as_view(), name='password-login'),

    # password management
    path('change/password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('forgot/password/', views.ForgotPasswordView.as_view(), name='forgot-password'),

    # change phone number
    path('change/phone/', views.ChangePhoneNumberView.as_view(), name='change-phone'),
]
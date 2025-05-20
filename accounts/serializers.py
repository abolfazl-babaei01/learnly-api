from rest_framework import serializers
from rest_framework.fields import empty
from .models import CustomUser, Otp
from utils.validators import phone_regex
from django.contrib.auth import authenticate, password_validation


class OtpRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a new OTP code for a given phone number.

    Fields:
        phone_number (str): The phone number to which the OTP will be sent.

    Behavior:
        - If the OTP is expired or delay is valid, a new OTP will be generated and sent.
        - If the OTP is still valid (not expired), raises a ValidationError.
    """

    phone_number = serializers.CharField(max_length=11, validators=(phone_regex,))

    def create(self, validated_data):

        otp, create = Otp.objects.get_or_create(phone_number=validated_data.get('phone_number'))

        if otp.valid_delay():
            otp.regenerate_otp()
            otp.send_sms_otp()
        else:
            raise serializers.ValidationError({'error': 'OTP has not expired.'})
        return otp


class BaseOtpVerificationSerializer(serializers.Serializer):
    """
    Base serializer for OTP verification, used in other serializers like password reset or phone number change.

    Fields:
        phone_number (str): The phone number to verify the OTP for.
        otp (str): The 6-digit OTP code.

    Behavior:
        - Validates the OTP against the database.
        - Stores the OTP instance if valid.
    """
    phone_number = serializers.CharField(max_length=11, validators=(phone_regex,))
    otp = serializers.CharField(max_length=6)

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.otp_verification = None

    def validate(self, data):
        otp = data.get('otp')
        phone_number = data.get('phone_number')

        try:
            otp_code = Otp.objects.get(phone_number=phone_number)
        except Otp.DoesNotExist:
            raise serializers.ValidationError({'error': 'invalid otp code or phone number.'})

        if not otp_code.is_otp_valid(otp) or not otp.isdigit():
            raise serializers.ValidationError('otp code invalid')
        self.otp_verification = otp_code
        return data


class VerifyUserOtpSerializer(BaseOtpVerificationSerializer):
    """
    Serializer to verify a user's OTP and optionally register them if not already registered.

    Fields:
        password (str, optional): Password for new user registration.

    Behavior:
        - If user with given phone exists and is active: Verifies OTP and returns the user.
        - If user does not exist: Registers a new user using the phone and password.
        - Deletes the used OTP upon success.
       """
    password = serializers.CharField(write_only=True, required=False)

    def create(self, validated_data):
        phone_number = validated_data.get('phone_number')
        password = validated_data.get('password')

        user = CustomUser.objects.filter(phone_number=phone_number, is_active=True).first()

        if not user:
            if not password:
                raise serializers.ValidationError({'Error': 'Password is required for registration'})

            user = CustomUser.objects.create_user(phone_number=phone_number, password=password, username=phone_number)
        self.otp_verification.delete()
        return user


class PasswordLoginSerializer(serializers.Serializer):
    """
    Serializer for authenticating users with phone number and password.

    Fields:
        phone_number (str): User's registered phone number.
        password (str): User's password.

    Behavior:
        - Authenticates user with credentials.
        - Checks if account is active.
        - Returns user instance in validated data if authentication succeeds.
    """
    phone_number = serializers.CharField(max_length=11, validators=(phone_regex,))
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        user = authenticate(phone_number=phone_number, password=password)
        if not user:
            raise serializers.ValidationError({'error': 'Invalid phone number or password'})
        if not user.is_active:
            raise serializers.ValidationError({'error': 'Account not active'})
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer to allow authenticated users to change their password.

    Fields:
        old_password (str): Current password for verification.
        new_password (str): New password to be set.

    Behavior:
        - Validates current password.
        - Validates strength of the new password.
        - Updates user's password upon success.
    """
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def get_user(self):
        user = self.context['request'].user
        try:
            user = CustomUser.objects.get(id=user.id)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({'error': 'Invalid phone number or password'})
        return user

    def validate(self, data):
        user = self.get_user()

        if not user.check_password(data.get('old_password')):
            raise serializers.ValidationError({'error': 'Invalid old password'})

        password_validation.validate_password(data.get('new_password'))
        return data

    def save(self):
        user = self.get_user()

        user.set_password(self.validated_data.get('new_password'))
        user.save()
        return user


class ForgotPasswordSerializer(BaseOtpVerificationSerializer):
    """
    Serializer for resetting password using OTP (forgot password flow).

    Fields:
        new_password (str): New password to be set.
        confirm_password (str): Confirmation of the new password.

    Behavior:
        - Verifies OTP using base class.
        - Ensures new_password and confirm_password match.
        - Validates new password strength.
        - Updates user's password and deletes OTP.
    """
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        data = super().validate(data)

        if data.get('confirm_password') != data.get('new_password'):
            raise serializers.ValidationError({'error': 'New password and confirm password do not match'})

        password_validation.validate_password(data.get('new_password'))
        return data

    def get_user(self, data):
        user = CustomUser.objects.get(phone_number=data.get('phone_number'))
        return user

    def save(self, **kwargs):
        user = self.get_user(self.validated_data)

        user.set_password(self.validated_data.get('new_password'))
        user.save()
        self.otp_verification.delete()
        return user


class ChangePhoneNumberSerializer(BaseOtpVerificationSerializer):
    """
    Serializer to change the authenticated user's phone number using OTP verification.

    Fields:
        phone_number (str): New phone number to update.

    Behavior:
        - Verifies OTP for the new number.
        - Ensures new phone number is not already in use.
        - Updates user's phone number and deletes OTP.
    """

    def save(self, **kwargs):
        new_phone_number = self.validated_data.get('phone_number')
        user = self.context['request'].user
        if CustomUser.objects.filter(phone_number=new_phone_number).exists():
            raise serializers.ValidationError({'error': 'phone number already exists'})

        user.phone_number = new_phone_number
        user.save()
        self.otp_verification.delete()
        return user

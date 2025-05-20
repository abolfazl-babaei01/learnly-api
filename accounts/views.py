from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from .serializers import (OtpRequestSerializer, VerifyUserOtpSerializer, PasswordLoginSerializer,
                          ChangePasswordSerializer,
                          ChangePhoneNumberSerializer, ForgotPasswordSerializer)
from utils.jwt_token import create_token_response



class OtpRequestView(generics.GenericAPIView):
    """
    Handles OTP request by phone number.

    This view accepts a POST request with a phone number. If valid, it generates (or regenerates)
    an OTP and sends it via SMS. If the previous OTP is still valid and not expired, it returns an error.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = OtpRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'otp code sent successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyUserOtpView(generics.GenericAPIView):
    """
    Verifies the OTP code for user authentication or registration.

    This view accepts a POST request with a phone number and OTP code.
    If the user exists, it authenticates them.
    If not, it creates a new user (requires a password).
    On success, it returns a JWT token response.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = VerifyUserOtpSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(create_token_response(user), status=status.HTTP_200_OK)


class PasswordLoginView(generics.GenericAPIView):
    """
    Authenticates a user using phone number and password.

    This view accepts a POST request with phone number and password.
    If the credentials are valid, it returns a JWT token response.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordLoginSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(create_token_response(user), status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    """
    Allows an authenticated user to change their password.

    This view accepts a POST request with the old password and a new password.
    It verifies the old password, validates the new one, and updates it upon success.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password change successfully'}, status=status.HTTP_200_OK)


class ForgotPasswordView(generics.GenericAPIView):
    """
    Resets user password via OTP verification.

    This view accepts a POST request with a phone number, OTP, new password,
    and password confirmation. If the OTP is valid and passwords match, it sets the new password.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = ForgotPasswordSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'set new password successfully'}, status=status.HTTP_200_OK)


class ChangePhoneNumberView(generics.GenericAPIView):
    """
    Allows an authenticated user to change their phone number via OTP.

    This view accepts a POST request with a new phone number and OTP.
    If the OTP is valid and the new number is not already used, the phone number is updated.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChangePhoneNumberSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Phone number change successfully'}, status=status.HTTP_200_OK)

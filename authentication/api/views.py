from datetime import timedelta

import phonenumbers
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import User


def normalize_phone(raw):
    """Parse a phone number and return E.164 format, defaulting to North America (+1)."""
    parsed = phonenumbers.parse(raw, "US")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class WelcomeView(APIView):
    def get(self, request):
        return Response({"success": True, "message": "welcome message"})


class PhoneLoginView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response(
                {"success": False, "message": "Phone number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            normalized = normalize_phone(phone_number)
        except phonenumbers.NumberParseException:
            return Response(
                {"success": False, "message": "Invalid phone number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(phone_number=normalized).first()

        if not user:
            return Response(
                {"success": False, "registered": False, "phone_number": normalized},
                status=status.HTTP_200_OK,
            )

        now = timezone.now()
        recent_login = (
            user.last_login
            and (now - user.last_login) < timedelta(minutes=30)
        )
        access_lifetime = timedelta(minutes=5) if recent_login else timedelta(seconds=30)

        refresh = RefreshToken.for_user(user)
        refresh.access_token.set_exp(lifetime=access_lifetime)

        user.last_login = now
        user.save(update_fields=['last_login'])

        return Response({
            "success": True,
            "message": "Login successful.",
            "session_duration": str(access_lifetime),
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
            },
        })


class EmailLoginView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response(
                {"success": False, "message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"success": False, "registered": False, "email": email},
                status=status.HTTP_200_OK,
            )

        now = timezone.now()
        recent_login = (
            user.last_login
            and (now - user.last_login) < timedelta(minutes=30)
        )
        access_lifetime = timedelta(minutes=5) if recent_login else timedelta(seconds=30)

        refresh = RefreshToken.for_user(user)
        refresh.access_token.set_exp(lifetime=access_lifetime)

        user.last_login = now
        user.save(update_fields=['last_login'])

        return Response({
            "success": True,
            "message": "Login successful.",
            "session_duration": str(access_lifetime),
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
            },
        })


class RegisterView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        email = request.data.get('email', '').strip()
        username = request.data.get('username', '').strip()

        if not first_name or not last_name or not email or not username:
            return Response(
                {"success": False, "message": "All fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if phone_number:
            try:
                phone_number = normalize_phone(phone_number)
            except phonenumbers.NumberParseException:
                return Response(
                    {"success": False, "message": "Invalid phone number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if User.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"success": False, "message": "An account with this phone number already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if User.objects.filter(username=username).exists():
            return Response(
                {"success": False, "message": "Username is already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"success": False, "message": "Email is already in use."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        }
        if phone_number:
            user_data['phone_number'] = phone_number
        user = User.objects.create_user(**user_data)

        refresh = RefreshToken.for_user(user)
        refresh.access_token.set_exp(lifetime=timedelta(minutes=5))

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            "success": True,
            "message": "Registration successful.",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
            },
        }, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": str(user.phone_number) if user.phone_number else None,
            },
        })

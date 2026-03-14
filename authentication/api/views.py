from datetime import timedelta

import phonenumbers
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import User


class WelcomeView(APIView):
    def get(self, request):
        return Response({"success": True, "message": "welcome message"})


class PhoneLoginView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        print('>>>>>>>>>>.THIS IS PHONE NUMBER')
        if not phone_number:
            return Response(
                {"success": False, "message": "Phone number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prepend '+' if missing so international numbers are parsed correctly
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'

        try:
            parsed = phonenumbers.parse(phone_number, None)
            normalized = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            return Response(
                {"success": False, "message": "Invalid phone number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(phone_number=normalized).first()

        if not user:
            return Response(
                {"success": False, "message": "No account found with that phone number."},
                status=status.HTTP_404_NOT_FOUND,
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

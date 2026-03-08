from datetime import timedelta

from django.utils import timezone
from rest_framework import status
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
        if not phone_number:
            return Response(
                {"success": False, "message": "Phone number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Strip non-digit characters and normalize
        digits = ''.join(c for c in phone_number if c.isdigit())
        candidates = [digits, f'+{digits}', f'+1{digits}']

        user = None
        for candidate in candidates:
            user = User.objects.filter(phone_number=candidate).first()
            if user:
                break

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
            },
        })

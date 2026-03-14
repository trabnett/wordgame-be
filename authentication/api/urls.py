from django.urls import re_path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    re_path(r'^welcome/?$', views.WelcomeView.as_view(), name='api-welcome'),
    re_path(r'^login/?$', views.PhoneLoginView.as_view(), name='api-phone-login'),
    re_path(r'^user/?$', views.UserProfileView.as_view(), name='api-user-profile'),
    re_path(r'^token/refresh/?$', TokenRefreshView.as_view(), name='api-token-refresh'),
]

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^welcome/?$', views.WelcomeView.as_view(), name='api-welcome'),
    re_path(r'^login/?$', views.PhoneLoginView.as_view(), name='api-phone-login'),
    re_path(r'^user/?$', views.UserProfileView.as_view(), name='api-user-profile'),
]

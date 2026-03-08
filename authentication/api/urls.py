from django.urls import path

from . import views

urlpatterns = [
    path('welcome', views.WelcomeView.as_view(), name='api-welcome'),
    path('login', views.PhoneLoginView.as_view(), name='api-phone-login'),
]

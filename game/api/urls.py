from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^game/?$', views.CreateGameView.as_view(), name='api-create-game'),
]

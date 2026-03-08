from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Phone', {'fields': ('phone_number',)}),
    )

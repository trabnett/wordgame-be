from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'phone_number', 'is_staff')
    ordering = ('-id',)
    fieldsets = UserAdmin.fieldsets + (
        ('Phone', {'fields': ('phone_number',)}),
    )

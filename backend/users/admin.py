from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class UsersAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = (
        'username',
        'email',
    )
    ordering = (
        'username',
    )
    empty_value_display = '-пусто-'


admin.site.register(User, UsersAdmin)

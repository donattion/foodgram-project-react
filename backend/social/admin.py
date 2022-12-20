from django.contrib import admin

from .models import FavoritesList, FollowsList, ShoppingList


class FavoritesListAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    list_filter = (
        'user',
        'recipe',
    )
    search_fields = (
        'user',
        'recipe',
    )
    empty_value_display = '-пусто-'


class FollowsListAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
    list_filter = (
        'user',
        'author',
    )
    search_fields = (
        'user',
        'author',
    )
    empty_value_display = '-пусто-'


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    list_filter = (
        'user',
        'recipe',
    )
    search_fields = (
        'user',
        'recipe',
    )
    empty_value_display = '-пусто-'


admin.site.register(FavoritesList, FavoritesListAdmin)
admin.site.register(FollowsList, FollowsListAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)

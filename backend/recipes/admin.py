from django.contrib import admin

from .models import Ingredients, RecipeIngredients, Recipes, Tags


class TagsAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )
    search_fields = (
        'name',
        'slug',
    )
    empty_value_display = '-пусто-'


class IngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = (
        'name',
    )
    empty_value_display = '-пусто-'


class RecipesAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name',
        'get_tags',
    )
    list_filter = (
        'author',
        'name',
        'tags',
    )
    empty_value_display = '-пусто-'

    def get_tags(self, obj):
        return ', '.join([
            tags.name for tags
            in obj.tags.all()
        ])


class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ingredient',
        'recipe',
    )


admin.site.register(Tags, TagsAdmin)
admin.site.register(Ingredients, IngredientsAdmin)
admin.site.register(Recipes, RecipesAdmin)
admin.site.register(RecipeIngredients, RecipeIngredientsAdmin)

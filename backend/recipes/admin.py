from django.contrib import admin

from .models import Tags, Ingredients, Recipes


class TagsAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'color',
        'slug',
    )
    search_fields = (
        'title',
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
        'title',
        'get_tags',
    )
    list_filter = (
        'author',
        'title',
        'tags',
    )
    empty_value_display = '-пусто-'

    def get_tags(self, obj):
        return ', '.join([
                tags.title for tags
                in obj.tags.all()
            ])


admin.site.register(Tags, TagsAdmin)
admin.site.register(Ingredients, IngredientsAdmin)
admin.site.register(Recipes, RecipesAdmin)

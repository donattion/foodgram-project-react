from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Ingredients, Tags, Recipes


class IngredientsFilter(SearchFilter):
    """Фильтр ингредиентов"""
    search_param = 'title'

    class Meta:
        model = Ingredients
        fields = (
            'title',
        )


class RecipesFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tags.objects.all(),
    )
    is_favorited = filters.NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_list = filters.NumberFilter(
        method='filter_is_in_shopping_list'
    )

    class Meta:
        model = Recipes
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_list',
        )

    def filter_is_favorited(self, queryset, title, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorites__user=self.request.user
            )
        return queryset

    def filter_is_in_shopping_list(self, queryset, title, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shopping_list__user=self.request.user
            )
        return queryset

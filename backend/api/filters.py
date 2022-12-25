from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredients, Recipes, Tags
from rest_framework.filters import SearchFilter


class IngredientsFilter(SearchFilter):
    """Фильтр ингредиентов"""
    search_param = 'name'

    class Meta:
        model = Ingredients
        fields = (
            'name',
        )


class RecipesFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tags.objects.all(),
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipes
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_is_favorited(self, queryset, title, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorites__user=self.request.user
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, title, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shopping__user=self.request.user
            )
        return queryset

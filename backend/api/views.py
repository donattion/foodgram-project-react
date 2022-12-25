from django.db.models import Sum
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from social.models import FavoritesList, FollowsList, ShoppingList
from users.models import User

from .filters import IngredientsFilter, RecipesFilter
from .pagination import Pagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (CreateRecipesSerializer, FavoriteListSerializer,
                          IngredientsSerializer, RecipeReadSerializer,
                          ShoppingListSerializer, SubscriptionsSerializer,
                          TagsSerializer, UserSerializer)


class UserViewSet(UserViewSet):
    """Вывод пользователей"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = Pagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            serializer = SubscriptionsSerializer(
                author,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            FollowsList.objects.create(
                user=user,
                author=author
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            get_object_or_404(
                FollowsList,
                user=user,
                author=author
            ).delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(
            status=status.HTTP_404_NOT_FOUND
        )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(
            following__user=user
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    """Вывод тегов"""
    queryset = Tags.objects.all()
    permission_classes = (
        IsAuthenticatedOrReadOnly,
    )
    serializer_class = TagsSerializer


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод ингредиентов"""
    queryset = Ingredients.objects.all()
    permission_classes = (
        IsAuthenticatedOrReadOnly,
    )
    serializer_class = IngredientsSerializer
    filter_backends = (
        IngredientsFilter,
    )
    search_fields = ('^name',)


class RecipesViewSet(viewsets.ModelViewSet):
    """Вывод рецептов"""
    queryset = Recipes.objects.all()
    permission_classes = (
        IsOwnerOrReadOnly,
    )
    pagination_class = Pagination
    filter_backends = (
        DjangoFilterBackend,
    )
    serializer_class = CreateRecipesSerializer
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return CreateRecipesSerializer

    @action(
        detail=False,
        methods=['GET']
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredients.objects.filter(
            recipe__shopping__user=request.user
        ).order_by('ingredient__name').values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(amount=Sum('count'))
        return self.send_message(ingredients)

    @staticmethod
    def send_message(ingredients):
        shopping_list = 'Требуется к покупке:'
        for ingredient in ingredients:
            shopping_list += (
                f"\n{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['count']}"
            )
        file = 'shopping_list'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}.txt"'
        return response

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        context = {'request': request}
        recipe = get_object_or_404(Recipes, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = ShoppingListSerializer(
            data=data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            ShoppingList,
            user=request.user.id,
            recipe=get_object_or_404(Recipes, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        context = {"request": request}
        recipe = get_object_or_404(Recipes, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = FavoriteListSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            FavoritesList,
            user=request.user,
            recipe=get_object_or_404(Recipes, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

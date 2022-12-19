from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http.response import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)
from djoser.views import UserViewSet

from recipes.models import Tags, Ingredients, Recipes
from social.models import FollowsList
from users.models import User
from .serializers import (
    TagsSerializer,
    UsersSerializer,
    SubscriptionsSerializer,
    IngredientsSerializer,
    RecipeReadSerializer,
    CreateRecipesSerializer,
    UserPostCreateSerializer,
)
from .filters import IngredientsFilter, RecipesFilter
from .permissions import IsOwnerOrReadOnly
from .pagination import Pagination


class UserViewSet(UserViewSet):
    """Вывод пользователей"""
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = Pagination

    def create(self, request):
        if request.method == 'POST':
            serializer = UserPostCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

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
    search_fields = ('^title')


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
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return CreateRecipesSerializer

    @staticmethod
    def send_message(ingredients):
        for ingredient in ingredients:
            shopping_list += (
                f"\n{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['amount']}"
            )
        file = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}.txt"'
        return

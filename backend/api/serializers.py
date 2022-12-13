from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.fields import SerializerMethodField

from recipes.models import Tags, Recipes, Ingredients
from users.models import User


class RecipesFavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов"""
    class Meta:
        model = Recipes
        fields = (
            'id',
            'title',
            'image',
            'time',
        )


class UsersSerializer(UserSerializer):
    """Сериализатор пользователей"""
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

        def get_is_subscribed(self, obj):
            request = self.context.get('request')
            if self.context.get('request').user.is_anonymous:
                return False
            return obj.following.filter(user=request.user).exists()


class SubscriptionsSerializer(UserSerializer):
    """Сериализатор подписок"""
    class Meta(UsersSerializer.Meta):
        fields = UsersSerializer.Meta.fields + (
            'recipes_count',
            'recipes',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
        )

        def get_recipes_count(self, obj):
            return obj.recipes.count()

        def get_recipes(self, obj):
            request = self.context.get('request')
            recipes = obj.recipes.all()
            serializers = RecipesFavoritesSerializer(
                recipes,
                many=True,
                read_only=True
            )
            return serializers.data


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор тегов"""
    class Meta:
        model = Tags
        fields = (
            'id',
            'title',
            'color',
            'slug',
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра ингридиентов """

    class Meta:
        model = Ingredients
        fields = (
            'id',
            'title',
            'units_of_measurement',
        )



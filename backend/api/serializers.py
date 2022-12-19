from rest_framework import serializers, status
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework.fields import SerializerMethodField
from rest_framework.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField
from django.shortcuts import get_object_or_404

from recipes.models import Tags, Recipes, Ingredients, RecipeIngredients
from social.models import FavoritesList, ShoppingList, FollowsList
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
    is_subscribed = SerializerMethodField(read_only=True)

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
        if self.context.get('request').user.is_anonymous:
            return False
        return FollowsList.objects.filter(
                user=self.context.get('request').user, author=obj.id
            ).exists()


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя"""
    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class UserPostCreateSerializer(UserSerializer):
    """Сериализатор ответа после создания профиля"""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
        )


class SubscriptionsSerializer(UserSerializer):
    """Сериализатор подписок"""
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

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
        recipes = obj.recipes.all()
        serializers = RecipesFavoritesSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializers.data

    def validate(self, data):
        author_id = self.context.get(
            'request').parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.follower.filter(author=author_id).exists():
            raise ValidationError(
                detail='Подписка уже существует',
                code=status.HTTP_400_BAD_REQUEST,
        )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data


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
    """Сериализатор просмотра ингридиентов"""
    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class FavoriteListSerializer(serializers.ModelSerializer):
    """Сериализатор списка избранных"""
    class Meta:
        model = FavoritesList
        fields = (
            'user',
            'recipe',
        )

        def validate(self, data):
            user = data['user']
            if user.favorites.filter(recipe=data['recipe']).exists:
                raise serializers.ValidationError(
                    'Этот рецепт уже находится в избранном'
                )
            return data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок"""
    class Meta:
        model = ShoppingList
        fields = (
            'user',
            'recipe',
        )

        def validate(self, data):
            user = data['user']
            if user.shopping.filter(recipe=data['recipe']).exists():
                raise serializers.ValidationError(
                    'Этот рецепт уже находится в списке покупок'
                )
            return data


class RecipeFieldsSerializer(serializers.ModelSerializer):
    """Сериализатор для полей избранных и списка покупок"""
    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'time',
        )


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингридентов рецепта"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all()
    )
    title = serializers.ReadOnlyField(
        source='ingredients.title',
    )
    units_of_measurement = serializers.ReadOnlyField(
        source='ingredients.units_of_measurement'
    )

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'title',
            'units_of_measurement',
            'count',
        )


class CreateRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецептов"""
    ingredients = IngredientsSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all(),
        error_messages={
            'does_not_exist': 'Указанного тега не существует'
        }
    )
    image = Base64ImageField()
    author = UsersSerializer(
        read_only=True,
    )
    time = serializers.IntegerField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'author',
            'tags',
            'ingredients',
            'title',
            'image',
            'description',
            'time',
        )

    def validate_tags(self, tags):
        for tag in tags:
            if not Tags.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Этого тега не существует'
                )
            return tags

    def validate_time(self, time):
        if time < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть как минимум 1 минуту'
            )
        return time

    def validate_ingredients(self, ingredients):
        ingredients_ls = []
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_ls:
                raise serializers.ValidationError(
                    'Этот ингредиент уже есть'
                )
            ingredients_ls.append(ingredient['id'])
        return ingredients

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredients_ls = []
        for ingredient in ingredients:
            ingredients_ls.append(
                RecipeIngredients(
                    ingredient=ingredient.pop('id'),
                    count=ingredient.pop('count'),
                    recipe=recipe,
                )
            )
        RecipeIngredients.objects.bulk_create(ingredients_ls)

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(
            author=request.user,
            **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        RecipeIngredients.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецптов"""
    tags = TagsSerializer(
        many=True,
    )
    author = UsersSerializer(
        read_only=True,
        many=False,
    )
    ingredients = RecipeIngredientsSerializer(
        many=True,
        source='recipe_r',
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_list = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_list',
            'title',
            'image',
            'description',
            'time',
        )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredients.object.filter(recipe=obj)
        return RecipeIngredientsSerializer(
            ingredients,
            many=True
        ).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return obj.favor.filter(user=request.user).exists()

    def get_is_in_shopping_list(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return obj.shopping.filter(user=request.user).exists()
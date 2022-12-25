from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredients, RecipeIngredients, Recipes, Tags
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from social.models import FavoritesList, FollowsList, ShoppingList
from users.models import User


class RecipesFavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов"""
    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserSerializer(UserSerializer):
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

    def get_is_subscribed(self, author):
        return (not self.context.get('request').user.is_anonymous
                and FollowsList.objects.filter(
                user=self.context.get('request').user,
                author=author
                ).exists()
                )


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


class SubscriptionsSerializer(UserSerializer):
    """Сериализатор подписок"""
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes_count',
            'recipes'
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
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = RecipeFieldsSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data

    def validate(self, data):
        author_id = self.context.get(
            'request').parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.follower.filter(author=author_id).exists():
            raise ValidationError(
                detail='Данная подписка уже осуществлена',
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
            'name',
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
            'cooking_time',
        )


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор ингридентов рецепта"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all()
    )
    name = serializers.ReadOnlyField(
        source='ingredients.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
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
    author = UserSerializer(
        read_only=True,
    )
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'author',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_tags(self, tags):
        tags_ls = []
        if not tags:
            raise serializers.ValidationError(
                'Не указаны теги'
            )
        for tag in tags:
            if not Tags.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Этого тега не существует'
                )
            if tag['id'] in tags_ls:
                raise serializers.ValidationError(
                    'Этот тег уже есть'
                )
            tags_ls.append(tag['id'])
        return tags

    def validate_cooking_time(self, cooking_time: int):
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть как минимум 1 минуту'
            )
        return cooking_time

    def validate_ingredients(self, ingredients):
        ingredients_ls = []
        if not ingredients:
            raise serializers.ValidationError(
                'Не указаны ингредиенты'
            )
        for ingredient in ingredients:
            if not Ingredients.objects.filter(id=ingredient.id).exists():
                raise serializers.ValidationError(
                    'Этого ингредиента не существует'
                )
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
                    amount=ingredient.pop('amount'),
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
    author = UserSerializer(
        read_only=True,
        many=False,
    )
    ingredients = RecipeIngredientsSerializer(
        many=True,
        source='recipe_recipe',
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredients.objects.filter(recipe=obj)
        return RecipeIngredientsSerializer(
            ingredients,
            many=True
        ).data

    def get_is_favorited(self, obj):
        return (not self.context.get('request').user.is_anonymous
                and FavoritesList.objects.filter(
                user=self.context.get('request').user
                ).exists()
                )

    def get_is_in_shopping_cart(self, obj):
        return (not self.context.get('request').user.is_anonymous
                and ShoppingList.objects.filter(
                user=self.context.get('request').user
                ).exists()
                )

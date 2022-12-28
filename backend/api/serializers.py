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
        if FollowsList.objects.filter(
            user=user,
            author=author_id,
        ).exists():
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
            if FavoritesList.objects.filter(
                user=data['user'],
                recipe=data['recipe'],
            ).exists:
                raise serializers.ValidationError(
                    'Этот рецепт уже находится в избранном'
                )
            return data

    def to_representation(self, instance):
        return RecipesFavoritesSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок"""
    class Meta:
        model = ShoppingList
        fields = (
            'user',
            'recipe',
        )

        def validate(self, data):
            if ShoppingList.objects.filter(
                user=data['user'],
                recipe=data['recipe'],
            ).exists():
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
        queryset=Ingredients.objects.all(),
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class AddIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления Ингредиентов
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class CreateRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецептов"""
    ingredients = AddIngredientSerializer(
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
            'tags',
            'author',
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
            if tag in tags_ls:
                raise serializers.ValidationError(
                    'Этот тег уже есть'
                )
            tags_ls.append(tag)
        return tags

    def validate_cooking_time(self, cooking_time: int):
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть как минимум 1 минуту'
            )
        if cooking_time > 1440:
            raise serializers.ValidationError(
                'Время приготовления должно быть максимум 24 часа'
            )
        return cooking_time

    def validate(self, data):
        ingredients = data['ingredients']
        ingredients_ls = []
        for ingredient in ingredients:
            if ingredient in ingredients_ls:
                raise ValidationError(
                    'ывывы'
                )
            ingredients_ls.append(ingredient)
        return ingredients

    @staticmethod
    def create_ingredients(ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredients.objects.create(
                recipe=recipe, ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        context = self.context['request']
        tags_set = context.data['tags']
        recipe = instance
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        instance.tags.set(tags_set)
        RecipeIngredients.objects.filter(recipe=instance).delete()
        ingredients_req = context.data['ingredients']
        for ingredient in ingredients_req:
            ingredient_model = Ingredients.objects.get(id=ingredient['id'])
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredient=ingredient_model,
                amount=ingredient['amount'],
            )
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецптов"""
    tags = TagsSerializer(
        read_only=False,
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
    is_favorited = serializers.SerializerMethodField()
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
                and obj.favorites.filter(
                user=self.context.get('request').user
                ).exists()
                )

    def get_is_in_shopping_cart(self, obj):
        return (not self.context.get('request').user.is_anonymous
                and obj.shopping.filter(
                user=self.context.get('request').user
                ).exists()
                )

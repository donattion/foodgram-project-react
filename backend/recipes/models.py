from django.db import models

from users.models import User


class Tags(models.Model):
    """Модель тегов"""
    name = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Название',
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='Цветовой HEX-код',
    )
    slug = models.SlugField(
        max_length=10,
        unique=True,
        verbose_name='Slug',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredients(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(
        max_length=20,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=20,
        verbose_name='Единицы измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Игнредиенты'

    def __str__(self) -> str:
        return self.name


class Recipes(models.Model):
    """Модель рецептов"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=20,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='RecipeIngredients',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.name


class RecipeIngredients(models.Model):
    """Модель ингридиентов рецепта"""
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredient',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_r',
    )
    count = models.PositiveIntegerField(
        verbose_name='Количество ингредиента',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return (
            f'{self.ingredient.name} :: {self.ingredient.measurement_unit}'
            f' - {self.count}'
        )

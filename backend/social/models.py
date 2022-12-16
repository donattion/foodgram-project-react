from django.db import models
from django.db.models import UniqueConstraint, CheckConstraint, Q, F

from recipes.models import Recipes
from users.models import User


class FavoritesList(models.Model):
    """Модель добавления рецептов в избраное"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='adder',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецпет',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorites'


class FollowsList(models.Model):
    """Модель подписки на автора"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Последователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписка',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow'
            ),
            CheckConstraint(
                check=~Q(user=F('author')),
                name='no_self_following'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class ShoppingList(models.Model):
    """Модель списка покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='buyer',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='purchase',
        verbose_name='Рецпет',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping'
            )
        ]
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        default_related_name = 'shopping'
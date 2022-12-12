from django.db import models
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    username = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Логин',
    )
    email = models.EmailField(
        max_length=30,
        unique=True,
        verbose_name='Email',
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name='Фамилия',
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username
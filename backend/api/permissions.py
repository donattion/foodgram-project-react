from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Редактирование объекта возможно только для Автора.
    Для чтения доступно всем.
    """
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Редактирование объекта возможно только для Администратора.
    Для чтения доступно всем.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated and request.user.is_admin))

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated and request.user.is_admin))


class IsAdmin(permissions.BasePermission):
    """
    Редактирование объекта возможно только для Администратора.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin or request.user.is_superuser
        )

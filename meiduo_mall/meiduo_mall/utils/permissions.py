from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    要求访问用户是资源的拥有者
    """
    def has_permission(self, request, view):
        return str(request.user.id) == view.kwargs['pk']

from rest_framework import permissions

def in_editors_group(user):
    for group in user.groups.all():
        if group.name == 'editors':
            return True
    return False

class IsReadOnlyOrCanEdit(permissions.BasePermission):
    def has_permission(self, request, view):
        """
        Called on post to verify we're allowed to create an object.
        """
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Staff, editors, and superusers can create objects.
        user = request.user
        return user.is_staff or user.is_superuser or in_editors_group(user)

    def has_object_permission(self, request, view, obj):
        """
        Called on patch to verify we're allowed to edit an object.
        """
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user

        # Staff users can edit anything.
        if user.is_staff:
            return True

        # Non-staff users must be in the 'editors' group to edit.
        if not in_editors_group(user):
            return False

        # Non-staff editors can only edit models they are the owners of.
        if obj.owner != user:
            return False

        return True

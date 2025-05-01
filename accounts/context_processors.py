from django.contrib.auth.models import Group

def user_groups_context(request):
    if request.user.is_authenticated:
        return {
            'is_contributor': request.user.groups.filter(name="Contributors").exists(),
            'is_admin': request.user.groups.filter(name="Administrators").exists(),
            'is_superuser': request.user.is_superuser,
        }
    return {
        'is_contributor': False,
        'is_admin': False,
        'is_superuser': False,
    }

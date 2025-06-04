# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_groups')
    list_filter = ('groups',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups',)

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = "Groupes"

# Désenregistrer les modèles existants et les réenregistrer avec la configuration personnalisée
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Pour Group, on peut soit le laisser tel quel, soit le personnaliser
# Si vous voulez le personnaliser, décommentez les lignes ci-dessous :
# admin.site.unregister(Group)
# admin.site.register(Group, BaseGroupAdmin)

# Sinon, Group reste avec sa configuration par défaut
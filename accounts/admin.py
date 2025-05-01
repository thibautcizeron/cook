from django.contrib import admin
from django.contrib.auth.models import User, Group

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_groups')
    list_filter = ('groups',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups',)

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = "Groupes"

# Enregistre le modèle User avec la configuration personnalisée
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Assurer que le modèle Group est bien visible aussi
admin.site.register(Group)

from django.contrib import admin
from .models import Recette, Ingredient, Etape, Categorie, RecetteIngredient
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_type', 'object_name', 'ip_address')
    list_filter = ('action', 'model_type', 'timestamp', 'user')
    search_fields = ('object_name', 'user__username', 'details')
    readonly_fields = ('timestamp', 'user', 'action', 'model_type', 'object_name', 'object_id', 'details', 'ip_address')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        # Empêcher l'ajout manuel de logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # Empêcher la modification des logs
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permettre seulement aux superutilisateurs de supprimer les logs
        return request.user.is_superuser
    
class RecetteIngredientInline(admin.TabularInline):
    model = RecetteIngredient
    extra = 1
    autocomplete_fields = ['ingredient']

class EtapeInline(admin.TabularInline):
    model = Etape
    extra = 1
    can_delete = True  

@admin.register(Recette)
class RecetteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'nbpersonne')
    inlines = [RecetteIngredientInline, EtapeInline]

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['nom']

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom',)

@admin.register(RecetteIngredient)
class RecetteIngredientAdmin(admin.ModelAdmin):
    list_display = ('recette', 'ingredient', 'quantite')


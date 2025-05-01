from django.contrib import admin
from .models import Recette, Ingredient, Etape, Categorie, RecetteIngredient

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


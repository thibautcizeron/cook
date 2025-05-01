from django import forms
from .models import Ingredient, Categorie, Etape, Recette, RecetteIngredient
# from django.contrib.auth.models import User


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['nom', 'image']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'ingrédient'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'image']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la catégorie'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class RecetteForm(forms.ModelForm):
    class Meta:
        model = Recette
        fields = ['titre', 'categorie', 'nbpersonne', 'image']  

    etapes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class RecetteIngredientForm(forms.ModelForm):
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control ingredient-select'})
    )
    quantite = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control ingredient-quantity', 'placeholder': 'Quantité'})
    )

    class Meta:
        model = RecetteIngredient
        fields = ['ingredient', 'quantite']

class EtapeForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control etape-description', 'placeholder': 'Description de l’étape'})
    )

    class Meta:
        model = Etape
        fields = ['description']



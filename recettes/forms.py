# recettes/forms.py
from django import forms
from .models import Ingredient, Categorie, Etape, Recette, RecetteIngredient

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['nom']  # Retirer 'image' car on le gère manuellement
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'ingrédient'}),
        }

    # Ajouter un champ image personnalisé
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="Formats acceptés: JPG, PNG, WEBP (Max: 5MB)"
    )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Vérifier la taille du fichier (5MB max)
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("L'image ne peut pas dépasser 5MB.")
            
            # Vérifier le format
            allowed_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError("Format d'image non supporté. Utilisez JPG, PNG ou WEBP.")
        
        return image

class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom']  # Retirer 'image' car on le gère manuellement
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la catégorie'}),
        }

    # Ajouter un champ image personnalisé
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="Formats acceptés: JPG, PNG, WEBP (Max: 5MB)"
    )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Vérifier la taille du fichier (5MB max)
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("L'image ne peut pas dépasser 5MB.")
            
            # Vérifier le format
            allowed_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError("Format d'image non supporté. Utilisez JPG, PNG ou WEBP.")
        
        return image

class RecetteForm(forms.ModelForm):
    class Meta:
        model = Recette
        fields = ['titre', 'categorie', 'nbpersonne']  # Retirer 'image' car on le gère manuellement

    # Ajouter un champ image personnalisé
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text="Formats acceptés: JPG, PNG, WEBP (Max: 5MB)"
    )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Vérifier la taille du fichier (5MB max)
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("L'image ne peut pas dépasser 5MB.")
            
            # Vérifier le format
            allowed_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError("Format d'image non supporté. Utilisez JPG, PNG ou WEBP.")
        
        return image

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



from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Image(models.Model):
    """Modèle centralisé pour gérer toutes les images"""
    nom = models.CharField(max_length=255)
    fichier = models.ImageField(upload_to='images/')
    description = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"

class Categorie(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)  

    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categories"
        

class Ingredient(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='ingredients/')  

    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
    
class Recette(models.Model):
    titre = models.CharField(max_length=255)
    nbpersonne = models.IntegerField(default=1)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='recettes/', null=True, blank=True)

    def __str__(self):
        return self.titre
    
    def note_moyenne(self):
        notes = self.notes.all()
        if notes.exists():
            return sum(note.valeur for note in notes) / notes.count()
        return 0 
    
    class Meta:
        verbose_name = "Recette"
        verbose_name_plural = "Recettes"

class RecetteIngredient(models.Model):
    recette = models.ForeignKey(Recette, on_delete=models.CASCADE, related_name="recette_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantite = models.CharField(max_length=50)

    class Meta:
        unique_together = ('recette', 'ingredient')

    class Meta:
        verbose_name = "RecetteIngredient"
        verbose_name_plural = "RecetteIngredients"

class Etape(models.Model):
    recette = models.ForeignKey(Recette, on_delete=models.CASCADE, related_name="etapes")
    description = models.TextField()

    def __str__(self):
        return f"Étape {self.id} de {self.recette.titre}"
    
    class Meta:
        verbose_name = "Etape"
        verbose_name_plural = "Etapes"

class Note(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    recette = models.ForeignKey(Recette, on_delete=models.CASCADE, related_name="notes")
    valeur = models.IntegerField(
        validators=[
            MinValueValidator(1, message="La note minimale est 1"),
            MaxValueValidator(5, message="La note maximale est 5")
        ]
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ('utilisateur', 'recette')
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.recette.titre} - {self.valeur}/5"

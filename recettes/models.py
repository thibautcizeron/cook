from django.db import models

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
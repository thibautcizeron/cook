# recettes/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.templatetags.static import static
from django.utils import timezone

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Ajouté'),
        ('UPDATE', 'Modifié'),
        ('DELETE', 'Supprimé'),
    ]
    
    MODEL_CHOICES = [
        ('RECETTE', 'Recette'),
        ('INGREDIENT', 'Ingrédient'),
        ('CATEGORIE', 'Catégorie'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Action")
    model_type = models.CharField(max_length=20, choices=MODEL_CHOICES, verbose_name="Type")
    object_name = models.CharField(max_length=200, verbose_name="Nom de l'objet")
    object_id = models.PositiveIntegerField(verbose_name="ID de l'objet", null=True, blank=True)
    details = models.TextField(blank=True, verbose_name="Détails")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Date et heure")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Log d'activité"
        verbose_name_plural = "Logs d'activité"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} {self.get_model_type_display()} '{self.object_name}' - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    
    @staticmethod
    def log_activity(user, action, model_type, object_name, object_id=None, details='', request=None):
        """
        Méthode statique pour enregistrer une activité
        """
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        ActivityLog.objects.create(
            user=user,
            action=action,
            model_type=model_type,
            object_name=object_name,
            object_id=object_id,
            details=details,
            ip_address=ip_address
        )
class Image(models.Model):
    """Modèle centralisé pour gérer toutes les images"""
    nom = models.CharField(max_length=255)
    fichier = models.CharField(max_length=500)  # Chemin vers le fichier static
    description = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom
    
    @property
    def url(self):
        """Retourne l'URL static de l'image"""
        if self.fichier:
            return static(self.fichier)
        return None
    
    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"

class Categorie(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    image = models.CharField(max_length=500, null=True, blank=True)  # Chemin vers l'image static

    def __str__(self):
        return self.nom
    
    @property
    def image_url(self):
        """Retourne l'URL static de l'image de catégorie"""
        if self.image:
            return static(self.image)
        return None
    
    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categories"
        

class Ingredient(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    image = models.CharField(max_length=500, null=True, blank=True)  # Chemin vers l'image static

    def __str__(self):
        return self.nom
    
    @property
    def image_url(self):
        """Retourne l'URL static de l'image d'ingrédient"""
        if self.image:
            return static(self.image)
        return None
    
    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
    
class Recette(models.Model):
    titre = models.CharField(max_length=255)
    nbpersonne = models.IntegerField(default=1)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.CharField(max_length=500, null=True, blank=True)  # Chemin vers l'image static

    def __str__(self):
        return self.titre
    
    @property
    def image_url(self):
        """Retourne l'URL static de l'image de recette"""
        if self.image:
            return static(self.image)
        return None
    
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
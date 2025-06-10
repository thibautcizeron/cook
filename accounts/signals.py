# accounts/signals.py - Version corrigée

from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """
    Signal appelé avant la suppression d'un utilisateur
    Gère la suppression ou l'anonymisation des contenus liés
    """
    try:
        user = instance
        logger.info(f"Début de la suppression des données pour l'utilisateur: {user.username}")
        
        # Importer les modèles de façon sécurisée
        try:
            from recettes.models import Recette, Note
            from utils.storage import StaticImageStorage
            
            storage = StaticImageStorage()
            
            # 1. Récupérer toutes les recettes de l'utilisateur
            # CORRECTION: Utiliser le bon nom de champ (probablement 'user' au lieu de 'utilisateur')
            user_recipes = Recette.objects.filter(user=user)
            
            for recipe in user_recipes:
                # Supprimer les images des recettes
                if recipe.image:
                    try:
                        storage.delete_image(recipe.image)
                        logger.info(f"Image supprimée pour la recette: {recipe.titre}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la suppression de l'image {recipe.image}: {e}")
            
            # 2. Supprimer les notes de l'utilisateur
            # CORRECTION: Utiliser le bon nom de champ
            user_notes = Note.objects.filter(user=user)
            notes_count = user_notes.count()
            
            logger.info(f"Suppression de {notes_count} notes")
            
            # 3. Log final
            recipes_count = user_recipes.count()
            logger.info(f"Suppression programmée de {recipes_count} recettes pour l'utilisateur {user.username}")
            
        except ImportError as e:
            logger.warning(f"Impossible d'importer les modèles de recettes: {e}")
        except Exception as e:
            logger.error(f"Erreur lors du traitement des recettes pour {user.username}: {e}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la gestion de la suppression de l'utilisateur {instance.username}: {e}")

@receiver(post_delete, sender=User)
def user_deletion_complete(sender, instance, **kwargs):
    """
    Signal appelé après la suppression d'un utilisateur
    Log de confirmation
    """
    logger.info(f"Suppression terminée pour l'utilisateur: {instance.username}")

# Signal pour la suppression des images lors de la suppression d'une recette
@receiver(pre_delete)
def delete_recipe_image(sender, instance, **kwargs):
    """
    Signal pour supprimer l'image d'une recette lors de sa suppression
    Utilise un signal générique pour éviter les erreurs d'import
    """
    # Vérifier si c'est un modèle Recette en vérifiant les attributs nécessaires
    if hasattr(instance, 'image') and hasattr(instance, 'titre') and hasattr(instance, 'user'):
        if instance.image:
            try:
                from utils.storage import StaticImageStorage
                storage = StaticImageStorage()
                storage.delete_image(instance.image)
                logger.info(f"Image supprimée pour la recette: {instance.titre}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de l'image de la recette {instance.titre}: {e}")
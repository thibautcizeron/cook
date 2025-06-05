# recettes/utils.py - Créer ce nouveau fichier

import json
from .models import ActivityLog

def log_recette_activity(user, action, recette, request=None, additional_details=None):
    """
    Enregistre l'activité liée aux recettes
    """
    details = {}
    
    if action == 'CREATE':
        details = {
            'categorie': recette.categorie.nom if recette.categorie else None,
            'nb_personnes': recette.nbpersonne,
            'ingredients_count': recette.ingredients.count() if hasattr(recette, 'ingredients') else 0,
        }
    elif action == 'UPDATE':
        details = {
            'categorie': recette.categorie.nom if recette.categorie else None,
            'nb_personnes': recette.nbpersonne,
            'last_modified': recette.date_modification.isoformat() if hasattr(recette, 'date_modification') else None,
        }
    elif action == 'DELETE':
        details = {
            'categorie': recette.categorie.nom if recette.categorie else None,
            'nb_personnes': recette.nbpersonne,
            'deleted_at': additional_details.get('deleted_at') if additional_details else None,
        }
    
    if additional_details:
        details.update(additional_details)
    
    ActivityLog.log_activity(
        user=user,
        action=action,
        model_type='RECETTE',
        object_name=recette.titre,
        object_id=recette.id if hasattr(recette, 'id') else None,
        details=json.dumps(details, ensure_ascii=False),
        request=request
    )

def log_ingredient_activity(user, action, ingredient, request=None, additional_details=None):
    """
    Enregistre l'activité liée aux ingrédients
    """
    details = {}
    
    if action == 'CREATE':
        details = {
            'has_image': bool(ingredient.image),
            'created_at': ingredient.date_creation.isoformat() if hasattr(ingredient, 'date_creation') else None,
        }
    elif action == 'UPDATE':
        details = {
            'has_image': bool(ingredient.image),
            'last_modified': ingredient.date_modification.isoformat() if hasattr(ingredient, 'date_modification') else None,
        }
    elif action == 'DELETE':
        details = {
            'had_image': bool(ingredient.image),
            'deleted_at': additional_details.get('deleted_at') if additional_details else None,
        }
    
    if additional_details:
        details.update(additional_details)
    
    ActivityLog.log_activity(
        user=user,
        action=action,
        model_type='INGREDIENT',
        object_name=ingredient.nom,
        object_id=ingredient.id if hasattr(ingredient, 'id') else None,
        details=json.dumps(details, ensure_ascii=False),
        request=request
    )

def log_categorie_activity(user, action, categorie, request=None, additional_details=None):
    """
    Enregistre l'activité liée aux catégories
    """
    details = {}
    
    if action == 'CREATE':
        details = {
            'has_image': bool(categorie.image),
        }
    elif action == 'UPDATE':
        details = {
            'has_image': bool(categorie.image),
        }
    elif action == 'DELETE':
        details = {
            'had_image': bool(categorie.image),
            'deleted_at': additional_details.get('deleted_at') if additional_details else None,
        }
    
    if additional_details:
        details.update(additional_details)
    
    ActivityLog.log_activity(
        user=user,
        action=action,
        model_type='CATEGORIE',
        object_name=categorie.nom,
        object_id=categorie.id if hasattr(categorie, 'id') else None,
        details=json.dumps(details, ensure_ascii=False),
        request=request
    )
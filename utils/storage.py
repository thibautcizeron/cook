# utils/storage.py
import os
import uuid
import re
from django.conf import settings
from PIL import Image

class StaticImageStorage:
    """
    Gestionnaire personnalisé pour stocker les images dans les dossiers static
    """
    
    def __init__(self):
        self.static_root = getattr(settings, 'STATICFILES_DIRS', [settings.BASE_DIR / 'static'])[0]
        
    def save_recipe_image(self, uploaded_file, recipe_title, recipe_id=None):
        """
        Sauvegarde une image de recette dans static/images/recettes/
        """
        return self._save_image(uploaded_file, 'recettes', recipe_title, recipe_id)
    
    def save_ingredient_image(self, uploaded_file, ingredient_name, ingredient_id=None):
        """
        Sauvegarde une image d'ingrédient dans static/images/ingredients/
        """
        return self._save_image(uploaded_file, 'ingredients', ingredient_name, ingredient_id)
    
    def _save_image(self, uploaded_file, folder_name, item_name, item_id=None):
        """
        Méthode privée pour sauvegarder une image
        """
        if not uploaded_file:
            return None
            
        # Créer le dossier de destination
        destination_folder = os.path.join(self.static_root, 'images', folder_name)
        os.makedirs(destination_folder, exist_ok=True)
        
        # Nettoyer le nom pour le nom de fichier
        clean_name = self._clean_filename(item_name)
        
        # Générer un nom de fichier avec le nom de l'item
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if not file_extension:
            file_extension = '.jpg'  # Extension par défaut
            
        if item_id:
            filename = f"{clean_name}_{item_id}{file_extension}"
        else:
            filename = f"{clean_name}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        file_path = os.path.join(destination_folder, filename)
        
        # Vérifier si un fichier avec ce nom existe déjà et le supprimer
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Sauvegarder le fichier
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Optimiser l'image
        self._optimize_image(file_path)
        
        # Retourner le chemin relatif pour l'URL
        return f"images/{folder_name}/{filename}"
    
    def _clean_filename(self, name):
        """
        Nettoie le nom pour créer un nom de fichier valide
        """
        if not name:
            return "item"
        
        # Supprimer les accents et caractères spéciaux
        import unicodedata
        name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('ascii')
        
        # Remplacer les espaces et caractères spéciaux par des underscores
        name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
        
        # Supprimer les underscores multiples
        name = re.sub(r'_+', '_', name)
        
        # Limiter la longueur
        name = name[:30]
        
        # Supprimer les underscores en début et fin
        name = name.strip('_')
        
        return name.lower() if name else "item"
    
    def _optimize_image(self, file_path, max_size=(800, 600), quality=85):
        """
        Optimise et redimensionne l'image
        """
        try:
            with Image.open(file_path) as img:
                # Convertir en RGB si nécessaire
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Redimensionner si nécessaire
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Sauvegarder avec compression
                img.save(file_path, optimize=True, quality=quality)
        except Exception as e:
            print(f"Erreur lors de l'optimisation de l'image {file_path}: {e}")
    
    def delete_image(self, image_path):
        """
        Supprime une image du système de fichiers
        """
        if not image_path:
            return
            
        full_path = os.path.join(self.static_root, image_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception as e:
                print(f"Erreur lors de la suppression de l'image {full_path}: {e}")
    
    def update_image(self, old_image_path, new_uploaded_file, folder_name, item_name, item_id=None):
        """
        Met à jour une image (supprime l'ancienne et sauvegarde la nouvelle)
        """
        # Supprimer l'ancienne image
        if old_image_path:
            self.delete_image(old_image_path)
        
        # Sauvegarder la nouvelle image
        return self._save_image(new_uploaded_file, folder_name, item_name, item_id)
    
    def delete_old_images_for_item(self, folder_name, item_name, item_id=None):
        """
        Supprime les anciennes images pour un item donné
        """
        try:
            destination_folder = os.path.join(self.static_root, 'images', folder_name)
            clean_name = self._clean_filename(item_name)
            
            if os.path.exists(destination_folder):
                for filename in os.listdir(destination_folder):
                    # Vérifier si le fichier correspond au pattern de l'item
                    if item_id:
                        pattern = f"{clean_name}_{item_id}"
                    else:
                        pattern = f"{clean_name}_"
                    
                    if filename.startswith(pattern):
                        file_path = os.path.join(destination_folder, filename)
                        os.remove(file_path)
                        
        except Exception as e:
            print(f"Erreur lors de la suppression des anciennes images: {e}")
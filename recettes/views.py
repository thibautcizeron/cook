from django.shortcuts import render, get_object_or_404, redirect
from .models import Recette, Ingredient, Categorie, Etape, RecetteIngredient, Note
from .forms import RecetteForm, IngredientForm, CategorieForm, EtapeForm, RecetteIngredientForm
from django.forms import formset_factory, inlineformset_factory
from unidecode import unidecode
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib import messages
from django.conf import settings
import os
import uuid
import re
from PIL import Image
from django.utils.text import slugify
from django.core.paginator import Paginator
from .models import ActivityLog
from .utils import log_recette_activity, log_ingredient_activity, log_categorie_activity
import json
from datetime import datetime
from unidecode import unidecode


def is_superuser(user):
    """Vérifie si l'utilisateur est un superutilisateur"""
    return user.is_superuser

@user_passes_test(is_superuser)
def activity_logs(request):
    """Vue pour afficher les logs d'activité - uniquement pour les superutilisateurs"""
    logs = ActivityLog.objects.select_related('user').all()
    
    # Filtres
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    user_filter = request.GET.get('user', '')
    search_query = request.GET.get('search', '')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if model_filter:
        logs = logs.filter(model_type=model_filter)
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if search_query:
        logs = logs.filter(
            Q(object_name__icontains=search_query) |
            Q(details__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(logs, 25)  # 25 logs par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques rapides
    stats = {
        'total_logs': ActivityLog.objects.count(),
        'total_creates': ActivityLog.objects.filter(action='CREATE').count(),
        'total_updates': ActivityLog.objects.filter(action='UPDATE').count(),
        'total_deletes': ActivityLog.objects.filter(action='DELETE').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'user_filter': user_filter,
        'search_query': search_query,
        'stats': stats,
        'action_choices': ActivityLog.ACTION_CHOICES,
        'model_choices': ActivityLog.MODEL_CHOICES,
    }
    
    return render(request, 'recettes/activity_logs.html', context)

@user_passes_test(is_superuser)
def activity_log_detail(request, log_id):
    """Vue pour afficher le détail d'un log"""
    log = get_object_or_404(ActivityLog, id=log_id)
    
    # Essayer de parser les détails comme JSON s'ils existent
    parsed_details = None
    if log.details:
        try:
            parsed_details = json.loads(log.details)
        except (json.JSONDecodeError, ValueError):
            parsed_details = log.details
    
    context = {
        'log': log,
        'parsed_details': parsed_details,
    }
    
    return render(request, 'recettes/activity_log_detail.html', context)

# Gestionnaire de stockage personnalisé pour les images
class StaticImageStorage:
    """Gestionnaire personnalisé pour stocker les images dans les dossiers static"""
    
    def __init__(self):
        self.static_root = getattr(settings, 'STATICFILES_DIRS', [settings.BASE_DIR / 'static'])[0]
        
    def save_recipe_image(self, uploaded_file, recipe_title, recipe_id=None):
        """Sauvegarde une image de recette avec le nom de la recette"""
        return self._save_image(uploaded_file, 'recettes', recipe_title, recipe_id)
    
    def save_ingredient_image(self, uploaded_file, ingredient_name, ingredient_id=None):
        """Sauvegarde une image d'ingrédient avec le nom de l'ingrédient"""
        return self._save_image(uploaded_file, 'ingredients', ingredient_name, ingredient_id)
    
    def _save_image(self, uploaded_file, folder_name, item_name, item_id=None):
        """Méthode privée pour sauvegarder une image avec un nom personnalisé"""
        if not uploaded_file:
            return None
            
        # Créer le dossier de destination
        destination_folder = os.path.join(self.static_root, 'images', folder_name)
        os.makedirs(destination_folder, exist_ok=True)
        
        # Nettoyer le nom de l'élément pour créer un nom de fichier valide
        clean_name = self._clean_filename(item_name)
        
        # Générer un nom de fichier basé sur le nom de l'élément
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if not file_extension:
            file_extension = '.jpg'  # Extension par défaut
            
        # Créer le nom de fichier : nom_de_la_recette_id.extension
        if item_id:
            filename = f"{clean_name}_{item_id}{file_extension}"
        else:
            # Si pas d'ID, ajouter un identifiant unique court
            filename = f"{clean_name}_{uuid.uuid4().hex[:6]}{file_extension}"
        
        file_path = os.path.join(destination_folder, filename)
        
        # Vérifier si le fichier existe déjà et le supprimer pour éviter les doublons
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression de l'ancien fichier {file_path}: {e}")
        
        # Sauvegarder le fichier
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Optimiser l'image
        self._optimize_image(file_path)
        
        # Retourner le chemin relatif pour l'URL
        return f"images/{folder_name}/{filename}"
    
    def _clean_filename(self, name):
        """Nettoie un nom pour en faire un nom de fichier valide"""
        if not name:
            return "image"
        
        # Utiliser slugify pour créer un nom de fichier propre
        clean_name = slugify(name)
        
        # Limiter la longueur pour éviter les noms de fichiers trop longs
        if len(clean_name) > 50:
            clean_name = clean_name[:50]
        
        # Si le nom devient vide après nettoyage, utiliser un nom par défaut
        if not clean_name:
            clean_name = "image"
            
        return clean_name
    
    def _optimize_image(self, file_path, max_size=(800, 600), quality=85):
        """Optimise et redimensionne l'image"""
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
        """Supprime une image du système de fichiers"""
        if not image_path:
            return
            
        full_path = os.path.join(self.static_root, image_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"Image supprimée: {full_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression de l'image {full_path}: {e}")
    
    def update_image(self, old_image_path, new_uploaded_file, folder_name, item_name, item_id=None):
        """Met à jour une image (supprime l'ancienne et sauvegarde la nouvelle)"""
        # Supprimer l'ancienne image
        if old_image_path:
            self.delete_image(old_image_path)
        
        # Sauvegarder la nouvelle image
        return self._save_image(new_uploaded_file, folder_name, item_name, item_id)

# Instance globale du gestionnaire de stockage
storage = StaticImageStorage()

@login_required
def noter_recette(request, recette_id):
    if request.method == 'POST':
        recette = get_object_or_404(Recette, id=recette_id)
        valeur = int(request.POST.get('valeur', 0))
        
        if valeur < 1 or valeur > 5:
            messages.error(request, 'La note doit être entre 1 et 5')
            return redirect('recettes_details', recette_id=recette_id)
            
        # Créer ou mettre à jour la note
        note, created = Note.objects.update_or_create(
            utilisateur=request.user,
            recette=recette,
            defaults={'valeur': valeur}
        )
        
        # Logger l'activité de notation
        action_text = "ajoutée" if created else "mise à jour"
        ActivityLog.log_activity(
            user=request.user,
            action='CREATE' if created else 'UPDATE',
            model_type='RECETTE',
            object_name=f"Note pour {recette.titre}",
            object_id=recette.id,
            details=json.dumps({
                'note_valeur': valeur,
                'note_action': action_text,
                'recette_id': recette.id,
                'recette_titre': recette.titre,
            }, ensure_ascii=False),
            request=request
        )
        
        if created:
            messages.success(request, 'Votre note a été enregistrée')
        else:
            messages.success(request, 'Votre note a été mise à jour')
        
        return redirect('recettes_details', recette_id=recette_id)
    
    return redirect('recettes_details', recette_id=recette_id)

def is_user(user):
    return user.groups.filter(name="Users").exists()

def is_contributor(user):
    return user.groups.filter(name="Contributors").exists()

def is_admin(user):
    return user.groups.filter(name="Administrators").exists()

def home(request):
    recettes = Recette.objects.all()
    return render(request, 'index/layout.html', {'recettes': recettes})

def search_recipe(request):
    query = request.GET.get('q', '').strip()  
    normalized_query = unidecode(query).lower() 

    recettes = Recette.objects.all()
    
    matching_recettes = [
        {
            "id": recette.id,
            "titre": recette.titre,
        }
        for recette in recettes
        if normalized_query in unidecode(recette.titre).lower()
    ]

    return JsonResponse(matching_recettes, safe=False)

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def recettes_list(request):
    order = request.GET.get("order", "asc")
    search_query = request.GET.get("search", "").strip()

    recettes = Recette.objects.all()

    # Appliquer la recherche si un terme est fourni
    if search_query:
        search_query = unidecode(search_query).lower()
        recettes = [recette for recette in recettes if search_query in unidecode(recette.titre).lower()]

    # Appliquer le tri
    recettes = sorted(recettes, key=lambda r: unidecode(r.titre).lower(), reverse=(order == "desc"))

    categories = Categorie.objects.all()

    return render(request, "recettes/recettes.html", {
        "recettes": recettes,
        "categories": categories,
        "order": order,
        "search_query": search_query
    })

def recettes_details(request, recette_id):
    recette = get_object_or_404(Recette, id=recette_id)
    ingredients_originaux = RecetteIngredient.objects.filter(recette=recette)
    
    # Récupérer la note de l'utilisateur actuel si connecté
    note_utilisateur = None
    if request.user.is_authenticated:
        note_utilisateur = Note.objects.filter(utilisateur=request.user, recette=recette).first()
    
    # Calcul de la note moyenne
    notes = Note.objects.filter(recette=recette)
    note_moyenne = 0
    nombre_votes = notes.count()
    if nombre_votes > 0:
        note_moyenne = sum(note.valeur for note in notes) / nombre_votes
    
    nb_personnes_souhaite = request.GET.get('nb_personnes', None)
    
    ingredients = []
    ratio = 1  
    
    if nb_personnes_souhaite and recette.nbpersonne:
        try:
            nb_personnes_souhaite = int(nb_personnes_souhaite)
            if recette.nbpersonne > 0:
                ratio = nb_personnes_souhaite / recette.nbpersonne
        except (ValueError, ZeroDivisionError):
            nb_personnes_souhaite = recette.nbpersonne
    
    for ri in ingredients_originaux:
        quantite_ajustee = ri.quantite
        if ratio != 1:
            import re
            nombres = re.findall(r'(\d+(?:[.,]\d+)?)', ri.quantite)
            if nombres:
                quantite_ajustee = ri.quantite
                for nombre in nombres:
                    nombre_float = float(nombre.replace(',', '.'))
                    nouvelle_valeur = nombre_float * ratio
                    if nouvelle_valeur == int(nouvelle_valeur):
                        nouvelle_valeur_str = str(int(nouvelle_valeur))
                    else:
                        nouvelle_valeur_str = f"{nouvelle_valeur:.1f}".replace('.', ',')
                    quantite_ajustee = quantite_ajustee.replace(nombre, nouvelle_valeur_str, 1)
        
        ingredients.append({
            'ingredient': ri.ingredient,
            'quantite_originale': ri.quantite,
            'quantite_ajustee': quantite_ajustee
        })
    
    return render(request, 'recettes/recettes_details.html', {
        'recette': recette, 
        'ingredients': ingredients,
        'nb_personnes_souhaite': nb_personnes_souhaite,
        'nb_personnes_original': recette.nbpersonne,
        'note_utilisateur': note_utilisateur,
        'note_moyenne': note_moyenne,
        'nombre_votes': nombre_votes
    })

@login_required
@user_passes_test(lambda u: is_contributor(u) or is_admin(u) or is_superuser(u))
def recettes_add(request):
    RecetteIngredientFormSet = formset_factory(RecetteIngredientForm, extra=1)
    EtapeFormSet = formset_factory(EtapeForm, extra=1)

    if request.method == 'POST':  
        recette_form = RecetteForm(request.POST, request.FILES)
        ingredient_formset = RecetteIngredientFormSet(request.POST, prefix='ingredients')
        etape_formset = EtapeFormSet(request.POST, prefix='etapes')

        if recette_form.is_valid() and ingredient_formset.is_valid() and etape_formset.is_valid():
            # Créer la recette d'abord sans l'image
            recette = recette_form.save(commit=False)
            recette.save()  # Sauvegarder pour obtenir l'ID
            
            # Gérer l'upload de l'image avec le titre de la recette
            if 'image' in request.FILES:
                image_path = storage.save_recipe_image(
                    request.FILES['image'], 
                    recette.titre,  # Utiliser le titre de la recette
                    recette.id
                )
                recette.image = image_path
                recette.save()  # Sauvegarder à nouveau avec l'image

            # Créer les ingrédients
            ingredients_count = 0
            for form in ingredient_formset:
                if form.cleaned_data.get('ingredient') and form.cleaned_data.get('quantite'):
                    RecetteIngredient.objects.create(
                        recette=recette,
                        ingredient=form.cleaned_data['ingredient'],
                        quantite=form.cleaned_data['quantite']
                    )
                    ingredients_count += 1

            # Créer les étapes
            etapes_count = 0
            for form in etape_formset:
                if form.cleaned_data.get('description'):
                    Etape.objects.create(
                        recette=recette,
                        description=form.cleaned_data['description']
                    )
                    etapes_count += 1

            # Logger l'activité de création
            log_recette_activity(
                user=request.user,
                action='CREATE',
                recette=recette,
                request=request,
                additional_details={
                    'ingredients_count': ingredients_count,
                    'etapes_count': etapes_count,
                    'has_image': bool(recette.image),
                    'created_at': datetime.now().isoformat(),
                }
            )

            messages.success(request, f'Recette "{recette.titre}" créée avec succès!')
            return redirect('recettes')
        else:
            # Afficher les erreurs
            for field, errors in recette_form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans {field}: {error}")

    else:
        recette_form = RecetteForm()
        ingredient_formset = RecetteIngredientFormSet(prefix='ingredients')
        etape_formset = EtapeFormSet(prefix='etapes')

    categories = Categorie.objects.all()  
    ingredients = Ingredient.objects.all()  
    return render(request, 'recettes/recettes_add.html', {
        'recette_form': recette_form,
        'ingredient_formset': ingredient_formset,
        'etape_formset': etape_formset,
        'categories': categories,
        'ingredients': ingredients, 
    })

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def recettes_edit(request, pk):
    recette = get_object_or_404(Recette, pk=pk)
    
    # Stocker les valeurs originales pour le log
    original_titre = recette.titre
    original_categorie = recette.categorie.nom if recette.categorie else None
    original_nbpersonne = recette.nbpersonne
    original_image = recette.image

    RecetteIngredientFormSet = inlineformset_factory(
        Recette, RecetteIngredient, form=RecetteIngredientForm, extra=1, can_delete=True
    )
    EtapeFormSet = inlineformset_factory(
        Recette, Etape, form=EtapeForm, extra=1, can_delete=True
    )

    if request.method == 'POST':  
        recette_form = RecetteForm(request.POST, request.FILES, instance=recette)
        ingredient_formset = RecetteIngredientFormSet(request.POST, instance=recette, prefix='ingredients')
        etape_formset = EtapeFormSet(request.POST, instance=recette, prefix='etapes')

        if recette_form.is_valid() and ingredient_formset.is_valid() and etape_formset.is_valid():
            # Sauvegarder la recette d'abord
            old_image = recette.image
            recette = recette_form.save()
            
            # Gérer l'upload de l'image si une nouvelle image est fournie
            image_updated = False
            if 'image' in request.FILES:
                new_image_path = storage.update_image(
                    old_image, 
                    request.FILES['image'], 
                    'recettes', 
                    recette.titre,  # Utiliser le titre de la recette
                    recette.id
                )
                recette.image = new_image_path
                recette.save()
                image_updated = True
            
            ingredient_formset.save()
            etape_formset.save()
            
            # Préparer les détails des modifications
            modifications = []
            if original_titre != recette.titre:
                modifications.append(f"Titre: '{original_titre}' → '{recette.titre}'")
            if original_categorie != (recette.categorie.nom if recette.categorie else None):
                new_cat = recette.categorie.nom if recette.categorie else "Aucune"
                modifications.append(f"Catégorie: '{original_categorie}' → '{new_cat}'")
            if original_nbpersonne != recette.nbpersonne:
                modifications.append(f"Nb personnes: {original_nbpersonne} → {recette.nbpersonne}")
            if image_updated:
                modifications.append("Image mise à jour")
            
            # Logger l'activité de modification
            log_recette_activity(
                user=request.user,
                action='UPDATE',
                recette=recette,
                request=request,
                additional_details={
                    'modifications': modifications,
                    'original_titre': original_titre,
                    'ingredients_count': recette.recette_ingredients.count(),
                    'etapes_count': recette.etapes.count(),
                    'image_updated': image_updated,
                    'modified_at': datetime.now().isoformat(),
                }
            )
            
            messages.success(request, f'Recette "{recette.titre}" modifiée avec succès!')
            return redirect('recettes')
        else:
            # Afficher les erreurs
            for field, errors in recette_form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans {field}: {error}")
    else:
        recette_form = RecetteForm(instance=recette)
        ingredient_formset = RecetteIngredientFormSet(instance=recette, prefix='ingredients')
        etape_formset = EtapeFormSet(instance=recette, prefix='etapes')

    categories = Categorie.objects.all()
    ingredients = Ingredient.objects.all()

    return render(request, 'recettes/recettes_edit.html', {
        'recette_form': recette_form,
        'ingredient_formset': ingredient_formset,
        'etape_formset': etape_formset,
        'categories': categories,
        'ingredients': ingredients,
        'recette': recette,  
    })

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def recettes_delete(request, pk):
    recette = get_object_or_404(Recette, pk=pk)
    if request.method == "POST":
        recette_titre = recette.titre
        recette_categorie = recette.categorie.nom if recette.categorie else None
        recette_nbpersonne = recette.nbpersonne
        ingredients_count = recette.recette_ingredients.count()
        etapes_count = recette.etapes.count()
        had_image = bool(recette.image)
        
        # Supprimer l'image associée
        if recette.image:
            storage.delete_image(recette.image)
        
        # Logger l'activité de suppression avant de supprimer la recette
        log_recette_activity(
            user=request.user,
            action='DELETE',
            recette=recette,
            request=request,
            additional_details={
                'deleted_at': datetime.now().isoformat(),
                'ingredients_count': ingredients_count,
                'etapes_count': etapes_count,
                'had_image': had_image,
                'categorie': recette_categorie,
                'nb_personnes': recette_nbpersonne,
            }
        )
        
        recette.delete()
        messages.success(request, f'Recette "{recette_titre}" supprimée avec succès!')
        return redirect('recettes')
    return render(request, 'recette/recettes.html', {'recette': recette})

# VUES POUR LES INGRÉDIENTS

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def ingredient_list(request):
    search_query = request.GET.get('search', '')  
    ingredients = Ingredient.objects.all()

    if search_query:
        ingredients = ingredients.filter(nom__icontains=search_query)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        ingredients_data = []
        for ingredient in ingredients:
            data = {
                'id': ingredient.id,
                'nom': ingredient.nom,
                'image': ingredient.image_url if ingredient.image else None
            }
            ingredients_data.append(data)
        return JsonResponse({'ingredients': ingredients_data})

    return render(request, 'ingredients/ingredients.html', {
        'ingredients': ingredients,
        'search_query': search_query,
    })

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def ingredients_add(request):
    if request.method == "POST":
        form = IngredientForm(request.POST, request.FILES)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.save()  # Sauvegarder pour obtenir l'ID
            
            # Gérer l'upload de l'image avec le nom de l'ingrédient
            if 'image' in request.FILES:
                image_path = storage.save_ingredient_image(
                    request.FILES['image'], 
                    ingredient.nom,  # Utiliser le nom de l'ingrédient
                    ingredient.id
                )
                ingredient.image = image_path
                ingredient.save()  # Sauvegarder à nouveau avec l'image
            
            # Logger l'activité de création
            log_ingredient_activity(
                user=request.user,
                action='CREATE',
                ingredient=ingredient,
                request=request,
                additional_details={
                    'created_at': datetime.now().isoformat(),
                }
            )
            
            messages.success(request, f'Ingrédient "{ingredient.nom}" créé avec succès!')
            return redirect('ingredients')
        else:
            # Afficher les erreurs
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans {field}: {error}")
    else:
        form = IngredientForm()
    return render(request, 'ingredients/ingredients_add.html', {'form': form})

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def ingredients_edit(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    
    # Stocker les valeurs originales pour le log
    original_nom = ingredient.nom
    original_image = ingredient.image
    
    if request.method == "POST":
        form = IngredientForm(request.POST, request.FILES, instance=ingredient) 
        if form.is_valid():
            # Sauvegarder l'ingrédient d'abord
            old_image = ingredient.image
            ingredient = form.save()
            
            # Gérer l'upload de l'image si une nouvelle image est fournie
            image_updated = False
            if 'image' in request.FILES:
                new_image_path = storage.update_image(
                    old_image, 
                    request.FILES['image'], 
                    'ingredients', 
                    ingredient.nom,  # Utiliser le nom de l'ingrédient
                    ingredient.id
                )
                ingredient.image = new_image_path
                ingredient.save()
                image_updated = True
            
            # Préparer les détails des modifications
            modifications = []
            if original_nom != ingredient.nom:
                modifications.append(f"Nom: '{original_nom}' → '{ingredient.nom}'")
            if image_updated:
                modifications.append("Image mise à jour")
            
            # Logger l'activité de modification
            log_ingredient_activity(
                user=request.user,
                action='UPDATE',
                ingredient=ingredient,
                request=request,
                additional_details={
                    'modifications': modifications,
                    'original_nom': original_nom,
                    'image_updated': image_updated,
                    'modified_at': datetime.now().isoformat(),
                }
            )
            
            messages.success(request, f'Ingrédient "{ingredient.nom}" modifié avec succès!')
            return redirect('ingredients')
        else:
            # Afficher les erreurs
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans {field}: {error}")
    else:
        form = IngredientForm(instance=ingredient)  
    return render(request, 'ingredients/ingredients_edit.html', {'form': form, 'ingredient': ingredient})

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def ingredients_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == "POST":
        ingredient_nom = ingredient.nom
        had_image = bool(ingredient.image)
        
        # Compter les recettes utilisant cet ingrédient
        recettes_count = RecetteIngredient.objects.filter(ingredient=ingredient).count()
        
        # Supprimer l'image associée
        if ingredient.image:
            storage.delete_image(ingredient.image)
        
        # Logger l'activité de suppression avant de supprimer l'ingrédient
        log_ingredient_activity(
            user=request.user,
            action='DELETE',
            ingredient=ingredient,
            request=request,
            additional_details={
                'deleted_at': datetime.now().isoformat(),
                'had_image': had_image,
                'used_in_recipes_count': recettes_count,
            }
        )
        
        ingredient.delete()
        messages.success(request, f'Ingrédient "{ingredient_nom}" supprimé avec succès!')
        return redirect('ingredients')
    return render(request, 'recette/ingredients.html', {'ingredient': ingredient})

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def search_recettes(request):
    query = request.GET.get("q", "").strip() 
    normalized_query = unidecode(query).lower()  

    if normalized_query:
        recettes = Recette.objects.filter(
            Q(titre__icontains=normalized_query) | Q(categorie__nom__icontains=normalized_query)
        )
        results = [
            {"id": recette.id, "titre": recette.titre, "categorie": recette.categorie.nom if recette.categorie else "Non défini"}
            for recette in recettes
        ]
    else:
        results = []

    return JsonResponse(results, safe=False)

def show_starts(request):
    try:
        categorie_entree = Categorie.objects.get(nom="entree")  
        entrees = Recette.objects.filter(categorie=categorie_entree)  
    except Categorie.DoesNotExist:
        entrees = Recette.objects.none()  

    return render(request, 'index/layout_starts.html', {'entrees': entrees})

def show_dishes(request):
    try:
        categorie_plat = Categorie.objects.get(nom="plat")  
        plats = Recette.objects.filter(categorie=categorie_plat)  
    except Categorie.DoesNotExist:
        plats = Recette.objects.none()  
    return render(request, 'index/layout_dishes.html', {'plats': plats})

def show_desserts(request):
    try:
        categorie_dessert = Categorie.objects.get(nom="dessert")  
        desserts = Recette.objects.filter(categorie=categorie_dessert)  
    except Categorie.DoesNotExist:
        desserts = Recette.objects.none()  

    return render(request, 'index/layout_desserts.html', {'desserts': desserts})

def show_cocktails(request):
    try:
        categorie_cocktail = Categorie.objects.get(nom="cocktail")  
        cocktails = Recette.objects.filter(categorie=categorie_cocktail)  
    except Categorie.DoesNotExist:
        cocktails = Recette.objects.none() 

    return render(request, 'index/layout_cocktails.html', {'cocktails': cocktails})

def loading_page(request):
    return render(request, 'index/loading.html')


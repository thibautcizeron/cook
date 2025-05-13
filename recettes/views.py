from django.shortcuts import render, get_object_or_404, redirect
from .models import Recette, Ingredient, Categorie, Etape, RecetteIngredient, Note
from .forms import RecetteForm, IngredientForm, CategorieForm, EtapeForm, RecetteIngredientForm
from django.forms import formset_factory, inlineformset_factory
from unidecode import unidecode
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib import messages

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

def is_superuser(user):
    return user.is_superuser


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
    order = request.GET.get("order", "asc")  # Ordre de tri par défaut
    search_query = request.GET.get("search", "").strip()  # Récupérer la recherche

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
        "search_query": search_query  # Transmettre la recherche au template
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
            recette = recette_form.save()

            for form in ingredient_formset:
                if form.cleaned_data.get('ingredient') and form.cleaned_data.get('quantite'):
                    RecetteIngredient.objects.create(
                        recette=recette,
                        ingredient=form.cleaned_data['ingredient'],
                        quantite=form.cleaned_data['quantite']
                    )

            for form in etape_formset:
                if form.cleaned_data.get('description'):
                    Etape.objects.create(
                        recette=recette,
                        description=form.cleaned_data['description']
                    )

            return redirect('recettes')

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
            recette = recette_form.save()
            ingredient_formset.save()
            etape_formset.save()
            return redirect('recettes')
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
        recette.delete()
        return redirect('recettes')
    return render(request, 'recette/recettes.html', {'recette': recette})



@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def ingredient_list(request):
    search_query = request.GET.get('search', '')  
    ingredients = Ingredient.objects.all()

    if search_query:
        ingredients = ingredients.filter(nom__icontains=search_query)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        ingredients_data = list(ingredients.values('id', 'nom', 'image'))
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
            ingredient = form.save()
            return redirect('ingredients')
    else:
        form = IngredientForm()
    return render(request, 'ingredients/ingredients_add.html', {'form': form})

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def ingredients_edit(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == "POST":
        form = IngredientForm(request.POST, request.FILES, instance=ingredient) 
        if form.is_valid():
            form.save()
            return redirect('ingredients')
    else:
        form = IngredientForm(instance=ingredient)  
    return render(request, 'ingredients/ingredients_edit.html', {'form': form, 'ingredient': ingredient})

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def ingredients_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == "POST":
        ingredient.delete()
        return redirect('ingredients')
    return render(request, 'recette/ingredients.html', {'ingredient': ingredient})

@login_required
@user_passes_test(lambda u: is_admin(u) or is_superuser(u))
def search_recettes(request):
    query = request.GET.get("q", "").strip() 
    normalized_query = unidecode(query).lower()  

    if normalized_query:
        recettes = Recette.objects.filter(
            Q(titre__icontains=normalized_query) | Q(categorie__name__icontains=normalized_query)
        )
        results = [
            {"id": recette.id, "titre": recette.titre, "categorie": recette.categorie.name if recette.categorie else "Non défini"}
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






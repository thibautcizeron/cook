from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q
from unidecode import unidecode
from .forms import RegisterForm
import re

# Importer les utilitaires d'email
try:
    from utils.email_utils import send_account_deletion_notification, send_admin_deletion_notification, send_welcome_email
except ImportError:
    # Fonctions de fallback si le module n'existe pas
    def send_account_deletion_notification(user):
        return False
    def send_admin_deletion_notification(user):
        return False
    def send_welcome_email(user):
        return False

@login_required
def user_account_delete(request):
    """Vue pour supprimer le compte utilisateur avec confirmation et envoi d'email"""
    if request.method == "POST":
        # Vérifier le mot de passe actuel pour sécuriser la suppression
        password = request.POST.get('password')
        confirm_delete = request.POST.get('confirm_delete')
        
        if not password:
            messages.error(request, "Veuillez saisir votre mot de passe pour confirmer la suppression.")
            return render(request, 'accounts/users_account_delete.html')
        
        if not confirm_delete:
            messages.error(request, "Veuillez cocher la case de confirmation pour supprimer votre compte.")
            return render(request, 'accounts/users_account_delete.html')
        
        # Vérifier le mot de passe
        if not request.user.check_password(password):
            messages.error(request, "Mot de passe incorrect.")
            return render(request, 'accounts/users_account_delete.html')
        
        # Récupérer l'utilisateur avant suppression pour le message et l'email
        user = request.user
        username = user.username
        user_email = user.email
        
        try:
            # Envoyer l'email de confirmation AVANT la suppression
            email_sent = False
            if user_email:
                try:
                    email_sent = send_account_deletion_notification(user)
                    if email_sent:
                        messages.info(request, f"Un email de confirmation a été envoyé à {user_email}")
                except Exception as e:
                    # Log l'erreur mais continue la suppression
                    print(f"Erreur lors de l'envoi de l'email de confirmation: {e}")
            
            # Envoyer la notification aux administrateurs
            try:
                send_admin_deletion_notification(user)
            except Exception as e:
                print(f"Erreur lors de l'envoi de la notification admin: {e}")
            
            # Déconnecter l'utilisateur avant la suppression
            logout(request)
            
            # Supprimer le compte utilisateur
            # Les recettes et autres contenus associés seront gérés par les signaux Django
            user.delete()
            
            # Message de confirmation
            success_message = f"Le compte '{username}' a été supprimé avec succès."
            if email_sent:
                success_message += f" Un email de confirmation a été envoyé à {user_email}."
            success_message += " Nous espérons vous revoir bientôt !"
            
            messages.success(request, success_message)
            return redirect('users_login')
            
        except Exception as e:
            # En cas d'erreur, reconnecter l'utilisateur si possible
            try:
                login(request, user)
            except:
                pass
            messages.error(request, "Une erreur est survenue lors de la suppression du compte. Veuillez réessayer ou contacter le support.")
            return render(request, 'accounts/users_account_delete.html')
    
    return render(request, 'accounts/users_account_delete.html')

@login_required
def user_account_edit(request):
    """Vue pour modifier le profil de l'utilisateur avec vérifications renforcées pour le mot de passe"""
    if request.method == "POST":
        # Récupérer les données du formulaire
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Récupérer les données de mot de passe
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Initialiser un indicateur pour savoir si le formulaire est valide
        form_is_valid = True
        
        user = request.user
        
        # Vérifier si les données de base sont valides
        if not username or len(username) < 3:
            messages.error(request, "Le nom d'utilisateur doit contenir au moins 3 caractères.")
            form_is_valid = False
        
        if not email or '@' not in email:
            messages.error(request, "Veuillez fournir une adresse email valide.")
            form_is_valid = False
            
        # Vérifier si ce nom d'utilisateur existe déjà (et n'est pas l'utilisateur actuel)
        if username != user.username and User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà utilisé.")
            form_is_valid = False
            
        # Vérifier si cet email existe déjà (et n'est pas l'email de l'utilisateur actuel)
        if email != user.email and User.objects.filter(email=email).exists():
            messages.error(request, "Cette adresse email est déjà utilisée.")
            form_is_valid = False
        
        # Vérifications spécifiques au mot de passe
        if new_password or confirm_password or current_password:
            # Si l'un des champs de mot de passe est renseigné, tous doivent l'être
            if not (new_password and confirm_password and current_password):
                messages.error(request, "Pour changer votre mot de passe, vous devez remplir tous les champs associés.")
                form_is_valid = False
            else:
                # Vérifier que le mot de passe actuel est correct
                if not user.check_password(current_password):
                    messages.error(request, "Le mot de passe actuel est incorrect.")
                    form_is_valid = False
                # Vérifier que le nouveau mot de passe est différent de l'ancien
                elif current_password == new_password:
                    messages.error(request, "Le nouveau mot de passe doit être différent de l'ancien.")
                    form_is_valid = False
                # Vérifier que les nouveaux mots de passe correspondent
                elif new_password != confirm_password:
                    messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
                    form_is_valid = False
                # Vérifier la complexité du mot de passe
                elif not is_password_valid(new_password):
                    messages.error(request, "Le mot de passe doit contenir au moins 8 caractères, incluant une lettre majuscule, une lettre minuscule, un chiffre et un caractère spécial.")
                    form_is_valid = False
                # Vérifier que le mot de passe ne contient pas d'informations personnelles évidentes
                elif contains_personal_info(new_password, user):
                    messages.error(request, "Le mot de passe ne doit pas contenir votre nom d'utilisateur, prénom, nom ou adresse email.")
                    form_is_valid = False
        
        # Si le formulaire est valide, mettre à jour les données
        if form_is_valid:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            
            # Si un nouveau mot de passe est fourni et vérifié, le mettre à jour
            if new_password and current_password and user.check_password(current_password):
                user.set_password(new_password)
                # Maintenir la session active après changement de mot de passe
                update_session_auth_hash(request, user)
                messages.success(request, "Votre mot de passe a été modifié avec succès.")
            
            user.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('users_account')
            
    return render(request, 'accounts/users_account_edit.html')

def is_password_valid(password, previous_passwords=None):
    """Vérifie si le mot de passe répond aux critères de complexité et s'il est différent des 5 derniers."""
    # Si previous_passwords n'est pas fourni, initialiser à une liste vide
    if previous_passwords is None:
        previous_passwords = []
    
    # Vérifier si le mot de passe est différent des 5 derniers
    if password in previous_passwords[-5:]:
        return False
    
    # Au moins 8 caractères
    if len(password) < 8:
        return False
    
    # Au moins une lettre majuscule
    if not re.search(r'[A-Z]', password):
        return False
    
    # Au moins une lettre minuscule
    if not re.search(r'[a-z]', password):
        return False
    
    # Au moins un chiffre
    if not re.search(r'[0-9]', password):
        return False
    
    # Au moins un caractère spécial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+[\];:\'"\\`~]', password):
        return False
    
    return True

def contains_personal_info(password, user):
    """Vérifie si le mot de passe contient des informations personnelles de l'utilisateur."""
    password_lower = password.lower()
    
    # Liste des informations personnelles à vérifier
    personal_info = [
        user.username.lower(),
        user.email.lower().split('@')[0],  # Partie locale de l'email
        user.first_name.lower(),
        user.last_name.lower()
    ]
    
    # Vérifier si le mot de passe contient l'une de ces informations
    for info in personal_info:
        if info and len(info) > 2 and info in password_lower:  # Ignorer les infos trop courtes
            return True
    
    return False

@login_required
def user_account(request):
    """Vue pour afficher le profil de l'utilisateur"""
    return render(request, 'accounts/users_account.html')


def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    
    return render(request, 'accounts/users_login.html')

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Envoyer l'email de bienvenue
            try:
                send_welcome_email(user)
            except Exception as e:
                # Log l'erreur mais ne pas empêcher l'inscription
                print(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
            
            login(request, user)  
            return redirect('home')  
    else:
        form = RegisterForm()

    return render(request, 'accounts/users_register.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('users_login')

def is_superadmin(user):
    return user.is_superuser

@user_passes_test(is_superadmin)
def user_list(request):
    order = request.GET.get("order", "asc")  
    search_query = request.GET.get("search", "").strip()  

    users = User.objects.filter(is_superuser=False)

    if search_query:
        search_query = unidecode(search_query).lower()
        users = [user for user in users if search_query in unidecode(user.username).lower()]

    users = sorted(users, key=lambda u: unidecode(u.username).lower(), reverse=(order == "desc"))

    groups = Group.objects.all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        group_id = request.POST.get("group_id")

        user = User.objects.get(id=user_id)
        group = Group.objects.get(id=group_id)

        user.groups.clear()
        user.groups.add(group)

        return redirect("users")

    return render(request, "accounts/users.html", {
        "users": users,
        "groups": groups,
        "order": order,
        "search_query": search_query  
    })

def search_users(request):
    query = request.GET.get("q", "").strip() 
    normalized_query = unidecode(query).lower()  

    if normalized_query:
        users = User.objects.filter(
            Q(username__icontains=normalized_query) | Q(email__icontains=normalized_query)
        )[:10]  

        results = [{"id": user.id, "username": user.username} for user in users]
    else:
        results = []

    return JsonResponse(results, safe=False)

def show_politique(request):
    return render(request, 'index/politique.html')

def show_mentions(request):
    return render(request, 'index/mentions.html')
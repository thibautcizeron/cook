from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
import re


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        """ Vérifie si l'email est déjà utilisé (si renseigné) """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_username(self):
        """ Vérifie si le nom d'utilisateur existe déjà et sa longueur minimale """
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise forms.ValidationError("Le nom d'utilisateur doit contenir au moins 3 caractères.")
        
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def clean_password1(self):
        """ Vérifie la complexité du mot de passe """
        password = self.cleaned_data.get('password1')
        
        # Vérifier la longueur du mot de passe
        if len(password) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        
        # Vérifier la présence d'une lettre majuscule
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins une lettre majuscule.")
        
        # Vérifier la présence d'une lettre minuscule
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins une lettre minuscule.")
        
        # Vérifier la présence d'un chiffre
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        
        # Vérifier la présence d'un caractère spécial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+[\];:\'"\\`~]', password):
            raise forms.ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
        
        return password

    def clean(self):
        """ Validation supplémentaire pour vérifier que le mot de passe ne contient pas d'informations personnelles """
        cleaned_data = super().clean()
        password = cleaned_data.get('password1')
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        if password:
            # Vérifier si le mot de passe contient des informations personnelles
            if username and len(username) > 2 and password.lower().find(username.lower()) != -1:
                self.add_error('password1', "Le mot de passe ne doit pas contenir votre nom d'utilisateur.")
            
            if email:
                email_part = email.split('@')[0].lower()
                if email_part and len(email_part) > 2 and password.lower().find(email_part) != -1:
                    self.add_error('password1', "Le mot de passe ne doit pas contenir votre adresse email.")
            
            if first_name and len(first_name) > 2 and password.lower().find(first_name.lower()) != -1:
                self.add_error('password1', "Le mot de passe ne doit pas contenir votre prénom.")
            
            if last_name and len(last_name) > 2 and password.lower().find(last_name.lower()) != -1:
                self.add_error('password1', "Le mot de passe ne doit pas contenir votre nom.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Enregistrement de l'utilisateur
        if commit:
            user.save()

            # Ajoute l'utilisateur au groupe "Users" par défaut
            users_group, created = Group.objects.get_or_create(name="Users")
            user.groups.add(users_group)

        return user
# utils/email_utils.py
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.utils.html import strip_tags
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

def send_account_deletion_notification(user):
    """
    Envoie un email de confirmation de suppression de compte
    """
    try:
        subject = "Confirmation de suppression de votre compte CookFamily"
        
        # Context pour le template
        context = {
            'user': user,
            'username': user.username,
            'site_name': 'CookFamily',
            'contact_email': settings.DEFAULT_FROM_EMAIL or 'contact@cookfamily.com',
        }
        
        # Vérifier l'existence des templates avant de les utiliser
        html_template = 'emails/account_deletion_confirmation.html'
        txt_template = 'emails/account_deletion_confirmation.txt'
        
        try:
            # Essayer de générer le contenu HTML
            html_message = render_to_string(html_template, context)
            logger.info(f"Template HTML trouvé: {html_template}")
        except TemplateDoesNotExist as e:
            logger.error(f"Template HTML non trouvé: {html_template}")
            html_message = f"""
            <html>
            <body>
                <h2>Confirmation de suppression de compte - {context['site_name']}</h2>
                <p>Bonjour {context['user'].first_name or context['username']},</p>
                <p>Votre compte "{context['username']}" a été supprimé avec succès.</p>
                <p>Merci d'avoir fait partie de notre communauté !</p>
                <p>L'équipe {context['site_name']}</p>
            </body>
            </html>
            """
        
        try:
            # Essayer de générer le contenu texte
            text_message = render_to_string(txt_template, context)
            logger.info(f"Template texte trouvé: {txt_template}")
        except TemplateDoesNotExist as e:
            logger.error(f"Template texte non trouvé: {txt_template}")
            text_message = f"""
{context['site_name']} - Confirmation de suppression de compte

Bonjour {context['user'].first_name or context['username']},

Votre compte "{context['username']}" a été supprimé avec succès de notre plateforme {context['site_name']}.

Toutes vos données ont été définitivement supprimées de nos serveurs.

Merci d'avoir fait partie de notre communauté !

L'équipe {context['site_name']}
Contact: {context['contact_email']}
            """
        
        # Vérifier la configuration email
        if not settings.EMAIL_HOST_USER:
            logger.warning("EMAIL_HOST_USER non configuré")
            return False
            
        # Envoyer l'email
        result = send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result:
            logger.info(f"Email de confirmation de suppression envoyé avec succès à {user.email}")
            return True
        else:
            logger.error(f"Échec de l'envoi de l'email à {user.email}")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de suppression pour {user.email}: {e}")
        # Afficher plus de détails sur l'erreur
        import traceback
        logger.error(f"Traceback complet: {traceback.format_exc()}")
        return False

def send_admin_deletion_notification(user):
    """
    Envoie une notification aux administrateurs lors de la suppression d'un compte
    """
    try:
        # Vérifier s'il y a des administrateurs à notifier
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if not admin_email:
            logger.info("Aucun ADMIN_EMAIL configuré, pas d'envoi de notification admin")
            return False
            
        subject = f"Suppression de compte utilisateur - {user.username}"
        
        context = {
            'user': user,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined,
            'site_name': 'CookFamily',
        }
        
        # Templates avec fallback
        try:
            html_message = render_to_string('emails/admin_account_deletion.html', context)
        except TemplateDoesNotExist:
            html_message = f"""
            <html>
            <body>
                <h2>Suppression de compte - {context['site_name']}</h2>
                <p>L'utilisateur "{context['username']}" ({context['email']}) a supprimé son compte.</p>
                <p>Date d'inscription: {context['date_joined']}</p>
            </body>
            </html>
            """
        
        try:
            text_message = render_to_string('emails/admin_account_deletion.txt', context)
        except TemplateDoesNotExist:
            text_message = f"""
{context['site_name']} - Suppression de compte

L'utilisateur "{context['username']}" ({context['email']}) a supprimé son compte.
Date d'inscription: {context['date_joined']}
            """
        
        # Envoyer l'email
        result = send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=True,
        )
        
        if result:
            logger.info(f"Notification admin envoyée avec succès pour la suppression de {user.username}")
            return True
        else:
            logger.warning(f"Échec de l'envoi de la notification admin pour {user.username}")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification admin pour {user.username}: {e}")
        return False

def send_welcome_email(user):
    """
    Envoie un email de bienvenue lors de l'inscription
    """
    try:
        subject = "Bienvenue sur CookFamily !"
        
        context = {
            'user': user,
            'username': user.username,
            'site_name': 'CookFamily',
            'contact_email': settings.DEFAULT_FROM_EMAIL or 'contact@cookfamily.com',
        }
        
        # Templates avec fallback
        try:
            html_message = render_to_string('emails/welcome_email.html', context)
        except TemplateDoesNotExist:
            html_message = f"""
            <html>
            <body>
                <h2>Bienvenue sur {context['site_name']} !</h2>
                <p>Bonjour {context['user'].first_name or context['username']},</p>
                <p>Votre compte "{context['username']}" a été créé avec succès !</p>
                <p>Bienvenue dans notre communauté de passionnés de cuisine.</p>
                <p>L'équipe {context['site_name']}</p>
            </body>
            </html>
            """
        
        try:
            text_message = render_to_string('emails/welcome_email.txt', context)
        except TemplateDoesNotExist:
            text_message = f"""
{context['site_name']} - Bienvenue !

Bonjour {context['user'].first_name or context['username']},

Votre compte "{context['username']}" a été créé avec succès !
Bienvenue dans notre communauté de passionnés de cuisine.

L'équipe {context['site_name']}
Contact: {context['contact_email']}
            """
        
        # Envoyer l'email
        result = send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
        
        if result:
            logger.info(f"Email de bienvenue envoyé avec succès à {user.email}")
            return True
        else:
            logger.warning(f"Échec de l'envoi de l'email de bienvenue à {user.email}")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de bienvenue pour {user.email}: {e}")
        return False

def test_email_configuration():
    """
    Fonction utilitaire pour tester la configuration email
    """
    try:
        logger.info("Test de la configuration email...")
        logger.info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        logger.info(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Non configuré')}")
        logger.info(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Non configuré')}")
        logger.info(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Non configuré')}")
        logger.info(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Non configuré')}")
        logger.info(f"ADMIN_EMAIL: {getattr(settings, 'ADMIN_EMAIL', 'Non configuré')}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du test de configuration: {e}")
        return False
# utils/email_utils.py
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
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
    
def send_contact_email(form_data):
    """
    Envoie un email de contact à l'équipe
    """
    try:
        # Données du formulaire
        nom = form_data.get('nom', '')
        prenom = form_data.get('prenom', '')
        email = form_data.get('email', '')
        telephone = form_data.get('telephone', '')
        sujet = form_data.get('sujet', '')
        message = form_data.get('message', '')
        newsletter = form_data.get('newsletter', False)
        
        # Email de destination (équipe)
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'contact@cookfamily.com')
        
        # Sujet de l'email
        subject = f"Contact CookFamily - {sujet}"
        
        # Contenu HTML
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #16a085, #2ecc71); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin: 0; font-size: 24px;">Nouveau message de contact</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">CookFamily</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #16a085; border-bottom: 2px solid #16a085; padding-bottom: 5px;">Informations du contact</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #333; width: 120px;">Nom :</td>
                            <td style="padding: 8px 0; color: #555;">{nom}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #333;">Prénom :</td>
                            <td style="padding: 8px 0; color: #555;">{prenom}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #333;">Email :</td>
                            <td style="padding: 8px 0; color: #555;"><a href="mailto:{email}" style="color: #16a085;">{email}</a></td>
                        </tr>
                        {f'<tr><td style="padding: 8px 0; font-weight: bold; color: #333;">Téléphone :</td><td style="padding: 8px 0; color: #555;">{telephone}</td></tr>' if telephone else ''}
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #333;">Sujet :</td>
                            <td style="padding: 8px 0; color: #555;">{sujet}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #333;">Newsletter :</td>
                            <td style="padding: 8px 0; color: #555;">{'Oui' if newsletter else 'Non'}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="color: #16a085; border-bottom: 2px solid #16a085; padding-bottom: 5px;">Message</h3>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #16a085;">
                        <p style="margin: 0; color: #333; line-height: 1.6; white-space: pre-wrap;">{message}</p>
                    </div>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <p style="margin: 0; color: #2c5530; font-size: 14px;">
                        <strong>📧 Répondre au contact :</strong> Vous pouvez répondre directement à ce message à l'adresse {email}
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px; margin: 0;">
                        Message envoyé automatiquement depuis le formulaire de contact de CookFamily
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Contenu texte
        text_message = f"""
NOUVEAU MESSAGE DE CONTACT - CookFamily

INFORMATIONS DU CONTACT:
- Nom: {nom}
- Prénom: {prenom}
- Email: {email}
{f'- Téléphone: {telephone}' if telephone else ''}
- Sujet: {sujet}
- Newsletter: {'Oui' if newsletter else 'Non'}

MESSAGE:
{message}

---
Répondre à: {email}
Message envoyé depuis le formulaire de contact CookFamily
        """
        
        # Envoyer l'email
        email_message = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
            reply_to=[email],  # Permet de répondre directement au contact
        )
        email_message.content_subtype = "html"
        email_message.body = html_message
        
        result = email_message.send()
        
        if result:
            logger.info(f"Email de contact envoyé avec succès depuis {email}")
            return True
        else:
            logger.error(f"Échec de l'envoi de l'email de contact depuis {email}")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de contact: {e}")
        import traceback
        logger.error(f"Traceback complet: {traceback.format_exc()}")
        return False

def send_contact_confirmation_email(form_data):
    """
    Envoie un email de confirmation à la personne qui a envoyé le message
    """
    try:
        nom = form_data.get('nom', '')
        prenom = form_data.get('prenom', '')
        email = form_data.get('email', '')
        sujet = form_data.get('sujet', '')
        
        subject = "Confirmation de réception de votre message - CookFamily"
        
        # Contenu HTML
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #16a085, #2ecc71); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin: 0; font-size: 24px;">Merci pour votre message !</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">CookFamily</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">
                        Bonjour {prenom} {nom},
                    </p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">
                        Nous avons bien reçu votre message concernant "<strong>{sujet}</strong>".
                    </p>
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">
                        Notre équipe vous répondra dans les plus brefs délais, généralement sous 24 à 48 heures ouvrées.
                    </p>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #2c5530; font-size: 14px;">
                        <strong>💡 En attendant notre réponse :</strong><br>
                        N'hésitez pas à explorer nos recettes et à rejoindre notre communauté de passionnés de cuisine !
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://cookfamily.com" style="display: inline-block; background: linear-gradient(135deg, #16a085, #2ecc71); color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Découvrir CookFamily
                    </a>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px; margin: 0;">
                        L'équipe CookFamily<br>
                        <a href="mailto:contact@cookfamily.com" style="color: #16a085;">contact@cookfamily.com</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Contenu texte
        text_message = f"""
Merci pour votre message ! - CookFamily

Bonjour {prenom} {nom},

Nous avons bien reçu votre message concernant "{sujet}".

Notre équipe vous répondra dans les plus brefs délais, généralement sous 24 à 48 heures ouvrées.

En attendant notre réponse, n'hésitez pas à explorer nos recettes sur https://cookfamily.com

Cordialement,
L'équipe CookFamily
contact@cookfamily.com
        """
        
        # Envoyer l'email
        result = send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=True,
        )
        
        if result:
            logger.info(f"Email de confirmation envoyé avec succès à {email}")
            return True
        else:
            logger.warning(f"Échec de l'envoi de l'email de confirmation à {email}")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {e}")
        return False
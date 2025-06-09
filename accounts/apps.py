from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    
    def ready(self):
        """
        Méthode appelée quand l'application est prête
        Importe les signaux pour qu'ils soient enregistrés
        """
        import accounts.signals

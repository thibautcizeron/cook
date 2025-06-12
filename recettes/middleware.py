from django.shortcuts import render

class LoadingPageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.first_request = True
        
    def __call__(self, request):
        if self.first_request and request.path == '/' and not request.session.get('page_loaded', False):
            # Marquer que l'utilisateur a vu la page de chargement
            request.session['page_loaded'] = True
            # Afficher la page de chargement pour la première visite
            return render(request, 'base/loading.html')
        
        # Pour les requêtes suivantes, continuer normalement
        response = self.get_response(request)
        return response


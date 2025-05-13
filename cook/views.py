# cook/views.py
from django.shortcuts import render

def handler404(request, exception):
    return render(request, 'index/404.html', status=404)

def handler500(request):
    return render(request, 'index/500.html', status=500)

def handler403(request, exception):
    return render(request, 'index/403.html', status=403)

def handler400(request, exception):
    return render(request, 'index/400.html', status=400)
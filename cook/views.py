from django.shortcuts import render

def handler404(request, exception):
    return render(request, 'base/errors/404.html', status=404)

def handler500(request):
    return render(request, 'base/errors/500.html', status=500)

def handler403(request, exception):
    return render(request, 'base/errors/403.html', status=403)

def handler400(request, exception):
    return render(request, 'base/errors/400.html', status=400)
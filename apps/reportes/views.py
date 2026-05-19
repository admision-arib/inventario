from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def reportes(request):
    contexto = {
        'titulo': 'Reportes del Sistema',
    }
    return render(request, 'reportes.html', contexto)
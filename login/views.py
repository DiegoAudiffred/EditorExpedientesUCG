from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
    
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index:index')  # si ya está loggeado, redirige directo

    form = LoginForm(request.POST or None)
    msg = ''
    
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('index:index')  # redirige al index después del login
            else:
                msg = 'Usuario o contraseña incorrectos'
    
    return render(request, 'login/login.html', {'form': form, 'msg': msg})

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login:login')  # Redirige al login después de cerrar sesión
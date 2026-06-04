from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from dashboard.models import Cliente
from .forms import LoginClienteForm


def login_cliente(request):
    form = LoginClienteForm(request.POST or None)
    error = None

    if request.method == 'POST' and form.is_valid():
        correo = form.cleaned_data['correo']
        contraseña = form.cleaned_data['contraseña']

        try:
            cliente = Cliente.objects.get(correo=correo)
        except Cliente.DoesNotExist:
            error = 'Correo o contraseña incorrectos.'
        else:
            if cliente.estado == 'inactivo':
                error = 'Tu cuenta está inactiva.'
            elif check_password(contraseña, cliente.contraseña):
                request.session['cliente_id'] = cliente.pk
                request.session['cliente_nombre'] = cliente.nombre
                return redirect('tienda_inicio')
            else:
                error = 'Correo o contraseña incorrectos.'

    return render(request, 'tienda/login.html', {'form': form, 'error': error})


def logout_cliente(request):
    request.session.flush()
    return redirect('tienda_login')


def inicio(request):
    # Si no hay sesión, manda al login
    if not request.session.get('cliente_id'):
        return redirect('tienda_login')

    nombre = request.session.get('cliente_nombre')
    return render(request, 'tienda/inicio.html', {'nombre': nombre})

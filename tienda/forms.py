from django import forms

class LoginClienteForm(forms.Form):
    correo = forms.EmailField(label='Correo')
    contraseña = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Perfil

class RegistroAlumnoForm(UserCreationForm):
    # Añadimos campos extra al formulario estándar de Django
    email = forms.EmailField(required=True, help_text="Para enviarte tus reportes de progreso")
    idioma_nativo = forms.ChoiceField(choices=Perfil.IDIOMAS)
    variante_interes = forms.ChoiceField(choices=Perfil.VARIANTES)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Aquí es donde la magia ocurre:
            # Gracias a que ya tenemos las signals, el perfil se crea solo.
            # Ahora solo le pasamos los datos que el usuario eligió:
            perfil = user.perfil
            perfil.idioma_nativo = self.cleaned_data.get('idioma_nativo')
            perfil.variante_interes = self.cleaned_data.get('variante_interes')
            perfil.save()
        return user

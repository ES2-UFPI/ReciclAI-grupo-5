from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, RegistroMaterial

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False 
    verbose_name_plural = 'Informações de Perfil (CPF/CNPJ, Telefone, Moedas)'
    fields = ('cpf_cnpj', 'telefone', 'tipo_usuario', 'num_moedas') 


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(RegistroMaterial)
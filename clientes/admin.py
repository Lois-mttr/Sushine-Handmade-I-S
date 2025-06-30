from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('persona', 'correo', 'estado')
    list_filter = ('estado',)
    search_fields = ('persona__nombre', 'persona__apellido', 'correo')
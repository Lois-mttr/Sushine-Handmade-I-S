from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db import transaction, IntegrityError, connection
from django.core.exceptions import ValidationError
from AuthLogin.decorators import nexo_login_required, nexo_role_required
from .forms import PersonaForm, ClienteForm
from .models import Cliente, Persona
from .services import ClienteService, logger


@nexo_login_required
@nexo_role_required(['admin', 'ventas'])
def listar_clientes(request):
    """Lista paginada de clientes con filtros"""
    filtros = {
        'cedula': request.GET.get('cedula', ''),
        'nombre': request.GET.get('nombre', ''),
        'apellido': request.GET.get('apellido', ''),
        'correo': request.GET.get('correo', '')
    }

    page = int(request.GET.get('page', 1))
    per_page = 10

    data = ClienteService.obtener_clientes_paginados(filtros, page, per_page)

    context = {
        'clientes': data['clientes'],
        'filtros': filtros,
        'paginacion': {
            'page': page,
            'per_page': per_page,
            'total': data['total'],
            'total_pages': data['total_pages'],
            'has_previous': page > 1,
            'has_next': page < data['total_pages']
        }
    }
    return render(request, 'clientes/list.html', context)


@nexo_login_required
@nexo_role_required(['admin', 'ventas'])
def crear_cliente(request):
    if request.method == 'POST':
        persona_form = PersonaForm(request.POST)
        cliente_form = ClienteForm(request.POST)

        if persona_form.is_valid() and cliente_form.is_valid():
            try:
                # Guardar persona primero
                persona = persona_form.save()

                # Luego guardar cliente
                cliente = cliente_form.save(commit=False)
                cliente.persona = persona
                cliente.save()

                messages.success(request, 'Cliente registrado exitosamente')
                return redirect('clientes:list')
            except IntegrityError:
                messages.error(request, 'Esta cédula ya está registrada')
            except Exception as e:
                messages.error(request, f'Error al registrar: {str(e)}')
    else:
        persona_form = PersonaForm()
        cliente_form = ClienteForm()

    return render(request, 'clientes/create.html', {
        'persona_form': persona_form,
        'cliente_form': cliente_form
    })


@nexo_login_required
@nexo_role_required(['admin', 'ventas'])
def detalle_cliente(request, pk):
    messages.info(request, 'Los detalles del cliente se gestionan desde el listado.')
    return redirect('clientes:list')

@nexo_login_required
@nexo_role_required(['admin', 'ventas'])
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        persona_form = PersonaForm(request.POST, instance=cliente.persona)
        cliente_form = ClienteForm(request.POST, instance=cliente)

        if persona_form.is_valid() and cliente_form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar persona (asegurando mantener estado)
                    persona = persona_form.save(commit=False)
                    persona.estado = True  # Forzar estado activo
                    persona.cedula = cliente.persona.cedula  # Mantener cédula
                    persona.save()

                    # Guardar cliente (asegurando mantener estado)
                    cliente = cliente_form.save(commit=False)
                    cliente.estado = True  # Forzar estado activo
                    cliente.persona = persona
                    cliente.save()

                messages.success(request, 'Cliente actualizado y mantenido activo')
                return redirect('clientes:list')

            except Exception as e:
                logger.error(f"Error al actualizar cliente {pk}: {str(e)}")
                messages.error(request, 'Error al actualizar el cliente')
    else:
        persona_form = PersonaForm(instance=cliente.persona)
        cliente_form = ClienteForm(instance=cliente)

    context = {
        'cliente': cliente,
        'persona_form': persona_form,
        'cliente_form': cliente_form,
    }
    return render(request, 'clientes/edit.html', context)
@nexo_login_required
@nexo_role_required(['admin'])
def desactivar_cliente(request, pk):
    """Desactiva un cliente (soft delete)"""
    if request.method == 'POST':
        try:
            ClienteService.desactivar_cliente(pk)
            messages.success(request, 'Cliente desactivado correctamente')
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('clientes:list')


@nexo_login_required
def validar_cedula(request):
    """API para validar cédula disponible (AJAX)"""
    cedula = request.GET.get('cedula', '')
    existe = Persona.objects.filter(cedula=cedula).exists()
    return JsonResponse({'disponible': not existe, 'cedula': cedula})

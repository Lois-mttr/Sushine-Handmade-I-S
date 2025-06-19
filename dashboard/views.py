from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import connection
from core_data.models import *
import json

def login_required_custom(view_func):
    """
    Custom login required decorator for NEXO system
    """
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required_custom
def dashboard_home(request):
    """
    Vista principal del dashboard con estadísticas y datos recientes
    """
    context = {
        'current_time': timezone.now(),
        'recent_entries': get_recent_entries(),
        'recent_sales': get_recent_sales(),
        'stats': get_dashboard_stats(),
    }
    return render(request, 'dashboard/home.html', context)

def get_recent_entries():
    """
    Obtener las entradas más recientes usando stored procedure
    """
    try:
        with connection.cursor() as cursor:
            # Simulación de datos - reemplazar con stored procedure real
            return [
                {'fecha': '12/11/2024', 'producto': 'Cartera', 'total': 'C$ XXXX'},
                {'fecha': '12/11/2024', 'producto': 'Bolso', 'total': 'C$ XXXX'},
                {'fecha': '12/11/2024', 'producto': 'Monedero', 'total': 'C$ XXXX'},
                {'fecha': '12/11/2024', 'producto': 'Bolso', 'total': 'C$ XXXX'},
                {'fecha': '11/11/2024', 'producto': 'Monedero', 'total': 'C$ XXXX'},
                {'fecha': '11/11/2024', 'producto': 'Cartera', 'total': 'C$ XXXX'},
            ]
    except Exception as e:
        return []

def get_recent_sales():
    """
    Obtener las ventas más recientes usando stored procedure
    """
    try:
        with connection.cursor() as cursor:
            # Simulación de datos - reemplazar con stored procedure real
            return [
                {'fecha': '12/11/2024', 'cantidad': '73', 'total': 'C$ XXXX'},
                {'fecha': '11/11/2024', 'cantidad': '58', 'total': 'C$ XXXX'},
                {'fecha': '10/11/2024', 'cantidad': '51', 'total': 'C$ XXXX'},
                {'fecha': '09/11/2024', 'cantidad': '48', 'total': 'C$ XXXX'},
                {'fecha': '08/11/2024', 'cantidad': '82', 'total': 'C$ XXXX'},
                {'fecha': '07/11/2024', 'cantidad': '68', 'total': 'C$ XXXX'},
            ]
    except Exception as e:
        return []

def get_dashboard_stats():
    """
    Obtener estadísticas importantes del dashboard
    """
    try:
        with connection.cursor() as cursor:
            # Simulación de datos - reemplazar con stored procedures reales
            return {
                'productos': 79,
                'devoluciones': 26,
                'entradas': 4,
                'salidas': 2,
            }
    except Exception as e:
        return {
            'productos': 0,
            'devoluciones': 0,
            'entradas': 0,
            'salidas': 0,
        }

# Funciones para usar stored procedures
def call_stored_procedure(procedure_name, params=None):
    """
    Función genérica para llamar stored procedures
    """
    try:
        with connection.cursor() as cursor:
            if params:
                cursor.callproc(procedure_name, params)
            else:
                cursor.callproc(procedure_name)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error calling stored procedure {procedure_name}: {e}")
        return None

# Funciones específicas para cada stored procedure
def cancel_sale(sale_id):
    return call_stored_procedure('CancelSale', [sale_id])

def create_employee(employee_data):
    return call_stored_procedure('CreateEmployee', employee_data)

def terminate_production(production_id):
    return call_stored_procedure('TerminateProduction', [production_id])

def edit_customer(customer_data):
    return call_stored_procedure('EditCustomer', customer_data)

def edit_return(return_data):
    return call_stored_procedure('EditReturn', return_data)

def edit_employee(employee_data):
    return call_stored_procedure('EditEmployee', employee_data)

def edit_person(person_data):
    return call_stored_procedure('EditPerson', person_data)

def edit_production(production_data):
    return call_stored_procedure('EditProduction', production_data)

def edit_product(product_data):
    return call_stored_procedure('EditProduct', product_data)

def edit_sale(sale_data):
    return call_stored_procedure('EditSale', sale_data)

def delete_customer(customer_id):
    return call_stored_procedure('DeleteCustomer', [customer_id])

def delete_employee(employee_id):
    return call_stored_procedure('DeleteEmployee', [employee_id])

def delete_person(person_id):
    return call_stored_procedure('DeletePerson', [person_id])

def delete_product(product_id):
    return call_stored_procedure('DeleteProduct', [product_id])

def insert_customer(customer_data):
    return call_stored_procedure('InsertCustomer', customer_data)

def insert_person(person_data):
    return call_stored_procedure('InsertPerson', person_data)

def insert_product(product_data):
    return call_stored_procedure('InsertProduct', product_data)

def make_sale(sale_data):
    return call_stored_procedure('MakeSale', sale_data)

def register_return(return_data):
    return call_stored_procedure('RegisterReturn', return_data)

def register_production(production_data):
    return call_stored_procedure('RegisterProduction', production_data)

def register_user(user_data):
    return call_stored_procedure('RegisterUser', user_data)

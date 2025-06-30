import logging
from django.db import connection
from django.core.exceptions import ValidationError
from datetime import datetime

logger = logging.getLogger('nexo.clientes')

class ClienteService:
    """Servicio para operaciones CRUD de clientes con procedimientos almacenados"""

    @staticmethod
    def crear_cliente_completo(cedula, primer_nombre, primer_apellido, direccion,
                             correo=None, segundo_nombre=None, segundo_apellido=None):
        """
        Crea un nuevo cliente con su persona asociada usando procedimientos almacenados
        """
        try:
            with connection.cursor() as cursor:
                # Insertar Persona
                cursor.callproc('InsertarPersona', [
                    cedula,
                    primer_nombre,
                    segundo_nombre or '',
                    primer_apellido,
                    segundo_apellido or '',
                    direccion
                ])

                # Insertar Cliente si hay correo
                if correo:
                    cursor.callproc('InsertarCliente', [correo, cedula])

                logger.info(f'Cliente creado: {cedula}')
                return True

        except Exception as e:
            logger.error(f'Error al crear cliente: {str(e)}')
            error_msg = str(e)
            if 'Duplicate entry' in error_msg:
                raise ValidationError('La cédula ya está registrada')
            raise ValidationError('Error al registrar el cliente')

    @staticmethod
    def obtener_clientes_paginados(filtros=None, page=1, per_page=10):
        """
        Obtiene clientes paginados con filtros avanzados
        """
        try:
            base_query = """
                SELECT 
                    c.idCliente,
                    p.cedula,
                    CONCAT(p.primerNombre, ' ', p.primerApellido) as nombre_completo,
                    p.direccion,
                    c.correo,
                    c.estadoCliente,
                    p.estadoPersona
                FROM Persona p
                JOIN Cliente c ON p.cedula = c.idPersonaCliente
                WHERE p.estadoPersona = 1 AND c.estadoCliente = 1
            """
            params = []
            
            # Aplicar filtros
            if filtros:
                if filtros.get('cedula'):
                    base_query += " AND p.cedula LIKE %s"
                    params.append(f"%{filtros['cedula']}%")
                
                if filtros.get('nombre'):
                    base_query += " AND (p.primerNombre LIKE %s OR p.segundoNombre LIKE %s)"
                    params.extend([f"%{filtros['nombre']}%", f"%{filtros['nombre']}%"])
                
                if filtros.get('apellido'):
                    base_query += " AND (p.primerApellido LIKE %s OR p.segundoApellido LIKE %s)"
                    params.extend([f"%{filtros['apellido']}%", f"%{filtros['apellido']}%"])
                
                if filtros.get('correo'):
                    base_query += " AND c.correo LIKE %s"
                    params.append(f"%{filtros['correo']}%")

            # Ordenación
            base_query += " ORDER BY p.primerApellido, p.primerNombre"

            # Paginación
            offset = (page - 1) * per_page
            paginated_query = f"{base_query} LIMIT {per_page} OFFSET {offset}"

            with connection.cursor() as cursor:
                # Obtener datos paginados
                cursor.execute(paginated_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                # Contar total
                count_query = f"SELECT COUNT(*) FROM ({base_query}) AS total_query"
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]

                return {
                    'clientes': results,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }

        except Exception as e:
            logger.error(f'Error al listar clientes: {str(e)}')
            return {'clientes': [], 'total': 0}

    @staticmethod
    def actualizar_cliente(id_cliente, correo=None, cedula=None):
        """
        Actualiza datos del cliente usando procedimiento almacenado
        """
        try:
            with connection.cursor() as cursor:
                cursor.callproc('EditarCliente', [
                    id_cliente,
                    correo or '',
                    cedula or ''
                ])
                logger.info(f'Cliente actualizado: {id_cliente}')
                return True
        except Exception as e:
            logger.error(f'Error al actualizar cliente {id_cliente}: {str(e)}')
            raise ValidationError(f'Error al actualizar cliente: {str(e)}')

    @staticmethod
    def desactivar_cliente(id_cliente):
        """
        Desactiva un cliente (soft delete) usando procedimiento almacenado
        """
        try:
            with connection.cursor() as cursor:
                cursor.callproc('EliminarCliente', [id_cliente])
                logger.info(f'Cliente desactivado: {id_cliente}')
                return True
        except Exception as e:
            logger.error(f'Error al desactivar cliente {id_cliente}: {str(e)}')
            raise ValidationError(f'Error al desactivar cliente: {str(e)}')

    @staticmethod
    def obtener_detalle_cliente(id_cliente):
        """
        Obtiene información detallada de un cliente específico
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        c.idCliente,
                        p.cedula,
                        p.primerNombre,
                        p.segundoNombre,
                        p.primerApellido,
                        p.segundoApellido,
                        p.direccion,
                        c.correo,
                        c.estadoCliente
                    FROM Cliente c
                    JOIN Persona p ON c.idPersonaCliente = p.cedula
                    WHERE c.idCliente = %s
                """, [id_cliente])
                
                columns = [col[0] for col in cursor.description]
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return dict(zip(columns, result))
                
        except Exception as e:
            logger.error(f'Error al obtener detalle cliente {id_cliente}: {str(e)}')
            return None
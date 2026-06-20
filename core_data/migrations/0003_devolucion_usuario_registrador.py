from django.db import migrations


def add_usuario_registrador(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, 'Devolucion')
        }
        if 'idUsuarioDev' not in existing_columns:
            cursor.execute('ALTER TABLE Devolucion ADD COLUMN idUsuarioDev INT NULL')

        cursor.execute("SHOW INDEX FROM Devolucion WHERE Key_name = %s", ['idx_devolucion_usuario_dev'])
        if not cursor.fetchone():
            cursor.execute('CREATE INDEX idx_devolucion_usuario_dev ON Devolucion (idUsuarioDev)')


def remove_usuario_registrador(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute("SHOW INDEX FROM Devolucion WHERE Key_name = %s", ['idx_devolucion_usuario_dev'])
        if cursor.fetchone():
            cursor.execute('DROP INDEX idx_devolucion_usuario_dev ON Devolucion')

        existing_columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, 'Devolucion')
        }
        if 'idUsuarioDev' in existing_columns:
            cursor.execute('ALTER TABLE Devolucion DROP COLUMN idUsuarioDev')


class Migration(migrations.Migration):

    dependencies = [
        ('core_data', '0002_alter_detalleventa_options_alter_detalleventa_table'),
    ]

    operations = [
        migrations.RunPython(add_usuario_registrador, remove_usuario_registrador),
    ]

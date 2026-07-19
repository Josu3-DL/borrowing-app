# Borrowing

Aplicación web construida con Django para registrar y gestionar préstamos
personales. Cada usuario administra el dinero que presta a personas externas a
la aplicación; los prestatarios no necesitan una cuenta.

## Funcionalidades

- Registro, inicio y cierre de sesión.
- Edición del perfil del usuario.
- Creación, edición y eliminación de préstamos.
- Datos de contacto del prestatario en cada préstamo.
- Listado de préstamos propios.
- Filtros combinables por estado, rango de fecha y nombre del prestatario.
- Validación de montos y fechas.
- Separación de datos entre usuarios autenticados.

## Requisitos

- Python
- `pip`

Las dependencias de Python están declaradas en `requirements.txt`.

## Ejecución local

1. Crea y activa un entorno virtual.

   En Windows:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   En macOS o Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Instala las dependencias.

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Crea las tablas de la base de datos.

   ```bash
   python manage.py migrate
   ```

4. Inicia el servidor de desarrollo.

   ```bash
   python manage.py runserver
   ```

5. Abre `http://127.0.0.1:8000/`, crea una cuenta y comienza a registrar
   préstamos.

## Pruebas

Ejecuta toda la suite con:

```bash
python manage.py test
```

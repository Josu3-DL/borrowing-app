# Borrowing App

Aplicación Django para la gestión de préstamos.

## Requisitos

- Python 3.13+
- Ver `requirements.txt` (Django 6.0.7)

## Puesta en marcha

```bash
env\Scripts\python manage.py migrate
env\Scripts\python manage.py runserver
```

La app queda disponible en `http://127.0.0.1:8000/`.

## Módulos implementados

### 1. Usuarios y autenticación (`users`)

- Modelo de usuario personalizado (`users.User`, `AUTH_USER_MODEL`) que extiende `AbstractUser` con `email` único (case-insensitive) y `phone`.
- Manager personalizado (`UserManager`) para creación de usuarios y superusuarios.
- Vistas: registro (`/registro/`), inicio de sesión (`/iniciar-sesion/`), cierre de sesión (`/cerrar-sesion/`) y perfil (`/perfil/`, requiere sesión iniciada).
- Validación de correo duplicado en registro y edición de perfil.
- Integración con el admin de Django (`CustomUserAdmin`).

### 2. Gestión de préstamos (`prestamos`)

Módulo con operaciones CRUD completas sobre préstamos:

- **Modelos**:
  - `Cliente`: nombre, teléfono, email.
  - `Prestamo`: cliente (FK), monto, fecha de préstamo, fecha de vencimiento, estado (`Pendiente` / `Pagado`), usuario que lo creó (FK a `AUTH_USER_MODEL`), timestamps de creación/actualización.
- **Vistas** (`/prestamos/`):
  - Listar préstamos, con filtro por estado (`?estado=PENDIENTE` o `?estado=PAGADO`).
  - Crear préstamo (`/prestamos/nuevo/`).
  - Editar préstamo (`/prestamos/<id>/editar/`).
  - Eliminar préstamo, con confirmación (`/prestamos/<id>/eliminar/`).
- Validación de formulario: la fecha de vencimiento no puede ser anterior a la fecha del préstamo.
- Registrado en el admin de Django.

## Estado del repositorio

- `master`: contiene el módulo de usuarios (mergeado vía PR #1).
- `feature/loan-management`: rama de trabajo con el módulo de préstamos, rebasada sobre `master` para incluir ambos módulos. Pendiente de abrir pull request hacia `master`.

## Flujo de trabajo

Los cambios se desarrollan en ramas de feature (`feature/<nombre>`) y se integran a `master` mediante pull request, documentando en la descripción del PR qué se implementó.

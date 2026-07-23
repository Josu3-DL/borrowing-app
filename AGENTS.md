# Guía para agentes de código

Este archivo contiene las instrucciones del repositorio para Codex y Claude.
Se aplica a todo el proyecto.

## Descripción del proyecto

Borrowing es una aplicación web para registrar y administrar préstamos
personales. Cada usuario autenticado gestiona sus propios préstamos a personas
externas, conserva los datos de contacto de los prestatarios, registra abonos
en dólares estadounidenses o córdobas nicaragüenses y consulta saldos,
vencimientos y estados.

## Tecnologías

- Python 3.
- Django 6.
- SQLite como base de datos de desarrollo.
- Plantillas de Django para la interfaz renderizada en el servidor.
- HTML, CSS y JavaScript sin frameworks de frontend.
- Lucide para los iconos, distribuido localmente.
- El framework de pruebas de Django.

## Reglas de idioma

1. Escribe en inglés el código fuente, incluidos nombres de variables,
   funciones, clases, módulos y ramas de Git.
2. Escribe en español los títulos y las descripciones de los pull requests, así
   como los mensajes de commit.
3. Escribe en español todo el contenido visible de la página, incluidos textos,
   etiquetas, mensajes de validación, notificaciones y atributos de
   accesibilidad dirigidos a usuarios.

## Nombrado de ramas

No uses el prefijo `agent/` en los nombres de ramas. Anteponles directamente uno
de los prefijos habituales según el tipo de cambio: `feature/` o `feat/` para
funcionalidades, `fix/` o `bugfix/` para correcciones, `chore/` para tareas de
mantenimiento, `docs/` para documentación, `refactor/` para refactorizaciones y
`test/` para pruebas. Escribe la descripción en inglés y usa `kebab-case`. Por
ejemplo: `feat/add-payment-reminders`.

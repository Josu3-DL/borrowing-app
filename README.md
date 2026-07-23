# Borrowing

Aplicación web construida con Django para registrar y gestionar préstamos
personales. Cada usuario administra el dinero que presta a personas externas a
la aplicación; los prestatarios no necesitan una cuenta.

## Funcionalidades

- Registro, inicio y cierre de sesión.
- Edición del perfil del usuario.
- Creación, edición y eliminación de préstamos.
- Registro y eliminación de abonos (pagos) en dólares (USD) o córdobas (NIO).
- Datos de contacto del prestatario en cada préstamo.
- Listado de préstamos y de abonos propios, con historial por préstamo.
- Filtros combinables por estado, moneda, rango de fecha y nombre del prestatario.
- Panel con métricas y gráficas de préstamos/recuperación por periodo.
- Validación de montos y fechas.
- Separación de datos entre usuarios autenticados.

## Moneda, tasa y reglas de estado

- Monedas admitidas: dólares (USD) y córdobas (NIO).
- La tasa de cambio es fija: **1 USD = 37 NIO**. No se guarda un historial de
  tasas por abono; toda conversión usa siempre esta tasa.
- Toda conversión y formateo de dinero vive en `borrowing_app/money.py`
  (fuente única: monedas admitidas, redondeo a 2 decimales con
  `ROUND_HALF_UP`, símbolos, formateo). Ningún otro módulo debe duplicar la
  tasa o la lógica de redondeo.
- `Loan.status` (pendiente/pagado) es un valor **derivado**, no editable
  directamente: refleja siempre el saldo restante (`amount` menos abonos
  convertidos a la moneda del préstamo). Se recalcula exclusivamente a
  través de `Loan.recompute_status()`, invocado por `loans.services` y
  `payments.services` dentro de la misma transacción que crea o elimina un
  abono.
- Un préstamo con al menos un abono registrado no puede cambiar de moneda.
- El monto de un préstamo no puede reducirse por debajo de lo ya abonado.
- Un abono nunca puede superar el saldo restante del préstamo (convertido a
  su moneda); un préstamo ya pagado no admite más abonos. Esta regla se
  aplica primero en el formulario (mensaje amigable) y de nuevo, como
  autoridad final, en `payments.services.create_payment` dentro de una
  transacción con el préstamo bloqueado (`select_for_update`), para
  prevenir sobrepagos por escrituras concurrentes.

## Arquitectura

- `borrowing_app/money.py`: núcleo monetario compartido.
- `borrowing_app/reporting.py`: capa de reporting del panel (única autorizada
  a consultar préstamos y pagos juntos).
- `loans/domain.py`, `loans/services.py`, `loans/selectors.py`: reglas de
  negocio, escrituras transaccionales y consultas de lectura de préstamos.
- `payments/services.py`, `payments/selectors.py`: escrituras transaccionales
  y consultas de lectura de abonos.
- Las vistas (`loans/views.py`, `payments/views.py`) solo validan entrada,
  invocan un selector o servicio, y renderizan o redirigen.
- `Loan.objects.owned_by(user)` / `Payment.objects.owned_by(user)` centralizan
  el aislamiento de datos entre usuarios.

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

## Variables de entorno

Ninguna es obligatoria en desarrollo: sin configurarlas, la app arranca con
valores locales seguros (`DEBUG=true`, `SECRET_KEY` de desarrollo, cookies
sin `Secure`). Antes de desplegar con `DEBUG=false` es obligatorio definir al
menos `DJANGO_SECRET_KEY` y `DJANGO_ALLOWED_HOSTS`.

| Variable                              | Por defecto                | Descripción |
|----------------------------------------|-----------------------------|-------------|
| `DJANGO_DEBUG`                         | `true`                       | `false` en produccion. |
| `DJANGO_SECRET_KEY`                    | clave insegura de desarrollo | Obligatoria (y distinta) cuando `DJANGO_DEBUG=false`. |
| `DJANGO_ALLOWED_HOSTS`                 | `localhost,127.0.0.1`        | Lista separada por comas; vacía por defecto si `DEBUG=false`. |
| `DJANGO_SESSION_COOKIE_SECURE`         | igual a `not DEBUG`          | Fuerza cookie de sesión solo por HTTPS. |
| `DJANGO_CSRF_COOKIE_SECURE`            | igual a `not DEBUG`          | Fuerza cookie CSRF solo por HTTPS. |
| `DJANGO_SECURE_SSL_REDIRECT`           | `false`                       | Redirige todo HTTP a HTTPS. |
| `DJANGO_SECURE_HSTS_SECONDS`           | `0` (desactivado)             | Actívalo solo tras confirmar que HTTPS funciona en todo el dominio; no se activa automáticamente. |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`| `false`                       | Ver documentación de Django sobre HSTS antes de activarlo. |
| `DJANGO_SECURE_HSTS_PRELOAD`           | `false`                       | Ídem. |

## Pruebas y calidad

Instala las dependencias de desarrollo (incluye las de `requirements.txt`):

```bash
python -m pip install -r requirements-dev.txt
```

Comandos reproducibles:

```bash
python manage.py check                 # detecta configuración/deploy insegura
python manage.py makemigrations --check --dry-run  # sin migraciones pendientes
python manage.py test                  # suite completa
ruff check .                           # analisis estatico
ruff format .                          # formato
coverage run manage.py test && coverage report  # cobertura
```

## Migraciones

El historial de migraciones de `loans` y `payments` tiene ramas fusionadas
(`0004_merge_20260718_1833`, `0005_merge_20260718_dashboard`): dos features
en paralelo agregaron `0002`/`0003` por separado y Django generó una
migración de fusión para cada punto de choque. Esto es intencional y no debe
"aplanarse" (squash) sin coordinarlo antes con el equipo, ya que un squash
reescribe migraciones ya aplicadas en entornos existentes. Las migraciones
`0006`/`0007` (restricciones de dominio y recálculo de `status`) se añadieron
sobre la punta actual de ambos historiales sin tocar las ya aplicadas.

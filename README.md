# Sistema de Gestión de Resultados (SGR) — Municipalidad de La Serena

Aplicación académica para visualizar el seguimiento territorial y gestionar los catálogos maestros del SGR. Los datos generados para la demostración son ficticios. En esta etapa, actividades y compromisos se muestran sin persistir transacciones.

## Inicio rápido en Windows

1. Instala Python 3.11 o posterior.
2. Descarga este repositorio y abre PowerShell en su carpeta.
3. Ejecuta:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\iniciar_sgr_local.ps1
   ```

El script crea un entorno Python local, instala Django, prepara la base SQLite, carga catálogos ficticios y solicita crear una cuenta administradora la primera vez. Luego inicia la aplicación en <http://127.0.0.1:8000/>. Deja abierta la ventana de PowerShell mientras la usas; `Ctrl+C` detiene el servidor.

La cuenta administradora permite entrar al SGR. Los datos cargados son ficticios y no se crean contraseñas compartidas. La base queda guardada en `db.sqlite3` en ese equipo.

## Inicio manual

Requiere Python 3.11 o posterior y Node.js/npm solo si necesitas recompilar el CSS.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
npm run build:css
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py load_demo_data
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Abre <http://127.0.0.1:8000/> e inicia sesión con la cuenta que acabas de crear. La aplicación ya incluye el CSS compilado; Node no se necesita para ejecutarla si no modificas los estilos.

La configuración local usa SQLite y valores de desarrollo. Para ejecutar en producción se deben definir `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` y los parámetros de base de datos; la aplicación rechaza iniciar si faltan el secreto o los hosts permitidos.

Para usar MySQL, definir `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`. No guardar secretos ni credenciales en el repositorio.

## Pruebas

```powershell
python manage.py test -v 2
python manage.py check
```

El plan de casos y su ejecución están en [Plan de pruebas unitarias](docs/plan-pruebas-unitarias.md).

## Seguridad y arquitectura

- [Estándares de seguridad](SECURITY.md)
- [Arquitectura 4+1](docs/arquitectura-4mas1.md)
- [Preparación de despliegue AWS](docs/despliegue-aws.md)

## Paquete para Elastic Beanstalk

El repositorio incluye `Procfile`, `.ebextensions/01_django.config` y `.env.example` como base de configuración. `collectstatic` prepara los archivos servidos por WhiteNoise; Gunicorn inicia `config.wsgi:application`. `.env.example` es una plantilla de referencia: Django no carga archivos `.env` automáticamente, así que define las variables en tu terminal local. En AWS define las variables en la configuración protegida del entorno, sin subir `.env`. Las migraciones se ejecutan manualmente una vez tras verificar el destino.

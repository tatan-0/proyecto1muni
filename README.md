# Sistema de Gestión de Resultados (SGR) — Municipalidad de La Serena

Aplicación académica para visualizar el seguimiento territorial y gestionar los catálogos maestros del SGR. Los datos generados para la demostración son ficticios. En esta etapa, actividades y compromisos se muestran sin persistir transacciones.

## Requisitos

- Python 3.11 o posterior.
- Node.js y npm para compilar los estilos locales.
- SQLite para desarrollo local. MySQL se configura mediante variables de entorno para despliegue.

## Ejecución local

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm ci
npm run build:css
python manage.py migrate
python manage.py load_demo_data
python manage.py createsuperuser
python manage.py runserver
```

La aplicación queda disponible en `http://127.0.0.1:8000/`. El comando `load_demo_data` crea registros ficticios repetibles y no establece contraseñas de acceso. Los estilos se compilan localmente; Node no se necesita al ejecutar Django.

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

## Proyecto original

- Prototipo estático: [GitHub Pages](https://tatan-0.github.io/proyecto1muni/)
- Repositorio: [proyecto1muni](https://github.com/tatan-0/proyecto1muni)

# Despliegue — SGR Municipalidad de La Serena

**Estado:** configuración preparada; no hay entorno Elastic Beanstalk, base RDS, certificado ni URL de producción creados. La aplicación necesita un servicio Django: GitHub Pages solo sirve el prototipo estático.

## Arquitectura de destino

- AWS Elastic Beanstalk con plataforma Python para ejecutar Django y Gunicorn.
- Amazon RDS MySQL separado para persistencia. RDS debe estar en red privada, sin acceso público y con reglas que permitan el puerto 3306 solo desde el grupo de seguridad de la aplicación.
- Balanceador de carga con certificado TLS para exponer HTTPS. Configurar DNS y dominio con el equipo.
- CSS compilado y versionado en `gestion/static/`; Node se usa al desarrollar o actualizar estilos, no durante el runtime Django.

La documentación oficial explica [Django sobre Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html), [RDS separado para aplicaciones Python](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-rds.html) y [HTTPS en Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/configuring-https.html).

## Preparación local

Desde la raíz de `proyecto_integrado/`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm ci
npm run build:css
python manage.py migrate
python manage.py load_demo_data
python manage.py createsuperuser
python manage.py check
python manage.py test -v 2
```

El cargador añade seis delegaciones ficticias, cargos, perfiles, indicadores, servicios y grupos; no crea contraseñas de acceso. No usar estos registros como datos municipales reales.

## Configuración de producción

Configurar estas variables en el entorno de Elastic Beanstalk. No poner valores reales en `.env.example`, archivos committeados, capturas o comandos compartidos.

| Variable | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta generada para el ambiente. Mantenerla privada. |
| `DJANGO_DEBUG` | Debe ser `False`. |
| `DJANGO_ALLOWED_HOSTS` | Lista separada por comas con dominio y nombres DNS autorizados. |
| `DB_ENGINE` | `mysql`. |
| `DB_NAME` | Base creada en RDS. |
| `DB_USER` / `DB_PASSWORD` | Usuario de aplicación y secreto almacenado en configuración segura del entorno. |
| `DB_HOST` | Endpoint privado de RDS. |
| `DB_PORT` | Normalmente `3306`, salvo que la instancia use otro puerto. |

La app falla al iniciar en modo producción si no se definen `DJANGO_SECRET_KEY` o `DJANGO_ALLOWED_HOSTS`. Django aplica redirección HTTPS y cookies seguras con `DEBUG=False`. El certificado TLS debe estar asociado al balanceador antes de abrir acceso público.

## Procedimiento de lanzamiento propuesto

1. El equipo confirma cuenta AWS, región, presupuesto, dominio, responsables y permisos IAM.
2. Crear o validar red/VPC, subredes y grupos de seguridad. Mantener RDS privado y restringir 3306 al grupo de aplicación.
3. Crear la base MySQL y guardar las variables de conexión en la configuración segura del entorno Elastic Beanstalk.
4. Verificar la rama y versión a publicar. Ejecutar tests, `check`, `check --deploy` y compilar CSS localmente.
5. Crear el entorno Elastic Beanstalk y cargar el paquete de aplicación. Confirmar el proceso WSGI `config.wsgi:application` y que los estáticos se sirvan correctamente.
6. Antes de migrar, confirmar que el endpoint y credenciales apuntan al ambiente esperado, revisar backup y aprobar la ventana de cambio. Ejecutar `python manage.py migrate` una vez desde el mecanismo administrativo seguro del entorno.
7. Crear una cuenta administradora de forma controlada; cargar datos de ejemplo solo en ambientes de demostración.
8. Configurar HTTPS en el balanceador, DNS y hosts permitidos. Confirmar que las peticiones HTTP se redirigen a HTTPS.
9. Usar `/login/` como ruta de salud HTTP 200 para comprobar que la app responde sin requerir sesión. Este chequeo no prueba conectividad completa con RDS; validar también la aplicación y sus datos tras las migraciones.
10. Probar login, alcance de roles, listados y CRUD con datos ficticios. No ingresar registros reales hasta que seguridad, privacidad y operación hayan sido revisadas por el municipio y el equipo del curso.

No correr migraciones automáticas por instancia durante un despliegue con varias instancias. Aplicarlas una vez, de manera controlada y compatible con la versión que se libera.

## Verificaciones y advertencias

Para comprobar settings de producción localmente sin usar una clave ni base reales, PowerShell permite ejecutar:

```powershell
$env:DJANGO_DEBUG = 'False'
$env:DJANGO_SECRET_KEY = 'clave-temporal-de-prueba-no-usar-en-produccion-abc123XYZ987'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
$env:DB_ENGINE = 'sqlite'
python manage.py check --deploy
Remove-Item Env:\DJANGO_DEBUG, Env:\DJANGO_SECRET_KEY, Env:\DJANGO_ALLOWED_HOSTS, Env:\DB_ENGINE
```

La clave del ejemplo es solo de prueba y no debe copiarse a AWS. `python manage.py check --deploy` debe ejecutarse con `DJANGO_DEBUG=False`, una clave de prueba larga y `DJANGO_ALLOWED_HOSTS` no vacío.
- En la comprobación local registrada aparece el aviso `security.W021`: HSTS preload no está habilitado. Permanece pendiente hasta confirmar dominio propio, HTTPS funcional y que todos los subdominios admiten HTTPS; no habilitarlo por defecto para un dominio de prueba.
- Ajustar la configuración del proxy para que Django reconozca HTTPS cuando TLS termina en el balanceador. No marcar conexiones como seguras antes de configurar el encabezado confiable del proxy y el balanceador.
- El health check `/login/` confirma que Django puede responder; la prueba de base de datos debe realizarse tras ejecutar migraciones y consultar la aplicación con una cuenta de prueba.
- No se crearon recursos AWS ni se generaron capturas/URL de producción en este trabajo. Esos elementos quedan pendientes de autorización del equipo y se completarán solo después de desplegar.

## Evidencia para la entrega

- [ ] Versión y plataforma Python de Elastic Beanstalk.
- [ ] Variables de entorno visibles con los valores secretos ocultos.
- [ ] Estado saludable del entorno y respuesta HTTP 200 en `/login/`.
- [ ] URL HTTPS con certificado válido y redirección desde HTTP.
- [ ] RDS accesible desde la app y sin endpoint público abierto.
- [ ] Salida de `python manage.py migrate` y comprobación funcional posterior.
- [ ] Login y vistas según administrador, delegado y funcionario.
- [ ] CRUD de las cinco tablas maestras y validación de errores.
- [ ] Suite de pruebas y plan ejecutado en `docs/plan-pruebas-unitarias.md`.
- [ ] Captura del panel de configuración sin mostrar claves, contraseñas o datos personales.

**Pendiente:** cuenta, región, presupuesto, dominio, ejecución de AWS y capturas de evidencia requieren acuerdo explícito del equipo.

# Seguridad y estándares de desarrollo

**Alcance:** controles implementados en la aplicación académica SGR. Esta guía no representa una certificación ni una auditoría externa. No hay despliegue productivo en AWS ni datos personales reales en el repositorio.

## Perfiles y límites de acceso

| Perfil | Acceso implementado |
|---|---|
| Anónimo | Puede consultar el formulario de inicio de sesión. Las vistas SGR protegidas redirigen a inicio de sesión. |
| Administrador | Superusuario Django o miembro de `ADMINISTRADOR`; puede consultar personal y mantener los cinco catálogos. |
| Delegado | Miembro de `DELEGADO` con perfil SGR; consulta las fichas de su propia delegación. |
| Funcionario | Miembro de `FUNCIONARIO` con perfil SGR; consulta su propia ficha y las vistas demostrativas. |

La autorización se aplica en las vistas del servidor. Ocultar enlaces en templates solo mejora la navegación y nunca concede permisos. Los CRUD requieren administrador y las consultas usan `funcionarios_visibles()` para limitar resultados. Se evita consultar el perfil mediante un ID recibido en la URL si ese registro no pertenece al alcance del usuario.

## Reglas de desarrollo seguro aplicadas

- **Validación en servidor:** los formularios usan `ModelForm`; los modelos aplican unicidad, relaciones obligatorias, ponderadores entre 0 y 100 y metas positivas. Las restricciones críticas también están en la base de datos.
- **CSRF:** `CsrfViewMiddleware` permanece activo y los formularios POST incluyen token. La suite prueba que un POST CRUD sin token se rechaza.
- **Lecturas y escrituras diferenciadas:** las páginas de agenda, ficha, semáforo, resumen y dashboard aceptan GET. Las actividades y compromisos son datos ficticios; un POST devuelve 405 y no guarda transacciones.
- **Consultas y salida:** se usan ORM de Django y templates con escape automático. No se construyen sentencias SQL concatenando entradas ni se insertan datos de usuarios con `safe`.
- **Integridad histórica:** las bajas de catálogos son lógicas (`activo=False`). Las relaciones protegidas usan `on_delete=PROTECT`; desactivar no elimina funcionarios ni indicadores relacionados.
- **Contraseñas:** la autenticación delega en Django. El cargador de datos crea cuentas de demostración con contraseña no utilizable y no incluye credenciales de acceso.
- **Datos:** los registros de muestra son ficticios. No cargar RUT, teléfonos, nombres de vecinos, credenciales reales ni información sensible en capturas o ambientes de prueba.
- **Dependencias:** Python se fija en `requirements.txt`; Tailwind y daisyUI se fijan mediante `package-lock.json`. Node compila CSS durante desarrollo; el servidor sirve el archivo generado.

## Configuración local y producción

En desarrollo, `DJANGO_DEBUG` puede omitirse y la base predeterminada es SQLite. La clave local de respaldo está marcada como no apta para producción.

Con `DJANGO_DEBUG=False`, la aplicación no inicia si faltan `DJANGO_SECRET_KEY` o `DJANGO_ALLOWED_HOSTS`. Producción debe además configurar `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`; los secretos se proporcionan en el entorno del servicio y no se guardan en el repositorio ni en capturas.

Con `DEBUG=False` quedan activados `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, HSTS por un año y `SECURE_HSTS_INCLUDE_SUBDOMAINS`. `X_FRAME_OPTIONS` es `DENY` y `SECURE_CONTENT_TYPE_NOSNIFF` está activo. HSTS preload permanece desactivado hasta confirmar dominio propio, HTTPS y subdominios; `check --deploy` informa `security.W021` mientras siga pendiente.

Antes de publicar una versión se debe revisar:

1. `python manage.py test -v 2`.
2. `python manage.py check`.
3. `python manage.py check --deploy` con configuración de producción de prueba y sin secretos reales en la terminal compartida.
4. Migraciones revisadas y aplicadas en la base correspondiente.
5. HTTPS, grupos de seguridad y variables secretas configurados por el equipo responsable de AWS.

## Limitaciones conocidas

- La aplicación no está desplegada; GitHub Pages solo conserva el prototipo estático y no ejecuta Django.
- No se ha realizado prueba de penetración, auditoría externa ni verificación visual en navegador dentro de este entorno.
- AWS, su certificado TLS, cuenta, región, base RDS y dominio quedan pendientes de decisión y autorización del equipo.

## Referencias

- [Seguridad de Django 5.2](https://docs.djangoproject.com/en/5.2/topics/security/)
- [Despliegue de Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

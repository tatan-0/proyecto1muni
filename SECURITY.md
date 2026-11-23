# Seguridad y estándares de desarrollo

**Alcance:** controles implementados en la aplicación académica SGR. Esta guía no representa una certificación ni una auditoría externa. No hay despliegue productivo en AWS ni datos personales reales en el repositorio.

## Perfiles y límites de acceso

| Perfil | Acceso implementado |
|---|---|
| Anónimo | Puede consultar el formulario de inicio de sesión. Las vistas SGR protegidas redirigen a inicio de sesión. |
| Administrador | Superusuario Django o miembro de `ADMINISTRADOR`; puede consultar personal y mantener los seis catálogos implementados. |
| Delegado | Miembro de `DELEGADO` con perfil SGR; consulta las fichas de su delegación y puede ingresar ausencias para su equipo. |
| Funcionario | Miembro de `FUNCIONARIO` con perfil SGR; consulta su propia ficha y registra sus gestiones. |

La autorización se aplica en las vistas del servidor. Ocultar enlaces en templates solo mejora la navegación y nunca concede permisos. Los CRUD de catálogos requieren administrador y las consultas de funcionarios usan `funcionarios_visibles()` para limitar resultados. Se evita consultar el perfil mediante un ID recibido en la URL si ese registro no pertenece al alcance del usuario. Aún no existe un flujo de aprobación o edición de gestiones por estado.

## Reglas de desarrollo seguro aplicadas

- **Validación en servidor:** los formularios usan `ModelForm`; los modelos aplican unicidad, relaciones obligatorias, ponderadores entre 0 y 100 y metas positivas. Las restricciones de campo principales también están en la base de datos; las reglas que dependen de varias filas, como cruces de ausencias, se validan en la aplicación.
- **CSRF:** `CsrfViewMiddleware` permanece activo y los formularios POST incluyen token. La suite prueba que un POST CRUD sin token se rechaza.
- **Lecturas y escrituras diferenciadas:** ficha, agenda, resumen y dashboard son de solo lectura; el formulario de gestión persiste registros y el semáforo permite al delegado ingresar ausencias para su delegación. El Tubo de compromisos no tiene persistencia ni flujo de edición.
- **Health check:** `/health/` expone solo `ok`, no requiere sesión, acepta únicamente GET y no consulta la base de datos. Queda exenta de la redirección HTTPS para que el balanceador compruebe el proceso por HTTP.
- **Consultas y salida:** se usan ORM de Django y templates con escape automático. No se construyen sentencias SQL concatenando entradas ni se insertan datos de usuarios con `safe`.
- **Integridad histórica:** las bajas de catálogos son lógicas (`activo=False`). Las relaciones protegidas usan `on_delete=PROTECT`; desactivar no elimina funcionarios ni indicadores relacionados.
- **Contraseñas:** la autenticación y validación de contraseñas delegan en Django. El cargador de datos crea cuentas de demostración con contraseña no utilizable y no incluye credenciales de acceso. La interfaz SGR todavía no implementa entrega de contraseña temporal, cambio obligatorio en el primer ingreso ni recuperación por correo.
- **Evidencias:** todavía no hay carga ni control de acceso a evidencias asociadas a gestiones. No se deben cargar archivos reales ni información personal.
- **Datos:** los registros de muestra son ficticios. No cargar RUT, teléfonos, nombres de vecinos, credenciales reales ni información sensible en capturas o ambientes de prueba.
- **Dependencias:** Python se fija en `requirements.txt`; Tailwind y daisyUI se fijan mediante `package-lock.json`. Node compila CSS durante desarrollo; el servidor sirve el archivo generado.
- **Estáticos en producción:** WhiteNoise sirve archivos recolectados en `STATIC_ROOT` con nombres versionados mediante manifest; no se habilita el servidor estático de desarrollo en producción.

## Configuración local y producción

En desarrollo, `DJANGO_DEBUG` puede omitirse y la base predeterminada es SQLite. La clave local de respaldo está marcada como no apta para producción.

Con `DJANGO_DEBUG=False`, la aplicación no inicia si faltan `DJANGO_SECRET_KEY` o `DJANGO_ALLOWED_HOSTS`. Producción también exige `DB_ENGINE=mysql` y los valores `DB_NAME`, `DB_USER`, `DB_PASSWORD` y `DB_HOST`; `DB_PORT` es opcional y usa `3306` por defecto. No permite caer a SQLite. Los secretos se proporcionan en el entorno del servicio y no se guardan en el repositorio ni en capturas.

Con `DEBUG=False` quedan activados `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, HSTS por un año y `SECURE_HSTS_INCLUDE_SUBDOMAINS`. `X_FRAME_OPTIONS` es `DENY` y `SECURE_CONTENT_TYPE_NOSNIFF` está activo. HSTS preload permanece desactivado hasta confirmar dominio propio, HTTPS y subdominios; `check --deploy` informa `security.W021` mientras siga pendiente.

Detrás del proxy de Elastic Beanstalk, `SECURE_PROXY_SSL_HEADER` reconoce `X-Forwarded-Proto: https`. Esta confianza requiere que el proxy administrado sobrescriba el encabezado y que la aplicación no sea accesible directamente desde Internet; el equipo debe validar ese límite al crear el entorno.

Antes de publicar una versión se debe revisar:

1. `python manage.py test -v 2`.
2. `python manage.py check`.
3. `python manage.py check --deploy` con configuración de producción de prueba y sin secretos reales en la terminal compartida.
4. Migraciones revisadas y aplicadas en la base correspondiente.
5. HTTPS, grupos de seguridad y variables secretas configurados por el equipo responsable de AWS.

## Limitaciones conocidas

- La aplicación no está desplegada. Para ejecutarla, sigue el inicio rápido del README; no compartas la base local ni credenciales.
- No están implementados el flujo de revisión de gestiones, la aprobación que condicione el puntaje, la inmutabilidad tras aprobación, las evidencias, las metas por funcionario/trimestre ni la recuperación de contraseña.
- No se ha realizado prueba de penetración ni auditoría externa. Las pruebas automatizadas no sustituyen el protocolo funcional completo exigido por la evaluación.
- AWS, su certificado TLS, cuenta, región, base RDS y dominio quedan pendientes de decisión y autorización del equipo.

## Referencias

- [Seguridad de Django 5.2](https://docs.djangoproject.com/en/5.2/topics/security/)
- [Despliegue de Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

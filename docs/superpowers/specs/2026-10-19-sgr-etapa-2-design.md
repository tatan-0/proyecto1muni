# Diseño de mejora del SGR La Serena

**Estado:** propuesto para revisión del equipo
**Fecha:** 19 de octubre de 2026
**Base aprobada:** esqueleto Django local en `proyecto_integrado/`

## Propósito

Convertir la interfaz SGR existente en una aplicación web estructurada que pueda demostrar las vistas requeridas para la gestión de delegaciones y los CRUD persistentes de sus tablas maestras. El alcance corresponde a la etapa 2 descrita en la evaluación del curso: la interfaz debe representar los módulos del sistema, mientras que las operaciones CRUD persistentes se concentran en datos maestros; las transacciones de actividades y compromisos quedan fuera de esta etapa.

La página publicada en GitHub Pages es actualmente una versión estática. La aplicación Django se ejecutará como aplicación de servidor; GitHub Pages no ejecuta ese backend. El diseño conserva el flujo y propósito SGR visibles en la página publicada y usa el proyecto Node del ZIP como referencia de seguridad y presentación, sin mezclar sus pantallas SIGED con el SGR.

## Objetivos y criterios de aceptación

1. Entregar vistas integradas y navegables para el resumen de delegación, ficha y gestión por funcionario, tubo de compromisos, semáforo diario, resumen de actividad y administración de tablas maestras.
2. Implementar altas, consultas, modificaciones y bajas de delegaciones, cargos, funcionarios, indicadores/funciones y servicios.
3. Validar los datos en servidor, mantener relaciones válidas entre los catálogos y mostrar mensajes claros ante errores o acciones completadas.
4. Restringir edición de catálogos al perfil administrador. El delegado podrá consultar datos de su delegación y cada funcionario su propia ficha; las pantallas transaccionales serán demostrativas durante esta etapa.
5. Ejecutar pruebas unitarias para validaciones, operaciones CRUD y autorización; documentar casos, responsables y resultados.
6. Entregar diagramas de componentes/paquetes y despliegue coherentes con el código, con una explicación de cómo cubren las vistas 4+1 requeridas.
7. Preparar instrucciones y configuración para despliegue en AWS, junto a una lista de evidencias para configuración y funcionamiento. La creación de recursos AWS se realizará cuando el equipo cuente con cuenta y autorice el despliegue.
8. Mantener datos de demostración explícitamente identificados y ficticios; no incluir RUT, teléfonos ni datos personales reales.

## Alcance funcional

### Templates de la aplicación

- **Inicio y resumen:** selector/contexto de delegación, cifras de demostración y acceso a los módulos.
- **Ficha del funcionario:** metas, ponderadores, avance y registro demostrativo de actividades.
- **Tubo de compromisos:** agenda y estados de ejemplo, sin escritura transaccional persistente.
- **Semáforo diario:** comparación ilustrativa entre avance observado y avance esperado.
- **Resumen de delegación:** actividad agregada y últimos ingresos de ejemplo.
- **Tablas maestras:** listados y formularios de administración de catálogos con acciones CRUD y confirmación de baja.

Las actividades y compromisos no se guardarán ni alterarán como transacciones en esta etapa. Los elementos que parezcan interactivos en esas vistas deberán mostrarse como demostración o estar deshabilitados con una explicación visible, para no sugerir que los datos se persistieron.

### Tablas maestras

| Entidad | Datos principales | Relaciones y validaciones |
| --- | --- | --- |
| Delegación | nombre, descripción territorial, estado | nombre obligatorio y único |
| Cargo | nombre, área, estado | nombre obligatorio y único |
| Funcionario | usuario Django, nombre visible, cargo, delegación, estado | usuario asociado; cargo y delegación existentes |
| Indicador/función | nombre, cargo, ponderador, meta trimestral, unidad de medida, estado | cargo existente; ponderador entre 0 y 100; meta positiva |
| Servicio | nombre, descripción, estado | nombre obligatorio y único |

La baja de un registro relacionado será una baja lógica (`activo = False`) para conservar la integridad referencial. Los listados permitirán consultar registros activos e inactivos. No se aceptarán nombres vacíos, ponderadores fuera de rango ni metas negativas o nulas. Las vistas indicarán cuando la suma de ponderadores de un cargo no alcance 100%, sin impedir el mantenimiento progresivo del catálogo.

## Perfiles y permisos

- **Administrador:** administra todas las tablas maestras y consulta todos los módulos.
- **Delegado/coordinador:** consulta información de su delegación y las fichas de su equipo.
- **Funcionario:** consulta su ficha y las vistas demostrativas habilitadas para su perfil.

La autorización se valida en las vistas del servidor. Ocultar enlaces en el HTML no reemplaza los controles de permisos. Se utilizarán usuarios y grupos de Django; no habrá cuentas ni contraseñas predefinidas en el repositorio. Para demostraciones se crearán cuentas locales mediante el flujo administrativo de Django.

## Arquitectura y persistencia

- Aplicación monolítica Django con templates del servidor, formularios Django, modelos, vistas, migraciones y pruebas dentro de una app `gestion`.
- HTML, CSS y JavaScript del SGR se trasladarán a templates y archivos estáticos de Django. El diseño mantendrá identidad municipal, legibilidad, navegación por teclado y adaptación a móvil/escritorio.
- SQLite se usará para desarrollo local. La configuración de producción será externa por variables de entorno y apuntará a una base relacional MySQL administrada en AWS RDS.
- Los datos de ejemplo se cargarán mediante una fixture o comando de administración repetible y claramente marcado como ficticio.
- El dominio transaccional (actividades, evidencias y compromisos reales) se documentará como fuera de alcance para esta etapa; no se simulará persistencia de esas transacciones en la base.

## Seguridad y manejo de errores

- Autenticación y autorización con los mecanismos integrados de Django.
- Validación en servidor para todas las escrituras; validación del navegador solo como ayuda de uso.
- Protección CSRF en formularios; consultas y renderizado con APIs de Django para reducir riesgos de inyección y XSS.
- Secretos y credenciales fuera del repositorio; `DEBUG=False`, `ALLOWED_HOSTS` explícito, cookies seguras y redirección HTTPS en producción.
- Mensajes de error comprensibles sin filtrar trazas ni detalles de configuración.
- La interfaz distinguirá errores de validación, restricciones de permisos y fallos inesperados, conservando los datos del formulario cuando sea posible.

## Pruebas

La suite unitaria verificará al menos:

1. Validación de campos obligatorios, unicidad, ponderadores y metas.
2. Creación, consulta, edición y baja lógica de cada tabla maestra.
3. Integridad de relaciones entre funcionario, delegación, cargo e indicador.
4. Acceso anónimo denegado a vistas protegidas.
5. Administrador autorizado para mantener catálogos; delegado y funcionario sin permiso de escritura.
6. Restricción de consulta del delegado a su delegación y del funcionario a su ficha.
7. Respuesta accesible y estable ante entradas inválidas, registro inexistente o baja de una entidad relacionada.

El plan de pruebas entregable identificará ID, objetivo, precondiciones, datos, pasos, resultado esperado, criterio de aprobación y responsable. Las pruebas se ejecutarán sobre base de datos de prueba de Django, no sobre datos de producción.

## Despliegue y arquitectura 4+1

### Despliegue AWS propuesto

- AWS Elastic Beanstalk para alojar el proceso Django en la plataforma Python.
- Amazon RDS MySQL separado del entorno de aplicación para persistencia.
- Variables de entorno protegidas para configuración, conexión y secretos; HTTPS antes de exponer el acceso.
- La guía de AWS para Django describe Elastic Beanstalk y recomienda RDS separado para producción; la documentación también indica HTTPS para transmitir información de acceso.
- Se prepararán instrucciones repetibles de despliegue, chequeo de salud, migraciones, creación del usuario administrador y evidencias requeridas. La cuenta, región y recursos reales se decidirán con el equipo antes de crear infraestructura facturable.

### Vistas 4+1

- **Escenarios (+1):** casos de uso de iniciar sesión, consultar gestión de una delegación y mantener un catálogo.
- **Lógica:** modelos y relaciones de delegación, cargo, funcionario, indicador y servicio.
- **Desarrollo:** paquetes de configuración, modelos, formularios, vistas, templates, estáticos y pruebas de Django.
- **Procesos:** flujo de autenticación/autorización y flujo de validación y persistencia de CRUD.
- **Física:** navegador → aplicación Django en Elastic Beanstalk → base MySQL en RDS, con HTTPS hacia la aplicación y conexión privada entre aplicación y base.

Se entregarán como mínimo los diagramas de componentes/paquetes y despliegue solicitados en la pauta; el resto de vistas se explicará de manera breve para mostrar su correspondencia con esos diagramas y con el código.

## Fuera de alcance

- CRUD transaccional para actividades, fotografías/evidencias o compromisos.
- Integración con Google Drive, WhatsApp, MySQL local del usuario u otros servicios no incluidos en el proyecto aprobado.
- Cargar datos reales de funcionarios o vecinos.
- Crear infraestructura AWS facturable sin acuerdo específico del equipo.
- Publicar cambios en el repositorio o dominio del grupo: el directorio entregado no contiene metadatos Git ni se confirmó acceso de escritura al repositorio remoto.

## Supuestos y riesgos

- `proyecto_integrado/` es la base local autorizada; la página de GitHub Pages sirve como referencia visual/funcional.
- El ZIP `proyecto-la-serena-main.zip` pertenece a una variante SIGED y sirve solo de referencia técnica.
- Los roles, cargos, metas y servicios de producción deberán confirmarse con el equipo; el prototipo usará registros ficticios basados en la estructura funcional descrita en la presentación.
- GitHub Pages no podrá servir el backend Django; para acceso remoto de la aplicación se necesitará un entorno de aplicación, por ejemplo Elastic Beanstalk.
- El despliegue en AWS y las capturas de evidencia dependen de una cuenta del equipo y pueden incurrir en costos.

## Fuentes de requisitos

- `II Evaluaci__n Proyecto Integrado.docx` y la matriz `Hoja de cálculo en C  Users chevi Downloads II Evaluaci__n Proyecto Integrado.xlsx`: templates, CRUD de tablas maestras, validaciones, pruebas unitarias, AWS, 4+1 y estándares.
- `PRESENTACI__N  MATRIZ  REGIMIENTO RESULTADO.pptx`: funciones de las vistas del SGR, tipos de cargos, indicadores, agenda colectiva, semáforo y resumen.
- `Contexto_Institucional_Municipalidad_La_Serena_2026.pdf`: territorio, seis delegaciones y rol de cercanía/coordinación municipal.
- Documentación oficial de AWS: [Django en Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html), [RDS con aplicaciones Python](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-rds.html) y [HTTPS en Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/configuring-https.html).

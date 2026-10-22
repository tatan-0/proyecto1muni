# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Funcionarios municipales y equipos de las delegaciones de La Serena que consultan el seguimiento de resultados territoriales y mantienen los catálogos del sistema.

## Product Purpose

El Sistema de Gestión de Resultados (SGR) reúne la consulta del seguimiento territorial de las delegaciones y la administración de los catálogos que organizan esa información. El éxito consiste en que sus usuarios puedan entender el estado de los resultados y mantener esos datos de referencia desde una interfaz municipal clara.

## Operating Context

- Aplicación académica construida para la Municipalidad de La Serena.
- Las vistas principales incluyen dashboard, ficha de funcionario, agenda/tubo, semáforo y resumen.
- El usuario del proyecto tiene a cargo Diseño y Experiencia de Usuario (UX/UI), prototipos funcionales, consistencia visual, adaptación responsive e integración de retroalimentación. La seguridad técnica está fuera de su responsabilidad asignada.

## Capabilities and Constraints

- Django sirve la aplicación web y persiste los catálogos maestros en una base de datos. El desarrollo local usa SQLite; el proyecto documenta MySQL para despliegue.
- Los catálogos incluyen delegaciones, cargos, funcionarios, indicadores/funciones y servicios.
- Los registros de demostración son ficticios.
- En el alcance actual, actividades y compromisos se muestran sin persistir transacciones; la interfaz debe comunicar esa limitación con precisión.
- No se confirmó un diferenciador de mercado ni se deben inventar afirmaciones de impacto o resultados institucionales.

## Brand Commitments

- Usar el nombre institucional Municipalidad de La Serena y el nombre SGR.
- Conservar la identidad cromática de la interfaz municipal existente. El usuario pidió evitar una presentación excesivamente minimalista y mantener sus colores.
- Mantener el contenido y los datos de demostración claramente identificados como ficticios.

## Evidence on Hand

- `README.md`: propósito, capacidades, alcance de demostración y stack.
- `gestion/models.py`: estructura persistente de delegaciones, cargos, funcionarios, indicadores y servicios.
- `gestion/urls.py` y `gestion/templates/gestion/`: vistas y terminología actualmente implementadas.
- `db.sqlite3`: base local de desarrollo; no constituye evidencia de datos municipales reales.

## Product Principles

- Mostrar con claridad qué información está guardada y qué partes aún son demostrativas.
- Organizar el seguimiento según delegaciones y responsabilidades municipales.
- Permitir mantener los catálogos de referencia desde el sistema.
- Mantener una experiencia visual institucional, coherente y adaptable a distintos tamaños de pantalla.

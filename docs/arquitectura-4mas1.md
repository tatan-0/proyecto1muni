# Arquitectura 4+1 — SGR La Serena

## Escenarios (+1)

1. **Administrar catálogos:** una persona administradora inicia sesión, crea o modifica delegaciones, cargos, funcionarios, indicadores y servicios, y desactiva registros conservando sus relaciones.
2. **Consultar una delegación:** el delegado revisa el dashboard y las fichas del equipo asignado a su delegación.
3. **Consultar la ficha propia:** el funcionario ve su ficha y las pantallas de ejemplo; cambiar el ID de una URL no amplía su alcance.
4. **Revisar indicadores y compromisos:** los perfiles autorizados consultan semáforo, agenda y resumen. Sus valores están marcados como demostración y no admiten escritura transaccional.

## Vista lógica

La app `gestion` contiene cinco modelos maestros persistentes. `Funcionario` enlaza un usuario Django con un cargo y una delegación; `Indicador` pertenece a un cargo; `Servicio` mantiene su descripción y estado. `Cargo`, `Delegacion` e `Indicador` son protegidos frente a borrado físico cuando hay referencias. La baja se expresa mediante `activo=False`.

```mermaid
erDiagram
    DELEGACION ||--o{ FUNCIONARIO : asigna
    CARGO ||--o{ FUNCIONARIO : organiza
    CARGO ||--o{ INDICADOR : define
    DJANGO_USER ||--o| FUNCIONARIO : autentica
    DELEGACION {
        string nombre UK
        text descripcion_territorial
        boolean activo
    }
    CARGO {
        string nombre UK
        string area
        boolean activo
    }
    FUNCIONARIO {
        string nombre
        boolean activo
    }
    INDICADOR {
        string nombre
        decimal ponderador
        integer meta_trimestral
        string unidad_medida
        boolean activo
    }
    SERVICIO {
        string nombre UK
        text descripcion
        boolean activo
    }
```

`SERVICIO` no se conecta con las demás entidades en el modelo actual. `DJANGO_USER` es el usuario configurado por Django; no es una tabla propia de la app.

## Vista de desarrollo: componentes y paquetes

```mermaid
flowchart LR
    Browser[ Navegador ] --> Root[config.urls]
    Root --> Auth[gestion.views.auth]
    Root --> ReadViews[gestion.views.dashboard]
    Root --> CRUDRoutes[gestion.maestros_urls]
    CRUDRoutes --> CRUD[gestion.views.maestros]
    CRUD --> Forms[gestion.forms]
    CRUD --> Permissions[gestion.permissions]
    ReadViews --> Permissions
    Permissions --> Models[gestion.models]
    Forms --> Models
    Auth --> Templates[Templates Django]
    ReadViews --> Templates
    CRUD --> Templates
    Templates --> Static[CSS Tailwind + daisyUI / JavaScript]
    Models --> DB[(SQLite local / MySQL producción)]
    Admin --> Models
    Tests[gestion.tests] -. verifica .-> Auth
    Tests -. verifica .-> ReadViews
    Tests -. verifica .-> CRUD
    Tests -. verifica .-> Models
```

Paquetes presentes: `config` para settings, URL raíz y WSGI; `gestion.models`, `forms`, `permissions`, `views`, `templates`, `static`, `management.commands` y `tests`; `pagina_muni/css/input.css` y `package.json` para compilar la hoja de estilos. Las rutas `maestros:*` se montan desde `config.urls`; las rutas de operación usan `gestion:*`.

## Vista de procesos

### Acceso

```mermaid
sequenceDiagram
    actor Persona
    participant Django as Django auth y rutas
    participant Permisos as gestion.permissions
    participant Modelo as Funcionario
    Persona->>Django: POST /login/ con CSRF
    Django-->>Persona: Sesión autenticada
    Persona->>Django: GET a una vista SGR
    Django->>Permisos: validar grupo y perfil
    Permisos->>Modelo: consultar solo filas visibles
    Modelo-->>Django: QuerySet acotado
    Django-->>Persona: template renderizado
```

### Mantención de catálogo

```mermaid
sequenceDiagram
    actor Admin as Administrador
    participant Vista as CRUD Django
    participant Form as ModelForm
    participant DB as Base de datos
    Admin->>Vista: POST con token CSRF
    Vista->>Vista: verificar login y grupo ADMINISTRADOR
    Vista->>Form: validar campos y relaciones
    alt datos válidos
        Form->>DB: insertar o actualizar
        DB-->>Vista: registro guardado
        Vista-->>Admin: mensaje y redirección al listado
    else datos inválidos
        Form-->>Vista: errores por campo
        Vista-->>Admin: formulario con datos y errores
    end
```

Las rutas demostrativas solo admiten GET; las escrituras de actividades y compromisos quedan fuera de esta etapa.

## Vista física: despliegue

```mermaid
flowchart LR
    Browser[Navegador] -->|HTTPS| ALB[Balanceador / certificado TLS]
    ALB --> EB[Elastic Beanstalk · plataforma Python]
    EB --> Gunicorn[Gunicorn · config.wsgi:application]
    Gunicorn --> Django[Django · templates y seguridad]
    Django --> Static[CSS estático compilado]
    Django -->|TCP 3306 · red privada| RDS[(Amazon RDS MySQL)]
    Dev[Desarrollo local] --> SQLite[(SQLite)]
```

El diagrama representa el destino propuesto, no infraestructura existente. El acceso público queda en el balanceador con HTTPS. RDS debe permanecer sin acceso público y permitir conexión desde el grupo de seguridad de la aplicación. GitHub Pages conserva el sitio estático actual; no forma parte del camino de ejecución de Django.

## Resumen de las cinco vistas

| Vista | Contenido en este proyecto |
|---|---|
| Escenarios (+1) | Flujos de administrador, delegado y funcionario descritos arriba. |
| Lógica | Relaciones y restricciones entre usuario, funcionario, cargo, delegación, indicador y servicio. |
| Desarrollo | Paquetes Django, templates, static, build de CSS, migraciones y pruebas. |
| Procesos | Autenticación y autorización; validación, persistencia y baja lógica; páginas GET demostrativas. |
| Física | Navegador → Elastic Beanstalk/Django → RDS MySQL; SQLite para desarrollo local. |

El diagrama de componentes/paquetes describe los módulos de código; el diagrama de despliegue describe los nodos de ejecución solicitados por la pauta.

# Magnus|SIG — Sistema Web de Gestión de la Batería de Riesgo Psicosocial

## 1. Nombre y descripción del proyecto

**Magnus|SIG** es una aplicación web para apoyar la gestión y aplicación de la Batería de Instrumentos para la Evaluación de Factores de Riesgo Psicosocial. La plataforma permite administrar organizaciones y usuarios, gestionar cuestionarios y evaluaciones, consultar resultados, generar informes y realizar seguimiento a diferentes procesos relacionados con la evaluación del riesgo psicosocial.

El sistema cuenta con una arquitectura cliente-servidor compuesta por un Frontend desarrollado con React y un Backend desarrollado con Python y FastAPI. La información se almacena en PostgreSQL y la comunicación entre ambas partes se realiza mediante una API REST.

Entre sus capacidades se encuentran la gestión de organizaciones, usuarios y roles; la aplicación de instrumentos de evaluación; la consulta de resultados e informes; el registro de auditoría; las notificaciones y recordatorios; y la administración de planes, productos, compras y pagos.

> **Nota:** las funcionalidades disponibles para cada usuario dependen de su rol, de las restricciones de acceso implementadas y de la organización activa.

---

## 2. Tecnologías utilizadas

El sistema utiliza las siguientes tecnologías y herramientas:

### 2.1. Frontend

| Tecnología | Uso |
|---|---|
| React 18 | Construcción de la interfaz de usuario mediante componentes. |
| JavaScript | Lenguaje utilizado para desarrollar la aplicación. |
| React DOM | Renderizado de la aplicación React en el navegador. |
| React Router DOM | Administración de rutas y navegación entre vistas. |
| Vite | Servidor de desarrollo y herramienta de compilación. |
| React Icons | Uso de iconos en la interfaz. |
| qrcode.react | Generación de códigos QR. |
| CSS | Estilos y presentación visual de la aplicación. |

### 2.2. Backend

| Tecnología | Uso |
|---|---|
| Python | Lenguaje de programación del servidor. |
| FastAPI | Desarrollo de la API REST. |
| Uvicorn | Servidor ASGI para ejecutar la aplicación. |
| SQLAlchemy | Mapeo objeto-relacional y acceso a la base de datos. |
| Pydantic y pydantic-settings | Validación de datos y configuración mediante variables de entorno. |
| Alembic | Administración de migraciones de la base de datos. |
| python-jose | Manejo de tokens JWT. |
| Passlib y bcrypt | Hash y verificación de contraseñas. |
| cryptography | Funciones criptográficas y cifrado de información. |
| APScheduler | Programación de tareas automáticas. |
| scikit-learn, NumPy y SciPy | Herramientas para procesamiento y análisis de datos. |
| ReportLab y pypdf | Generación y procesamiento de documentos PDF. |
| openpyxl | Generación y manipulación de archivos Excel. |
| python-multipart | Procesamiento de formularios y archivos enviados al servidor. |

### 2.3. Base de datos y servicios complementarios

- **PostgreSQL:** sistema de gestión de base de datos relacional.
- **Wompi:** integración para el procesamiento de pagos.
- **SMTP / Brevo:** servicios para el envío de correos electrónicos, de acuerdo con la configuración del entorno.
- **Git:** control de versiones del código fuente.
- **Node.js y npm:** entorno y administrador de paquetes necesarios para el Frontend.

---

## 3. Requisitos previos para ejecutar el sistema

Antes de instalar y ejecutar Magnus|SIG, se recomienda disponer de los siguientes programas y herramientas:

| Requisito | Descripción |
|---|---|
| Sistema operativo | Windows, Linux o macOS. |
| Python | Versión compatible con las dependencias del proyecto. Se recomienda Python 3.11 o superior. |
| Node.js | Versión compatible con Vite 8; se recomienda Node.js 20.19+ o 22.12+. |
| npm | Administrador de paquetes incluido con Node.js. |
| PostgreSQL | Motor de base de datos relacional. |
| Git | Herramienta para clonar y administrar el repositorio. |
| Editor de código | Se recomienda Visual Studio Code. |
| Navegador web | Google Chrome, Microsoft Edge o Mozilla Firefox. |

También se requiere:

- Conexión a Internet para descargar e instalar dependencias.
- Credenciales de acceso a PostgreSQL.
- Permisos para crear y administrar la base de datos.
- Configuración de las variables de entorno del Backend y del Frontend.
- Credenciales de los servicios externos que se vayan a utilizar, como Wompi y el servicio de correo electrónico.

Las versiones indicadas son recomendaciones de instalación. Se debe respetar la compatibilidad de las dependencias definidas en los archivos `backend/requirements.txt` y `frontend/package.json`.

---

## 4. Estructura de carpetas del proyecto

El repositorio está dividido principalmente en dos componentes: `backend` y `frontend`.

```text
BateriaPsicosocial/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── templates/
│   │   └── main.py
│   │
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   ├── data/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── styles/
│   │   └── utils/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
└── README.md
```

### 4.1. Directorios del Backend

- `app/api/v1`: contiene los endpoints y las rutas de la API.
- `app/core`: contiene la configuración general, seguridad y agrupaciones de roles.
- `app/db`: contiene la configuración de conexión, sesiones, inicialización y datos base de la base de datos.
- `app/models`: contiene los modelos que representan las entidades almacenadas en la base de datos.
- `app/schemas`: contiene los esquemas de validación y transferencia de datos.
- `app/services`: contiene servicios y lógica de negocio.
- `app/templates`: contiene plantillas utilizadas por la aplicación.
- `alembic/versions`: almacena el historial de migraciones.
- `tests`: contiene las pruebas automatizadas.
- `main.py`: crea y configura la aplicación FastAPI, registra las rutas y configura tareas programadas.

### 4.2. Directorios del Frontend

- `src/api`: funciones de comunicación con el Backend.
- `src/components`: componentes reutilizables de la interfaz.
- `src/context`: contextos para compartir estado e información entre componentes.
- `src/data`: datos y configuraciones utilizados por la interfaz.
- `src/hooks`: hooks reutilizables de React.
- `src/pages`: páginas y vistas principales.
- `src/styles`: hojas de estilos.
- `src/utils`: funciones auxiliares.
- `public`: recursos estáticos.
- `package.json`: dependencias y comandos disponibles del Frontend.

---

## 5. Instalación y configuración del Backend

El Backend contiene la lógica de negocio, los servicios, la autenticación, la gestión de usuarios, el procesamiento de evaluaciones y la comunicación con la base de datos.

### 5.1. Ingresar a la carpeta del Backend

Desde una terminal, ubicarse en la carpeta principal del proyecto y ejecutar:

```bash
cd backend
```

### 5.2. Crear un entorno virtual

```bash
python -m venv venv
```

Activar el entorno virtual en Windows:

```bash
venv\Scripts\activate
```

En Linux o macOS:

```bash
source venv/bin/activate
```

### 5.3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Este comando instala las dependencias definidas en `requirements.txt`.

### 5.4. Configurar las variables de entorno

Crear un archivo llamado `.env` dentro de la carpeta `backend`, tomando como referencia `backend/.env.example`.

Completar las variables necesarias, especialmente la conexión a PostgreSQL, la clave JWT, la clave de cifrado y las credenciales de los servicios que se utilizarán.

### 5.5. Aplicar las migraciones

Con la base de datos creada y la conexión configurada, consultar primero las revisiones principales:

```bash
alembic heads
```

Si el historial tiene una única revisión principal, aplicar las migraciones:

```bash
alembic upgrade head
```

Si existen varias revisiones principales, revisar y resolver la ramificación de Alembic antes de ejecutar la actualización. Consultar el apartado 10.

### 5.6. Inicializar los datos del sistema

El proyecto dispone de un módulo de inicialización de datos. Para ejecutarlo:

```bash
python -m app.db.seed
```

Este módulo crea o actualiza los permisos y roles definidos en el código, prepara datos base de los instrumentos y crea el usuario inicial de Super Administrador si no existe.

El usuario inicial utiliza las variables `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NOMBRE` y `ADMIN_APELLIDO` configuradas en el archivo `.env`.

La inicialización debe ejecutarse después de aplicar las migraciones. No se debe asumir que vuelve a crear o restablece la contraseña de un administrador que ya existe.

### 5.7. Iniciar el servidor Backend

```bash
uvicorn app.main:app --reload
```

Por defecto, el servidor estará disponible en:

```text
http://localhost:8000
```

La documentación interactiva de la API estará disponible en:

```text
http://localhost:8000/docs
```

La documentación alternativa estará disponible en:

```text
http://localhost:8000/redoc
```

---

## 6. Instalación y configuración del Frontend

El Frontend corresponde a la interfaz gráfica mediante la cual los usuarios interactúan con los módulos y funcionalidades de Magnus|SIG.

### 6.1. Abrir una segunda terminal

Mantener el Backend ejecutándose y abrir otra terminal. Desde la carpeta principal del proyecto, ingresar a:

```bash
cd frontend
```

### 6.2. Instalar las dependencias

```bash
npm install
```

Este comando instala las dependencias definidas en `package.json`.

### 6.3. Configurar las variables de entorno

Crear un archivo `.env` dentro de la carpeta `frontend`, tomando como referencia `frontend/.env.example`.

La configuración local incluida como ejemplo es:

```env
VITE_API_URL=http://localhost:8000/api
```

Esta variable establece la dirección base de la API utilizada por el Frontend.

### 6.4. Iniciar el servidor de desarrollo

```bash
npm run dev
```

Vite mostrará en la terminal la dirección local de la aplicación. En la configuración habitual será:

```text
http://localhost:5173
```

### 6.5. Generar la compilación de producción

Para generar los archivos optimizados del Frontend:

```bash
npm run build
```

Los archivos compilados se almacenarán en la carpeta `dist`.

Para probar localmente la compilación:

```bash
npm run preview
```

---

## 7. Configuración de la base de datos

Magnus|SIG utiliza PostgreSQL como sistema de gestión de bases de datos relacional. Allí se almacena la información de usuarios, organizaciones, evaluaciones, cuestionarios, resultados, informes, productos, planes, compras y otros procesos de la plataforma.

### 7.1. Crear la base de datos

Instalar y ejecutar PostgreSQL. Luego, desde pgAdmin o desde la consola de PostgreSQL, crear la base de datos principal:

```sql
CREATE DATABASE magnussing;
```

Para ejecutar pruebas, configurar también una base de datos independiente cuyo nombre incluya la palabra `test`:

```sql
CREATE DATABASE magnussing_test;
```

### 7.2. Configurar la conexión

En el archivo `backend/.env`, definir la variable `DATABASE_URL` con los datos del servidor PostgreSQL:

```env
DATABASE_URL="postgresql://usuario:contrasena@localhost:5432/magnussing"
```

Reemplazar los valores de ejemplo:

- `usuario`: usuario de PostgreSQL.
- `contrasena`: contraseña del usuario.
- `localhost`: dirección del servidor de base de datos.
- `5432`: puerto de PostgreSQL.
- `magnussing`: nombre de la base de datos.

Para la base de datos de pruebas, configurar:

```env
TEST_DATABASE_URL="postgresql://usuario:contrasena@localhost:5432/magnussing_test"
```

El proyecto valida que el nombre de la base de datos de pruebas contenga `test`.

### 7.3. Conexión con el Backend

El Backend utiliza SQLAlchemy para administrar las conexiones y operaciones con PostgreSQL. La configuración de la conexión y las sesiones se encuentra en:

```text
backend/app/db/session.py
```

### 7.4. Administración de la estructura

Alembic administra los cambios de estructura de la base de datos mediante migraciones. Su configuración se encuentra en:

```text
backend/alembic.ini
backend/alembic/
```

Las migraciones deben aplicarse después de configurar la conexión y antes de inicializar los datos del sistema.

> **Importante:** mantener separadas las bases de datos de desarrollo, pruebas y producción. No ejecutar pruebas destructivas sobre una base de datos que contenga información real.

---

## 8. Variables de entorno

Magnus|SIG utiliza variables de entorno para administrar conexiones, parámetros de funcionamiento y credenciales de servicios externos. Los archivos `.env` deben crearse localmente a partir de los archivos de ejemplo.

Archivos de referencia:

```text
backend/.env.example
frontend/.env.example
```

Crear las copias locales:

```text
backend/.env
frontend/.env
```

### 8.1. Variables del Backend

Las siguientes variables están definidas en el archivo de ejemplo y en la configuración del Backend:

| Variable | Descripción |
|---|---|
| `ENV` | Entorno de ejecución, por ejemplo `development` o `production`. |
| `DATABASE_URL` | Cadena de conexión a PostgreSQL. Es obligatoria. |
| `TEST_DATABASE_URL` | Conexión a la base de datos destinada a pruebas. |
| `PORT` | Puerto configurado para el servicio. |
| `FRONTEND_URL` | Dirección del Frontend, utilizada, entre otras cosas, para configurar CORS. |
| `JWT_SECRET` | Clave secreta para firmar tokens JWT. |
| `ENCRYPTION_KEY` | Clave Fernet utilizada para cifrar información. |
| `SMTP_HOST` | Servidor SMTP para el envío de correos. |
| `SMTP_PORT` | Puerto del servidor SMTP. |
| `SMTP_USER` | Usuario del servicio SMTP. |
| `SMTP_PASS` | Contraseña o clave de aplicación SMTP. |
| `SMTP_FROM` | Nombre y dirección del remitente. |
| `BREVO_API_KEY` | Clave de la API de Brevo. Si se configura, la aplicación puede utilizar el envío por API. |
| `ADMIN_EMAIL` | Correo del Super Administrador inicial. |
| `ADMIN_PASSWORD` | Contraseña inicial del Super Administrador. |
| `ADMIN_NOMBRE` | Nombre del Super Administrador inicial. |
| `ADMIN_APELLIDO` | Apellido del Super Administrador inicial. |
| `STORAGE_PATH` | Ruta de almacenamiento configurada para archivos. |
| `MIN_GRUPO_ANONIMATO` | Tamaño mínimo de grupo configurado para proteger el anonimato de resultados. |
| `DOS_PASOS_ACTIVO` | Activa o desactiva la verificación en dos pasos. |
| `WOMPI_API_URL` | Dirección de la API de Wompi. |
| `WOMPI_PUBLIC_KEY` | Clave pública de Wompi. |
| `WOMPI_PRIVATE_KEY` | Clave privada de Wompi. |
| `WOMPI_INTEGRITY_SECRET` | Secreto utilizado para la firma de integridad del checkout. |
| `WOMPI_EVENTS_SECRET` | Secreto utilizado para validar la firma de los eventos o webhook de Wompi. |

La configuración también contempla valores internos con valores predeterminados, como `SOPORTE_EMAIL`, `JWT_EXPIRA_MINUTOS`, `RESET_EXPIRA_MINUTOS`, `CODIGO_EXPIRA_MINUTOS`, `DOBLE_FACTOR_CORREOS_EXENTOS`, `MAX_INTENTOS_LOGIN` y `BLOQUEO_MINUTOS`. Estos valores se pueden establecer como variables de entorno si se necesita modificar los valores predeterminados definidos en el Backend.

### 8.2. Ejemplo de configuración del Backend

El siguiente ejemplo muestra la estructura de `backend/.env`. Los valores sensibles deben reemplazarse por credenciales propias:

```env
ENV="development"

DATABASE_URL="postgresql://usuario:contrasena@localhost:5432/magnussing"
TEST_DATABASE_URL="postgresql://usuario:contrasena@localhost:5432/magnussing_test"

PORT=8000
FRONTEND_URL="http://localhost:5173"

JWT_SECRET="reemplazar-por-una-clave-larga-y-aleatoria"
ENCRYPTION_KEY=""

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM="Magnus|SIG <noreply@tudominio.com>"

ADMIN_EMAIL="admin@tudominio.com"
ADMIN_PASSWORD="reemplazar-por-una-contrasena-segura"
ADMIN_NOMBRE="Administrador"
ADMIN_APELLIDO="Sistema"

STORAGE_PATH="./storage"
MIN_GRUPO_ANONIMATO=5
DOS_PASOS_ACTIVO=true

BREVO_API_KEY=

WOMPI_API_URL="https://sandbox.wompi.co/v1"
WOMPI_PUBLIC_KEY=""
WOMPI_PRIVATE_KEY=""
WOMPI_INTEGRITY_SECRET=""
WOMPI_EVENTS_SECRET=""
```

La clave de cifrado Fernet se puede generar con el siguiente comando, ejecutado en el entorno virtual del Backend:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copiar el resultado en `ENCRYPTION_KEY`.

### 8.3. Variables del Frontend

Archivo: `frontend/.env`

```env
VITE_API_URL=http://localhost:8000/api
```

Vite expone al código del navegador las variables que comienzan por `VITE_`. Por esta razón, no se deben guardar contraseñas, claves privadas ni secretos en el archivo `.env` del Frontend.

### 8.4. Consideraciones de seguridad

- No publicar los archivos `.env` en repositorios públicos.
- No compartir contraseñas, claves JWT, claves Fernet ni credenciales privadas de Wompi.
- Utilizar credenciales diferentes para desarrollo y producción.
- En producción, configurar HTTPS y las direcciones reales de los servicios.
- Si la verificación en dos pasos está activa, configurar correctamente el servicio de correo.
- En producción, la configuración del Backend exige claves y credenciales de Wompi, además de los demás valores obligatorios definidos en `app/core/config.py`.
- Los archivos `.env.example` deben contener únicamente valores de ejemplo, nunca secretos reales.

---

## 9. Roles y permisos de usuario

Magnus|SIG implementa un control de acceso basado en roles y permisos. Los roles determinan el tipo de usuario y los permisos de gestión que tiene asignados. Además, el Backend aplica restricciones de acceso según la organización y el contexto de cada operación.

Los roles y permisos base se encuentran definidos en el proceso de inicialización del sistema, en:

```text
backend/app/db/seed.py
backend/app/core/roles.py
```

### 9.1. Roles disponibles

| Rol | Descripción |
|---|---|
| Super Administrador (`SUPER_ADMINISTRADOR`) | Cuenta con privilegios globales para administrar la plataforma. |
| Administrador (`ADMINISTRADOR`) | Rol de dirección de una organización, sin privilegios globales. |
| Jefe (`JEFE`) | Rol de dirección de un área u organización. |
| Responsable SST (`RESPONSABLE_SST`) | Gestiona los procesos de evaluación de su empresa, con alcance limitado a la empresa activa. |
| Psicólogo (`EVALUADOR_SST`) | Profesional encargado de aplicar y gestionar evaluaciones de riesgo psicosocial. En la interfaz se presenta como Psicólogo. |
| Paciente (`PACIENTE`) | Participante que responde la batería mediante un enlace público, sin cuenta propia de gestión. |

### 9.2. Descripción de los roles

**Super Administrador**

Cuenta con privilegios globales para administrar la plataforma. El catálogo base de permisos le asigna:

- Gestionar usuarios.
- Gestionar organizaciones.
- Gestionar cuestionarios.
- Gestionar evaluaciones.
- Consultar resultados.
- Generar informes.
- Consultar registros de auditoría.

**Administrador**

Es un rol de dirección de una organización y no cuenta con privilegios globales de administración de la plataforma. En la definición base del sistema no tiene permisos de gestión asignados en el catálogo de permisos. Sus operaciones se encuentran sujetas a las reglas específicas de acceso y alcance organizacional implementadas en el Backend.

**Jefe**

Es un rol de dirección de área u organización. En la definición base del sistema no tiene permisos de gestión asignados en el catálogo de permisos. Su acceso se encuentra sujeto a las reglas específicas de consulta y alcance organizacional implementadas en el Backend.

**Responsable SST**

Gestiona los procesos de su empresa con las mismas capacidades funcionales de evaluación asignadas al Psicólogo, pero limitado a su empresa activa. No tiene acceso a la administración global de empresas, pagos ni al panel de administración.

**Psicólogo**

Es el profesional encargado de aplicar y gestionar evaluaciones de riesgo psicosocial. El catálogo base de permisos le asigna:

- Gestionar cuestionarios.
- Gestionar evaluaciones.
- Consultar resultados.
- Generar informes.

Su acceso también está sujeto a las restricciones organizacionales implementadas en el Backend.

**Paciente**

Es el participante que responde la batería mediante un enlace público generado por el profesional encargado. No tiene una cuenta propia de gestión ni permisos administrativos. Sus acciones se limitan al proceso de respuesta de los instrumentos asignados.

### 9.3. Catálogo de permisos

El sistema define los siguientes permisos base:

| Código | Descripción |
|---|---|
| `GESTIONAR_USUARIOS` | Gestionar usuarios. |
| `GESTIONAR_ORGANIZACIONES` | Gestionar organizaciones. |
| `GESTIONAR_CUESTIONARIOS` | Gestionar cuestionarios. |
| `GESTIONAR_EVALUACIONES` | Gestionar evaluaciones. |
| `VER_RESULTADOS` | Consultar resultados de evaluaciones. |
| `GENERAR_INFORMES` | Generar informes. |
| `VER_AUDITORIA` | Consultar registros de auditoría. |

Los permisos asignados en la inicialización base son:

| Rol | Permisos del catálogo base |
|---|---|
| Super Administrador | Todos los permisos definidos. |
| Administrador | Ninguno asignado en el catálogo base. |
| Jefe | Ninguno asignado en el catálogo base. |
| Responsable SST | Ninguno asignado en el catálogo base; sus capacidades se determinan mediante las reglas de acceso compartidas con el Psicólogo. |
| Psicólogo | `GESTIONAR_CUESTIONARIOS`, `GESTIONAR_EVALUACIONES`, `VER_RESULTADOS`, `GENERAR_INFORMES`. |
| Paciente | Ninguno. |

> **Importante:** la tabla representa las asignaciones iniciales del catálogo de permisos, no una lista exhaustiva de cada botón o pantalla visible. Algunas capacidades se controlan mediante reglas específicas del Backend y restricciones por organización. Los roles Administrador y Jefe tienen pendientes de definición de permisos de gestión en el código de inicialización; no se deben interpretar como roles con permisos globales.

---

## 10. Migraciones de base de datos

El proyecto utiliza Alembic para gestionar las migraciones de PostgreSQL. Las migraciones permiten crear, modificar y actualizar la estructura de la base de datos conforme evoluciona el sistema, conservando un historial de los cambios.

Los archivos se encuentran en:

```text
backend/
├── alembic.ini
└── alembic/
    ├── env.py
    └── versions/
```

### 10.1. Consultar las revisiones principales

Desde una terminal ubicada en la carpeta `backend`, con el entorno virtual activado, ejecutar:

```bash
alembic heads
```

Este comando permite identificar las revisiones principales del historial de migraciones.

### 10.2. Consultar el historial

```bash
alembic history --verbose
```

### 10.3. Consultar la revisión aplicada

```bash
alembic current
```

### 10.4. Aplicar las migraciones

Si el historial cuenta con una única revisión principal:

```bash
alembic upgrade head
```

Este comando aplica las migraciones pendientes hasta la última revisión.

### 10.5. Crear una nueva migración

Después de modificar los modelos, se puede generar una migración automática con:

```bash
alembic revision --autogenerate -m "descripcion_del_cambio"
```

El archivo generado se guarda en:

```text
backend/alembic/versions/
```

La migración debe revisarse antes de aplicarla. La generación automática no reemplaza la revisión manual del SQL o de las operaciones que Alembic propone.

### 10.6. Actualizar a una revisión específica

```bash
alembic upgrade ID_REVISION
```

Reemplazar `ID_REVISION` por el identificador real de la revisión.

### 10.7. Retroceder a una revisión anterior

```bash
alembic downgrade ID_REVISION
```

Esta operación debe realizarse con precaución, ya que puede revertir cambios de estructura y afectar información almacenada.

### 10.8. Manejo de múltiples revisiones principales

Si `alembic heads` muestra más de una revisión principal, no se debe asumir que `alembic upgrade head` funcionará. Primero se deben revisar las dependencias y el historial de las ramas.

Cuando corresponda, las ramas pueden integrarse mediante una migración de merge:

```bash
alembic merge -m "unificar_revisiones" REVISION_1 REVISION_2
```

Los identificadores deben reemplazarse por las revisiones reales y la operación debe realizarse únicamente después de verificar que la integración sea correcta. No se deben eliminar ni modificar migraciones ya compartidas sin revisar sus efectos.

### 10.9. Recomendaciones

- Realizar una copia de seguridad antes de aplicar migraciones en producción.
- Revisar cada migración generada automáticamente.
- Mantener sincronizados los modelos y las migraciones.
- No eliminar migraciones que ya hayan sido aplicadas en ambientes compartidos.
- Verificar las revisiones principales antes de ejecutar actualizaciones.
- No ejecutar migraciones ni pruebas sobre una base de datos de producción sin un procedimiento de respaldo y validación.

---

## 11. Ejecución del proyecto

Para ejecutar Magnus|SIG en un entorno local, se deben iniciar PostgreSQL, el Backend y el Frontend. El Backend y el Frontend se ejecutan en terminales independientes.

### 11.1. Iniciar PostgreSQL

Verificar que el servicio de PostgreSQL esté activo y que la base de datos configurada en `DATABASE_URL` exista y permita la conexión.

### 11.2. Iniciar el Backend

Abrir una primera terminal desde la carpeta principal del proyecto:

```bash
cd backend
```

Activar el entorno virtual en Windows:

```bash
venv\Scripts\activate
```

En Linux o macOS:

```bash
source venv/bin/activate
```

Verificar que el archivo `.env` esté configurado. Consultar las revisiones principales:

```bash
alembic heads
```

Si existe una única revisión principal, aplicar las migraciones:

```bash
alembic upgrade head
```

Inicializar los datos base cuando corresponda:

```bash
python -m app.db.seed
```

Iniciar el servidor:

```bash
uvicorn app.main:app --reload
```

El Backend estará disponible por defecto en:

```text
http://localhost:8000
```

### 11.3. Iniciar el Frontend

Abrir una segunda terminal desde la carpeta principal del proyecto:

```bash
cd frontend
```

Instalar las dependencias si todavía no se han instalado:

```bash
npm install
```

Verificar que `frontend/.env` contenga la dirección de la API:

```env
VITE_API_URL=http://localhost:8000/api
```

Iniciar el servidor de desarrollo:

```bash
npm run dev
```

Vite mostrará la dirección local de la aplicación. Normalmente será:

```text
http://localhost:5173
```

### 11.4. Direcciones de acceso

| Servicio | Dirección |
|---|---|
| Aplicación web | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Documentación interactiva de la API | http://localhost:8000/docs |
| Documentación alternativa de la API | http://localhost:8000/redoc |

### 11.5. Consideraciones para la ejecución

- PostgreSQL debe estar activo antes de iniciar el Backend.
- El archivo `backend/.env` debe contener una conexión válida a PostgreSQL y las claves requeridas.
- Las migraciones deben estar aplicadas antes de utilizar la aplicación.
- El Frontend debe apuntar a la dirección correcta del Backend mediante `VITE_API_URL`.
- El Backend y el Frontend deben permanecer activos mientras se utiliza el entorno local.
- Los servicios de correo y pagos requieren sus respectivas credenciales para funcionar.
- El modo `--reload` está destinado al desarrollo local; para producción se debe utilizar una configuración de despliegue apropiada.

---

## Información de mantenimiento

Para mantener el proyecto actualizado:

1. Obtener los cambios más recientes del repositorio.
2. Revisar si cambiaron `backend/requirements.txt` o `frontend/package.json`.
3. Instalar las dependencias nuevas cuando corresponda.
4. Revisar las migraciones pendientes antes de actualizar la base de datos.
5. Mantener las variables de entorno actualizadas sin compartir sus valores secretos.
6. Ejecutar las verificaciones y pruebas disponibles antes de desplegar cambios.

**Seguridad:** nunca incluir en el repositorio contraseñas reales, claves privadas, tokens, secretos de cifrado ni información personal de usuarios.

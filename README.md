# SwissDesk Web

Sistema de torneos formato suizo para TCG — versión web.
Desarrollado por DavidZ | FastAPI + PostgreSQL

---

## Instalación local (paso a paso)

### 1. Crear la base de datos en PostgreSQL

Abre pgAdmin o la consola de PostgreSQL y ejecuta:
```sql
CREATE DATABASE swissdesk;
```

### 2. Crear entorno virtual e instalar dependencias

```bash
cd swissdesk-web/backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
copy .env.example .env
```
Edita `.env` con tu password de PostgreSQL:
```
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/swissdesk
```

### 4. Arrancar el servidor

```bash
uvicorn main:app --reload
```

La API queda en: http://localhost:8000
Documentación automática: http://localhost:8000/docs

---

## Deploy en Railway

1. Sube el proyecto a GitHub
2. En railway.app → New Project → Deploy from GitHub
3. Selecciona el repositorio
4. Agrega un servicio PostgreSQL (Add Service → Database → PostgreSQL)
5. En Variables del servicio FastAPI, agrega:
   - `DATABASE_URL` → copia el valor que Railway genera para PostgreSQL
6. Listo — Railway detecta el Procfile y despliega automáticamente

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/torneos | Listar torneos |
| POST | /api/torneos | Crear torneo |
| POST | /api/torneos/{id}/iniciar | Iniciar torneo (genera ronda 1) |
| POST | /api/torneos/{id}/siguiente-ronda | Avanzar ronda |
| GET | /api/torneos/{id}/partidas?ronda=N | Ver partidas de una ronda |
| PUT | /api/torneos/{id}/partidas/{pid}/resultado | Registrar resultado |
| GET | /api/torneos/{id}/ranking | Standing actual |
| GET | /api/jugadores | Listar jugadores |
| POST | /api/jugadores | Crear jugador |

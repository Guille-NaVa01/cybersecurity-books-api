Backend API developed in Python (FastAPI) for managing the book catalog. It requires a valid JWT to be provided in the Authorization: Bearer <token> header. The API validates token signatures in real time using the RS256 public keys exposed through Keycloak's JWKS endpoint.

# Repos needed

This repository is part of a complete project that requires the following repositories:

frontend: https://github.com/Guille-NaVa01/cybersecurity-books-frontend.git

backend: https://github.com/Guille-NaVa01/cybersecurity-books-api.git

auth : https://github.com/Guille-NaVa01/cybersecurity-identity-auth-lab.git

To run the complete project, you must download/clone all three repositories.

# Backend Dashboard — Books API

FastAPI backend para el catálogo de libros. Valida JWTs emitidos por Keycloak antes de procesar cada request.

## Endpoints

| Método | Ruta | Protegido | Descripción |
|--------|------|-----------|-------------|
| GET | `/health` | ❌ | Liveness probe |
| GET | `/books` | ✅ JWT | Lista todos los libros |
| POST | `/books` | ✅ JWT | Agrega un libro nuevo |

## Flujo de validación JWT

1. El cliente envía `Authorization: Bearer <token>`
2. El backend descarga la JWKS pública de Keycloak
3. Valida firma RS256, issuer y audience
4. Si es válido, ejecuta la operación; si no, retorna 401

## Correr con Docker (recomendado)

```bash
# Desde ldap-keycloak-oauth2-lab/
docker compose up -d --build
```

El servicio `books-api` se levanta en **http://localhost:8001**.

## Correr localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

> ⚠️ Keycloak debe estar corriendo en localhost:8081 antes de arrancar el backend.

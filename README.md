Backend API developed in Python (FastAPI) for managing the book catalog. It requires a valid JWT to be provided in the Authorization: Bearer <token> header. The API validates token signatures in real time using the RS256 public keys exposed through Keycloak's JWKS endpoint.

This repository is part of a complete project that requires the following repositories:

frontend: https://github.com/Guille-NaVa01/cybersecurity-books-frontend.git

backend: https://github.com/Guille-NaVa01/cybersecurity-books-api.git

auth : https://github.com/Guille-NaVa01/cybersecurity-identity-auth-lab.git

ddos : https://github.com/Guille-NaVa01/cybersecurity-ddos-load-tester.git

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

## Protección contra DDoS e Inyecciones con Fail2Ban

El contenedor incluye **Fail2Ban** y reglas de filtrado en tiempo real con `iptables`:
- **Jail**: `http-flood` en el puerto `8001`.
- **Filtro**: `/etc/fail2ban/filter.d/http-flood.conf` monitoreando `/var/log/app/access.log`.
- **Regla**: Bloquea (`iptables-allports`) cualquier IP que supere 60 solicitudes en una ventana de 10 segundos por un periodo de 10 minutos (con incremento progresivo).

Para verificar el estado de Fail2Ban dentro del contenedor:
```bash
docker exec books-dashboard-api fail2ban-client status http-flood
```


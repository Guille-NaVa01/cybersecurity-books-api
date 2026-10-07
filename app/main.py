import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import List, Optional

# ── Keycloak config ────────────────────────────────────────────────────────────
KC_INTERNAL = os.getenv("KEYCLOAK_INTERNAL", "http://keycloak:8080")
KC_PUBLIC   = os.getenv("KEYCLOAK_PUBLIC",   "http://localhost:8081")
REALM       = os.getenv("KEYCLOAK_REALM",     "cybersecurity")
CLIENT_ID   = os.getenv("KEYCLOAK_CLIENT_ID", "fastapi-api")

ISSUER   = f"{KC_PUBLIC}/realms/{REALM}"
JWKS_URL = f"{KC_INTERNAL}/realms/{REALM}/protocol/openid-connect/certs"

# ── In-memory books store ──────────────────────────────────────────────────────
books_db: List[dict] = [
    {"id": 1, "title": "Clean Code",               "author": "Robert C. Martin", "year": 2008, "genre": "Programming"},
    {"id": 2, "title": "The Pragmatic Programmer",  "author": "David Thomas",     "year": 1999, "genre": "Programming"},
    {"id": 3, "title": "Design Patterns",           "author": "Gang of Four",     "year": 1994, "genre": "Architecture"},
    {"id": 4, "title": "The Web Application Hacker's Handbook", "author": "Stuttard & Pinto", "year": 2011, "genre": "Security"},
    {"id": 5, "title": "Hacking: The Art of Exploitation", "author": "Jon Erickson", "year": 2008, "genre": "Security"},
]
_next_id = 6

# ── App setup ──────────────────────────────────────────────────────────────────
security = HTTPBearer()

app = FastAPI(
    title="Books Dashboard API",
    version="1.0.0",
    description="Protected REST API — requires a valid Keycloak JWT as Bearer Token.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Fail2Ban Access Log Setup & Middleware ────────────────────────────────────
import logging
from logging.handlers import RotatingFileHandler
from fastapi import Request

try:
    os.makedirs("/var/log/app", exist_ok=True)
    access_logger = logging.getLogger("fail2ban.access")
    access_logger.setLevel(logging.INFO)
    file_handler = RotatingFileHandler("/var/log/app/access.log", maxBytes=10*1024*1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    access_logger.addHandler(file_handler)
except Exception:
    access_logger = None

@app.middleware("http")
async def log_access_for_fail2ban(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    response = await call_next(request)
    if access_logger:
        access_logger.info(f'{client_ip} - "{request.method} {request.url.path} HTTP/1.1" {response.status_code}')
    return response

# ── JWT validation ─────────────────────────────────────────────────────────────
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validates the Bearer JWT against Keycloak's JWKS endpoint.
    Returns the decoded token payload on success, raises 401 on failure.
    """
    token = credentials.credentials
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL, timeout=5)
            resp.raise_for_status()
            jwks = resp.json()

        header = jwt.get_unverified_header(token)
        key = next(
            (k for k in jwks["keys"] if k.get("kid") == header.get("kid")),
            None,
        )
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signing key not found in JWKS.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=ISSUER,
        )
        return payload

    except (JWTError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Pydantic models ────────────────────────────────────────────────────────────
class BookIn(BaseModel):
    title:  str
    author: str
    year:   int
    genre:  str

class BookOut(BookIn):
    id: int

class BooksResponse(BaseModel):
    books:    List[BookOut]
    total:    int
    username: Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    """Unauthenticated liveness probe."""
    return {"status": "ok", "service": "books-dashboard-api"}


@app.get("/books", response_model=BooksResponse, tags=["Books"])
async def get_books(user: dict = Depends(validate_token)):
    """
    Returns the full book catalogue.
    Requires a valid Bearer JWT (validated against Keycloak).
    """
    return BooksResponse(
        books=books_db,
        total=len(books_db),
        username=user.get("preferred_username"),
    )


@app.post("/books", response_model=BookOut, status_code=status.HTTP_201_CREATED, tags=["Books"])
async def add_book(book: BookIn, user: dict = Depends(validate_token)):
    """
    Adds a new book to the catalogue.
    Requires a valid Bearer JWT (validated against Keycloak).
    """
    global _next_id
    new_book = {"id": _next_id, **book.model_dump()}
    _next_id += 1
    books_db.append(new_book)
    return new_book

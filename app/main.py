import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from fastapi.openapi.utils import get_openapi

from app.database import Base, engine, SessionLocal
from app.models import Admin, AdminProfile
from app.auth import hash_password
from app.routers.admin import router as admin_router
from app.routers.ea import router as ea_router
from app.routers.license import router as license_router
from app.routers.client import router as client_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NolimitzBots Backend", version="1.0.0")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def seed_super_admin():
    db: Session = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.email == "superadmin@nolimitz.com").first()
        if not existing:
            super_admin = Admin(
                admin_code=100,
                full_name="Super Admin",
                email="superadmin@nolimitz.com",
                password_hash=hash_password("admin12345"),
                role="super_admin",
                is_approved=True,
                is_active=True,
            )
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)

            profile = AdminProfile(
                admin_id=super_admin.id,
                display_name="NolimitzBots",
                company_name="NolimitzBots",
                support_email="support@nolimitz.com",
            )
            db.add(profile)
            db.commit()
    finally:
        db.close()


seed_super_admin()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(admin_router)
app.include_router(ea_router)
app.include_router(license_router)
app.include_router(client_router)

@app.get("/")
def root(): 
    return {"message": "NolimitzBots backend is running"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="NolimitzBots Backend",
        version="1.0.0",
        description="API for NolimitzBots",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
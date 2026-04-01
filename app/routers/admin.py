import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Admin, AdminProfile
from app.schemas import (
    AdminSignupRequest,
    AdminLoginRequest,
    AdminProfileUpdateRequest,
    TokenResponse,
    AdminMeResponse,
    AdminApprovalResponse,
    AdminListItem,
    LogoUploadResponse,
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_current_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> Admin:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    admin_id = payload.get("admin_id")
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return admin


def get_current_super_admin(current_admin: Admin = Depends(get_current_admin)) -> Admin:
    if current_admin.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_admin


def get_current_approved_admin(current_admin: Admin = Depends(get_current_admin)) -> Admin:
    if current_admin.role != "super_admin" and not current_admin.is_approved:
        raise HTTPException(status_code=403, detail="Your account is pending approval")
    return current_admin

def generate_admin_code(db: Session):
    last_admin = db.query(Admin).order_by(Admin.admin_code.desc()).first()

    if not last_admin or not last_admin.admin_code:
        return 100

    return last_admin.admin_code + 1

@router.post("/signup")
def admin_signup(payload: AdminSignupRequest, db: Session = Depends(get_db)):
    existing = db.query(Admin).filter(Admin.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = Admin(
        admin_code=generate_admin_code(db),  # 👈 NEW
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="admin",
        is_approved=False,
        is_active=True,
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)

    profile = AdminProfile(admin_id=admin.id)
    db.add(profile)
    db.commit()

    return {
        "message": "Signup successful. Your account is pending approval.",
        "admin_id": admin.id,
        "is_approved": admin.is_approved,
    }


@router.post("/login", response_model=TokenResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == payload.email).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(
        {"admin_id": admin.id, "email": admin.email, "role": admin.role}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        admin_id=admin.id,
        admin_code=admin.admin_code,
        full_name=admin.full_name,
        email=admin.email,
        role=admin.role,
        is_approved=admin.is_approved,
    )


@router.get("/me", response_model=AdminMeResponse)
def admin_me(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    profile = db.query(AdminProfile).filter(AdminProfile.admin_id == current_admin.id).first()

    return AdminMeResponse(
        admin_id=current_admin.id,
        full_name=current_admin.full_name,
        admin_code=current_admin.admin_code,
        email=current_admin.email,
        role=current_admin.role,
        is_approved=current_admin.is_approved,
        is_active=current_admin.is_active,
        display_name=profile.display_name if profile else None,
        logo_url=profile.logo_url if profile else None,
        phone=profile.phone if profile else None,
        support_email=profile.support_email if profile else None,
        telegram=profile.telegram if profile else None,
        whatsapp=profile.whatsapp if profile else None,
        company_name=profile.company_name if profile else None,
    )


@router.put("/profile")
def update_profile(
    payload: AdminProfileUpdateRequest,
    current_admin: Admin = Depends(get_current_approved_admin),
    db: Session = Depends(get_db),
):
    profile = db.query(AdminProfile).filter(AdminProfile.admin_id == current_admin.id).first()
    if not profile:
        profile = AdminProfile(admin_id=current_admin.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    if payload.display_name is not None:
        profile.display_name = payload.display_name
    if payload.phone is not None:
        profile.phone = payload.phone
    if payload.support_email is not None:
        profile.support_email = payload.support_email
    if payload.telegram is not None:
        profile.telegram = payload.telegram
    if payload.whatsapp is not None:
        profile.whatsapp = payload.whatsapp
    if payload.company_name is not None:
        profile.company_name = payload.company_name

    db.commit()

    return {"message": "Profile updated successfully"}


@router.post("/profile/logo", response_model=LogoUploadResponse)
def upload_logo(
    file: UploadFile = File(...),
    current_admin: Admin = Depends(get_current_approved_admin),
    db: Session = Depends(get_db),
):
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG, and WEBP images are allowed")

    ext = os.path.splitext(file.filename)[1].lower()
    safe_filename = f"admin_{current_admin.id}_logo{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    profile = db.query(AdminProfile).filter(AdminProfile.admin_id == current_admin.id).first()
    if not profile:
        profile = AdminProfile(admin_id=current_admin.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    profile.logo_url = f"/uploads/{safe_filename}"
    db.commit()

    return LogoUploadResponse(
        message="Logo uploaded successfully",
        logo_url=profile.logo_url,
    )


@router.get("/dashboard")
def admin_dashboard(current_admin: Admin = Depends(get_current_approved_admin)):
    return {
        "message": "Welcome to NolimitzBots admin dashboard",
        "admin_id": current_admin.id,
        "full_name": current_admin.full_name,
        "role": current_admin.role,
    }


@router.get("/pending-admins", response_model=List[AdminListItem])
def list_pending_admins(
    current_admin: Admin = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    admins = (
        db.query(Admin)
        .filter(Admin.role == "admin", Admin.is_approved == False)
        .order_by(Admin.id.desc())
        .all()
    )

    return [
        AdminListItem(
            admin_id=admin.id,
            full_name=admin.full_name,
            email=admin.email,
            role=admin.role,
            is_approved=admin.is_approved,
            is_active=admin.is_active,
        )
        for admin in admins
    ]


@router.post("/approve/{admin_id}", response_model=AdminApprovalResponse)
def approve_admin(
    admin_id: int,
    current_admin: Admin = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.id == admin_id, Admin.role == "admin").first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    admin.is_approved = True
    db.commit()

    return AdminApprovalResponse(
        message="Admin approved successfully",
        admin_id=admin.id,
        is_approved=admin.is_approved,
    )


@router.post("/deactivate/{admin_id}")
def deactivate_admin(
    admin_id: int,
    current_admin: Admin = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.id == admin_id, Admin.role == "admin").first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    admin.is_active = False
    db.commit()

    return {"message": "Admin deactivated successfully", "admin_id": admin.id}


@router.get("/all-admins", response_model=List[AdminListItem])
def list_all_admins(
    current_admin: Admin = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    admins = db.query(Admin).order_by(Admin.id.desc()).all()

    return [
        AdminListItem(
            admin_id=admin.id,
            full_name=admin.full_name,
            email=admin.email,
            role=admin.role,
            is_approved=admin.is_approved,
            is_active=admin.is_active,
        )
        for admin in admins
    ]
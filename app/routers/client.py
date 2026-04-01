from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import License, ExpertAdvisor, ClientActivation
from app.schemas import ClientActivateRequest, ClientActivateResponse

router = APIRouter(prefix="/client", tags=["Client"])


@router.post("/activate", response_model=ClientActivateResponse)
def activate_client_license(payload: ClientActivateRequest, db: Session = Depends(get_db)):
    license = db.query(License).filter(License.license_key == payload.license_key).first()

    if not license:
        raise HTTPException(status_code=404, detail="Invalid license key")

    if not license.is_active:
        raise HTTPException(status_code=403, detail="License is deactivated")

    if license.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="License has expired")

    ea = db.query(ExpertAdvisor).filter(ExpertAdvisor.id == license.ea_id).first()
    if not ea:
        raise HTTPException(status_code=404, detail="EA linked to license not found")

    existing_activation = db.query(ClientActivation).filter(
        ClientActivation.license_id == license.id
    ).first()

    if not existing_activation:
        activation = ClientActivation(license_id=license.id, activated=True)
        db.add(activation)
        db.commit()

    return ClientActivateResponse(
        message="License activated successfully",
        license_key=license.license_key,
        client_name=license.client_name,
        client_email=license.client_email,
        mode_type=license.mode_type,
        expires_at=license.expires_at,
        ea_name=ea.name,
        ea_code_name=ea.code_name,
        branding=license.branding_snapshot or {},
    )
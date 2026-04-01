from pydantic import BaseModel, EmailStr
from typing import Optional, List


class AdminSignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    phone: Optional[str] = None
    support_email: Optional[EmailStr] = None
    telegram: Optional[str] = None
    whatsapp: Optional[str] = None
    company_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    admin_id: int
    admin_code: int
    full_name: str
    email: EmailStr
    role: str
    is_approved: bool


class AdminMeResponse(BaseModel):
    admin_id: int
    admin_code: int
    full_name: str
    email: EmailStr
    role: str
    is_approved: bool
    is_active: bool
    display_name: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    support_email: Optional[str] = None
    telegram: Optional[str] = None
    whatsapp: Optional[str] = None
    company_name: Optional[str] = None


class AdminApprovalResponse(BaseModel):
    message: str
    admin_id: int
    is_approved: bool


class AdminListItem(BaseModel):
    admin_id: int
    full_name: str
    email: EmailStr
    role: str
    is_approved: bool
    is_active: bool


class LogoUploadResponse(BaseModel):
    message: str
    logo_url: str


class EACreateRequest(BaseModel):
    name: str
    code_name: str
    version: Optional[str] = None
    description: Optional[str] = None
    mode_type: str  # signal or robot


class EAUpdateRequest(BaseModel):
    name: Optional[str] = None
    code_name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    mode_type: Optional[str] = None
    is_active: Optional[bool] = None


class EASymbolsRequest(BaseModel):
    symbols: List[str]


class EASymbolItem(BaseModel):
    id: int
    symbol_name: str
    enabled: bool


class EAItem(BaseModel):
    id: int
    name: str
    code_name: str
    version: Optional[str] = None
    description: Optional[str] = None
    mode_type: str
    is_active: bool
    symbols: List[EASymbolItem] = []


class BasicMessageResponse(BaseModel):
    message: str

from datetime import datetime


class LicenseCreateRequest(BaseModel):
    ea_id: int
    client_name: str
    client_email: EmailStr
    duration_days: int


class LicenseItem(BaseModel):
    id: int
    license_key: str
    client_name: str
    client_email: str
    mode_type: str
    expires_at: datetime
    is_active: bool


class LicenseResponse(BaseModel):
    message: str
    license: LicenseItem


from typing import Any, Dict


class ClientActivateRequest(BaseModel):
    license_key: str


class ClientActivateResponse(BaseModel):
    message: str
    license_key: str
    client_name: str
    client_email: str
    mode_type: str
    expires_at: datetime
    ea_name: str
    ea_code_name: str
    branding: Dict[str, Any]
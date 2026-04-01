from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    admin_code = Column(Integer, unique=True, index=True)

    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    role = Column(String, default="admin")
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("AdminProfile", back_populates="admin", uselist=False)  # 👈 MUST EXIST
    eas = relationship("ExpertAdvisor", back_populates="admin")

class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), unique=True, nullable=False)

    display_name = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    support_email = Column(String, nullable=True)
    telegram = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)
    company_name = Column(String, nullable=True)

    admin = relationship("Admin", back_populates="profile")  # 👈 MUST EXIST


class ExpertAdvisor(Base):
    __tablename__ = "expert_advisors"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)

    name = Column(String, nullable=False)
    code_name = Column(String, nullable=False)
    version = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    mode_type = Column(String, nullable=False, default="signal")  # signal or robot
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="eas")
    symbols = relationship("EASymbol", back_populates="ea", cascade="all, delete-orphan")


class EASymbol(Base):
    __tablename__ = "ea_symbols"

    id = Column(Integer, primary_key=True, index=True)
    ea_id = Column(Integer, ForeignKey("expert_advisors.id"), nullable=False)

    symbol_name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)

    ea = relationship("ExpertAdvisor", back_populates="symbols")

from sqlalchemy import JSON
import uuid


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)

    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    ea_id = Column(Integer, ForeignKey("expert_advisors.id"), nullable=False)

    license_key = Column(String, unique=True, index=True, nullable=False)

    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)

    mode_type = Column(String, nullable=False)  # signal or robot

    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    branding_snapshot = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ClientActivation(Base):
    __tablename__ = "client_activations"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), unique=True, nullable=False)

    activated = Column(Boolean, default=True)
    activated_at = Column(DateTime(timezone=True), server_default=func.now())
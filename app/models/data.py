import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey,
    Integer, Enum as SQLEnum, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from enum import Enum
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass

# ----------------- RESIDENCE ------------------
class Residence(Base):
    __tablename__ = "residences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    users = relationship("User", back_populates="residence")
    guards = relationship("Guard", back_populates="residence")
    owners = relationship("Owner", back_populates="residence")

# ----------------- USER ------------------
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    appartement = Column(String(255), nullable=False)
    resident = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # Foreign key vers Residence
    residence_id = Column(UUID(as_uuid=True), ForeignKey("residences.id"), nullable=False)
    residence = relationship("Residence", back_populates="users")

    # Relation avec les formulaires
    form_data = relationship("FormData", back_populates="user")

# ----------------- FORM DATA ------------------
class FormData(Base):
    __tablename__ = "form_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False, unique=True)
    qr_code_data = Column(Text, nullable=True)
    apartment_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    duration_minutes = Column(Integer)

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    user = relationship("User", back_populates="form_data")

    guard_scans = relationship("GuardQRScan", back_populates="form_data")

# ----------------- GUARD ------------------
class Guard(Base):
    __tablename__ = "guards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # Foreign key vers Residence
    residence_id = Column(UUID(as_uuid=True), ForeignKey("residences.id"), nullable=False)
    residence = relationship("Residence", back_populates="guards")

    attendances = relationship("Attendance", back_populates="guard")
    qr_scans = relationship("GuardQRScan", back_populates="guard")

# ----------------- ATTENDANCE ------------------
class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    guard_id = Column(UUID(as_uuid=True), ForeignKey('guards.id'))
    guard = relationship("Guard", back_populates="attendances")

# ----------------- GUARD QR SCAN ------------------
class GuardQRScan(Base):
    __tablename__ = "guard_qr_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    qr_code_data = Column(Text, nullable=False)
    guard_id = Column(UUID(as_uuid=True), ForeignKey("guards.id"), nullable=False)
    form_data_id = Column(UUID(as_uuid=True), ForeignKey("form_data.id"), nullable=True)
    confirmed = Column(Boolean, nullable=True)
    scanned_at = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    guard = relationship("Guard", back_populates="qr_scans")
    form_data = relationship("FormData", back_populates="guard_scans")

# ----------------- OWNER ------------------
class Owner(Base):
    __tablename__ = "owners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    logo_path = Column(String(255), nullable=True)

    # Foreign key vers Residence
    residence_id = Column(UUID(as_uuid=True), ForeignKey("residences.id"), nullable=False)
    residence = relationship("Residence", back_populates="owners")

    reports = relationship("Report", back_populates="owner")

# ----------------- REPORT ------------------
class ReportTypeEnum(str, Enum):
    USER_REPORT = "user_report"
    QR_CODE_REPORT = "qr_code_report"
    ACTIVITY_REPORT = "activity_report"
    SECURITY_REPORT = "security_report"
    

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    report_type = Column(SQLEnum(ReportTypeEnum), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("owners.id"), nullable=False)
    residence_id = Column(UUID(as_uuid=True), ForeignKey("residences.id"), nullable=False) 

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Owner", back_populates="reports")
    residence = relationship("Residence")


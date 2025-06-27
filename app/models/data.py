import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from enum import Enum
from sqlalchemy.sql import func



class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    appartement = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    form_data = relationship("FormData", back_populates="user")

class FormData(Base):
    __tablename__ = "form_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False, unique=True)
    qr_code_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    duration_minutes = Column(Integer)

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    user = relationship("User", back_populates="form_data")

    guard_scans = relationship("GuardQRScan", back_populates="form_data")

class Guard(Base):
    __tablename__ = "guards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    attendances = relationship("Attendance", back_populates="guard")
    qr_scans = relationship("GuardQRScan", back_populates="guard")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    guard_id = Column(UUID(as_uuid=True), ForeignKey('guards.id'))
    guard = relationship("Guard", back_populates="attendances")

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

    # Relationships
    guard = relationship("Guard", back_populates="qr_scans")
    form_data = relationship("FormData", back_populates="guard_scans")

class Owner(Base):
    __tablename__ = "owners"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    logo_path = Column(String(255), nullable=True) 

    reports = relationship("Report", back_populates="owner")


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    owner = relationship("Owner", back_populates="reports")


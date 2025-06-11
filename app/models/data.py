import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship

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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_time = Column(DateTime, default=datetime.now)
    qr_code_data = Column(Text, nullable=False)

    guard_id = Column(UUID(as_uuid=True), ForeignKey('guards.id'))
    guard = relationship("Guard", back_populates="qr_scans")

    form_data_id = Column(UUID(as_uuid=True), ForeignKey('form_data.id'))
    form_data = relationship("FormData", back_populates="guard_scans")


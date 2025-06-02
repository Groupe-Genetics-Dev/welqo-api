import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class FormData(Base):
    __tablename__ = "form_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    qr_code_data: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    expires_at: Mapped[datetime] = mapped_column()

    def set_expiration(self, duration_minutes: int):
        self.expires_at = datetime.now() + timedelta(minutes=duration_minutes)



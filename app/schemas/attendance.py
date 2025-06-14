from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AttendanceBase(BaseModel):
    start_time: datetime
    end_time: datetime | None = None

class AttendanceCreate(AttendanceBase):
    guard_id: UUID

class AttendanceOut(AttendanceBase):
    id: UUID
    created_at: datetime
    guard_id: UUID

    class Config:
        from_attributes = True



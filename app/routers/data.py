from typing import Annotated, List
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

from app.oauth2 import get_current_user
from app.schemas.data import (
    FormDataCreate,
    FormDataResponse,
    QRValidationResponse,
    QRValidationData,
    FormDataUpdate
)
from app.models.data import FormData
from app.postgres_connect import get_db
from app.utils import generate_qr_code_base64, generate_qr_content
from app.models.data import User

router = APIRouter(prefix="/forms", tags=["Form Data"])

@router.post("/create-form", response_model=FormDataResponse, status_code=status.HTTP_201_CREATED)
async def create_form_data(
    form_data: FormDataCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    existing_form = db.query(FormData).filter_by(phone=form_data.phone).first()
    if existing_form:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un formulaire avec le numéro {form_data.phone} existe déjà."
        )

    qr_content = generate_qr_content(form_data.name, form_data.phone, form_data.duration_minutes)
    qr_code_base64 = generate_qr_code_base64(qr_content)
    created_at = datetime.now()
    expires_at = created_at + timedelta(minutes=form_data.duration_minutes)

    new_form = FormData(
        name=form_data.name,
        phone=form_data.phone,
        qr_code_data=qr_code_base64,
        created_at=created_at,
        expires_at=expires_at,
        user_id=current_user.id
    )

    db.add(new_form)
    db.commit()
    db.refresh(new_form)

    return new_form

@router.get("/user-forms", response_model=List[FormDataResponse])
async def get_user_forms(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    forms = db.query(FormData).filter(FormData.user_id == current_user.id).all()
    return forms

@router.get("/validate-qr-code", response_model=QRValidationResponse)
async def validate_qr_code(
    qr_data: Annotated[str, Query(..., description="Donnée QR encodée (ex: base64)")],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    form = db.query(FormData).filter_by(qr_code_data=qr_data).first()

    if not form:
        return QRValidationResponse(valid=False, message="QR code introuvable", data=None)

    if datetime.now() > form.expires_at:
        return QRValidationResponse(valid=False, message="QR code expiré", data=None)

    return QRValidationResponse(
        valid=True,
        message="QR code valide.",
        data=QRValidationData(
            name=form.name,
            phone=form.phone,
            created_at=form.created_at,
            expires_at=form.expires_at
        )
    )

@router.get("/all", response_model=List[FormDataResponse])
async def get_all_forms(
    db: Annotated[Session, Depends(get_db)],
    __current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100
):
    forms = db.query(FormData).offset(skip).limit(limit).all()
    return forms

@router.get("/{form_id}", response_model=FormDataResponse)
async def get_form(
    form_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    form = db.query(FormData).filter(FormData.id == form_id, FormData.user_id == current_user.id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")
    return form

@router.put("/{form_id}", response_model=FormDataResponse)
async def update_form(
    form_id: UUID,
    form_data: FormDataUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    form = db.query(FormData).filter(FormData.id == form_id, FormData.user_id == current_user.id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")

    for key, value in form_data.dict(exclude_unset=True).items():
        setattr(form, key, value)

    db.commit()
    db.refresh(form)
    return form


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    form_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    form = db.query(FormData).filter(FormData.id == form_id, FormData.user_id == current_user.id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")

    db.delete(form)
    db.commit()
    return {"message": "Formulaire supprimé avec succès"}

@router.post("/{form_id}/renew", response_model=FormDataResponse)
async def renew_qr_code(
    form_id: UUID,
    duration_minutes: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    form = db.query(FormData).filter(FormData.id == form_id, FormData.user_id == current_user.id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")

    qr_content = generate_qr_content(form.name, form.phone, duration_minutes)
    form.qr_code_data = generate_qr_code_base64(qr_content)
    form.expires_at = datetime.now() + timedelta(minutes=duration_minutes)

    db.commit()
    db.refresh(form)
    return form


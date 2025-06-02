from typing import Annotated, List
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

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

router = APIRouter(prefix="/forms", tags=["Form Data"])


@router.post("/create-form", response_model=FormDataResponse, status_code=status.HTTP_201_CREATED)
async def create_form_data(
    form_data: FormDataCreate,
    db: Annotated[Session, Depends(get_db)]
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
        expires_at=expires_at
    )

    db.add(new_form)
    db.commit()
    db.refresh(new_form)

    return new_form
 

@router.get("/validate-qr-code", response_model=QRValidationResponse)
async def validate_qr_code(
    qr_data: Annotated[str, Query(..., description="Donnée QR encodée (ex: base64)")],
    db: Annotated[Session, Depends(get_db)]
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
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    forms = db.query(FormData).offset(skip).limit(limit).all()
    return forms


@router.get("/{form_id}", response_model=FormDataResponse)
async def get_form(
    form_id: UUID,
    db: Session = Depends(get_db)
):
    form = db.query(FormData).filter(FormData.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")
    return form

# Endpoint pour mettre à jour un formulaire
@router.put("/{form_id}", response_model=FormDataResponse)
async def update_form(
    form_id: UUID,
    form_data: FormDataUpdate,
    db: Session = Depends(get_db)
):
    form = db.query(FormData).filter(FormData.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")

    for key, value in form_data.dict(exclude_unset=True).items():
        setattr(form, key, value)

    db.commit()
    db.refresh(form)
    return form

# Endpoint pour supprimer un formulaire
@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    form_id: UUID,
    db: Session = Depends(get_db)
):
    form = db.query(FormData).filter(FormData.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")

    db.delete(form)
    db.commit()
    return {"message": "Formulaire supprimé avec succès"}

# Endpoint pour renouveler un QR code
@router.post("/{form_id}/renew", response_model=FormDataResponse)
async def renew_qr_code(
    form_id: UUID,
    duration_minutes: int,
    db: Session = Depends(get_db)
):
    form = db.query(FormData).filter(FormData.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire non trouvé")

    # Générer un nouveau contenu QR et mettre à jour expires_at
    qr_content = generate_qr_content(form.name, form.phone, duration_minutes)
    form.qr_code_data = generate_qr_code_base64(qr_content)
    form.expires_at = datetime.now() + timedelta(minutes=duration_minutes)

    db.commit()
    db.refresh(form)
    return form


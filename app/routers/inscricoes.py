from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import obter_sessao
from app.regras import inscricoes as regras_inscricoes
from app.schemas.inscricao import InscricaoSaida
from app.schemas.participante import ParticipanteSaida

router = APIRouter(prefix="/eventos", tags=["Inscrições"])


@router.post(
    "/{evento_id}/inscricoes/{participante_id}",
    response_model=InscricaoSaida,
    status_code=status.HTTP_201_CREATED,
)
def inscrever(evento_id: int, participante_id: int, db: Session = Depends(obter_sessao)):
    return regras_inscricoes.confirmar_inscricao(db, evento_id, participante_id)


@router.get("/{evento_id}/inscricoes", response_model=list[ParticipanteSaida])
def obter_inscritos(evento_id: int, db: Session = Depends(obter_sessao)):
    return regras_inscricoes.listar_inscritos_do_evento(db, evento_id)

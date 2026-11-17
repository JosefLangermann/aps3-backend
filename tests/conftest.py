import os
import sys
import tempfile

# banco temporário: os testes não mexem no eventos.db de verdade
ARQUIVO_TESTE = os.path.join(tempfile.gettempdir(), "eventos_teste.db")
if os.path.exists(ARQUIVO_TESTE):
    os.remove(ARQUIVO_TESTE)
os.environ["DATABASE_URL"] = f"sqlite:///{ARQUIVO_TESTE}"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)  # limpa o banco entre os testes

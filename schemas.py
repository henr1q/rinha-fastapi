import datetime
from pydantic import BaseModel
from typing import Optional, List


class TransacaoResponse(BaseModel):
    limite: int
    saldo: int
    

class TransacaoRequest(BaseModel):
    valor: int
    tipo: str
    descricao: str

           
class Saldo(BaseModel):
    total: int
    data_extrato: datetime.datetime
    limite: int
    
    
class Transacao(BaseModel):
    valor: int
    tipo: str 
    descricao: Optional[str] = None
    realizada_em: datetime.datetime
    
    
class ExtratoResponse(BaseModel):
    saldo: Saldo
    ultimas_transacoes: List[Transacao] = []
    
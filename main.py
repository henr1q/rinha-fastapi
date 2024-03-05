import datetime as dt
import os
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from psycopg_pool import ConnectionPool
import schemas
import uvicorn


app = FastAPI()

database_host = "db"
database_port = 5432
database_name = "rinha"
database_password = "rinha2024"
database_user = "admin"


pool = ConnectionPool(
    f"host={database_host} port={database_port} dbname={database_name} user={database_user} password={database_password}",
    min_size=14,
    max_size=50,
)
pool.wait()


@app.post("/clientes/{cliente_id}/transacoes", response_model=schemas.TransacaoResponse)
def create_transacao_for_cliente(cliente_id: int, request: schemas.TransacaoRequest):
    
    if cliente_id > 5:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if request.tipo not in ("c", "d"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if not isinstance(request.valor, int):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if not isinstance(request.descricao, str):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    descricao_len = len(request.descricao)
    if descricao_len > 10 or descricao_len < 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    with pool.connection() as conn:
        result = conn.execute(
            f"SELECT saldo, limite FROM clientes WHERE id = {cliente_id} FOR UPDATE"
        ).fetchone()
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        
        if request.tipo not in ("c", "d"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY) 
        
        if request.tipo == "c":
            saldo_futuro = result[0] + request.valor
        else:
            saldo_futuro = result[0] - request.valor

        if saldo_futuro < 0 and abs(saldo_futuro) > result[1]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)        

        conn.execute(
            f"INSERT INTO transacoes (cliente_id, tipo, descricao, valor) VALUES ('{cliente_id}', '{request.tipo}', '{request.descricao}', '{request.valor}')"
        )
        conn.execute(f"UPDATE clientes SET saldo = {saldo_futuro} WHERE id={cliente_id}")
    
        response = schemas.TransacaoResponse(limite=result[1], saldo=saldo_futuro)
        return response

@app.get("/clientes/{cliente_id}/extrato")
def read_cliente(cliente_id: int):
    if cliente_id > 5:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    with pool.connection() as conn:
        saldo = conn.execute(
            f"SELECT saldo, limite FROM clientes WHERE id = {cliente_id}"
        ).fetchone()
        
        if saldo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        
        transacoes_db = conn.execute(
            f"SELECT valor, tipo, descricao, realizada_em FROM transacoes WHERE cliente_id = {cliente_id} ORDER BY realizada_em DESC LIMIT 10"
        ).fetchall()
        
        transacoes = []
        for row in transacoes_db:
            transacoes.append({
                "valor": row[0],
                "tipo": row[1],
                "descricao": row[2],
                "realizada_em": row[3].isoformat().replace("-03:00", "Z"),
            }
            )
        
        saldo_model = schemas.Saldo(total=saldo[0], limite=saldo[1], data_extrato=f'{dt.datetime.now()}Z')
        response = schemas.ExtratoResponse(saldo=saldo_model, ultimas_transacoes=transacoes)
        return response
        

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=9999, reload=True)
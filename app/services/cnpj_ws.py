from __future__ import annotations
import httpx
from typing import Optional

CNPJ_WS_PUBLIC = "https://publica.cnpj.ws/cnpj/{cnpj}"

class CNPJWsError(Exception):
    pass

async def fetch_cnpj_situacao(cnpj_digits: str, timeour_s: float = 6.0) -> str:
    url = CNPJ_WS_PUBLIC.format(cnpj=cnpj_digits)

    try:
        async with httpx.AsyncClient(timeout=timeour_s, follow_redirects=True) as client:
            res = await client.get(url, headers={"Accept": "application/json"})
    except httpx.RequestError as e:
        raise CNPJWsError(f"Falha na conexão com a API CPNJ.ws: {e}") from e
    
    if res.status_code == 404:
        raise CNPJWsError("O CNPJ não foi encontrado na base pública.")
    if res.status_code == 429:
        raise CNPJWsError("Limite de consultas atingido. Tente novamente mais tarde.")
    if res.status_code >= 400:
        raise CNPJWsError(f"Erro da API CNPJ.ws ({res.status_code}).")
    
    data = res.json()
    est = data.get("estabelecimento") or {}
    situ = (est.get("situacao_cadastral") or "").strip()

    if not situ:
        raise CNPJWsError("Não foi possível validar a situação do CNPJ.")
    return situ
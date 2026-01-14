from models.services import Services
from fastapi.responses import JSONResponse

def update_req_status(request, db, payload, new_status):
    if new_status not in ("pending", "in_progress", "completed"):
        return JSONResponse(
            {
                "ok": False,
                "message": "Status inválido fornecido.",
                "new_status": None
            }
        )

    service_id = request.session.get('service_id')

    if not service_id:
        return JSONResponse(
            {
                "ok": False,
                "message": "ID do pedido de serviço não encontrado na sessão.",
                "new_status": None
            }
        )
    
    service = db.query(Services).filter(Services.id == service_id).first()

    if not service:
        return JSONResponse(
            {
                "ok": False,
                "message": "Pedido de serviço não encontrado.",
                "new_status": None
            }
        )
    
    if service.status == "completed":
        return JSONResponse(
            {
                "ok": False,
                "message": "O pedido já foi concluído e não pode ser alterado.",
                "new_status": service.status
            }
        )

    if service.status == new_status:
        return JSONResponse(
            {
                "ok": False,
                "message": "O pedido já está com esse status.",
                "new_status": new_status
            }
        )

    service.status = new_status
    db.commit()
    db.refresh(service)
    return JSONResponse(
        {
            "ok": True,
            "message": "Status do pedido atualizado com sucesso.",
            "new_status": new_status
        }
    )
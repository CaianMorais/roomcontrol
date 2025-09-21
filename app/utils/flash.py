from typing import Literal, List, Tuple, Dict, Any
from fastapi import Request
from fastapi.templating import Jinja2Templates

FlashCategory = Literal["success", "info", "warning", "danger"]

def add_flash_message(request: Request, message: str, category: FlashCategory = "info") -> None:
    flashes: List[Tuple[str, str]] = request.session.get("_flashes", [])
    flashes.append((category, message))
    request.session["_flashes"] = flashes

def consume_flash_messages(request: Request) -> List[Tuple[str, str]]:
    return request.session.pop("_flashes", [])

def render(templates: Jinja2Templates, request: Request, template_name: str,
           context: Dict[str, Any] | None = None, status_code: int = 200):
    
    ctx = {
        "request": request,
        "flash": consume_flash_messages(request),
        "current_hotel": {
            "id": request.session.get("hotel_id"),
            "name": request.session.get("hotel_name")
        }
    }

    if context:
        ctx.update(context)
    return templates.TemplateResponse(template_name, ctx, status_code=status_code)
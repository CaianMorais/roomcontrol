# import de libs built-in
from typing import List, Optional

# import de libs third-party
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.core.security import generate_csrf_token, hash_password, validate_csrf_token, verify_password
from app.models.collaborator import Collaborator
from app.models.hotel import Hotel
from app.schemas.hotel import HotelOut, RegisterHotelStep1In, RegisterHotelStep1Out
from app.services.cnpj_ws import CNPJWsError, fetch_cnpj_situacao
from app.utils.brdocs import is_valid_cnpj, only_digits
from app.utils.flash import add_flash_message, render

router = APIRouter(prefix="/auth", tags=["hotels"])

api_router = APIRouter(
    prefix="/api",
    tags=["hotels"],
    dependencies=[Depends(get_api_access)]
)

templates = Jinja2Templates(directory="app/templates")

@api_router.get("/hotels", response_model=List[HotelOut], summary="Filtrar hotéis (Exclusivo para chave global)")
def get_hotels(
    access: dict = Depends(get_api_access),
    cnpj: Optional[str] = Query(None, description="Filtrar pelo CNPJ do hotel"),
    name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel"),
    db: Session = Depends(get_db)
):
    if not access["is_global"]:
        raise HTTPException(status_code=403, detail="API Key não autorizada")
    
    query = db.query(Hotel)

    if cnpj:
        query = query.filter(Hotel.cnpj.ilike(f"%{cnpj}%"))
    if name:
        query = query.filter(Hotel.name.ilike(f"%{name}%"))

    hotels = query.all()

    if not hotels:
        raise HTTPException(status_code=404, detail="Nenhum hotel encontrado")
    
    return hotels

@router.get("/hotel", response_class=HTMLResponse, include_in_schema=False)
def get_registration_form(request: Request):
    if request.session.get("collaborator_id") or request.session.get("hotel_id"):
        return RedirectResponse(url="/dashboard", status_code=303)
    csrf_token = generate_csrf_token()
    return render(
        templates,
        request,
        "/auth/register.html",
        {
            "request": request,
            "csrf_token": csrf_token
        }
    )

@router.post("/register/check", response_model=RegisterHotelStep1Out, include_in_schema=False)
async def register_check(request: Request, payload: RegisterHotelStep1In, db: Session = Depends(get_db),):
    email = payload.email
    cnpj = payload.cnpj
    if not is_valid_cnpj(cnpj):
        return RegisterHotelStep1Out(ok=False, message="CNPJ inválido")

    cnpj_digits = only_digits(cnpj)
    query = db.query(Hotel).filter(Hotel.cnpj == cnpj_digits).filter(Hotel.email == email)
    if query.first():
        return RegisterHotelStep1Out(ok=False, message="CNPJ ou email já cadastrado")
    
    request.session["reg_email"] = str(email)
    request.session["reg_cnpj"] = cnpj_digits
    
    return RegisterHotelStep1Out(
        ok=True,
        message="Validação bem-sucedida",
        cnpj=cnpj_digits,
        email=email)

@router.get('/register/step2', response_class=HTMLResponse, include_in_schema=False)
def register_step2_partial(request: Request, email: str, cnpj: str):
    csrf_token = generate_csrf_token()
    email = request.session.get("reg_email")
    cnpj_digits = request.session.get("reg_cnpj")
    if not email or not cnpj_digits:
        add_flash_message(request, "Sessão expirada, tente novamente.", "danger")
        return RedirectResponse(url="/auth/register", status_code=303)
    return templates.TemplateResponse("/auth/partials/register_step2.html", {"request": request, "csrf_token": csrf_token, "email": email, "cnpj": cnpj})


@router.post("/register", response_model=HotelOut, include_in_schema=False)
async def register_hotel(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    ddd: str = Form(...),
    phone_number: str = Form(...),
    cnpj: str = Form(...),
    login: str = Form(...),
    address: str = Form(...),
    number: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    form = await request.form()
    csrf_token = form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    sess_email = request.session.get('reg_email')
    sess_cnpj = request.session.get('reg_cnpj')

    if not sess_email or not sess_cnpj:
        add_flash_message(request, "Sessão expirada.", "danger")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    cnpj_digits = only_digits(cnpj)
    if str(email).strip().lower() != str(sess_email).strip().lower() or cnpj_digits != sess_cnpj:
        add_flash_message(request, "Dados não foram validados, adulteração detectada.", "danger")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    if not is_valid_cnpj(cnpj):
        add_flash_message(request, "CNPJ Inválido", "danger")
        return RedirectResponse(url="/auth/hotel", status_code=303)

    db_hotel = db.query(Hotel).filter(Hotel.cnpj == cnpj).first()
    if db_hotel:
        add_flash_message(request, "O hotel já existe em nossos registros", "danger")
        return RedirectResponse(url="/auth/hotel", status_code=303)

    if password != confirm_password:
        add_flash_message(request, "As senhas não conferem.", "danger")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    try:
        situ = await fetch_cnpj_situacao(cnpj_digits)
    except CNPJWsError as e:
        add_flash_message(request, str(e), "danger")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    if situ.lower() != "ativa":
        add_flash_message(request, "CNPJ com situação irregular", "danger")
        return RedirectResponse(url='/auth/hotel', status_code=303)

    hashed_password = bcrypt.hash(password)

    new_hotel = Hotel(
        name=name,
        email=email,
        phone_number=ddd+phone_number,
        cnpj=cnpj,
        login=login,
        address=address + ", " + number,
        city=city,
        state=state,
        zip_code=zip_code,
        password=hashed_password
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)
    add_flash_message(request, "Hotel cadastrado com sucesso!", "success")
    return RedirectResponse(url="/auth/hotel", status_code=303)

@router.post("/login", include_in_schema=False)
async def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):    
    form = await request.form()
    csrf_token = form.get("csrf_token")
    if validate_csrf_token(csrf_token):
        hotel = db.query(Hotel).filter(Hotel.login == login).first()
        if not hotel:
            cnpj_digits = only_digits(login)
            hotel = db.query(Hotel).filter(Hotel.cnpj == cnpj_digits).first()
            if not hotel:
                add_flash_message(request, "Login ou CNPJ não encontrado.", "warning")
                return RedirectResponse(url="/auth/hotel", status_code=303)
    else:
        add_flash_message(request, "Token de segurança inválido, tente novamente", "warning")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    if not verify_password(password, hotel.password):
        add_flash_message(request, "Senha incorreta.", "warning")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    if not hotel.is_active:
        add_flash_message(request, "O hotel está desativado no sistema", "warning")
        return RedirectResponse(url="/auth/hotel", status_code=303)
    
    request.session.clear()
    request.session['hotel_id'] = hotel.id
    request.session['hotel_name'] = hotel.name

    add_flash_message(request, "Login bem-sucedido,", "success")
    response = RedirectResponse(url="/dashboard", status_code=302)
    return response

@router.get("/logout", include_in_schema=False)
def logout(request: Request):
    request.session.pop("hotel_id", None)
    request.session.pop("hotel_name", None)
    request.session.pop("collaborator_id", None)
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@router.get("/collaborator", response_class=HTMLResponse, include_in_schema=False)
def auth_collaborator(
    request: Request,
    db: Session = Depends(get_db)
):
    # verifica se nao tem sessão ativa
    if request.session.get("collaborator_id") or request.session.get("hotel_id"):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    hotels = db.query(Hotel).filter(Hotel.is_active).all()
    
    csrf_token = generate_csrf_token()

    return render(
        templates,
        request,
        "/auth/collaborator_login.html",
        {
            "request": request,
            "hotels": hotels,
            "csrf_token": csrf_token
        }
    )

@router.post("/collaborator", response_class=HTMLResponse, include_in_schema=False)
def login_collaborator(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    hotel: int = Form(...),
    db: Session = Depends(get_db)
):
    # consulta se existe um colaborador com esse username, ativo e não deletado
    collaborator = db.query(Collaborator) \
        .filter(Collaborator.is_active == True) \
        .filter(Collaborator.is_deleted == False) \
        .filter(Collaborator.username == username) \
        .filter(Collaborator.hotel_id == hotel) \
        .first()

    if not collaborator:
        add_flash_message(request, "Usuário não encontrado", "danger")
        return RedirectResponse("/auth/collaborator", status_code=303)

    # verifica se a senha informada bate com a salva
    if not verify_password(password, collaborator.password):
        add_flash_message(request, "Credenciais inválidas", "danger")
        return RedirectResponse("/auth/collaborator", status_code=303)
    
    # força troca de senha se change_password for true
    if collaborator.change_password:
        request.session.clear()
        request.session["force_change_password"] = True
        request.session["hotel_id"] = collaborator.hotel_id
        request.session["hotel_name"] = collaborator.hotel.name
        request.session["collaborator_id"] = collaborator.id
        request.session["collaborator_name"] = collaborator.firstname + " " + collaborator.lastname
        add_flash_message(request, "Redefinição de senha necessária", "info")

        return RedirectResponse(url="/auth/collaborator/change_password", status_code=303)

    # login normal
    request.session.clear()
    request.session["hotel_id"] = collaborator.hotel_id
    request.session["hotel_name"] = collaborator.hotel.name
    request.session["collaborator_id"] = collaborator.id
    request.session["collaborator_name"] = collaborator.firstname + ' ' + collaborator.lastname

    return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/collaborator/change_password", response_class=HTMLResponse, include_in_schema=False)
def change_password_page(request: Request):

    # verifica se realmente tem a exigencia de mudança de senha no request
    # isso evita que a rota seja acessada pelo URL manual
    if not request.session.get("force_change_password"):
        return RedirectResponse("/dashboard", status_code=303)

    return render(
        templates,
        request,
        "auth/collaborator_change_password.html",
        {
            "csrf_token": generate_csrf_token()
        }
    )

@router.post("/collaborator/change_password", response_class=HTMLResponse, include_in_schema=False)
def change_password(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    # valida o token
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url="/auth/collaborator", status_code=303)
    
    # verifica se as senhas informadas sao iguais
    if new_password != confirm_password:
        add_flash_message(request, "As senhas não coincidem", "danger")
        return RedirectResponse("/auth/collaborator/change_password", status_code=303)

    # pega o id do colaborador na sessao
    collaborator_id = request.session.get("collaborator_id")

    # consulta o colaboradora para saber se ele não está inativo ou deletado
    collaborator = db.query(Collaborator) \
    .filter(Collaborator.id == collaborator_id) \
    .filter(Collaborator.is_active) \
    .filter(Collaborator.is_deleted == False) \
    .first()

    # salva a senha e desativa a exigencia de mudança de senha
    collaborator.password = hash_password(new_password)
    collaborator.change_password = False

    db.commit()

    # tira a exigencia da sessao depois de salvar a senha nova no banco
    request.session.pop("force_change_password", None)

    add_flash_message(request, "Senha alterada com sucesso", "success")
    return RedirectResponse("/dashboard", status_code=303)
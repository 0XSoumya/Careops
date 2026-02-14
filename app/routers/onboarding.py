from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Workspace, User, Inventory
from app.utils.security import hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/onboarding")
def onboarding_form(request: Request, db: Session = Depends(get_db)):
    owner_exists = db.query(User).filter(User.role == "owner").first()

    if owner_exists:
        return RedirectResponse("/login", status_code=302)

    return templates.TemplateResponse(
        "onboarding.html",
        {"request": request}
    )


@router.post("/onboarding")
def onboarding_submit(
    request: Request,
    business_name: str = Form(...),
    address_line: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    postal_code: str = Form(...),
    timezone: str = Form(...),
    active_days: str = Form(...),
    active_hours_start: str = Form(...),
    active_hours_end: str = Form(...),
    default_service_duration_minutes: int = Form(...),
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    owner_exists = db.query(User).filter(User.role == "owner").first()

    if owner_exists:
        return RedirectResponse("/login", status_code=302)

    # Create workspace
    workspace = Workspace(
        business_name=business_name,
        address_line=address_line,
        city=city,
        state=state,
        postal_code=postal_code,
        timezone=timezone,
        active_days=active_days,
        active_hours_start=active_hours_start,
        active_hours_end=active_hours_end,
        default_service_duration_minutes=default_service_duration_minutes,
        is_active=True
    )
    db.add(workspace)

    # Create owner user
    owner = User(
        name=name,
        username=username,
        password_hash=hash_password(password),
        role="owner",
        is_active=True
    )
    db.add(owner)

    db.commit()

    # Create default inventory item
    default_item = Inventory(
        name="consumable_1",
        quantity=0,
        threshold=5
    )
    db.add(default_item)
    db.commit()

    # Auto-login owner
    request.session["user_id"] = owner.id

    return RedirectResponse("/", status_code=302)

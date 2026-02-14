from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from app.config import SESSION_SECRET
from app.database import engine, Base, SessionLocal
from app.models import User
from app.routers import auth, onboarding, owner, staff, client

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def onboarding_gate(request, call_next):
    db = SessionLocal()
    owner_exists = db.query(User).filter(User.role == "owner").first()
    db.close()

    if not owner_exists and request.url.path not in ["/onboarding"]:
        return RedirectResponse("/onboarding")

    response = await call_next(request)
    return response


app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(owner.router)
app.include_router(staff.router)
app.include_router(client.router)


@app.get("/")
def root():
    return RedirectResponse("/login", status_code=302)

from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database, auth
from jose import jwt, JWTError
import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_current_user_from_cookie(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(database.User).filter(database.User.username == username).first()
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": "Invalid username or password"})
    
    if user.requires_password_reset:
        reset_token = auth.create_access_token(data={"sub": user.username, "reset": True}, expires_delta=datetime.timedelta(minutes=15))
        return RedirectResponse(url=f"/reset/{reset_token}", status_code=status.HTTP_302_FOUND)

    access_token = auth.create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"request": request})

@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    db_user = db.query(database.User).filter(database.User.username == username).first()
    if db_user:
        return templates.TemplateResponse(request=request, name="register.html", context={"request": request, "error": "Username already registered"})
    
    hashed_password = auth.get_password_hash(password)
    new_user = database.User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@app.get("/reset-request", response_class=HTMLResponse)
async def reset_request_form(request: Request):
    return templates.TemplateResponse(request=request, name="reset_request.html", context={"request": request})

@app.post("/reset-request")
async def reset_request(request: Request, email: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.username == email).first()
    if user:
        token = auth.create_access_token(
            data={"sub": user.username, "reset": True},
            expires_delta=datetime.timedelta(minutes=15)
        )
        # TODO: send token via email service
    return templates.TemplateResponse(
        request=request,
        name="reset_request.html",
        context={"request": request, "msg": "If the email exists, a reset link was sent."}
    )

@app.get("/reset/{token}", response_class=HTMLResponse)
async def reset_form(request: Request, token: str):
    return templates.TemplateResponse(request=request, name="reset_form.html", context={"request": request, "token": token})

@app.post("/reset")
async def reset_password(token: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        if payload.get("reset") is not True:
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(database.User).filter(database.User.username == payload["sub"]).first()
    user.hashed_password = auth.get_password_hash(password)
    user.requires_password_reset = False
    db.commit()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.post("/admin/force-global-reset")
async def force_global_reset(db: Session = Depends(database.get_db)):
    # This represents Phase 1: Global Invalidation
    db.query(database.User).update({database.User.requires_password_reset: True})
    db.commit()
    return {"message": "Global password reset forced for all users. Attacker sessions invalidated."}


@app.get("/mail", response_class=HTMLResponse)
async def mail(request: Request, user=Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request=request, name="mail.html", context={"request": request, "user": user})

@app.get("/finance", response_class=HTMLResponse)
async def finance(request: Request, user=Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request=request, name="finance.html", context={"request": request, "user": user})

@app.get("/category/{name}", response_class=HTMLResponse)
async def category(request: Request, name: str, user=Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request=request, name="category.html", context={"request": request, "category_name": name.capitalize(), "user": user})

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", user=Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse(request=request, name="search.html", context={"request": request, "query": q, "user": user})

class Article(BaseModel):
    title: str
    source: str
    imageUrl: str

class Hero(BaseModel):
    title: str
    summary: str
    imageUrl: str

class MarketItem(BaseModel):
    symbol: str
    change: str
    positive: bool

class NewsResponse(BaseModel):
    hero: Hero
    articles: list[Article]
    market: list[MarketItem]
    trending: list[str]

@app.get("/api/news", response_model=NewsResponse)
async def get_news():
    data = {
        "hero": {
            "title": "Global Markets Rally Following Tech Earnings Reports",
            "summary": "Technology sector leads the charge as major indices hit new highs today.",
            "imageUrl": "/static/images/market_rally_1777221873858.png"
        },
        "articles": [
            {
                "title": "Electric Vehicle Sales Surge in Q3",
                "source": "Auto News",
                "imageUrl": "/static/images/ev_car_1777221897968.png"
            },
            {
                "title": "New Discoveries in Quantum Computing",
                "source": "Science Daily",
                "imageUrl": "/static/images/quantum_computer_1777221917184.png"
            },
            {
                "title": "Championship Finals Set for This Weekend",
                "source": "Sports Update",
                "imageUrl": "/static/images/sports_finals_1777221934464.png"
            },
            {
                "title": "Top 10 Travel Destinations for Next Year",
                "source": "Lifestyle",
                "imageUrl": "/static/images/travel_destination_1777221952495.png"
            }
        ],
        "market": [
            {"symbol": "S&P 500", "change": "+1.2%", "positive": True},
            {"symbol": "Dow Jones", "change": "+0.8%", "positive": True},
            {"symbol": "Nasdaq", "change": "+1.5%", "positive": True}
        ],
        "trending": [
            "1. Tech Earnings",
            "2. Climate Summit",
            "3. New Smartphone Release",
            "4. Award Show Winners",
            "5. Weekend Weather"
        ]
    }
    return data

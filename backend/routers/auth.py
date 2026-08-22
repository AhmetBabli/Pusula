import logging
import secrets

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.config import settings
from backend.database import get_db
from backend.models.user import UserProfile
from backend.models.inbox import EmailAccount
from backend.auth import create_user_token, get_current_user, hash_password, verify_password
from backend.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    code: str  # Google Identity Services'in auth-code (popup) akışından gelen tek kullanımlık kod


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("10/hour")
def register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı oluşturur ve otomatik giriş yapar (token döner)."""
    existing = db.query(UserProfile).filter(UserProfile.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")

    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalı")

    user = UserProfile(
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        # Kayıt sonrası bilgi formu doldurulana kadar sahte varsayılan
        # değerlerle (ör. "Doğuş Üniversitesi") eşleştirme/üretim yapılmasın.
        university=None,
        department=None,
        target_sectors=[],
        skills=[],
        languages=[],
        onboarding_completed=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_user_token(user)
    return {
        "access_token": token,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
    }


@router.post("/google", response_model=TokenResponse)
@limiter.limit("15/minute")
def google_auth(request: Request, req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Google ile giriş/kayıt: frontend'den gelen tek kullanımlık auth-code'u
    Google'ın token endpoint'inde değişip kullanıcıyı doğrular. Kullanıcı Gmail
    gönderim iznini (gmail.send) de verdiyse, aynı hesabı doğrudan e-posta
    göndermek için bağlar — ayrıca uygulama şifresi girmesine gerek kalmaz."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google girişi bu sunucuda henüz yapılandırılmadı.")

    try:
        token_res = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": req.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                # Google Identity Services'in popup (auth-code) akışında redirect_uri
                # gerçek bir sayfa değil, sabit "postmessage" değeridir.
                "redirect_uri": "postmessage",
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
    except requests.RequestException as e:
        logger.error(f"Google token değişimi başarısız (ağ hatası): {e}")
        raise HTTPException(status_code=502, detail="Google ile bağlantı kurulamadı.")

    if not token_res.ok:
        logger.error(f"Google token değişimi reddedildi: {token_res.status_code} {token_res.text}")
        raise HTTPException(status_code=400, detail="Google doğrulaması başarısız oldu.")

    tokens = token_res.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    granted_scope = tokens.get("scope", "")

    try:
        userinfo_res = requests.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=10
        )
    except requests.RequestException as e:
        logger.error(f"Google kullanıcı bilgisi isteği başarısız (ağ hatası): {e}")
        raise HTTPException(status_code=502, detail="Google ile bağlantı kurulamadı.")

    if not userinfo_res.ok:
        raise HTTPException(status_code=400, detail="Google kullanıcı bilgisi alınamadı.")

    info = userinfo_res.json()
    email = info.get("email")
    if not email or not info.get("email_verified"):
        raise HTTPException(status_code=400, detail="Google hesabınızın e-postası doğrulanmamış.")
    full_name = info.get("name") or email.split("@")[0]

    user = db.query(UserProfile).filter(UserProfile.email == email).first()
    if not user:
        user = UserProfile(
            email=email,
            full_name=full_name,
            # Bu hesap sadece Google ile giriş yapabilir; tahmin edilemeyecek
            # rastgele bir şifre hash'lenip saklanır (e-posta/şifre girişi kapalı kalır).
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            university=None,
            department=None,
            target_sectors=[],
            skills=[],
            languages=[],
            onboarding_completed=False,
        )
        db.add(user)
        db.flush()

    # Kullanıcı Gmail gönderim iznini de verdiyse (refresh_token + gmail.send scope),
    # bu hesabı otomatik olarak e-posta gönderimi için bağla — uygulama şifresi gerekmez.
    # Not: inbox.py'deki add_account ile aynı sahiplik kuralı — e-posta zaten
    # BAŞKA bir kullanıcıya bağlıysa sessizce el değiştirmesine izin verme
    # (aksi halde biri A'nın app-password ile bağladığı bir kutuyu, aynı adresle
    # Google girişi yaparak kendi hesabına çalabilir).
    if refresh_token and GMAIL_SEND_SCOPE in granted_scope:
        account = db.query(EmailAccount).filter(EmailAccount.email == email).first()
        if account and account.user_id != user.id:
            logger.warning(
                f"Google OAuth Gmail bağlama atlandı: {email} zaten başka bir kullanıcıya bağlı (user_id={account.user_id})."
            )
        else:
            if not account:
                account = EmailAccount(user_id=user.id, email=email)
                db.add(account)
            account.user_id = user.id
            account.auth_method = "oauth"
            account.oauth_refresh_token = refresh_token
            account.is_active = True

    db.commit()
    db.refresh(user)

    token = create_user_token(user)
    return {
        "access_token": token,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """E-posta + şifre ile giriş yapar, JWT token döner."""
    user = db.query(UserProfile).filter(UserProfile.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre")

    token = create_user_token(user)
    return {
        "access_token": token,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
    }


@router.post("/logout", status_code=204)
def logout(current_user: UserProfile = Depends(get_current_user), db: Session = Depends(get_db)):
    """Kullanıcının token_version'ını artırır — daha önce üretilmiş tüm JWT'ler
    (tüm cihazlar dahil) bu andan itibaren geçersiz olur."""
    current_user.token_version += 1
    db.commit()

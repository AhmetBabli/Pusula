"""
Kariyer Ajanı 2.0 — Agents Router
4 ajan için birleşik HTTP + WebSocket tetikleyici endpoint'ler.
Tüm ağır işlemler BackgroundTasks'e atılır, WS üzerinden progress push edilir.
"""
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import UserProfile
from backend.models.job import Job
from backend.models.event import Event
from backend.models.cv import CV
from backend.config import settings
from backend.auth import get_current_user
from backend.rate_limiter import limiter
from backend.routers.ws import push_agent_event
from backend.routers.events import EventCreate

router = APIRouter(prefix="/agents", tags=["Ajan Merkezi"])
logger = logging.getLogger(__name__)

# ─── Pydantic Modelleri ─────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="'İstanbul React Staj' gibi")
    location: str = Field(default="Türkiye")
    session_id: str = Field(..., description="WebSocket session ID")

class EventSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="'İstanbul kariyer fuarı' gibi")
    location: str = Field(default="Türkiye")
    session_id: str = Field(..., description="WebSocket session ID")

class BuildCvRequest(BaseModel):
    session_id: str
    target_job_id: Optional[int] = None
    extra_experience: str = ""

class InterviewStartRequest(BaseModel):
    session_id: str
    job_id: Optional[int] = None
    company_name: str = ""
    job_title: str = ""
    job_description: str = ""
    round_type: Literal["technical", "hr", "mixed"] = "mixed"

class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_id: int
    question: str
    question_type: str
    hint: str
    answer: str
    company_name: str
    job_title: str

class OutreachRequest(BaseModel):
    session_id: str
    company_name: str = Field(..., min_length=2)
    job_title: str = ""
    job_description: str = ""

class StrategyRequest(BaseModel):
    session_id: str
    target_job: str = Field(..., min_length=3)
    target_location: str = "Global"

# ─── Background Task İşlevleri ──────────────────────────────────────────────

async def _run_web_search(session_id: str, query: str, location: str, db_user_id: int):
    from backend.ai.web_search_agent import search_jobs_live
    from backend.database import SessionLocal
    from backend.schemas.agent_contracts import ScrapedJobContract

    await push_agent_event(session_id, "web_search", "running", "Gemini Grounding aktif...", 10, user_id=db_user_id)
    try:
        with SessionLocal() as db:
            requester = db.query(UserProfile).filter(UserProfile.id == db_user_id).first()
            requester_api_key = requester.gemini_api_key if requester else None

        jobs = await search_jobs_live(query, location, api_key=requester_api_key)
        await push_agent_event(session_id, "web_search", "running", f"{len(jobs)} ilan bulundu, DB'ye kaydediliyor...", 70, user_id=db_user_id)

        saved = 0
        with SessionLocal() as db:
            for raw in jobs:
                try:
                    validated = ScrapedJobContract.model_validate(raw)
                    existing = db.query(Job).filter(Job.source_url == validated.source_url).first()
                    if not existing:
                        db.add(Job(**validated.to_job_dict()))
                        saved += 1
                except Exception:
                    pass
            db.commit()

        await push_agent_event(
            session_id, "web_search", "done",
            f"Tamamlandı: {saved} yeni ilan kaydedildi.", 100,
            data={"saved_count": saved, "found_count": len(jobs)},
            user_id=db_user_id,
        )
    except Exception as e:
        logger.error(f"[Agents] web_search hatası: {e}")
        await push_agent_event(session_id, "web_search", "failed", str(e), 0, user_id=db_user_id)


async def _run_event_search(session_id: str, query: str, location: str, db_user_id: int):
    from backend.ai.web_search_agent import search_events_live
    from backend.database import SessionLocal

    await push_agent_event(session_id, "event_search", "running", "Gemini Grounding aktif...", 10, user_id=db_user_id)
    try:
        with SessionLocal() as db:
            requester = db.query(UserProfile).filter(UserProfile.id == db_user_id).first()
            requester_api_key = requester.gemini_api_key if requester else None
            user_context = (
                f"Aday Profili: {requester.university or ''} — {requester.department or ''}. "
                f"Beceriler: {', '.join(requester.skills or [])}."
                if requester else ""
            )

        events = await search_events_live(query, location, user_context=user_context, api_key=requester_api_key)
        await push_agent_event(session_id, "event_search", "running", f"{len(events)} etkinlik bulundu, DB'ye kaydediliyor...", 70, user_id=db_user_id)

        saved = 0
        with SessionLocal() as db:
            for raw in events:
                source_url = (raw.get("source_url") or "").strip()
                if not source_url:
                    continue  # source_url DB'de unique+NOT NULL — güvenilir dedup için linksiz sonuçları atla
                try:
                    existing = db.query(Event).filter(Event.source_url == source_url).first()
                    if existing:
                        continue
                    validated = EventCreate.model_validate({**raw, "source": raw.get("source", "gemini_grounding")})
                    event = Event(**validated.model_dump())
                    event.relevance_score = raw.get("relevance_score")
                    event.relevance_reason = raw.get("relevance_reason")
                    db.add(event)
                    saved += 1
                except Exception:
                    continue
            db.commit()

        await push_agent_event(
            session_id, "event_search", "done",
            f"Tamamlandı: {saved} yeni etkinlik kaydedildi.", 100,
            data={"saved_count": saved, "found_count": len(events)},
            user_id=db_user_id,
        )
    except Exception as e:
        logger.error(f"[Agents] event_search hatası: {e}")
        await push_agent_event(session_id, "event_search", "failed", str(e), 0, user_id=db_user_id)


async def _run_build_cv(session_id: str, user_id: int, target_job_id: Optional[int], extra_exp: str):
    from backend.ai.cv_architect_agent import fetch_github_repos, build_ats_cv, export_cv_to_pdf
    from backend.database import SessionLocal

    await push_agent_event(session_id, "cv_architect", "running", "Kullanıcı profili okunuyor...", 5, user_id=user_id)
    try:
        with SessionLocal() as db:
            user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
            if not user:
                raise ValueError("Kullanıcı profili bulunamadı.")
            job = db.query(Job).filter(Job.id == target_job_id).first() if target_job_id else None

        await push_agent_event(session_id, "cv_architect", "running", "GitHub repoları çekiliyor...", 15, user_id=user_id)
        repos = await fetch_github_repos(user.github_url or "")

        await push_agent_event(session_id, "cv_architect", "running", f"{len(repos)} repo analiz edildi. CV üretiliyor...", 50, user_id=user_id)
        cv_markdown = await build_ats_cv(
            user_name=user.full_name,
            email=user.email,
            university=user.university,
            department=user.department,
            skills=user.skills or [],
            github_repos=repos,
            target_job_title=job.title if job else "",
            target_job_description=job.description if job else "",
            extra_experience=extra_exp,
            api_key=user.gemini_api_key,
        )

        await push_agent_event(session_id, "cv_architect", "running", "PDF oluşturuluyor...", 80, user_id=user_id)

        settings.CV_STORE_PATH.mkdir(parents=True, exist_ok=True)
        pdf_path = str(settings.CV_STORE_PATH / f"cv_architect_{session_id}.pdf")
        if not export_cv_to_pdf(cv_markdown, pdf_path):
            # export_cv_to_pdf hatayı zaten loglayıp False döndürüyor — burada
            # sessizce devam edip "başarılı" göstermek yerine gerçek hatayı yansıtıyoruz.
            raise RuntimeError("PDF oluşturulamadı.")

        # DB'ye kaydet
        with SessionLocal() as db:
            user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
            cv_obj = CV(
                user_id=user_id,
                title=f"Architect CV — {job.company if job else 'Genel'}",
                variant_type="architect",
                extracted_text=cv_markdown,
                file_path=pdf_path,
                is_ai_generated=True,
            )
            db.add(cv_obj)
            db.commit()
            db.refresh(cv_obj)
            cv_id = cv_obj.id

        await push_agent_event(
            session_id, "cv_architect", "done",
            "CV tamamlandı! PDF indirilebilir.", 100,
            # pdf_path artık istemciye gönderilmiyor — sunucudaki dosya yolunu
            # ifşa etmenin bir anlamı yok, indirme artık cv_id ile
            # /cvs/{cv_id}/pdf üzerinden (sahiplik kontrollü) yapılıyor.
            data={"cv_id": cv_id, "session_id": session_id},
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"[Agents] cv_architect hatası: {e}")
        await push_agent_event(session_id, "cv_architect", "failed", str(e), 0, user_id=user_id)


async def _run_outreach(session_id: str, company_name: str, job_title: str, job_desc: str, user_id: int):
    from backend.database import SessionLocal
    from backend.ai.gemini_client import _call_model_async_json

    await push_agent_event(session_id, "outreach", "running", "Profil ve CV okunuyor...", 10, user_id=user_id)
    try:
        with SessionLocal() as db:
            user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
            cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.is_default.desc()).first()
            user_api_key = user.gemini_api_key if user else ""

        cv_text = cv.extracted_text[:1500] if cv else ""
        skills_str = ", ".join(user.skills or [])

        await push_agent_event(session_id, "outreach", "running", "Taslaklar oluşturuluyor...", 40, user_id=user_id)

        # Cold email + LinkedIn DM'i tek istekte üretiyoruz — ayrı ayrı
        # gönderilen iki ardışık çağrı, aynı dakika içinde Gemini'nin
        # ücretsiz kotasında sık sık "high demand" (503) hatasına yol
        # açıyordu; birleştirmek hem daha güvenilir hem de kotayı yarıya indiriyor.
        prompt = f"""Profesyonel bir kariyer danışmanısın.
"{company_name}" şirketine "{job_title}" pozisyonu için başvuran bir aday için iki ayrı metin hazırla.

Aday: {user.full_name}, {user.university} {user.department}
Beceriler: {skills_str}
İlan: {job_desc[:300]}
CV özeti: {cv_text[:300]}

1) cold_email: Etkileyici, kişiselleştirilmiş bir cold email. Max 200 kelime, resmi ama samimi, spesifik değer önerisi sun, "Sayın İlgili," ile başla.
2) linkedin_dm: LinkedIn'de {company_name} çalışanına gönderilecek kısa DM taslağı. Max 80 kelime, kişisel ve doğal.

Şu JSON formatında yanıt ver: {{"cold_email": "...", "linkedin_dm": "..."}}"""

        result = await _call_model_async_json(prompt, api_key=user_api_key)
        cold_email = (result.get("cold_email") or "").strip()
        linkedin_dm = (result.get("linkedin_dm") or "").strip()

        await push_agent_event(
            session_id, "outreach", "done", "Taslaklar hazır!", 100,
            data={"cold_email": cold_email, "linkedin_dm": linkedin_dm},
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"[Agents] outreach hatası: {e}")
        await push_agent_event(session_id, "outreach", "failed", str(e), 0, user_id=user_id)


async def _run_strategy(session_id: str, target_job: str, target_location: str, user_id: int):
    from backend.ai.strategy_agent import generate_career_strategy
    from backend.ai.cv_architect_agent import fetch_github_repos
    from backend.database import SessionLocal

    await push_agent_event(session_id, "strategy", "running", "Profil ve GitHub analizi yapılıyor...", 10, user_id=user_id)
    try:
        with SessionLocal() as db:
            user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
            if not user: raise ValueError("Profil bulunamadı.")
            
        repos = await fetch_github_repos(user.github_url or "")
        repo_summary = ", ".join([f"{r['name']} ({', '.join(r.get('languages') or [])})" for r in repos[:10]])

        await push_agent_event(session_id, "strategy", "running", "Yol haritası ve pazar analizi oluşturuluyor...", 50, user_id=user_id)
        
        strategy = await generate_career_strategy(
            current_skills=user.skills or [],
            current_title=user.department or "Junior",
            target_job=target_job,
            target_location=target_location,
            github_analysis=repo_summary,
            linkedin_data=user.linkedin_data or "",
            api_key=user.gemini_api_key,
        )

        await push_agent_event(
            session_id, "strategy", "done", "Kariyer stratejin hazır!", 100,
            data=strategy,
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"[Agents] strategy hatası: {e}")
        await push_agent_event(session_id, "strategy", "failed", str(e), 0, user_id=user_id)


# ─── HTTP Endpoints ─────────────────────────────────────────────────────────

@router.post("/search", status_code=202)
async def search_jobs(
    req: SearchRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
):
    """Gemini Grounding ile canlı iş ilanı arama."""
    background_tasks.add_task(_run_web_search, req.session_id, req.query, req.location, current_user.id)
    return {"status": "started", "session_id": req.session_id}


@router.post("/search-events", status_code=202)
async def search_events(
    req: EventSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
):
    """Gemini Grounding ile canlı kariyer etkinliği arama."""
    background_tasks.add_task(_run_event_search, req.session_id, req.query, req.location, current_user.id)
    return {"status": "started", "session_id": req.session_id}


@router.post("/build-cv", status_code=202)
async def build_cv(
    req: BuildCvRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
):
    """GitHub analizi + ATS CV üretimi + PDF export."""
    background_tasks.add_task(_run_build_cv, req.session_id, current_user.id, req.target_job_id, req.extra_experience)
    return {"status": "started", "session_id": req.session_id}


@router.post("/interview/start")
async def interview_start(
    req: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Şirkete, pozisyona ve adayın bölümüne özel mülakat soruları üretir.
    Soru sayısı sabit değildir — Gemini pozisyonun karmaşıklığına göre karar verir.
    AI araştırması geçici olarak kullanılamıyorsa (kota/503), mülakat pratiğini
    tamamen durdurmak yerine genel yedek sorulara düşer ve bunu 'personalized:
    false' ile açıkça belirtir."""
    from backend.ai.interview_coach_agent import generate_questions, get_fallback_questions
    from backend.exceptions import AIServiceError

    job_title = req.job_title
    job_desc = req.job_description
    company = req.company_name

    if req.job_id:
        job = db.query(Job).filter(Job.id == req.job_id).first()
        if job:
            job_title = job.title
            job_desc = job.description or ""
            company = company or job.company

    # Kullanıcı bağlamını çek (Kişiselleştirilmiş mülakat için)
    cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.is_default.desc()).first()
    cv_text = cv.extracted_text[:1000] if cv else ""
    skills_str = ", ".join(current_user.skills or [])
    user_context = f"Aday Özeti: {current_user.full_name}, Bölüm: {current_user.department}. Beceriler: {skills_str}. CV Özeti: {cv_text}"

    try:
        questions = await generate_questions(
            job_title=job_title or "Staj",
            job_description=job_desc,
            company_name=company or "Genel",
            round_type=req.round_type,
            user_context=user_context,
            api_key=current_user.gemini_api_key,
        )
        personalized = True
    except AIServiceError as e:
        logger.warning(f"[InterviewStart] AI soru üretimi başarısız, genel yedek sorulara düşülüyor: {e}")
        questions = get_fallback_questions(req.round_type)
        personalized = False

    return {"session_id": req.session_id, "questions": questions, "total": len(questions), "personalized": personalized}


@router.post("/interview/answer")
async def interview_answer(req: InterviewAnswerRequest, current_user: UserProfile = Depends(get_current_user)):
    """Tek bir cevabı değerlendirir."""
    from backend.ai.interview_coach_agent import evaluate_answer

    result = await evaluate_answer(
        question=req.question,
        answer=req.answer,
        question_type=req.question_type,
        hint=req.hint,
        job_title=req.job_title,
        company_name=req.company_name,
        api_key=current_user.gemini_api_key,
    )
    return {"question_id": req.question_id, "evaluation": result}


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.post("/tts")
@limiter.limit("60/hour")
async def text_to_speech(
    request: Request,
    req: TtsRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """Mülakat sorusunu sesli okumak için MP3 üretir. Uygulama genelinde tek
    bir Google Cloud TTS anahtarı kullanılır (kullanıcı bazlı değil)."""
    from backend.ai.tts_client import synthesize_speech

    audio_bytes = await synthesize_speech(req.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/outreach", status_code=202)
async def generate_outreach(
    req: OutreachRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
):
    """Cold email + LinkedIn DM taslağı üretir (Background Task)."""
    background_tasks.add_task(_run_outreach, req.session_id, req.company_name, req.job_title, req.job_description, current_user.id)
    return {"status": "started", "session_id": req.session_id}

@router.post("/outreach/sync")
async def generate_outreach_sync(
    req: OutreachRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Cold email + LinkedIn DM taslağı üretir (Senkron)."""
    from google import genai

    cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.is_default.desc()).first()
    cv_text = cv.extracted_text[:1500] if cv else ""
    skills_str = ", ".join(current_user.skills or [])

    client = genai.Client(api_key=current_user.gemini_api_key or settings.GEMINI_API_KEY)
    email_prompt = f"""Profesyonel bir kariyer danışmanısın.
"{req.company_name}" şirketine "{req.job_title}" pozisyonu için etkileyici, kişiselleştirilmiş bir cold email yaz.
Aday: {current_user.full_name}, {current_user.university} {current_user.department}
Beceriler: {skills_str}
İlan: {req.job_description[:300]}
CV özeti: {cv_text[:300]}

Kurallar: Max 200 kelime, resmi ama samimi, spesifik değer önerisi sun, "Sayın İlgili," ile başla."""

    email_resp = await client.aio.models.generate_content(model=settings.GEMINI_MODEL, contents=email_prompt)
    cold_email = email_resp.text.strip()

    dm_prompt = f"""LinkedIn'de {req.company_name} çalışanına gönderilecek kısa DM taslağı yaz.
Aday: {current_user.full_name}, {current_user.department}
Pozisyon: {req.job_title}
Max 80 kelime, kişisel ve doğal."""
    dm_resp = await client.aio.models.generate_content(model=settings.GEMINI_MODEL, contents=dm_prompt)
    linkedin_dm = dm_resp.text.strip()

    return {"cold_email": cold_email, "linkedin_dm": linkedin_dm}


@router.post("/strategy", status_code=202)
async def career_strategy(
    req: StrategyRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
):
    """Kariyer yol haritası ve strateji üretir."""
    background_tasks.add_task(_run_strategy, req.session_id, req.target_job, req.target_location, current_user.id)
    return {"status": "started", "session_id": req.session_id}


# Not: CV PDF indirme ucu buradan kaldırıldı — session_id istemcinin kendi
# seçtiği bir değerdi, sahiplik doğrulaması yapılmıyordu (IDOR). Artık
# GET /cvs/{cv_id}/pdf üzerinden, sahiplik kontrolüyle sunuluyor (bkz. cv.py).

"""
Kariyer Ajanı 2.0 — CV Architect Agent
GitHub API → repo analizi → ATS-uyumlu CV üretimi → PDF export.
Pure Python, sistem bağımlılığı yok (fpdf2 kullanır).
"""
import re
import logging
from typing import Optional
import httpx
from google import genai
from google.genai import types
from backend.config import settings

logger = logging.getLogger("CvArchitectAgent")

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def fetch_github_repos(github_url: str) -> list[dict]:
    """
    GitHub URL'den kullanıcı adını çıkarır ve herkese açık repolarını listeler.
    Returns: [{"name": "...", "description": "...", "languages": [...], "stars": 0}]
    """
    # URL'den username çıkar: https://github.com/ahmetbabli → ahmetbabli
    match = re.search(r'github\.com/([^/?\s]+)', github_url or "")
    if not match:
        logger.warning("[CvArchitect] Geçerli GitHub URL'si bulunamadı.")
        return []

    username = match.group(1)
    logger.info(f"[CvArchitect] GitHub repoları çekiliyor: {username}")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API}/users/{username}/repos",
                headers=HEADERS,
                params={"sort": "updated", "per_page": 10},
            )
            resp.raise_for_status()
            repos_raw = resp.json()

        enriched = []
        for repo in repos_raw:
            if repo.get("fork"):
                continue  # Fork'ları atla — asıl çalışmalar burada
            # Dil dağılımını çek
            langs = []
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    lang_resp = await client.get(repo["languages_url"], headers=HEADERS)
                    if lang_resp.status_code == 200:
                        langs = list(lang_resp.json().keys())
            except Exception:
                pass

            enriched.append({
                "name": repo["name"],
                "description": repo.get("description") or "",
                "stars": repo.get("stargazers_count", 0),
                "languages": langs,
                "url": repo["html_url"],
                "topics": repo.get("topics", []),
            })

        logger.info(f"[CvArchitect] {len(enriched)} repo analiz edildi.")
        return enriched
    except Exception as e:
        logger.error(f"[CvArchitect] GitHub API hatası: {e}")
        return []


def extract_tech_stack(repos: list[dict]) -> list[str]:
    """Repo listesinden benzersiz teknoloji yığınını çıkarır."""
    all_langs: dict[str, int] = {}
    all_topics: set[str] = set()

    for repo in repos:
        for lang in repo.get("languages", []):
            all_langs[lang] = all_langs.get(lang, 0) + 1
        for topic in repo.get("topics", []):
            all_topics.add(topic.replace("-", " ").title())

    # En çok kullanılan 10 dil
    top_langs = [k for k, _ in sorted(all_langs.items(), key=lambda x: x[1], reverse=True)][:10]
    return list(dict.fromkeys(top_langs + list(all_topics)))[:15]


async def build_ats_cv(
    user_name: str,
    email: str,
    university: str,
    department: str,
    skills: list[str],
    github_repos: list[dict],
    target_job_title: str = "",
    target_job_description: str = "",
    extra_experience: str = "",
    api_key: Optional[str] = None,
) -> str:
    """
    GitHub verisi + kullanıcı profili + hedef ilan → ATS-uyumlu CV Markdown.
    """
    tech_stack = extract_tech_stack(github_repos)
    all_skills = list(dict.fromkeys(skills + tech_stack))

    repo_summaries = "\n".join(
        f"- **{r['name']}** ({', '.join(r['languages'][:3])}): {r['description']}"
        for r in github_repos[:5]
    )

    prompt = f"""Sen uzman bir kariyer danışmanı ve ATS optimizasyon uzmanısın.
Aşağıdaki bilgilerle ATS filtrelerini %90+ geçecek Türkçe/İngilizce karma bir CV oluştur.

**Aday Bilgileri:**
Ad: {user_name}
E-posta: {email}
Üniversite: {university} — {department}
Beceriler: {', '.join(all_skills)}
Ek Deneyim: {extra_experience or 'Belirtilmemiş'}

**GitHub Projeleri:**
{repo_summaries or 'GitHub bağlantısı yok.'}

**Hedef Pozisyon:** {target_job_title or 'Staj / Entry-level'}
**İlan Açıklaması:** {target_job_description[:1000] if target_job_description else 'Belirtilmedi'}

**Kurallar:**
1. Markdown formatı: ##, ###, - madde işaretleri
2. Bölümler: Summary, Education, Technical Skills, Projects, Experience (varsa)
3. ATS için ilan anahtar kelimelerini doğal biçimde yerleştir
4. Ölçülebilir başarılar ekle (repo yıldızı, teknoloji çeşitliliği vb.)
5. Maksimum 600 kelime

Sadece CV metnini döndür, ek açıklama ekleme."""

    try:
        client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
        response = await client.aio.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"[CvArchitect] CV üretim hatası: {e}")
        # AI şu an ulaşılamıyor (ör. kota) — elimizdeki gerçek verilerle (AI
        # formatlaması olmadan) yine de eksiksiz, sunulabilir bir CV üret.
        # Önceki sürüm burada sadece ad+e-posta+beceri döndürüyordu, üniversite/
        # bölüm/GitHub projeleri gibi zaten elimizde olan veriyi bile atlıyordu.
        sections = [f"# {user_name}", email]
        if university or department:
            sections.append(f"\n## Eğitim\n{university or ''} — {department or ''}".strip())
        if all_skills:
            sections.append(f"\n## Teknik Beceriler\n{', '.join(all_skills)}")
        if extra_experience:
            sections.append(f"\n## Deneyim\n{extra_experience}")
        if github_repos:
            sections.append(f"\n## Projeler\n{repo_summaries}")
        sections.append(
            "\n\n*Not: AI servisi şu an geçici olarak ulaşılamaz durumda olduğu için "
            "bu CV otomatik biçimlendirme olmadan hazırlandı. Birazdan tekrar "
            "deneyerek daha ayrıntılı bir sürüm üretebilirsiniz.*"
        )
        return "\n".join(sections)


def _sanitize_for_pdf(text: str) -> str:
    """Helvetica çekirdek fontu Latin-1/WinAnsi ile sınırlı — Türkçe'ye özgü
    ı/İ/ğ/Ğ/ş/Ş karakterleri bu kümede yok ve fpdf2 bunlarla karşılaşınca sert
    hata fırlatıp PDF üretimini tamamen çökertiyordu (Gemini'nin ürettiği her
    gerçek Türkçe CV bu karakterlerden en az birini içerdiği için bu, PDF
    indirmenin fiilen hiç çalışmadığı anlamına geliyordu). ç/ö/ü zaten
    Latin-1'de olduğu için dokunulmuyor; geri kalan (beklenmeyen) karakterler
    PDF'i çökertmek yerine sessizce '?' olur."""
    replacements = {"ı": "i", "İ": "I", "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S"}
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def export_cv_to_pdf(markdown_text: str, output_path: str) -> bool:
    """
    Markdown CV metnini PDF'e dönüştürür.
    fpdf2 kullanır — saf Python, sistem bağımlılığı yok.
    """
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos

        markdown_text = _sanitize_for_pdf(markdown_text)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_margins(20, 20, 20)

        for line in markdown_text.split("\n"):
            line = line.strip()
            if not line:
                pdf.ln(4)
                continue

            if line.startswith("## "):
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(30, 30, 30)
                pdf.ln(3)
                pdf.cell(0, 8, line[3:], ln=True)
                pdf.set_draw_color(100, 100, 100)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(2)
            elif line.startswith("### "):
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 7, line[4:], ln=True)
            elif line.startswith("# "):
                pdf.set_font("Helvetica", "B", 18)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 12, line[2:], ln=True, align="C")
            elif line.startswith("- "):
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 60, 60)
                # **bold** işaretlemesini temizle
                clean = re.sub(r'\*\*(.*?)\*\*', r'\1', line[2:])
                pdf.cell(5, 6, chr(149), ln=False)
                pdf.multi_cell(0, 6, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 60, 60)
                clean = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
                pdf.multi_cell(0, 6, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.output(output_path)
        logger.info(f"[CvArchitect] PDF oluşturuldu: {output_path}")
        return True
    except Exception as e:
        logger.error(f"[CvArchitect] PDF export hatası: {e}")
        return False

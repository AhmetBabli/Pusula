"""
CV Architect PDF export regresyon testi.

fpdf2'de multi_cell()'in varsayılan davranışı (new_x=XPos.RIGHT, new_y=YPos.TOP)
eski FPDF'den farklı — imleç bir sonraki satıra/sol kenar boşluğuna otomatik
dönmüyor. Bu yüzden art arda gelen madde işaretli (- ...) satırlarda, ikinci
maddenin imleci hâlâ sayfanın sağ kenarındaydı ve "Not enough horizontal
space to render a single character" hatasıyla PDF üretimi sessizce
başarısız oluyordu (export_cv_to_pdf hatayı yutup False dönüyordu, ve
_run_build_cv bu False'u hiç kontrol etmeden "Tamamlandı" diyordu — kullanıcı
arayüzde "Tamamlandı" görüp indirmeye çalışınca 404 alıyordu).
"""
import asyncio

import httpx

from backend.ai.cv_architect_agent import export_cv_to_pdf, fetch_github_repos


def test_export_cv_to_pdf_succeeds_with_multiple_bullet_lines(tmp_path):
    markdown = """# Test Kullanıcı

## Deneyim
- Doğuş Üniversitesi öğrencisi, Yönetim Bilişim Sistemleri bölümü.
- Türkçe karakterler: güneş, şarkı, çalışma, öğrenci, üniversite.
- Üçüncü madde de burada olsun.

## Beceriler
- Python
- SQL
- Docker
"""
    output_path = str(tmp_path / "test_cv.pdf")

    result = export_cv_to_pdf(markdown, output_path)

    assert result is True
    import os
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 500  # gerçek bir PDF gövdesi, boş/kırık dosya değil


def test_export_cv_to_pdf_single_line_still_works(tmp_path):
    output_path = str(tmp_path / "single.pdf")
    result = export_cv_to_pdf("- tek satırlık madde", output_path)
    assert result is True


def test_fetch_github_repos_skips_forks_and_fetches_languages(monkeypatch):
    """Regresyon testi: her repo için ayrı bir AsyncClient açıp sırayla
    (N sıralı round-trip) bekleyen eski uygulama, tek client + asyncio.gather
    ile paralel hale getirildi (audit — N+1 istek bulgusu). Bu test davranışın
    doğruluğunu (fork'lar atlanıyor, her repoya doğru diller eşleniyor,
    bir repo'nun dil isteği başarısız olsa bile diğerleri etkilenmiyor)
    doğruluyor — zamanlama/paralellik değil."""
    calls = []

    def _response(status_code, json_body=None, *, req_url):
        return httpx.Response(status_code, json=json_body, request=httpx.Request("GET", req_url))

    async def fake_get(self, url, headers=None, params=None):
        calls.append(url)
        if url.endswith("/repos"):
            return _response(200, [
                {"name": "repo-a", "fork": False, "stargazers_count": 3,
                 "html_url": "https://github.com/u/repo-a", "topics": [],
                 "languages_url": "https://api.github.com/repos/u/repo-a/languages"},
                {"name": "repo-b-fork", "fork": True, "stargazers_count": 0,
                 "html_url": "https://github.com/u/repo-b-fork", "topics": [],
                 "languages_url": "https://api.github.com/repos/u/repo-b-fork/languages"},
                {"name": "repo-c", "fork": False, "stargazers_count": 1,
                 "html_url": "https://github.com/u/repo-c", "topics": [],
                 "languages_url": "https://api.github.com/repos/u/repo-c/languages"},
            ], req_url=url)
        if "repo-a" in url:
            return _response(200, {"Python": 100}, req_url=url)
        if "repo-c" in url:
            # Bu repo için dil isteği başarısız olsun — diğer repoyu etkilememeli.
            return _response(500, req_url=url)
        return _response(404, req_url=url)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    repos = asyncio.run(fetch_github_repos("https://github.com/testuser"))

    assert [r["name"] for r in repos] == ["repo-a", "repo-c"]  # fork hariç
    assert repos[0]["languages"] == ["Python"]
    assert repos[1]["languages"] == []  # başarısız istek çökmek yerine boş liste döndü
    assert not any("repo-b-fork" in c for c in calls)  # fork'un dil URL'i hiç çağrılmadı

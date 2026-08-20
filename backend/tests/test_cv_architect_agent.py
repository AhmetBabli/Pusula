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
from backend.ai.cv_architect_agent import export_cv_to_pdf


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

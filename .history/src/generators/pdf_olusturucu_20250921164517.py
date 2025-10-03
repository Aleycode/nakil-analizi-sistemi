"""
PDF raporu oluşturucu modülü
"""

import fnmatch
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from reportlab.lib.pagesizes import A4, A3, letter
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    from PyPDF2 import PdfMerger, PdfReader

    PDF_MERGER_AVAILABLE = True
except ImportError:
    PDF_MERGER_AVAILABLE = False

from ..core.config import PDF_CONFIG_DOSYA_YOLU

logger = logging.getLogger(__name__)


class PDFOlusturucu:
    """PDF rapor oluşturucu sınıfı"""

    def __init__(self):
        """PDF oluşturucu başlatır ve konfigürasyonu yükler"""
        self.config = self._config_yukle()
        self.styles = getSampleStyleSheet()
        self._turkce_font_ekle()
        self._ozel_stiller_olustur()

    def _config_yukle(self) -> Dict:
        """JSON config dosyasından PDF ayarlarını yükler"""
        try:
            with open(PDF_CONFIG_DOSYA_YOLU, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"PDF config dosyası okunamadı: {e}")
            # Varsayılan config döndür
            return {
                "pdf_olustur": True,
                "pdf_dosya_adi": "nakil_analiz_raporu_{tarih}.pdf",
                "font_ayarlari": {
                    "default_font": "Helvetica",
                    "fallback_font": "Helvetica",
                    "encoding": "utf-8",
                },
                "sayfa_ayarlari": {"boyut": "A4", "kenar_boslugu": 0.5},
                "grafik_sirasi": [],
                "ek_metinler": [],
            }

    def _turkce_font_ekle(self):
        """Türkçe karakter desteği için font ekler"""
        try:
            font_ayarlari = self.config.get("font_ayarlari", {})
            # Proje kök dizinini al (src/generators'dan 2 seviye yukarı)
            proje_kok = Path(__file__).parent.parent.parent

            # DejaVu Sans fontlarını kaydet
            font_dosyalari = [
                ("DejaVuSans", "fonts/DejaVuSans.ttf"),
                ("DejaVuSans-Bold", "fonts/DejaVuSans-Bold.ttf"),
                ("DejaVuSans-Oblique", "fonts/DejaVuSans-Oblique.ttf"),
            ]

            fonts_registered = False
            for font_name, font_path in font_dosyalari:
                font_full_path = proje_kok / font_path
                if font_full_path.exists():
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, str(font_full_path)))
                        fonts_registered = True
                        logger.info(f"{font_name} fontu başarıyla yüklendi")
                    except Exception as e:
                        logger.warning(f"{font_name} fontu yüklenemedi: {e}")
                else:
                    logger.warning(f"Font dosyası bulunamadı: {font_full_path}")

            # Font mapping ekle
            if fonts_registered:
                try:
                    from reportlab.lib.fonts import addMapping

                    addMapping("DejaVuSans", 0, 0, "DejaVuSans")  # normal
                    addMapping("DejaVuSans", 1, 0, "DejaVuSans-Bold")  # bold
                    addMapping("DejaVuSans", 0, 1, "DejaVuSans-Oblique")  # italic
                    addMapping("DejaVuSans", 1, 1, "DejaVuSans-Bold")  # bold-italic
                    self.default_font = "DejaVuSans"
                    logger.info("DejaVu Sans font ailesi başarıyla yapılandırıldı")
                except Exception as e:
                    logger.warning(f"Font mapping başarısız: {e}")
                    self.default_font = "Helvetica"
            else:
                self.default_font = font_ayarlari.get("fallback_font", "Helvetica")
                logger.warning(
                    f"Türkçe fontlar yüklenemedi, {self.default_font} kullanılacak"
                )

        except Exception as e:
            logger.error(f"Font yükleme hatası: {e}")
            self.default_font = "Helvetica"

    def _ozel_stiller_olustur(self):
        """Özel PDF stilleri oluşturur"""
        try:
            # Kapak sayfası başlık stili
            self.baslik_stili = ParagraphStyle(
                "KapakBaslik",
                parent=self.styles["Normal"],
                fontName=self.default_font,
                fontSize=24,
                textColor=HexColor("#2c3e50"),
                alignment=TA_CENTER,
                spaceAfter=20,
            )

            # Alt başlık stili
            self.alt_baslik_stili = ParagraphStyle(
                "AltBaslik",
                parent=self.styles["Normal"],
                fontName=self.default_font,
                fontSize=16,
                textColor=HexColor("#34495e"),
                alignment=TA_CENTER,
                spaceAfter=15,
            )

            # Normal metin stili
            self.metin_stili = ParagraphStyle(
                "Metin",
                parent=self.styles["Normal"],
                fontName=self.default_font,
                fontSize=12,
                textColor=HexColor("#2c3e50"),
                alignment=TA_LEFT,
                spaceAfter=10,
            )

            logger.info("PDF stilleri başarıyla oluşturuldu")

        except Exception as e:
            logger.error(f"PDF stili oluşturma hatası: {e}")
            # Varsayılan stiller kullan
            self.baslik_stili = self.styles["Title"]
            self.alt_baslik_stili = self.styles["Heading1"]
            self.metin_stili = self.styles["Normal"]

    def pdf_olustur(self, grafik_dizini: Path, gun_tarihi: str) -> str:
        """
        PDF raporu oluşturur

        Args:
            grafik_dizini: Grafik dosyalarının bulunduğu dizin
            gun_tarihi: Analiz günü (YYYY-MM-DD formatında)

        Returns:
            str: Oluşturulan PDF dosyasının yolu (başarısızsa boş string)
        """
        try:
            if not self.config.get("pdf_olustur", False):
                logger.info("PDF oluşturma config'de kapalı")
                return ""

            # PDF dosya adını oluştur
            pdf_dosya_adi = self.config.get(
                "pdf_dosya_adi", "nakil_analiz_raporu_{tarih}.pdf"
            )
            pdf_dosya_adi = pdf_dosya_adi.format(tarih=gun_tarihi)

            # Geçici PDF dosyası (içerik kısmı)
            temp_pdf_dosyasi = grafik_dizini / f"temp_{pdf_dosya_adi}"
            cikti_dosyasi = grafik_dizini / pdf_dosya_adi

            # İçerik PDF'ini oluştur
            doc = self._pdf_dokument_olustur(temp_pdf_dosyasi)

            # İçerik elementlerini hazırla (kapak olmadan)
            story = []

            # Giriş sayfası ekle (nakil bekleyen raporu)
            story.extend(self._giris_sayfasi_olustur(gun_tarihi))

            # Grafikleri bul ve sırala
            grafik_dosyalari = self._grafikleri_bul_ve_sirala(grafik_dizini)

            if not grafik_dosyalari:
                logger.warning("Hiç grafik dosyası bulunamadı")
                return ""

            # Grafikleri PDF'e ekle
            story.extend(self._grafik_elemanlari_olustur(grafik_dosyalari))

            # Ek metinleri ekle
            story.extend(self._ek_metinler_olustur())

            # İçerik PDF'ini oluştur
            doc.build(story)

            # Kapak PDF'i ile birleştir
            final_pdf_path = self._kapak_ile_birlestir(temp_pdf_dosyasi, cikti_dosyasi)

            # Geçici dosyayı sil
            if temp_pdf_dosyasi.exists():
                temp_pdf_dosyasi.unlink()

            if final_pdf_path:
                logger.info(f"PDF raporu başarıyla oluşturuldu: {final_pdf_path}")
                return str(final_pdf_path)
            else:
                logger.error("PDF birleştirme başarısız")
                return ""

        except Exception as e:
            logger.error(f"PDF oluşturma hatası: {e}")
            return ""

    def _pdf_dokument_olustur(self, dosya_yolu: Path) -> SimpleDocTemplate:
        """PDF doküment objesi oluşturur"""
        sayfa_ayarlari = self.config.get("sayfa_ayarlari", {})

        # Sayfa boyutunu belirle
        boyut_map = {"A4": A4, "A3": A3, "Letter": letter}
        sayfa_boyutu = boyut_map.get(sayfa_ayarlari.get("boyut", "A4"), A4)

        # Kenar boşluklarını belirle
        kenar_boslugu = sayfa_ayarlari.get("kenar_boslugu", 0.5) * inch

        return SimpleDocTemplate(
            str(dosya_yolu),
            pagesize=sayfa_boyutu,
            rightMargin=kenar_boslugu,
            leftMargin=kenar_boslugu,
            topMargin=kenar_boslugu,
            bottomMargin=kenar_boslugu,
        )

    def _kapak_sayfasi_olustur(self) -> List:
        """Kapak sayfası elementlerini oluşturur - Hazır PDF kapak kullanır"""
        elements = []

        try:
            # Assets klasöründeki hazır kapak PDF'ini kullan
            proje_kok = Path(__file__).parent.parent.parent
            kapak_dosyasi = proje_kok / "assets" / "kapak.pdf"

            if kapak_dosyasi.exists():
                # PDF kapağı mevcut dosyada birleştirmek yerine
                # Basit bir placeholder metni ekle
                # Ana PDF oluşturma işleminde kapak dosyası ayrıca birleştirilecek
                logger.info(f"Kapak dosyası bulundu: {kapak_dosyasi}")

                # Kapak ayrı dosya olarak birleştirilecek, burada boş sayfa gereksiz
            else:
                # Kapak dosyası yoksa basit metin kapak oluştur
                logger.warning(f"Kapak dosyası bulunamadı: {kapak_dosyasi}")

                elements.append(Spacer(1, 2 * inch))
                elements.append(Paragraph("NAKİL ANALİZ RAPORU", self.baslik_stili))
                elements.append(Spacer(1, 0.5 * inch))

                bugunku_tarih = datetime.now().strftime("%d/%m/%Y")
                elements.append(
                    Paragraph(f"Analiz Tarihi: {bugunku_tarih}", self.alt_baslik_stili)
                )
                elements.append(Spacer(1, 2 * inch))
                elements.append(
                    Paragraph("T.C. Sağlık Bakanlığı", self.alt_baslik_stili)
                )
                elements.append(PageBreak())

        except Exception as e:
            logger.error(f"Kapak sayfası oluşturma hatası: {e}")
            # Hata durumunda basit kapak ekle
            elements.append(Spacer(1, 2 * inch))
            elements.append(Paragraph("NAKİL ANALİZ RAPORU", self.baslik_stili))
            elements.append(PageBreak())

        return elements

    def _kapak_ile_birlestir(self, icerik_pdf: Path, cikti_pdf: Path) -> str:
        """Kapak PDF'i ile içerik PDF'ini birleştirir"""
        try:
            proje_kok = Path(__file__).parent.parent.parent
            kapak_dosyasi = proje_kok / "assets" / "kapak.pdf"

            if not kapak_dosyasi.exists():
                logger.warning(f"Kapak dosyası bulunamadı: {kapak_dosyasi}")
                # Kapak yoksa sadece içerik dosyasını kopyala
                import shutil

                shutil.copy2(icerik_pdf, cikti_pdf)
                return str(cikti_pdf)

            if not PDF_MERGER_AVAILABLE:
                logger.warning("PyPDF2 bulunamadı, kapak birleştirilemedi")
                import shutil

                shutil.copy2(icerik_pdf, cikti_pdf)
                return str(cikti_pdf)

            # PDF birleştirme işlemi
            merger = PdfMerger()

            # Önce kapak sayfasını ekle
            with open(kapak_dosyasi, "rb") as kapak_file:
                merger.append(kapak_file)

            # Sonra içerik sayfalarını ekle
            with open(icerik_pdf, "rb") as icerik_file:
                merger.append(icerik_file)

            # Birleştirilmiş PDF'yi kaydet
            with open(cikti_pdf, "wb") as output_file:
                merger.write(output_file)

            merger.close()

            logger.info(f"Kapak ve içerik başarıyla birleştirildi: {cikti_pdf}")
            return str(cikti_pdf)

        except Exception as e:
            logger.error(f"PDF birleştirme hatası: {e}")
            # Hata durumunda sadece içerik dosyasını kullan
            try:
                import shutil

                shutil.copy2(icerik_pdf, cikti_pdf)
                return str(cikti_pdf)
            except Exception as copy_error:
                logger.error(f"İçerik kopyalama hatası: {copy_error}")
                return ""

    def _grafikleri_bul_ve_sirala(self, grafik_dizini: Path) -> List[Tuple[Path, str]]:
        """Grafik dosyalarını bulur ve config'e göre sıralar"""
        try:
            # Tüm PNG dosyalarını bul
            tum_grafikler = list(grafik_dizini.glob("*.png"))

            if not tum_grafikler:
                logger.warning(
                    f"Grafik dizininde PNG dosyası bulunamadı: {grafik_dizini}"
                )
                return []

            sirali_grafikler = []
            grafik_sirasi = self.config.get("grafik_sirasi", [])

            # Config'deki sıraya göre grafikleri ekle
            for grafik_config in grafik_sirasi:
                pattern = grafik_config.get("desen", "")
                baslik = grafik_config.get("baslik", "")

                # Pattern'e uyan grafikleri bul
                eslesen_grafikler = [
                    g for g in tum_grafikler if fnmatch.fnmatch(g.name, pattern)
                ]

                for grafik in eslesen_grafikler:
                    sirali_grafikler.append((grafik, baslik if baslik else grafik.stem))
                    # Bu grafiği listeden çıkar (tekrar eklememek için)
                    if grafik in tum_grafikler:
                        tum_grafikler.remove(grafik)

            # Kalan grafikleri ekle (config'de belirtilmemiş olanlar) - SADECE CONFIG VARSA SKIPLA
            if (
                grafik_sirasi
            ):  # Config'de grafik sırası varsa, sadece config'dekileri kullan
                logger.info(
                    f"Config'de {len(grafik_sirasi)} desen var, {len(sirali_grafikler)} grafik eşleşti"
                )
            else:
                # Config yoksa tüm grafikleri ekle
                for grafik in tum_grafikler:
                    sirali_grafikler.append((grafik, grafik.stem))

            logger.info(f"{len(sirali_grafikler)} grafik dosyası bulundu ve sıralandı")
            return sirali_grafikler

        except Exception as e:
            logger.error(f"Grafik bulma ve sıralama hatası: {e}")
            return []

    def _grafik_elemanlari_olustur(
        self, grafik_dosyalari: List[Tuple[Path, str]]
    ) -> List:
        """Grafik elementlerini oluşturur - Config'den ayarları alır"""
        elements = []
        sayfa_sayaci = 0
        grafik_ayarlari = self.config.get("grafik_ayarlari", {})
        max_grafik_per_sayfa = grafik_ayarlari.get("maksimum_grafik_per_sayfa", 4)  # 4'e çıkarıldı

    def _grafik_elemanlari_olustur(
        self, grafik_dosyalari: List[Tuple[Path, str]]
    ) -> List:
        """Grafik elementlerini 2x2 grid düzeninde oluşturur"""
        elements = []
        grafik_ayarlari = self.config.get("grafik_ayarlari", {})
        max_grafik_per_sayfa = grafik_ayarlari.get("maksimum_grafik_per_sayfa", 4)
        
        # Grafikleri gruplar halinde işle (4'er 4'er)
        for i in range(0, len(grafik_dosyalari), max_grafik_per_sayfa):
            grafik_grubu = grafik_dosyalari[i:i + max_grafik_per_sayfa]
            
            # 2x2 tablo oluştur
            table_data = []
            
            # İlk satır (2 grafik)
            if len(grafik_grubu) >= 2:
                row1_col1 = self._grafik_hucre_olustur(grafik_grubu[0])
                row1_col2 = self._grafik_hucre_olustur(grafik_grubu[1])
                table_data.append([row1_col1, row1_col2])
            elif len(grafik_grubu) == 1:
                row1_col1 = self._grafik_hucre_olustur(grafik_grubu[0])
                table_data.append([row1_col1, ""])
            
            # İkinci satır (2 grafik daha)
            if len(grafik_grubu) >= 4:
                row2_col1 = self._grafik_hucre_olustur(grafik_grubu[2])
                row2_col2 = self._grafik_hucre_olustur(grafik_grubu[3])
                table_data.append([row2_col1, row2_col2])
            elif len(grafik_grubu) == 3:
                row2_col1 = self._grafik_hucre_olustur(grafik_grubu[2])
                table_data.append([row2_col1, ""])
            
            # Tablo oluştur
            if table_data:
                from reportlab.platypus import Table, TableStyle
                from reportlab.lib import colors
                
                table = Table(table_data, colWidths=[4.2*inch, 4.2*inch])
                table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 0.2 * inch))
                
                # Sayfa sonu (her 4 grafikten sonra)
                if i + max_grafik_per_sayfa < len(grafik_dosyalari):
                    elements.append(PageBreak())
        
        return elements

    def _grafik_hucre_olustur(self, grafik_data: Tuple[Path, str]):
        """Tek bir grafik hücresi oluşturur"""
        try:
            grafik_dosyasi, eski_baslik = grafik_data
            
            from reportlab.platypus import Table
            
            # Grafik config'ini bul
            grafik_config = self._grafik_config_bul(grafik_dosyasi)
            baslik = grafik_config.get("baslik", eski_baslik)
            
            # Teknik başlıkları temizle
            if baslik and ("_" in baslik or "threshold" in baslik.lower() or "butun" in baslik.lower()):
                baslik = ""
            
            # Grafik boyutunu hesapla
            grafik_genislik, grafik_yukseklik = self._grafik_boyutu_hesapla(grafik_dosyasi)
            
            # Hücre içeriği
            cell_content = []
            
            # Başlık varsa ekle
            if baslik:
                from reportlab.platypus import Paragraph
                cell_content.append([Paragraph(f"<b>{baslik}</b>", self.metin_stili)])
            
            # Grafik ekle
            cell_content.append([Image(str(grafik_dosyasi), width=grafik_genislik, height=grafik_yukseklik)])
            
            # Mini tablo olarak döndür
            mini_table = Table(cell_content, colWidths=[4.0*inch])
            return mini_table
            
        except Exception as e:
            logger.error(f"Grafik hücre oluşturma hatası ({grafik_dosyasi}): {e}")
            return ""

        return elements

    def _ara_metin_ekle(
        self, elements: List, pozisyon: str, grafik_pattern: str = ""
    ) -> None:
        """Belirli pozisyonlarda ara metin ekler"""
        try:
            ara_metinler = self.config.get("ara_metinler", [])

            for ara_metin in ara_metinler:
                if ara_metin.get("pozisyon") == pozisyon:
                    metin = ara_metin.get("metin", "")
                    stil_adi = ara_metin.get("stil", "ara_metin")

                    if metin:
                        # Stil belirle
                        if stil_adi == "baslik":
                            stil = self.alt_baslik_stili
                        else:
                            stil = self.metin_stili

                        elements.append(Spacer(1, 0.3 * inch))
                        elements.append(Paragraph(metin, stil))
                        elements.append(Spacer(1, 0.2 * inch))

        except Exception as e:
            logger.error(f"Ara metin ekleme hatası: {e}")

    def _pdf_grafik_metni_ekle(self, elements: List, grafik_dosyasi: Path) -> None:
        """PDF için grafik metinlerini config'den ekler"""
        try:
            metin_ayarlari = self.config.get("grafik_metin_ayarlari", {})

            if not metin_ayarlari.get("metin_ekleme_aktif", False):
                return

            dosya_adi = grafik_dosyasi.stem

            # Önce özel metinleri kontrol et
            ozel_metinler = metin_ayarlari.get("ozel_metinler", {})
            metin_config = None

            for desen, config_item in ozel_metinler.items():
                desen_temiz = desen.replace("*", "")
                if desen_temiz in dosya_adi:
                    metin_config = config_item
                    break

            # Sonra grafik özelliklerini kontrol et
            if not metin_config:
                grafik_ozellikleri = metin_ayarlari.get("grafik_ozellikleri", {})
                for desen, config_item in grafik_ozellikleri.items():
                    desen_temiz = desen.replace("*", "")
                    if desen_temiz in dosya_adi:
                        metin_config = config_item
                        break

            # Metin belirle
            if metin_config:
                metin = metin_config.get("metin", "")
                konum = metin_config.get("konum", "alt")
                font_boyutu = metin_config.get("font_boyutu", 10)
                font_kalin = metin_config.get("font_kalin", False)
            else:
                # Genel metin kullan
                metin = metin_ayarlari.get("genel_metin", "")
                konum = metin_ayarlari.get("metin_konumu", "alt")
                font_boyutu = metin_ayarlari.get("font_boyutu", 10)
                font_kalin = metin_ayarlari.get("font_kalin", False)

            if metin:
                # Font stilini belirle
                if font_kalin:
                    stil_metin = f"<b>{metin}</b>"
                else:
                    stil_metin = metin

                # Metni ekle
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph(stil_metin, self.metin_stili))

        except Exception as e:
            logger.warning(f"PDF grafik metin ekleme hatası: {e}")

    def _grafik_config_bul(self, grafik_dosyasi: Path) -> dict:
        """Grafik dosyası için config ayarlarını bulur"""
        try:
            grafik_sirasi = self.config.get("grafik_sirasi", [])
            dosya_adi = grafik_dosyasi.name

            for grafik_config in grafik_sirasi:
                pattern = grafik_config.get("desen", "")
                if pattern and pattern in dosya_adi:
                    return grafik_config

            # Config bulunamazsa varsayılan döndür
            return {"baslik": grafik_dosyasi.stem, "aciklama": "", "sayfa_sonu": False}

        except Exception as e:
            logger.error(f"Grafik config bulma hatası: {e}")
            return {"baslik": "", "aciklama": "", "sayfa_sonu": False}

    def _grafik_boyutu_hesapla(self, grafik_dosyasi: Path) -> Tuple[float, float]:
        """Grafik için uygun boyut hesaplar - 4'lü grid için optimize edildi"""
        try:
            from PIL import Image as PILImage

            # Grafik dosyasını aç ve boyutlarını al
            with PILImage.open(grafik_dosyasi) as img:
                orijinal_genislik, orijinal_yukseklik = img.size

            # 4'lü grid için daha büyük boyutlar (2x2 düzen)
            max_genislik = 4.0 * inch  # Her grafik için daha geniş
            max_yukseklik = 3.2 * inch  # Daha yüksek

            # Aspect ratio'yu koru
            aspect_ratio = orijinal_genislik / orijinal_yukseklik

            if aspect_ratio > 1:  # Yatay grafik
                grafik_genislik = min(max_genislik, 3.5 * inch)
                grafik_yukseklik = grafik_genislik / aspect_ratio
            else:  # Dikey grafik
                grafik_yukseklik = min(max_yukseklik, 2.8 * inch)
                grafik_genislik = grafik_yukseklik * aspect_ratio

            # Boyutları kontrol et
            if grafik_yukseklik > max_yukseklik:
                grafik_yukseklik = max_yukseklik
                grafik_genislik = grafik_yukseklik * aspect_ratio

            if grafik_genislik > max_genislik:
                grafik_genislik = max_genislik
                grafik_yukseklik = grafik_genislik / aspect_ratio

            return grafik_genislik, grafik_yukseklik

        except Exception as e:
            logger.warning(f"Grafik boyutu hesaplama hatası ({grafik_dosyasi}): {e}")
            # 4'lü grid için varsayılan boyut
            return 4.0 * inch, 3.2 * inch

    def _ek_metinler_olustur(self) -> List:
        """Ek metin elementlerini oluşturur"""
        elements = []
        ek_metinler = self.config.get("ek_metinler", [])

        for metin_config in ek_metinler:
            try:
                pozisyon = metin_config.get("pozisyon", "")
                if pozisyon == "sayfa_sonu":
                    metin = metin_config.get("metin", "")
                    if metin:
                        elements.append(Spacer(1, 0.5 * inch))
                        elements.append(Paragraph(metin, self.metin_stili))

            except Exception as e:
                logger.error(f"Ek metin oluşturma hatası: {e}")

        return elements

    def _giris_sayfasi_olustur(self, gun_tarihi: str) -> List:
        """Giriş sayfasını oluşturur (nakil bekleyen raporu içeriği)"""
        elements = []
        try:
            giris_config = self.config.get("giris_sayfasi", {})

            # Başlık ekle
            baslik_config = giris_config.get("baslik", {})
            if baslik_config:
                baslik_text = baslik_config.get("metin", "GÜNLÜK NAKİL DURUM RAPORU")
                baslik_paragraph = Paragraph(baslik_text, self.baslik_stili)
                elements.append(baslik_paragraph)
                elements.append(Spacer(1, 20))

            # Nakil bekleyen raporu dosyasını oku
            kaynak_dosya = giris_config.get(
                "kaynak_dosya", "nakil_bekleyen_raporu_{tarih}.txt"
            )
            kaynak_dosya = kaynak_dosya.format(tarih=gun_tarihi)

            # Rapor dizinini bul
            rapor_dizini = Path("data/reports") / gun_tarihi
            rapor_dosyasi = rapor_dizini / kaynak_dosya

            if rapor_dosyasi.exists():
                # Dosyayı oku ve UTF-8 encoding ile aç
                try:
                    with open(rapor_dosyasi, "r", encoding="utf-8") as f:
                        icerik = f.read()
                except UnicodeDecodeError:
                    # UTF-8 başarısızsa ISO-8859-9 (Turkish) ile dene
                    try:
                        with open(rapor_dosyasi, "r", encoding="iso-8859-9") as f:
                            icerik = f.read()
                    except UnicodeDecodeError:
                        # Son çare olarak Windows-1254 dene
                        with open(rapor_dosyasi, "r", encoding="windows-1254") as f:
                            icerik = f.read()

                # İçeriği profesyonel formatta düzenle
                satirlar = icerik.strip().split("\n")

                # İçeriği analiz et ve kategorize et
                baslik_bulundu = False
                istatistik_bolumu = False

                for satir in satirlar:
                    satir = satir.strip()
                    if not satir:
                        continue

                    # Ayırıcı çizgileri atla (=== ve ---)
                    if satir.startswith("=") or satir.startswith("-") or satir == "":
                        if not baslik_bulundu:
                            # İlk ayırıcıdan sonra boşluk ekle
                            elements.append(Spacer(1, 15))
                            baslik_bulundu = True
                        continue

                    # Ana başlık
                    if "RAPORU" in satir.upper() and not baslik_bulundu:
                        continue  # Ana başlığı atla, zaten giriş sayfası başlığı var

                    # Tarih bilgisi
                    elif satir.startswith("Tarih:"):
                        tarih_text = satir.replace("Tarih:", "").strip()
                        elements.append(
                            Paragraph(
                                f"<b>Rapor Tarihi:</b> {tarih_text}", self.metin_stili
                            )
                        )
                        elements.append(Spacer(1, 12))

                    # Ana istatistikler
                    elif "Nakil Bekleyen Toplam Talep:" in satir:
                        elements.append(
                            Paragraph(
                                "<b>GENEL İSTATİSTİKLER</b>", self.alt_baslik_stili
                            )
                        )
                        elements.append(Spacer(1, 8))

                        # Toplam talep sayısını al
                        toplam = satir.split(":")[-1].strip()
                        elements.append(
                            Paragraph(
                                f"• <b>Toplam Nakil Bekleyen Talep:</b> {toplam}",
                                self.metin_stili,
                            )
                        )

                    elif "İl İçi Talep:" in satir:
                        il_ici = satir.split(":")[-1].strip()
                        elements.append(
                            Paragraph(
                                f"• <b>İl İçi Talep:</b> {il_ici}", self.metin_stili
                            )
                        )

                    elif "İl Dışı Talep:" in satir:
                        il_disi = satir.split(":")[-1].strip()
                        elements.append(
                            Paragraph(
                                f"• <b>İl Dışı Talep:</b> {il_disi}", self.metin_stili
                            )
                        )
                        elements.append(Spacer(1, 12))

                    # Yoğun bakım istatistikleri
                    elif "Nakil Bekleyen Yoğun Bakım Toplam Talep:" in satir:
                        elements.append(
                            Paragraph(
                                "<b>YOĞUN BAKIM İSTATİSTİKLERİ</b>",
                                self.alt_baslik_stili,
                            )
                        )
                        elements.append(Spacer(1, 8))

                        yb_toplam = satir.split(":")[-1].strip()
                        elements.append(
                            Paragraph(
                                f"• <b>Toplam Yoğun Bakım Talebi:</b> {yb_toplam}",
                                self.metin_stili,
                            )
                        )

                    elif "İl İçi Yb Talep:" in satir:
                        yb_il_ici = satir.split(":")[-1].strip()
                        elements.append(
                            Paragraph(
                                f"• <b>İl İçi Yoğun Bakım:</b> {yb_il_ici}",
                                self.metin_stili,
                            )
                        )

                    elif "İl Dışı Yb Talep:" in satir:
                        yb_il_disi = satir.split(":")[-1].strip()
                        elements.append(
                            Paragraph(
                                f"• <b>İl Dışı Yoğun Bakım:</b> {yb_il_disi}",
                                self.metin_stili,
                            )
                        )
                        elements.append(Spacer(1, 8))

                    # Entübe/Non-entübe detayları
                    elif "Entübe" in satir or "Non-Entübe" in satir:
                        # Bu satırları alt kategoriler olarak işle
                        if "İl İçi" in satir and "Entübe" in satir:
                            entube_sayi = satir.split(":")[-1].strip()
                            entube_tip = (
                                "Entübe" if "Non-" not in satir else "Non-Entübe"
                            )
                            elements.append(
                                Paragraph(
                                    f"  - <b>İl İçi {entube_tip}:</b> {entube_sayi}",
                                    self.metin_stili,
                                )
                            )
                        elif "İl Dışı" in satir and "Entübe" in satir:
                            entube_sayi = satir.split(":")[-1].strip()
                            entube_tip = (
                                "Entübe" if "Non-" not in satir else "Non-Entübe"
                            )
                            elements.append(
                                Paragraph(
                                    f"  - <b>İl Dışı {entube_tip}:</b> {entube_sayi}",
                                    self.metin_stili,
                                )
                            )

                # Süre analizi bilgilerini ekle (JSON'dan oku)
                elements = self._sure_analizini_ekle(elements, rapor_dizini)

                # Son boşluk
                elements.append(Spacer(1, 20))
            else:
                # Dosya bulunamazsa uyarı mesajı
                uyari_text = f"Nakil bekleyen raporu bulunamadı: {rapor_dosyasi}"
                elements.append(Paragraph(uyari_text, self.metin_stili))
                logger.warning(uyari_text)

            # Sayfa sonu (sadece içerik varsa)
            if len(elements) > 2:  # Başlık + Spacer'dan fazlası varsa
                elements.append(PageBreak())

        except Exception as e:
            logger.error(f"Giriş sayfası oluşturma hatası: {e}")
            elements.append(
                Paragraph(f"Giriş sayfası oluşturma hatası: {e}", self.metin_stili)
            )
            if len(elements) > 1:  # Hata mesajından fazlası varsa
                elements.append(PageBreak())

        return elements

    def _sure_analizini_ekle(self, elements: List, rapor_dizini: Path) -> List:
        """
        JSON rapor dosyasından süre analizi bilgilerini okuyup PDF'e ekler
        
        Args:
            elements: PDF elementleri listesi
            rapor_dizini: Rapor dizini (tarih klasörü)
            
        Returns:
            Güncellenmiş elementler listesi
        """
        try:
            # JSON dosyasını bul
            json_dosyalari = list(rapor_dizini.glob("kapsamli_gunluk_analiz_*.json"))
            if not json_dosyalari:
                return elements
                
            json_dosya = json_dosyalari[0]  # İlk bulunan dosyayı al
            
            with open(json_dosya, 'r', encoding='utf-8') as f:
                analiz_data = json.load(f)
            
            # Süre analizleri var mı kontrol et
            if 'sure_analizleri' not in analiz_data:
                return elements
                
            sure_data = analiz_data['sure_analizleri']
            
            # Süre analizi başlığı
            elements.append(
                Paragraph(
                    "<b>SÜRE ANALİZLERİ</b>", 
                    self.alt_baslik_stili
                )
            )
            elements.append(Spacer(1, 8))
            
            # Genel süre bilgileri
            elements.append(
                Paragraph(
                    f"• <b>Toplam analiz edilen vaka:</b> {sure_data.get('toplam_vaka', 0)}",
                    self.metin_stili,
                )
            )
            elements.append(
                Paragraph(
                    f"• <b>Yer bulunmuş vaka:</b> {sure_data.get('tamamlanan_vaka', 0)}",
                    self.metin_stili,
                )
            )
            elements.append(
                Paragraph(
                    f"• <b>Halen bekleyen vaka:</b> {sure_data.get('bekleyen_vaka', 0)}",
                    self.metin_stili,
                )
            )
            elements.append(Spacer(1, 8))
            
            # Yer bulma süreleri
            if 'yer_bulma_suresi' in sure_data and sure_data['yer_bulma_suresi']:
                yer_data = sure_data['yer_bulma_suresi']
                elements.append(
                    Paragraph(
                        f"• <b>Ortalama yer bulma süresi:</b> {yer_data.get('ortalama_saat', 0):.1f} saat ({yer_data.get('ortalama_dk', 0):.0f} dakika)",
                        self.metin_stili,
                    )
                )
                elements.append(
                    Paragraph(
                        f"• <b>En hızlı yer bulan vaka:</b> {yer_data.get('min_dk', 0)/60:.1f} saat",
                        self.metin_stili,
                    )
                )
                elements.append(
                    Paragraph(
                        f"• <b>En yavaş yer bulan vaka:</b> {yer_data.get('max_dk', 0)/60:.1f} saat",
                        self.metin_stili,
                    )
                )
            else:
                # Yer bulma süresi verisi yoksa uyarı notu ekle
                elements.append(
                    Paragraph(
                        f"• <b>📝 Not:</b> Bu tarihte yeni vaka bulunmadığı için yer bulma süresi hesaplanamamıştır.",
                        self.metin_stili,
                    )
                )
            
            # Bekleme süreleri
            if 'bekleme_suresi' in sure_data:
                bekleme_data = sure_data['bekleme_suresi']
                elements.append(Spacer(1, 8))
                elements.append(
                    Paragraph(
                        f"• <b>Halen bekleyenlerin ortalama bekleme süresi:</b> {bekleme_data.get('ortalama_saat', 0):.1f} saat",
                        self.metin_stili,
                    )
                )
                elements.append(
                    Paragraph(
                        f"• <b>En uzun bekleyen vaka:</b> {bekleme_data.get('max_dk', 0)/60:.1f} saat ({bekleme_data.get('max_dk', 0)/60/24:.1f} gün)",
                        self.metin_stili,
                    )
                )
            
            # Klinik bazında top 5 en hızlı/yavaş
            if 'klinik_bazinda' in sure_data and sure_data['klinik_bazinda']:
                elements.append(Spacer(1, 12))
                elements.append(
                    Paragraph(
                        "<b>KLİNİK PERFORMANSI (Yer Bulma Süreleri)</b>",
                        self.alt_baslik_stili,
                    )
                )
                elements.append(Spacer(1, 8))
                
                # Klinikleri yer bulma süresine göre sırala
                klinik_sureler = []
                for klinik, data in sure_data['klinik_bazinda'].items():
                    if 'yer_bulma_ort_saat' in data and data.get('tamamlanan', 0) >= 2:  # En az 2 tamamlanmış vaka
                        klinik_sureler.append((klinik, data['yer_bulma_ort_saat'], data.get('tamamlanan', 0)))
                
                klinik_sureler.sort(key=lambda x: x[1])  # Süreye göre sırala
                
                # En hızlı 3
                elements.append(
                    Paragraph(
                        "<b>En Hızlı Yer Bulan Klinikler:</b>",
                        self.metin_stili,
                    )
                )
                for i, (klinik, sure, sayi) in enumerate(klinik_sureler[:3], 1):
                    elements.append(
                        Paragraph(
                            f"  {i}. <b>{klinik}:</b> {sure:.1f} saat (ortalama, {sayi} vaka)",
                            self.metin_stili,
                        )
                    )
                
                # En yavaş 3
                if len(klinik_sureler) > 3:
                    elements.append(Spacer(1, 4))
                    elements.append(
                        Paragraph(
                            "<b>En Yavaş Yer Bulan Klinikler:</b>",
                            self.metin_stili,
                        )
                    )
                    for i, (klinik, sure, sayi) in enumerate(klinik_sureler[-3:][::-1], 1):
                        elements.append(
                            Paragraph(
                                f"  {i}. <b>{klinik}:</b> {sure:.1f} saat (ortalama, {sayi} vaka)",
                                self.metin_stili,
                            )
                        )
                        
            elements.append(Spacer(1, 16))
            
        except Exception as e:
            logger.error(f"Süre analizi ekleme hatası: {e}")
            elements.append(
                Paragraph(
                    f"⚠️ Süre analizi bilgileri okunamadı: {e}",
                    self.metin_stili,
                )
            )
            elements.append(Spacer(1, 8))
        
        return elements

        return elements

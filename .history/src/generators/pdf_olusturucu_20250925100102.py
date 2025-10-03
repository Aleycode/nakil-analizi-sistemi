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
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph, PageBreak
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

    def pdf_olustur(self, grafik_dizini: Path, gun_tarihi: str, analiz_verisi: Dict) -> str:
        """
        PDF raporu oluşturur

        Args:
            grafik_dizini: Grafik dosyalarının bulunduğu dizin
            gun_tarihi: Analiz günü (YYYY-MM-DD formatında)
            analiz_verisi: Analiz motorundan gelen tüm veri

        Returns:
            str: Oluşturulan PDF dosyasının yolu (başarısızsa boş string)
        """
        try:
            if not self.config.get("pdf_olustur", False):
                logger.info("PDF oluşturma config'de kapalı")
                return ""

            pdf_dosya_adi = self.config.get(
                "pdf_dosya_adi", "nakil_analiz_raporu_{tarih}.pdf"
            ).format(tarih=gun_tarihi)

            temp_pdf_dosyasi = grafik_dizini / f"temp_{pdf_dosya_adi}"
            cikti_dosyasi = grafik_dizini / pdf_dosya_adi

            doc = self._pdf_dokument_olustur(temp_pdf_dosyasi)
            story = []

            # Giriş sayfası (istatistikler)
            story.extend(self._istatistik_sayfasi_olustur(gun_tarihi, analiz_verisi))
            story.append(PageBreak())

            # Grafikleri bul ve sırala
            grafik_dosyalari = self._grafikleri_bul_ve_sirala(grafik_dizini)

            if not grafik_dosyalari:
                logger.warning("Hiç grafik dosyası bulunamadı")
                story.append(Paragraph("Analiz için uygun grafik bulunamadı.", self.metin_stili))
            else:
                # Sadece dosya yollarını al
                grafik_yollari = [str(grafik_path) for grafik_path, _ in grafik_dosyalari]
                story.extend(self._grafikleri_grid_olarak_ekle(grafik_yollari, gun_tarihi))

            doc.build(story)
            logger.info(f"İçerik PDF'i oluşturuldu: {temp_pdf_dosyasi}")

            if PDF_MERGER_AVAILABLE:
                self._kapak_ile_birlestir(temp_pdf_dosyasi, cikti_dosyasi, gun_tarihi)
                temp_pdf_dosyasi.unlink()
                return str(cikti_dosyasi)
            else:
                logger.warning("PyPDF2 kütüphanesi bulunamadı, kapak eklenemiyor")
                temp_pdf_dosyasi.rename(cikti_dosyasi)
                return str(cikti_dosyasi)

        except Exception as e:
            logger.error(f"PDF oluşturma hatası: {e}", exc_info=True)
            return ""

    def _istatistik_sayfasi_olustur(self, gun_tarihi: str, analiz_verisi: Dict) -> List:
        """PDF'in ilk sayfasına genel istatistikleri ekler."""
        elements = []
        
        # Ana Başlık
        elements.append(Paragraph(f"Nakil Analiz Raporu Tarihi: {gun_tarihi}", self.baslik_stili))
        elements.append(Spacer(1, 0.2 * inch))

        # Genel İstatistikler
        genel_stats = analiz_verisi.get("genel_istatistikler", {})
        if genel_stats:
            elements.append(Paragraph("GENEL İSTATİSTİKLER", self.alt_baslik_stili))
            elements.append(Paragraph(f"• Toplam Nakil Bekleyen Talep: {genel_stats.get('toplam_talep', 0)}", self.metin_stili))
            elements.append(Paragraph(f"• İl İçi Talep: {genel_stats.get('il_ici_talep', 0)}", self.metin_stili))
            elements.append(Paragraph(f"• İl Dışı Talep: {genel_stats.get('il_disi_talep', 0)}", self.metin_stili))
            elements.append(Spacer(1, 0.2 * inch))

        # Yoğun Bakım İstatistikleri
        if genel_stats.get("yogun_bakim_talep"):
            yb_stats = genel_stats.get("yogun_bakim_talep", {})
            elements.append(Paragraph("YOĞUN BAKIM İSTATİSTİKLERİ", self.alt_baslik_stili))
            elements.append(Paragraph(f"• Toplam Yoğun Bakım Talebi: {yb_stats.get('toplam', 0)}", self.metin_stili))
            elements.append(Paragraph(f"• İl İçi Yoğun Bakım: {yb_stats.get('il_ici_toplam', 0)}", self.metin_stili))
            elements.append(Paragraph(f"• İl Dışı Yoğun Bakım: {yb_stats.get('il_disi_toplam', 0)}", self.metin_stili))
            elements.append(Paragraph(f"- İl İçi Entübe: {yb_stats.get('il_ici_entube', 0)}", self.metin_stili))
            elements.append(Paragraph(f"- İl İçi Non-Entübe: {yb_stats.get('il_ici_non_entube', 0)}", self.metin_stili))
            elements.append(Paragraph(f"- İl Dışı Entübe: {yb_stats.get('il_disi_entube', 0)}", self.metin_stili))
            elements.append(Paragraph(f"- İl Dışı Non-Entübe: {yb_stats.get('il_disi_non_entube', 0)}", self.metin_stili))
            elements.append(Spacer(1, 0.2 * inch))

        # Süre Analizleri
        sure_analizleri = analiz_verisi.get("sure_analizleri", {})
        if sure_analizleri:
            elements.append(Paragraph("SÜRE ANALİZLERİ", self.alt_baslik_stili))
            elements.append(Paragraph(f"• Toplam analiz edilen vaka: {analiz_verisi.get('toplam_vaka_sayisi', 0)}", self.metin_stili))
            elements.append(Paragraph(f"• Yer bulunmuş vaka: {sure_analizleri.get('yer_bulunmus_vaka_sayisi', 0)}", self.metin_stili))
            elements.append(Paragraph(f"• Halen bekleyen vaka: {sure_analizleri.get('bekleyen_vaka_sayisi', 0)}", self.metin_stili))
            elements.append(Paragraph(f"• Ortalama yer bulma süresi: {sure_analizleri.get('ortalama_yer_bulma_suresi_saat', 0):.1f} saat ({sure_analizleri.get('ortalama_yer_bulma_suresi_dakika', 0):.0f} dakika)", self.metin_stili))
            elements.append(Paragraph(f"• En hızlı yer bulan vaka: {sure_analizleri.get('en_hizli_yer_bulma_suresi_saat', 0):.1f} saat", self.metin_stili))
            elements.append(Paragraph(f"• En yavaş yer bulan vaka: {sure_analizleri.get('en_yavas_yer_bulma_suresi_saat', 0):.1f} saat", self.metin_stili))
            elements.append(Paragraph(f"• Halen bekleyenlerin ortalama bekleme süresi: {sure_analizleri.get('ortalama_bekleme_suresi_saat', 0):.1f} saat", self.metin_stili))
            elements.append(Paragraph(f"• En uzun bekleyen vaka: {sure_analizleri.get('en_uzun_bekleme_suresi_saat', 0):.1f} saat ({sure_analizleri.get('en_uzun_bekleme_suresi_gun', 0):.1f} gün)", self.metin_stili))
            elements.append(Spacer(1, 0.2 * inch))

        # Klinik Performansı
        klinik_performans = analiz_verisi.get('il_gruplari', {}).get('Butun_Bolgeler', {}).get('Butun_Vakalar', {}).get('klinik_analizi', {})
        if klinik_performans:
            elements.append(Paragraph("KLİNİK PERFORMANSI (Yer Bulma Süreleri)", self.alt_baslik_stili))
            
            en_hizli = klinik_performans.get('en_hizli_yer_bulan_klinikler', [])
            if en_hizli:
                elements.append(Paragraph("En Hızlı Yer Bulan Klinikler:", self.metin_stili))
                for i, klinik in enumerate(en_hizli[:3], 1):
                    elements.append(Paragraph(f"{i}. {klinik['klinik']}: {klinik['ortalama_sure_saat']:.1f} saat (ortalama, {klinik['vaka_sayisi']} vaka)", self.metin_stili))

            en_yavas = klinik_performans.get('en_yavas_yer_bulan_klinikler', [])
            if en_yavas:
                elements.append(Paragraph("En Yavaş Yer Bulan Klinikler:", self.metin_stili))
                for i, klinik in enumerate(en_yavas[:3], 1):
                    elements.append(Paragraph(f"{i}. {klinik['klinik']}: {klinik['ortalama_sure_saat']:.1f} saat (ortalama, {klinik['vaka_sayisi']} vaka)", self.metin_stili))

        return elements

    def _grafikleri_grid_olarak_ekle(self, grafik_dosyalari: List[str], gun_tarihi: str) -> List:
        """Grafikleri 2x2'lik bir grid düzeninde PDF'e ekler ve başlık ekler."""
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors

        story = []
        
        for i in range(0, len(grafik_dosyalari), 4):
            grafik_grubu = grafik_dosyalari[i:i+4]
            
            if i > 0:
                story.append(PageBreak())
            
            story.append(Paragraph(f"Günlük Analiz Grafikleri - {gun_tarihi}", self.alt_baslik_stili))
            story.append(Spacer(1, 0.2 * inch))

            data = []
            for j in range(0, len(grafik_grubu), 2):
                row_items = []
                for k in range(j, j + 2):
                    if k < len(grafik_grubu):
                        grafik_path = grafik_grubu[k]
                        
                        # Dosya adını daha okunaklı hale getir
                        dosya_adi = Path(grafik_path).stem
                        baslik_str = dosya_adi.replace("_", " ").replace("-", " ").title()
                        baslik_style = ParagraphStyle('GrafikBaslik', parent=self.styles['Normal'], fontName=self.default_font, fontSize=8, alignment=TA_CENTER)
                        baslik = Paragraph(baslik_str, baslik_style)
                        
                        if not Path(grafik_path).exists():
                            img = Paragraph(f"Grafik bulunamadı:<br/>{Path(grafik_path).name}", self.metin_stili)
                        else:
                            try:
                                img = Image(grafik_path, width=3.5*inch, height=2.2*inch, kind='proportional')
                            except Exception as e:
                                logger.warning(f"Grafik yüklenemedi: {grafik_path} - {e}")
                                img = Paragraph(f"Grafik yüklenemedi:<br/>{Path(grafik_path).name}", self.metin_stili)
                        
                        item_table = Table([[img], [baslik]], rowHeights=[2.3*inch, 0.4*inch])
                        item_table.setStyle(TableStyle([
                            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                            ('BOTTOMPADDING', (0,1), (0,1), 6),
                        ]))
                        row_items.append(item_table)
                    else:
                        row_items.append(Spacer(0,0))
                data.append(row_items)

            table = Table(data, colWidths=[3.8*inch, 3.8*inch])
            table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ]))
            story.append(table)

        return story

    def _pdf_dokument_olustur(self, dosya_yolu: Path) -> SimpleDocTemplate:
        """SimpleDocTemplate nesnesi oluşturur ve ayarlarını yapar"""
        sayfa_ayarlari = self.config.get("sayfa_ayarlari", {})
        sayfa_boyutu_str = sayfa_ayarlari.get("boyut", "A4")
        sayfa_boyutu = {"A4": A4, "A3": A3, "LETTER": letter}.get(
            sayfa_boyutu_str.upper(), A4
        )
        kenar_boslugu = sayfa_ayarlari.get("kenar_boslugu", 0.5) * inch

        doc = SimpleDocTemplate(
            str(dosya_yolu),
            pagesize=sayfa_boyutu,
            leftMargin=kenar_boslugu,
            rightMargin=kenar_boslugu,
            topMargin=kenar_boslugu,
            bottomMargin=kenar_boslugu,
        )
        return doc

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

    def _kapak_ile_birlestir(self, icerik_pdf: Path, cikti_pdf: Path, gun_tarihi: str = None) -> str:
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
            if 'yer_bulma_suresi' in sure_data:
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

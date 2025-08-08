"""
Nakil Analizi - Kapak Sayfası Oluşturucu
Türkçe karakter desteği ile tek sayfa kapak sayfaları oluşturur
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


class KapakSayfasiOlusturucu:
    """Kapak sayfası oluşturucu sınıfı"""

    def __init__(self, config_dosyasi: str = "assets/kapak_config.json"):
        """Kapak sayfası oluşturucu başlatır"""
        self.styles = getSampleStyleSheet()
        self.config = self._config_yukle(config_dosyasi)
        self._turkce_font_ekle()
        self._ozel_stiller_olustur()

    def _config_yukle(self, config_dosyasi: str) -> Dict[str, Any]:
        """Kapak konfigürasyon dosyasını yükler"""
        try:
            config_path = Path(config_dosyasi)
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"Kapak config dosyası yüklendi: {config_path}")
                return config
            else:
                logger.warning(f"Config dosyası bulunamadı: {config_path}")
                return self._varsayilan_config()
        except Exception as e:
            logger.error(f"Config dosyası yükleme hatası: {e}")
            return self._varsayilan_config()

    def _varsayilan_config(self) -> Dict[str, Any]:
        """Varsayılan konfigürasyon döndürür"""
        return {
            "baslik": {
                "metin": "NAKİL ANALİZ RAPORU",
                "font_boyutu": 24,
                "renk": "#2c3e50",
                "konum": "merkez",
                "ust_bosluk": 1.5,
                "alt_bosluk": 0.3,
            },
            "alt_baslik": {
                "metin": "Günlük Vaka Takip ve Değerlendirme",
                "font_boyutu": 16,
                "renk": "#34495e",
                "konum": "merkez",
                "alt_bosluk": 2.0,
            },
            "kurum": {
                "metin": "T.C. Sağlık Bakanlığı",
                "font_boyutu": 18,
                "renk": "#2c3e50",
                "konum": "merkez",
                "ust_bosluk": 1.5,
            },
            "logo": {
                "dosya_adi": "logo.png",
                "genislik": 2.0,
                "yukseklik": 2.0,
                "alt_bosluk": 0.5,
            },
            "sayfa_ayarlari": {"kenar_boslugu": 1.0, "sayfa_boyutu": "A4"},
            "tarih_goster": False,
        }

    def _turkce_font_ekle(self):
        """Türkçe karakter desteği için font ekler"""
        try:
            proje_kok = Path(__file__).parent

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

            if fonts_registered:
                try:
                    from reportlab.lib.fonts import addMapping

                    addMapping("DejaVuSans", 0, 0, "DejaVuSans")
                    addMapping("DejaVuSans", 1, 0, "DejaVuSans-Bold")
                    addMapping("DejaVuSans", 0, 1, "DejaVuSans-Oblique")
                    addMapping("DejaVuSans", 1, 1, "DejaVuSans-Bold")
                    self.default_font = "DejaVuSans"
                    logger.info("DejaVu Sans font ailesi başarıyla yapılandırıldı")
                except Exception as e:
                    logger.warning(f"Font mapping başarısız: {e}")
                    self.default_font = "Helvetica"
            else:
                self.default_font = "Helvetica"
                logger.warning("Türkçe fontlar yüklenemedi, Helvetica kullanılacak")

        except Exception as e:
            logger.error(f"Font yükleme hatası: {e}")
            self.default_font = "Helvetica"

    def _ozel_stiller_olustur(self):
        """Özel PDF stilleri oluşturur - Config'den ayarları alır"""
        try:
            # Alignment mapping
            alignment_map = {"sol": TA_LEFT, "merkez": TA_CENTER, "sag": TA_RIGHT}

            # Ana başlık stili
            baslik_config = self.config.get("baslik", {})
            self.ana_baslik_stili = ParagraphStyle(
                "AnaBaslik",
                parent=self.styles["Normal"],
                fontName=self.default_font,
                fontSize=baslik_config.get("font_boyutu", 24),
                textColor=HexColor(baslik_config.get("renk", "#2c3e50")),
                alignment=alignment_map.get(
                    baslik_config.get("konum", "merkez"), TA_CENTER
                ),
                spaceAfter=baslik_config.get("alt_bosluk", 0.3) * inch,
            )

            # Alt başlık stili
            alt_baslik_config = self.config.get("alt_baslik", {})
            self.alt_baslik_stili = ParagraphStyle(
                "AltBaslik",
                parent=self.styles["Normal"],
                fontName=self.default_font,
                fontSize=alt_baslik_config.get("font_boyutu", 16),
                textColor=HexColor(alt_baslik_config.get("renk", "#34495e")),
                alignment=alignment_map.get(
                    alt_baslik_config.get("konum", "merkez"), TA_CENTER
                ),
                spaceAfter=alt_baslik_config.get("alt_bosluk", 2.0) * inch,
            )

            # Kurum adı stili
            kurum_config = self.config.get("kurum", {})
            self.kurum_stili = ParagraphStyle(
                "Kurum",
                parent=self.styles["Normal"],
                fontName=self.default_font,
                fontSize=kurum_config.get("font_boyutu", 18),
                textColor=HexColor(kurum_config.get("renk", "#2c3e50")),
                alignment=alignment_map.get(
                    kurum_config.get("konum", "merkez"), TA_CENTER
                ),
                spaceAfter=20,
            )

            # Tarih stili (kullanılmayacak ama tanımlı kalsın)
            tarih_config = self.config.get("tarih", {})
            self.tarih_stili = ParagraphStyle(
                "Tarih",
                parent=self.styles["Normal"],
                fontName=self.default_font,
                fontSize=tarih_config.get("font_boyutu", 14),
                textColor=HexColor(tarih_config.get("renk", "#7f8c8d")),
                alignment=alignment_map.get(
                    tarih_config.get("konum", "merkez"), TA_CENTER
                ),
                spaceAfter=15,
            )

            logger.info("Kapak sayfası stilleri config'den oluşturuldu")

        except Exception as e:
            logger.error(f"Stil oluşturma hatası: {e}")
            # Varsayılan stiller oluştur
            self._varsayilan_stiller_olustur()

    def _varsayilan_stiller_olustur(self):
        """Hata durumunda varsayılan stiller oluşturur"""
        self.ana_baslik_stili = ParagraphStyle(
            "AnaBaslik",
            parent=self.styles["Normal"],
            fontName=self.default_font,
            fontSize=24,
            textColor=HexColor("#2c3e50"),
            alignment=TA_CENTER,
            spaceAfter=30,
        )

        self.alt_baslik_stili = ParagraphStyle(
            "AltBaslik",
            parent=self.styles["Normal"],
            fontName=self.default_font,
            fontSize=16,
            textColor=HexColor("#34495e"),
            alignment=TA_CENTER,
            spaceAfter=20,
        )

        self.kurum_stili = ParagraphStyle(
            "Kurum",
            parent=self.styles["Normal"],
            fontName=self.default_font,
            fontSize=18,
            textColor=HexColor("#2c3e50"),
            alignment=TA_CENTER,
            spaceAfter=20,
        )

    def kapak_olustur(
        self,
        baslik: Optional[str] = None,
        alt_baslik: Optional[str] = None,
        kurum: Optional[str] = None,
        logo_yolu: Optional[str] = None,
        cikti_dosyasi: str = "assets/kapak.pdf",
    ) -> bool:
        """
        Kapak sayfası oluşturur - Config dosyasından ayarları alır

        Args:
            baslik: Ana başlık (None ise config'den alınır)
            alt_baslik: Alt başlık (None ise config'den alınır)
            kurum: Kurum adı (None ise config'den alınır)
            logo_yolu: Logo dosya yolu (None ise config'den alınır)
            cikti_dosyasi: Çıktı PDF dosyası

        Returns:
            bool: Başarı durumu
        """
        try:
            # Config'den ayarları al
            baslik = baslik or self.config.get("baslik", {}).get(
                "metin", "NAKİL ANALİZ RAPORU"
            )
            alt_baslik = alt_baslik or self.config.get("alt_baslik", {}).get(
                "metin", ""
            )
            kurum = kurum or self.config.get("kurum", {}).get(
                "metin", "T.C. Sağlık Bakanlığı"
            )

            # Logo ayarları
            if logo_yolu is None:
                logo_config = self.config.get("logo", {})
                logo_dosya_adi = logo_config.get("dosya_adi", "logo.png")
                logo_yolu = f"assets/{logo_dosya_adi}"

            # Çıktı klasörünü oluştur
            cikti_path = Path(cikti_dosyasi)
            cikti_path.parent.mkdir(parents=True, exist_ok=True)

            # Sayfa ayarları
            sayfa_config = self.config.get("sayfa_ayarlari", {})
            kenar_boslugu = sayfa_config.get("kenar_boslugu", 1.0) * inch

            # PDF dökümanı oluştur
            doc = SimpleDocTemplate(
                str(cikti_path),
                pagesize=A4,
                rightMargin=kenar_boslugu,
                leftMargin=kenar_boslugu,
                topMargin=kenar_boslugu,
                bottomMargin=kenar_boslugu,
            )

            # İçerik elementleri
            story = []

            # Logo ekle (varsa)
            if logo_yolu and Path(logo_yolu).exists():
                try:
                    logo_config = self.config.get("logo", {})
                    logo_genislik = logo_config.get("genislik", 2.0) * inch
                    logo_yukseklik = logo_config.get("yukseklik", 2.0) * inch
                    logo_alt_bosluk = logo_config.get("alt_bosluk", 0.5) * inch

                    logo = Image(logo_yolu, width=logo_genislik, height=logo_yukseklik)
                    story.append(logo)
                    story.append(Spacer(1, logo_alt_bosluk))
                except Exception as e:
                    logger.warning(f"Logo yüklenemedi: {e}")

            # Üst boşluk (config'den)
            baslik_config = self.config.get("baslik", {})
            ust_bosluk = baslik_config.get("ust_bosluk", 1.5) * inch
            story.append(Spacer(1, ust_bosluk))

            # Ana başlık
            story.append(Paragraph(baslik, self.ana_baslik_stili))

            # Alt başlık (varsa)
            if alt_baslik:
                story.append(Paragraph(alt_baslik, self.alt_baslik_stili))

            # Kurum için üst boşluk
            kurum_config = self.config.get("kurum", {})
            kurum_ust_bosluk = kurum_config.get("ust_bosluk", 1.5) * inch
            story.append(Spacer(1, kurum_ust_bosluk))

            # Kurum adı
            story.append(Paragraph(kurum, self.kurum_stili))

            # PDF'i oluştur
            doc.build(story)

            logger.info(f"Kapak sayfası başarıyla oluşturuldu: {cikti_path}")
            return True

        except Exception as e:
            logger.error(f"Kapak sayfası oluşturma hatası: {e}")
            return False


def main():
    """Ana fonksiyon - Test amaçlı"""
    logging.basicConfig(level=logging.INFO)

    kapak_olusturucu = KapakSayfasiOlusturucu()

    # Kapak oluştur (config'den ayarlar alınacak)
    basari = kapak_olusturucu.kapak_olustur()

    if basari:
        print("✅ Kapak sayfası başarıyla oluşturuldu!")
        print("📁 Dosya: assets/kapak.pdf")
        print("⚙️  Ayarlar: assets/kapak_config.json dosyasından alındı")
    else:
        print("❌ Kapak sayfası oluşturulamadı!")


if __name__ == "__main__":
    main()

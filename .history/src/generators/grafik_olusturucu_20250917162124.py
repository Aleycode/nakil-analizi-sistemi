"""
Grafik oluşturucu modülü - Tüm grafik oluşturma fonksiyonları
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from ..core.config import (
    RAPOR_DIZIN,
    VARSAYILAN_GRAFIK_BOYUTU,
    VARSAYILAN_DPI,
    GRAFIK_GORUNUM_AYARLARI,
    GRAFIK_BASLIK_SABLONLARI,
    PASTA_GRAFIK_RENK_PALETI,
    GRUP_ADI_CEVIRI,
)

# Logger yapılandırması
logger = logging.getLogger(__name__)

# Grafik ayarları ve stil importları
from ..utils.grafik_sabitleri import (
    GRAFIK_RENK_PALETI,
    GRAFIK_STIL,
    format_etiket,
    renk_paleti_uret,
    grafik_ayarlarini_uygula
)


class GrafikOlusturucu:
    def pdf_sayfalari_yatay_birlestir(self, pdf_path: str, cikti_pdf: str = None):
        """
        Mevcut PDF raporundaki tüm sayfaları yatay A4 formatında tek bir sayfada birleştirir.
        """
        from pdf2image import convert_from_path
        from PIL import Image
        from fpdf import FPDF
        import os
        # PDF'i görsellere çevir
        sayfa_gorselleri = convert_from_path(pdf_path, dpi=200)
        # Yatay grid için toplam genişlik ve maksimum yükseklik
        toplam_genislik = sum(img.width for img in sayfa_gorselleri)
        max_yukseklik = max(img.height for img in sayfa_gorselleri)
        # Grid görseli oluştur
        grid_img = Image.new("RGB", (toplam_genislik, max_yukseklik), (255, 255, 255))
        x_offset = 0
        for img in sayfa_gorselleri:
            grid_img.paste(img, (x_offset, 0))
            x_offset += img.width
        # Geçici olarak kaydet
        grid_jpg = os.path.splitext(pdf_path)[0] + "_yatay_grid.jpg"
        grid_img.save(grid_jpg)
        # PDF olarak kaydet
        if cikti_pdf is None:
            cikti_pdf = os.path.splitext(pdf_path)[0] + "_yatay.pdf"
        pdf = FPDF(orientation="L", unit="pt", format=[grid_img.width, grid_img.height])
        pdf.add_page()
        pdf.image(grid_jpg, x=0, y=0, w=grid_img.width, h=grid_img.height)
        pdf.output(cikti_pdf)
        return cikti_pdf
    def tum_grafikleri_pdfde_birlestir(self, gun_tarihi: str, pdf_adi: str = None):
        """
        Belirtilen tarih klasöründeki tüm grafik ve tablo görsellerini yatay bir gridde birleştirip tek sayfa PDF olarak kaydeder.
        """
        import glob
        from PIL import Image
        from fpdf import FPDF
        import math
        # Grafik klasörünü bul
        tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
        # PNG dosyalarını topla (alfabetik sıralı)
        png_listesi = sorted(glob.glob(str(tarih_klasor / "*.png")))
        if not png_listesi:
            logger.warning(f"{gun_tarihi} için grafik bulunamadı.")
            return None
        # Görselleri aç
        img_list = [Image.open(png).convert("RGB") for png in png_listesi]
        # Grid ayarları: 2 satır, n/2 sütun (çok fazla grafik varsa)
        n = len(img_list)
        grid_cols = min(n, 4)  # max 4 sütun
        grid_rows = math.ceil(n / grid_cols)
        thumb_width = 800
        thumb_height = 600
        # Tüm görselleri aynı boyuta getir
        img_list = [img.resize((thumb_width, thumb_height)) for img in img_list]
        grid_img = Image.new("RGB", (grid_cols * thumb_width, grid_rows * thumb_height), (255, 255, 255))
        for idx, img in enumerate(img_list):
            x = (idx % grid_cols) * thumb_width
            y = (idx // grid_cols) * thumb_height
            grid_img.paste(img, (x, y))
        # Geçici olarak kaydet
        grid_path = tarih_klasor / "tum_grafikler_grid.jpg"
        grid_img.save(grid_path)
        # PDF oluştur (A4 yatay)
        if pdf_adi is None:
            pdf_adi = f"tum_grafikler_{gun_tarihi}.pdf"
        pdf_path = tarih_klasor / pdf_adi
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        # Görseli PDF'e ortala ve sığdır
        page_w = pdf.w - 20
        page_h = pdf.h - 20
        img_w, img_h = grid_img.size
        scale = min(page_w / img_w, page_h / img_h)
        w = img_w * scale
        h = img_h * scale
        x = (pdf.w - w) / 2
        y = (pdf.h - h) / 2
        pdf.image(str(grid_path), x=x, y=y, w=w, h=h)
        pdf.output(str(pdf_path))
        logger.info(f"Tüm grafikler ve tablolar tek PDF sayfasında grid olarak birleştirildi: {pdf_path}")
        return pdf_path
    """Tüm grafik oluşturma işlemleri"""

    def __init__(self):
        """Grafik oluşturucu başlatma"""
        # Grafik klasörü oluştur
        RAPOR_DIZIN.mkdir(parents=True, exist_ok=True)

    def _grafik_baslik_olustur(self, sablon_adi: str, **kwargs) -> str:
        """
        Config'den grafik başlık şablonunu kullanarak başlık oluşturur
        """
        try:
            if sablon_adi in GRAFIK_BASLIK_SABLONLARI:
                sablon = GRAFIK_BASLIK_SABLONLARI[sablon_adi]
                baslik = sablon.format(**kwargs)
            else:
                # Varsayılan şablon
                sablon = GRAFIK_BASLIK_SABLONLARI.get("genel", "{analiz_tipi}")
                baslik = sablon.format(**kwargs)

            # Grup adlarını çevir
            for kod, turkce in GRUP_ADI_CEVIRI.items():
                baslik = baslik.replace(kod, turkce)

            return baslik
        except Exception as e:
            logger.warning(
                f"Başlık oluşturma hatası: {e}, varsayılan başlık kullanılıyor"
            )
            return kwargs.get("analiz_tipi", "Grafik")

    def _tarih_klasoru_olustur(self, gun_tarihi: str) -> Path:
        """Verilen tarih için klasör oluşturur ve path döner"""
        tarih_klasor = RAPOR_DIZIN / gun_tarihi
        tarih_klasor.mkdir(parents=True, exist_ok=True)
        return tarih_klasor

    def iptal_eden_cubuk_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str
    ):
        """İptal eden dağılımı tek çubuk stacked grafik"""
        try:
            # Önce sadece geçerli vakaları al (Analiz dışı hariç)
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
            if len(gecerli_vakalar) == 0:
                logger.warning(f"Geçerli vaka bulunamadı: {grup_adi}")
                return None

            # Geçerli vakalar içinden iptal edilmiş olanları al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("İptal", na=False)
            ]
            if len(iptal_vakalar) == 0:
                mesaj = (
                    f"Geçerli vakalar içinde iptal edilmiş vaka bulunamadı, "
                    f"iptal eden çubuk grafiği oluşturulamadı: {grup_adi}"
                )
                logger.warning(mesaj)
                return None

            # İptal Eden sütununu kontrol et
            if "i̇ptal eden" not in iptal_vakalar.columns:
                logger.warning(f"'i̇ptal eden' sütunu bulunamadı: {grup_adi}")
                return None

            # İptal eden sayımları (boş değerleri hariç tut)
            iptal_eden_sayimlari = iptal_vakalar["i̇ptal eden"].dropna().value_counts()

            if iptal_eden_sayimlari.empty:
                logger.warning(f"İptal eden verisi bulunamadı: {grup_adi}")
                return None

            # En çok iptal eden ilk 10'u al
            top_iptal_eden = iptal_eden_sayimlari.head(10)

            # Renk paleti - her kuruma farklı renk
            import matplotlib.cm as cm

            colors = cm.Set3(range(len(top_iptal_eden)))

            # Tek çubuk stacked grafik oluştur
            fig, ax = plt.subplots(figsize=(12, 6))

            # Kümülatif değerler için başlangıç
            left = 0

            # Her kurum için stacked bar ekle (horizontal)
            for i, (kurum, sayi) in enumerate(top_iptal_eden.items()):
                ax.barh(
                    ["İptal Eden Kurumlar"],
                    [sayi],
                    left=left,
                    color=colors[i],
                    label=f"{kurum} ({sayi})",
                )
                left += sayi  # Bölge adını düzenle
            if grup_adi == "Il_Ici":
                bolge_adi = "İl İçi"
            elif grup_adi == "Il_Disi":
                bolge_adi = "İl Dışı"
            elif grup_adi == "Butun_Bolgeler":
                bolge_adi = "Bütün Bölgeler"
            else:
                bolge_adi = grup_adi

            # Başlık ve etiketler
            ax.set_title(
                f"İptal Eden Kurumlar - {bolge_adi}",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )
            ax.set_xlabel("Vaka Sayısı", fontweight="bold")
            ax.set_ylabel("")

            # Legend'ı sağ tarafa yerleştir
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

            # Grid
            ax.grid(True, alpha=0.3)
            ax.set_axisbelow(True)

            # Layout ayarla
            plt.tight_layout()

            # Dosya adını oluştur ve kaydet
            dosya_adi = f"iptal-eden-dagilimi_{bolge_adi}_{gun_tarihi}.png"
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi
            plt.savefig(dosya_yolu, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"İptal eden stacked çubuk grafiği oluşturuldu: {dosya_yolu}")
            return dosya_yolu

        except Exception as e:
            logger.error(f"İptal eden stacked çubuk grafiği oluşturma hatası: {e}")
            return None
        try:
            # Önce sadece geçerli vakaları al (Analiz dışı hariç)
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(f"Geçerli vaka bulunamadı: {grup_adi}")
                return None

            # Geçerli vakalar içinden iptal edilmiş olanları al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("İptal", na=False)
            ]

            if len(iptal_vakalar) == 0:
                mesaj = (
                    f"Geçerli vakalar içinde iptal edilmiş vaka bulunamadı, "
                    f"iptal eden çubuk grafiği oluşturulamadı: {grup_adi}"
                )
                logger.warning(mesaj)
                return None

            # İptal Eden sütununu kontrol et
            if "i̇ptal eden" not in iptal_vakalar.columns:
                logger.warning(f"'i̇ptal eden' sütunu bulunamadı: {grup_adi}")
                return None

            # İptal eden sayımları (boş değerleri hariç tut)
            iptal_eden_sayimlari = iptal_vakalar["i̇ptal eden"].dropna().value_counts()

            if len(iptal_eden_sayimlari) == 0:
                logger.warning(f"İptal eden verisi bulunamadı: {grup_adi}")
                return None

            # Minimum vaka sayısı kontrolü
            if iptal_eden_sayimlari.sum() < 3:
                logger.warning(
                    f"Yetersiz iptal vakası ({iptal_eden_sayimlari.sum()}), "
                    f"çubuk grafiği oluşturulamadı: {grup_adi}"
                )
                return None

            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)

            # Yatay çubuk grafiği oluştur
            bars = plt.barh(
                range(len(iptal_eden_sayimlari)),
                iptal_eden_sayimlari.values,
                color=PASTA_GRAFIK_RENK_PALETI[: len(iptal_eden_sayimlari)],
            )

            # Y ekseni etiketlerini ayarla
            plt.yticks(range(len(iptal_eden_sayimlari)), iptal_eden_sayimlari.index)

            # Çubukların üzerine sayıları yaz
            for i, (kurum, sayi) in enumerate(iptal_eden_sayimlari.items()):
                plt.text(sayi + 0.1, i, str(sayi), va="center", fontweight="bold")

            # Grup adını çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            plt.title(
                f"İptal Eden Kurumlar - {bolge_adi}\n"
                f"Toplam: {iptal_eden_sayimlari.sum()} vaka",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )

            plt.xlabel("Vaka Sayısı", fontweight="bold")
            plt.ylabel("İptal Eden Kurum", fontweight="bold")
            plt.grid(True, alpha=0.3, axis="x")
            plt.tight_layout()

            # Tarih ekle
            self._grafige_tarih_ekle(plt, gun_tarihi)

            # Kaydet
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            dosya_adi = (
                tarih_klasor
                / f"iptal-eden-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"
            )

            # Metin ekle (config'den)
            self._grafige_metin_ekle(plt, str(dosya_adi), gun_tarihi)

            plt.savefig(dosya_adi, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

            logger.info(f"İptal eden çubuk grafiği oluşturuldu: {dosya_adi}")
            return dosya_adi

        except Exception as e:
            logger.error(f"İptal eden çubuk grafiği oluşturma hatası: {e}")
            return None

    def pasta_grafik_olustur(self, veriler: pd.Series, baslik: str, dosya_adi: str):
        """Pasta grafiği oluşturur - hem sayı hem yüzde gösterir"""
        import os
        try:
            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)

            # En çok 10 kategori göster
            if len(veriler) > 10:
                top_10 = veriler.head(10)
                diger_toplam = veriler.iloc[10:].sum()
                if diger_toplam > 0:
                    top_10["Diğer"] = diger_toplam
                veriler = top_10

            # Başlıktaki grup adlarını çevir
            for kod, turkce in GRUP_ADI_CEVIRI.items():
                baslik = baslik.replace(kod, turkce)

            # Hem sayı hem yüzde göstermek için özel etiket fonksiyonu
            def autopct_format(pct):
                absolute = int(round(pct / 100.0 * veriler.sum()))
                return f"{pct:.1f}%\n({absolute:,})"

            # Gelişmiş renk paleti kullan
            colors = PASTA_GRAFIK_RENK_PALETI[: len(veriler)]

            plt.pie(
                veriler.values,
                labels=veriler.index,
                autopct=autopct_format,
                startangle=90,
                textprops={"fontsize": 9},
                colors=colors,
            )
            plt.title(baslik, fontsize=14, fontweight="bold")
            plt.axis("equal")

            # Tarih bilgisini dosya adından çıkar
            gun_tarihi = dosya_adi.split("_")[-1].replace(".png", "")

            # Tarih klasörü oluştur ve dosyaya kaydet
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi

            # Metin ekle (config'den)
            self._grafige_metin_ekle(plt, str(dosya_yolu), gun_tarihi)

            plt.savefig(dosya_yolu, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

            # Dosya gerçekten oluştu mu kontrol et
            if not os.path.exists(dosya_yolu):
                logger.error(f"Pasta grafiği dosyası kaydedilemedi: {dosya_yolu} (veri boyutu: {len(veriler)})")

        except Exception as e:
            logger.error(f"Pasta grafiği oluşturma hatası: {e} (dosya: {dosya_adi}, veri boyutu: {len(veriler)})")

    def _grafige_tarih_ekle(self, plt_obj, gun_tarihi: str):
        """Grafiklere tarih bilgisi ekler"""
        try:
            if not GRAFIK_GORUNUM_AYARLARI.get("tarih_goster", True):
                return

            konum = GRAFIK_GORUNUM_AYARLARI.get("tarih_konum", "alt_sag")
            boyut = GRAFIK_GORUNUM_AYARLARI.get("tarih_boyut", 8)

            # Tarih formatını düzenle
            tarih_obj = datetime.strptime(gun_tarihi, "%Y-%m-%d")
            tarih_text = tarih_obj.strftime("%d.%m.%Y")

            # Konum ayarları
            if konum == "alt_sag":
                x, y = 0.98, 0.02
                ha, va = "right", "bottom"
            elif konum == "alt_sol":
                x, y = 0.02, 0.02
                ha, va = "left", "bottom"
            elif konum == "ust_sag":
                x, y = 0.98, 0.98
                ha, va = "right", "top"
            else:  # ust_sol
                x, y = 0.02, 0.98
                ha, va = "left", "top"

            plt_obj.figtext(
                x,
                y,
                f"Tarih: {tarih_text}",
                fontsize=boyut,
                ha=ha,
                va=va,
                alpha=0.7,
                style="italic",
            )

        except Exception as e:
            logger.warning(f"Tarih ekleme hatası: {e}")

    def _tarih_klasoru_olustur(self, gun_tarihi: str) -> Path:
        """Verilen tarih için rapor klasörü oluşturur"""
        tarih_klasor = RAPOR_DIZIN / gun_tarihi
        tarih_klasor.mkdir(parents=True, exist_ok=True)
        return tarih_klasor

    def threshold_pasta_grafik(self, threshold_data: dict, baslik: str, dosya_adi: str):
        """Bekleme süresi threshold pasta grafiği"""
        try:
            if not threshold_data:
                return None

            # Dictionary'yi Series'e çevir
            import pandas as pd

            veriler = pd.Series(threshold_data)

            # Pasta grafik oluştur
            self.pasta_grafik_olustur(veriler, baslik, dosya_adi)
        except Exception as e:
            logger.error(f"Threshold pasta grafik hatası: {e}")

    def vaka_tipi_pasta_grafigi(self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str):
        """Vaka tipi dağılımı pasta grafiği (Yeni/Devreden)"""
        try:
            # Sadece geçerli vakaları al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(f"Vaka tipi için geçerli vaka bulunamadı: {grup_adi}")
                return None

            # Vaka tipi sayımları
            vaka_tipi_sayimlari = gecerli_vakalar["vaka_tipi"].value_counts()

            # Grup adını Türkçe'ye çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            baslik = f"Vaka Tipi Dağılımı - {bolge_adi}"
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            dosya_adi = f"il-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"

            # Pasta grafik oluştur
            self.pasta_grafik_olustur(vaka_tipi_sayimlari, baslik, dosya_adi)

            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Vaka tipi pasta grafiği hatası: {e}")
            return None

    def il_dagilim_pasta_grafigi(self, il_gruplari: dict, gun_tarihi: str):
        """Bölge dağılımı çubuk grafiği (İl İçi/İl Dışı)"""
        try:
            # Sadece İl İçi ve İl Dışı'nı kullan (Butun_Bolgeler hariç)
            il_ici_sayisi = 0
            il_disi_sayisi = 0

            if "Il_Ici" in il_gruplari:
                il_ici_gecerli = il_gruplari["Il_Ici"][
                    il_gruplari["Il_Ici"]["vaka_tipi"].isin(
                        ["Yeni Vaka", "Devreden Vaka"]
                    )
                ]
                il_ici_sayisi = len(il_ici_gecerli)

            if "Il_Disi" in il_gruplari:
                il_disi_gecerli = il_gruplari["Il_Disi"][
                    il_gruplari["Il_Disi"]["vaka_tipi"].isin(
                        ["Yeni Vaka", "Devreden Vaka"]
                    )
                ]
                il_disi_sayisi = len(il_disi_gecerli)

            # İl dağılımı dictionary'sini oluştur
            il_dagilim = {"İl İçi": il_ici_sayisi, "İl Dışı": il_disi_sayisi}

            if not il_dagilim or sum(il_dagilim.values()) == 0:
                logger.warning("Bölge dağılımı için geçerli vaka bulunamadı")
                return None

            # Pandas Series'e çevir
            import pandas as pd

            il_dagilim_series = pd.Series(il_dagilim)

            baslik = "Bölge Dağılımı"
            dosya_adi = f"il-dagilimi_Butun_Vakalar_{gun_tarihi}.png"

            # Pasta grafik oluştur
            self.pasta_grafik_olustur(il_dagilim_series, baslik, dosya_adi)

            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Bölge dağılımı çubuk grafiği hatası: {e}")
            return None

    def solunum_islemi_pasta_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str
    ):
        """Solunum işlemi dağılımı pasta grafiği"""
        try:
            # Sadece geçerli vakaları al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(
                    f"Solunum işlemi için geçerli vaka bulunamadı: {grup_adi}"
                )
                return None

            # Solunum işlemi sütununu kontrol et
            solunum_sutun = None
            for sutun in [
                "solunum i̇şlemi",
                "solunum işlemi",
                "solunum_islemi",
                "Solunum İşlemi",
                "solunum durumu",
            ]:
                if sutun in gecerli_vakalar.columns:
                    solunum_sutun = sutun
                    break

            if solunum_sutun is None:
                logger.warning(f"Solunum işlemi sütunu bulunamadı: {grup_adi}")
                return None

            # Solunum işlemi sayımları (boş değerleri hariç tut)
            solunum_sayimlari = gecerli_vakalar[solunum_sutun].dropna().value_counts()

            if len(solunum_sayimlari) == 0:
                logger.warning(f"Solunum işlemi verisi bulunamadı: {grup_adi}")
                return None

            # Grup adını Türkçe'ye çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            baslik = f"Solunum İşlemi Dağılımı - {bolge_adi}"
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            dosya_adi = f"solunum-islemi-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"

            # Pasta grafik oluştur
            self.pasta_grafik_olustur(solunum_sayimlari, baslik, dosya_adi)

            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Solunum işlemi pasta grafiği hatası: {e}")
            return None

    def iptal_nedenleri_cubuk_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str, vaka_tipi: str
    ):
        """İptal nedenleri çubuk grafiği"""
        try:
            # Sadece geçerli vakaları al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(
                    f"İptal nedenleri için geçerli vaka bulunamadı: {grup_adi}"
                )
                return None

            # İptal edilmiş vakaları al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("İptal", na=False)
            ]

            if len(iptal_vakalar) == 0:
                logger.warning(f"İptal edilmiş vaka bulunamadı: {grup_adi}")
                return None

            # İptal nedeni sütununu kontrol et
            iptal_nedeni_sutun = None
            for sutun in ["iptal nedeni", "iptal_nedeni", "İptal Nedeni"]:
                if sutun in iptal_vakalar.columns:
                    iptal_nedeni_sutun = sutun
                    break

            if iptal_nedeni_sutun is None:
                logger.warning(f"İptal nedeni sütunu bulunamadı: {grup_adi}")
                return None

            # İptal nedeni sayımları (boş değerleri hariç tut)
            iptal_nedeni_sayimlari = (
                iptal_vakalar[iptal_nedeni_sutun].dropna().value_counts()
            )

            if len(iptal_nedeni_sayimlari) == 0:
                logger.warning(f"İptal nedeni verisi bulunamadı: {grup_adi}")
                return None

            # Çubuk grafik oluştur
            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)
            renkler = PASTA_GRAFIK_RENK_PALETI[: len(iptal_nedeni_sayimlari)]

            bars = plt.bar(
                range(len(iptal_nedeni_sayimlari)),
                iptal_nedeni_sayimlari.values,
                color=renkler,
            )

            # Sayıları çubukların üzerinde göster
            for bar, sayi in zip(bars, iptal_nedeni_sayimlari.values):
                height = bar.get_height()
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + max(iptal_nedeni_sayimlari.values) * 0.01,
                    f"{sayi}",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )

            plt.xticks(
                range(len(iptal_nedeni_sayimlari)),
                iptal_nedeni_sayimlari.index,
                rotation=45,
                ha="right",
            )
            plt.ylabel("Vaka Sayısı", fontsize=12, fontweight="bold")
            plt.grid(axis="y", alpha=0.3)

            # Grup adını Türkçe'ye çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            vaka_tipi_adi = GRUP_ADI_CEVIRI.get(vaka_tipi, vaka_tipi)

            plt.title(
                f"İptal Nedenleri - {bolge_adi} - {vaka_tipi_adi}\n"
                f"Toplam: {iptal_nedeni_sayimlari.sum()} vaka",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )

            # Tarih ekle
            self._grafige_tarih_ekle(plt, gun_tarihi)

            # Kaydet
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            turkce_vaka_tipi = GRUP_ADI_CEVIRI.get(vaka_tipi, vaka_tipi)
            dosya_adi = (
                tarih_klasor
                / f"iptal-nedenleri_{turkce_dosya_adi}_{turkce_vaka_tipi}_{gun_tarihi}.png"
            )

            # Metin ekle (config'den)
            self._grafige_metin_ekle(plt, str(dosya_adi), gun_tarihi)

            plt.savefig(dosya_adi, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

            logger.info(f"İptal nedenleri çubuk grafiği oluşturuldu: {dosya_adi}")
            return dosya_adi

        except Exception as e:
            logger.error(f"İptal nedenleri çubuk grafiği hatası: {e}")
            if "plt" in locals():
                plt.close()
            return None

    def _grafige_metin_ekle(self, plt_obj, dosya_adi: str, gun_tarihi: str):
        """Grafiklere config'den gelen metinleri ekler"""
        try:
            # PDF config dosyasını oku
            import json
            from pathlib import Path

            config_dosya = Path(__file__).parent / "pdf_config.json"
            if not config_dosya.exists():
                return

            with open(config_dosya, "r", encoding="utf-8") as f:
                config = json.load(f)

            metin_ayarlari = config.get("grafik_metin_ayarlari", {})

            # Metin ekleme aktif mi?
            if not metin_ayarlari.get("metin_ekleme_aktif", False):
                return

            # Dosya adından grafik tipini belirle
            dosya_adi_base = Path(dosya_adi).stem

            # Özel metin var mı kontrol et
            ozel_metinler = metin_ayarlari.get("ozel_metinler", {})
            metin_config = None

            for desen, config_item in ozel_metinler.items():
                # Basit wildcard eşleşmesi
                desen_temiz = desen.replace("*", "")
                if desen_temiz in dosya_adi_base:
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

            if not metin:
                return

            # Tarihi metne ekle
            metin = metin.replace("2025-08-08", gun_tarihi)

            # Font ağırlığı
            fontweight = "bold" if font_kalin else "normal"

            # Metin rengini al
            metin_rengi = metin_ayarlari.get("metin_rengi", "#333333")

            # Grafik boyutlarını al
            fig = plt_obj.gcf()
            fig_width, fig_height = fig.get_size_inches()

            # Metin konumunu belirle
            if konum == "ust":
                x, y = 0.5, 0.95
                va = "top"
            else:  # alt
                x, y = 0.5, 0.02
                va = "bottom"

            # Metni ekle
            plt_obj.figtext(
                x,
                y,
                metin,
                fontsize=font_boyutu,
                fontweight=fontweight,
                color=metin_rengi,
                ha="center",
                va=va,
                wrap=True,
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor=metin_ayarlari.get("arka_plan_rengi", "#ffffff"),
                    alpha=metin_ayarlari.get("saydamlik", 0.8),
                    edgecolor="none",
                ),
            )

            # Layout'u ayarla ki metin kesilmesin
            plt_obj.tight_layout()
            if konum == "alt":
                plt_obj.subplots_adjust(bottom=0.15)
            else:
                plt_obj.subplots_adjust(top=0.85)

        except Exception as e:
            logger.warning(f"Grafik metin ekleme hatası: {e}")

    def iptal_eden_karsilastirma_grafigi_eski(
        self, il_gruplari: Dict[str, pd.DataFrame], gun_tarihi: str
    ):
        """Eski fonksiyon - devre dışı bırakıldı"""
        return None

    def iptal_eden_karsilastirma_grafigi(
        self, il_gruplari: Dict[str, pd.DataFrame], gun_tarihi: str
    ):
        """İl içi ve il dışı iptal eden kurumları karşılaştırma grafiği - Yatay Stacked Bar"""
        try:
            # İl içi ve il dışı verilerini al
            il_ici_df = il_gruplari.get("Il_Ici", pd.DataFrame())
            il_disi_df = il_gruplari.get("Il_Disi", pd.DataFrame())

            if il_ici_df.empty and il_disi_df.empty:
                logger.warning("İl içi veya il dışı verisi bulunamadı")
                return None

            # İptal eden veri toplama fonksiyonu
            def iptal_eden_sayisi_al(df):
                if df.empty:
                    return {"KKM": 0, "Gönderen": 0}

                # Geçerli vakaları al
                gecerli_vakalar = df[
                    df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])
                ]
                if len(gecerli_vakalar) == 0:
                    return {"KKM": 0, "Gönderen": 0}

                # İptal edilmiş vakaları al
                iptal_vakalar = gecerli_vakalar[
                    gecerli_vakalar["durum"].str.contains("İptal", na=False)
                ]
                if len(iptal_vakalar) == 0:
                    return {"KKM": 0, "Gönderen": 0}

                # İptal eden sütununu kontrol et
                if "i̇ptal eden" not in iptal_vakalar.columns:
                    return {"KKM": 0, "Gönderen": 0}

                # İptal eden sayımları
                iptal_eden_sayimlari = (
                    iptal_vakalar["i̇ptal eden"].dropna().value_counts()
                )

                # KKM ve Gönderen sayılarını hesapla
                kkm_sayi = iptal_eden_sayimlari.get("KKM", 0)
                gonderen_sayi = sum(
                    count
                    for kurum, count in iptal_eden_sayimlari.items()
                    if kurum != "KKM"
                )

                return {"KKM": kkm_sayi, "Gönderen": gonderen_sayi}

            # İl içi ve il dışı verilerini topla
            il_ici_veriler = iptal_eden_sayisi_al(il_ici_df)
            il_disi_veriler = iptal_eden_sayisi_al(il_disi_df)

            # Veri kontrolü
            toplam_veri = sum(il_ici_veriler.values()) + sum(il_disi_veriler.values())
            if toplam_veri == 0:
                logger.warning("İptal eden veri bulunamadı")
                return None

            # Grafik oluştur
            fig, ax = plt.subplots(figsize=(14, 10))

            # Veri hazırlama - STACKED BAR İÇİN
            il_ici_degerler = [
                il_ici_veriler.get("KKM", 0),
                il_ici_veriler.get("Gönderen", 0),
            ]
            il_disi_degerler = [
                il_disi_veriler.get("KKM", 0),
                il_disi_veriler.get("Gönderen", 0),
            ]

            # Y konumları
            y_pos = [0, 1]  # İl Dışı ve İl İçi için basit pozisyonlar

            # STACKED BAR MANTIGI - Yatay çubuk grafiği oluştur
            bar_height = 0.6

            # KKM değerleri (sol taraf)
            kkm_bars = ax.barh(
                y_pos,
                [il_disi_degerler[0], il_ici_degerler[0]],
                bar_height,
                label="KKM",
                color="#2E86AB",
                alpha=0.8,
            )
            # Gönderen değerleri (KKM'nin üzerine)
            gonderen_bars = ax.barh(
                y_pos,
                [il_disi_degerler[1], il_ici_degerler[1]],
                bar_height,
                left=[il_disi_degerler[0], il_ici_degerler[0]],
                label="Gönderen",
                color="#A23B72",
                alpha=0.8,
            )

            # Değerleri çubukların üzerine yaz
            # KKM değerleri
            if il_disi_degerler[0] > 0:
                ax.text(
                    il_disi_degerler[0] / 2,
                    0,
                    str(il_disi_degerler[0]),
                    ha="center",
                    va="center",
                    fontweight="bold",
                    fontsize=10,
                )
            if il_ici_degerler[0] > 0:
                ax.text(
                    il_ici_degerler[0] / 2,
                    1,
                    str(il_ici_degerler[0]),
                    ha="center",
                    va="center",
                    fontweight="bold",
                    fontsize=10,
                )

            # Gönderen değerleri
            if il_disi_degerler[1] > 0:
                ax.text(
                    il_disi_degerler[0] + il_disi_degerler[1] / 2,
                    0,
                    str(il_disi_degerler[1]),
                    ha="center",
                    va="center",
                    fontweight="bold",
                    fontsize=10,
                )
            if il_ici_degerler[1] > 0:
                ax.text(
                    il_ici_degerler[0] + il_ici_degerler[1] / 2,
                    1,
                    str(il_ici_degerler[1]),
                    ha="center",
                    va="center",
                    fontweight="bold",
                    fontsize=10,
                )

            # Eksen ayarları
            ax.set_yticks(y_pos)
            ax.set_yticklabels(["İl Dışı", "İl İçi"], fontsize=12)
            ax.set_xlabel("İptal Vaka Sayısı", fontweight="bold", fontsize=12)
            ax.set_title("İptal Eden Kurumlar", fontsize=16, fontweight="bold", pad=20)

            # Legend
            ax.legend(loc="lower right", fontsize=11)

            # Grid
            ax.grid(axis="x", alpha=0.3)

            # İstatistikler
            il_ici_toplam = sum(il_ici_degerler)
            il_disi_toplam = sum(il_disi_degerler)
            genel_toplam = il_ici_toplam + il_disi_toplam

            # Alt bilgi
            istatistik_metni = (
                f"İl İçi Toplam: {il_ici_toplam}\n"
                f"İl Dışı Toplam: {il_disi_toplam}\n"
                f"Genel Toplam: {genel_toplam}"
            )
            ax.text(
                0.02,
                0.98,
                istatistik_metni,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
            )

            plt.tight_layout()

            # Dosya kayıt
            dosya_adi = f"iptal-eden-kurumlar_{gun_tarihi}.png"
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi
            plt.savefig(dosya_yolu, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"İptal eden karşılaştırma grafiği oluşturuldu: {dosya_yolu}")
            return dosya_yolu

        except Exception as e:
            logger.error(f"İptal eden karşılaştırma grafiği oluşturma hatası: {e}")
            return None

    def _grafige_tarih_ekle_eski(self, plt_obj, gun_tarihi: str):
        """Eski tarih ekleme fonksiyonu - kullanılmıyor artık"""
        pass

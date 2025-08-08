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

from config import (
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

# Grafik ayarları
plt.style.use("default")
sns.set_palette("husl")


class GrafikOlusturucu:
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
        """İptal eden dağılımı yatay çubuk grafiği"""
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

        except Exception as e:
            logger.error(f"Pasta grafiği oluşturma hatası: {e}")

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
            dosya_adi = f"vaka-tipi-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"
            
            # Pasta grafik oluştur
            self.pasta_grafik_olustur(vaka_tipi_sayimlari, baslik, dosya_adi)
            
            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi
            
        except Exception as e:
            logger.error(f"Vaka tipi pasta grafiği hatası: {e}")
            return None

    def il_dagilim_pasta_grafigi(self, il_gruplari: dict, gun_tarihi: str):
        """İl dağılımı pasta grafiği (İl İçi/İl Dışı)"""
        try:
            # İl gruplarından veri sayılarını hesapla
            il_dagilim = {}
            for grup_adi, df in il_gruplari.items():
                if len(df) > 0:
                    gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
                    il_dagilim[grup_adi] = len(gecerli_vakalar)
            
            if not il_dagilim or sum(il_dagilim.values()) == 0:
                logger.warning("İl dağılımı için geçerli vaka bulunamadı")
                return None
                
            # Pandas Series'e çevir  
            import pandas as pd
            il_dagilim_series = pd.Series(il_dagilim)
            
            baslik = "İl Dağılımı - Bütün Vakalar"
            dosya_adi = f"il-dagilimi_Butun_Vakalar_{gun_tarihi}.png"
            
            # Pasta grafik oluştur
            self.pasta_grafik_olustur(il_dagilim_series, baslik, dosya_adi)
            
            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi
            
        except Exception as e:
            logger.error(f"İl dağılım pasta grafiği hatası: {e}")
            return None

    def solunum_islemi_pasta_grafigi(self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str):
        """Solunum işlemi dağılımı pasta grafiği"""
        try:
            # Sadece geçerli vakaları al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
            
            if len(gecerli_vakalar) == 0:
                logger.warning(f"Solunum işlemi için geçerli vaka bulunamadı: {grup_adi}")
                return None
                
            # Solunum işlemi sütununu kontrol et
            solunum_sutun = None
            for sutun in ["solunum işlemi", "solunum_islemi", "Solunum İşlemi"]:
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

    def iptal_nedenleri_cubuk_grafigi(self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str, vaka_tipi: str):
        """İptal nedenleri çubuk grafiği"""
        try:
            # Sadece geçerli vakaları al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
            
            if len(gecerli_vakalar) == 0:
                logger.warning(f"İptal nedenleri için geçerli vaka bulunamadı: {grup_adi}")
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
            iptal_nedeni_sayimlari = iptal_vakalar[iptal_nedeni_sutun].dropna().value_counts()
            
            if len(iptal_nedeni_sayimlari) == 0:
                logger.warning(f"İptal nedeni verisi bulunamadı: {grup_adi}")
                return None
                
            # Çubuk grafik oluştur
            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)
            renkler = PASTA_GRAFIK_RENK_PALETI[: len(iptal_nedeni_sayimlari)]
            
            bars = plt.bar(range(len(iptal_nedeni_sayimlari)), iptal_nedeni_sayimlari.values, color=renkler)
            
            # Sayıları çubukların üzerinde göster
            for bar, sayi in zip(bars, iptal_nedeni_sayimlari.values):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + max(iptal_nedeni_sayimlari.values) * 0.01,
                        f'{sayi}', ha='center', va='bottom', fontweight='bold')
            
            plt.xticks(range(len(iptal_nedeni_sayimlari)), iptal_nedeni_sayimlari.index, rotation=45, ha='right')
            plt.ylabel('Vaka Sayısı', fontsize=12, fontweight='bold')
            plt.grid(axis='y', alpha=0.3)
            
            # Grup adını Türkçe'ye çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            vaka_tipi_adi = GRUP_ADI_CEVIRI.get(vaka_tipi, vaka_tipi)
            
            plt.title(
                f"İptal Nedenleri - {bolge_adi} - {vaka_tipi_adi}\n"
                f"Toplam: {iptal_nedeni_sayimlari.sum()} vaka",
                fontsize=14,
                fontweight="bold",
                pad=20
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
                
            with open(config_dosya, 'r', encoding='utf-8') as f:
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
                x, y, metin,
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
                    edgecolor="none"
                )
            )
            
            # Layout'u ayarla ki metin kesilmesin
            plt_obj.tight_layout()
            if konum == "alt":
                plt_obj.subplots_adjust(bottom=0.15)
            else:
                plt_obj.subplots_adjust(top=0.85)
                
        except Exception as e:
            logger.warning(f"Grafik metin ekleme hatası: {e}")

    def _grafige_tarih_ekle_eski(self, plt_obj, gun_tarihi: str):
        """Eski tarih ekleme fonksiyonu - kullanılmıyor artık"""
        pass

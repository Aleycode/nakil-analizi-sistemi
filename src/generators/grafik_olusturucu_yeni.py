"""
Grafik oluþturucu modülü - Tüm grafik oluþturma fonksiyonlarý
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

# Logger yapýlandýrmasý
logger = logging.getLogger(__name__)

# Grafik ayarlarý
plt.style.use("default")
sns.set_palette("husl")


class GrafikOlusturucu:
    """Tüm grafik oluþturma iþlemleri"""

    def __init__(self):
        """Grafik oluþturucu baþlatma"""
        # Grafik klasörü oluþtur
        RAPOR_DIZIN.mkdir(parents=True, exist_ok=True)

    def _grafik_baslik_olustur(self, sablon_adi: str, **kwargs) -> str:
        """
        Config'den grafik baþlýk þablonunu kullanarak baþlýk oluþturur
        """
        try:
            if sablon_adi in GRAFIK_BASLIK_SABLONLARI:
                sablon = GRAFIK_BASLIK_SABLONLARI[sablon_adi]
                baslik = sablon.format(**kwargs)
            else:
                # Varsayýlan þablon
                sablon = GRAFIK_BASLIK_SABLONLARI.get("genel", "{analiz_tipi}")
                baslik = sablon.format(**kwargs)

            # Grup adlarýný çevir
            for kod, turkce in GRUP_ADI_CEVIRI.items():
                baslik = baslik.replace(kod, turkce)

            return baslik
        except Exception as e:
            logger.warning(
                f"Baþlýk oluþturma hatasý: {e}, varsayýlan baþlýk kullanýlýyor"
            )
            return kwargs.get("analiz_tipi", "Grafik")

    def _tarih_klasoru_olustur(self, gun_tarihi: str) -> Path:
        """Verilen tarih için klasör oluþturur ve path döner"""
        tarih_klasor = RAPOR_DIZIN / gun_tarihi
        tarih_klasor.mkdir(parents=True, exist_ok=True)
        return tarih_klasor

    def iptal_eden_cubuk_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str
    ):
        """Ýptal eden daðýlýmý tek çubuk stacked grafik"""
        try:
            # Önce sadece geçerli vakalarý al (Analiz dýþý hariç)
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
            if len(gecerli_vakalar) == 0:
                logger.warning(f"Geçerli vaka bulunamadý: {grup_adi}")
                return None

            # Geçerli vakalar içinden iptal edilmiþ olanlarý al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("Ýptal", na=False)
            ]
            if len(iptal_vakalar) == 0:
                mesaj = (
                    f"Geçerli vakalar içinde iptal edilmiþ vaka bulunamadý, "
                    f"iptal eden çubuk grafiði oluþturulamadý: {grup_adi}"
                )
                logger.warning(mesaj)
                return None

            # Ýptal Eden sütununu kontrol et
            if "i·ptal eden" not in iptal_vakalar.columns:
                logger.warning(f"'i·ptal eden' sütunu bulunamadý: {grup_adi}")
                return None

            # Ýptal eden sayýmlarý (boþ deðerleri hariç tut)
            iptal_eden_sayimlari = iptal_vakalar["i·ptal eden"].dropna().value_counts()

            if iptal_eden_sayimlari.empty:
                logger.warning(f"Ýptal eden verisi bulunamadý: {grup_adi}")
                return None

            # En çok iptal eden ilk 10'u al
            top_iptal_eden = iptal_eden_sayimlari.head(10)

            # Renk paleti - her kuruma farklý renk
            import matplotlib.cm as cm

            colors = cm.Set3(range(len(top_iptal_eden)))

            # Tek çubuk stacked grafik oluþtur
            fig, ax = plt.subplots(figsize=(12, 6))

            # Kümülatif deðerler için baþlangýç
            left = 0

            # Her kurum için stacked bar ekle (horizontal)
            for i, (kurum, sayi) in enumerate(top_iptal_eden.items()):
                ax.barh(
                    ["Ýptal Eden Kurumlar"],
                    [sayi],
                    left=left,
                    color=colors[i],
                    label=f"{kurum} ({sayi})",
                )
                left += sayi  # Bölge adýný düzenle
            if grup_adi == "Il_Ici":
                bolge_adi = "Ýl Ýçi"
            elif grup_adi == "Il_Disi":
                bolge_adi = "Ýl Dýþý"
            elif grup_adi == "Butun_Bolgeler":
                bolge_adi = "Bütün Bölgeler"
            else:
                bolge_adi = grup_adi

            # Baþlýk ve etiketler
            ax.set_title(
                f"Ýptal Eden Kurumlar - {bolge_adi}",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )
            ax.set_xlabel("Vaka Sayýsý", fontweight="bold")
            ax.set_ylabel("")

            # Legend'ý sað tarafa yerleþtir
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

            # Grid
            ax.grid(True, alpha=0.3)
            ax.set_axisbelow(True)

            # Layout ayarla
            plt.tight_layout()

            # Dosya adýný oluþtur ve kaydet
            dosya_adi = f"iptal-eden-dagilimi_{bolge_adi}_{gun_tarihi}.png"
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi
            plt.savefig(dosya_yolu, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Ýptal eden stacked çubuk grafiði oluþturuldu: {dosya_yolu}")
            return dosya_yolu

        except Exception as e:
            logger.error(f"Ýptal eden stacked çubuk grafiði oluþturma hatasý: {e}")
            return None
        try:
            # Önce sadece geçerli vakalarý al (Analiz dýþý hariç)
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(f"Geçerli vaka bulunamadý: {grup_adi}")
                return None

            # Geçerli vakalar içinden iptal edilmiþ olanlarý al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("Ýptal", na=False)
            ]

            if len(iptal_vakalar) == 0:
                mesaj = (
                    f"Geçerli vakalar içinde iptal edilmiþ vaka bulunamadý, "
                    f"iptal eden çubuk grafiði oluþturulamadý: {grup_adi}"
                )
                logger.warning(mesaj)
                return None

            # Ýptal Eden sütununu kontrol et
            if "i·ptal eden" not in iptal_vakalar.columns:
                logger.warning(f"'i·ptal eden' sütunu bulunamadý: {grup_adi}")
                return None

            # Ýptal eden sayýmlarý (boþ deðerleri hariç tut)
            iptal_eden_sayimlari = iptal_vakalar["i·ptal eden"].dropna().value_counts()

            if len(iptal_eden_sayimlari) == 0:
                logger.warning(f"Ýptal eden verisi bulunamadý: {grup_adi}")
                return None

            # Minimum vaka sayýsý kontrolü
            if iptal_eden_sayimlari.sum() < 3:
                logger.warning(
                    f"Yetersiz iptal vakasý ({iptal_eden_sayimlari.sum()}), "
                    f"çubuk grafiði oluþturulamadý: {grup_adi}"
                )
                return None

            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)

            # Yatay çubuk grafiði oluþtur
            bars = plt.barh(
                range(len(iptal_eden_sayimlari)),
                iptal_eden_sayimlari.values,
                color=PASTA_GRAFIK_RENK_PALETI[: len(iptal_eden_sayimlari)],
            )

            # Y ekseni etiketlerini ayarla
            plt.yticks(range(len(iptal_eden_sayimlari)), iptal_eden_sayimlari.index)

            # Çubuklarýn üzerine sayýlarý yaz
            for i, (kurum, sayi) in enumerate(iptal_eden_sayimlari.items()):
                plt.text(sayi + 0.1, i, str(sayi), va="center", fontweight="bold")

            # Grup adýný çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            plt.title(
                f"Ýptal Eden Kurumlar - {bolge_adi}\n"
                f"Toplam: {iptal_eden_sayimlari.sum()} vaka",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )

            plt.xlabel("Vaka Sayýsý", fontweight="bold")
            plt.ylabel("Ýptal Eden Kurum", fontweight="bold")
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

            logger.info(f"Ýptal eden çubuk grafiði oluþturuldu: {dosya_adi}")
            return dosya_adi

        except Exception as e:
            logger.error(f"Ýptal eden çubuk grafiði oluþturma hatasý: {e}")
            return None

    def pasta_grafik_olustur(self, veriler: pd.Series, baslik: str, dosya_adi: str):
        """Pasta grafiði oluþturur - hem sayý hem yüzde gösterir"""
        try:
            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)

            # En çok 10 kategori göster
            if len(veriler) > 10:
                top_10 = veriler.head(10)
                diger_toplam = veriler.iloc[10:].sum()
                if diger_toplam > 0:
                    top_10["Diðer"] = diger_toplam
                veriler = top_10

            # Baþlýktaki grup adlarýný çevir
            for kod, turkce in GRUP_ADI_CEVIRI.items():
                baslik = baslik.replace(kod, turkce)

            # Hem sayý hem yüzde göstermek için özel etiket fonksiyonu
            def autopct_format(pct):
                absolute = int(round(pct / 100.0 * veriler.sum()))
                return f"{pct:.1f}%\n({absolute:,})"

            # Geliþmiþ renk paleti kullan
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

            # Tarih bilgisini dosya adýndan çýkar
            gun_tarihi = dosya_adi.split("_")[-1].replace(".png", "")

            # Tarih klasörü oluþtur ve dosyaya kaydet
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi

            # Metin ekle (config'den)
            self._grafige_metin_ekle(plt, str(dosya_yolu), gun_tarihi)

            plt.savefig(dosya_yolu, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

        except Exception as e:
            logger.error(f"Pasta grafiði oluþturma hatasý: {e}")

    def _grafige_tarih_ekle(self, plt_obj, gun_tarihi: str):
        """Grafiklere tarih bilgisi ekler"""
        try:
            if not GRAFIK_GORUNUM_AYARLARI.get("tarih_goster", True):
                return

            konum = GRAFIK_GORUNUM_AYARLARI.get("tarih_konum", "alt_sag")
            boyut = GRAFIK_GORUNUM_AYARLARI.get("tarih_boyut", 8)

            # Tarih formatýný düzenle
            tarih_obj = datetime.strptime(gun_tarihi, "%Y-%m-%d")
            tarih_text = tarih_obj.strftime("%d.%m.%Y")

            # Konum ayarlarý
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
            logger.warning(f"Tarih ekleme hatasý: {e}")

    def _tarih_klasoru_olustur(self, gun_tarihi: str) -> Path:
        """Verilen tarih için rapor klasörü oluþturur"""
        tarih_klasor = RAPOR_DIZIN / gun_tarihi
        tarih_klasor.mkdir(parents=True, exist_ok=True)
        return tarih_klasor

    def threshold_pasta_grafik(self, threshold_data: dict, baslik: str, dosya_adi: str):
        """Bekleme süresi threshold pasta grafiði"""
        try:
            if not threshold_data:
                return None

            # Dictionary'yi Series'e çevir
            import pandas as pd

            veriler = pd.Series(threshold_data)

            # Pasta grafik oluþtur
            self.pasta_grafik_olustur(veriler, baslik, dosya_adi)
        except Exception as e:
            logger.error(f"Threshold pasta grafik hatasý: {e}")

    def vaka_tipi_pasta_grafigi(self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str):
        """Vaka tipi daðýlýmý pasta grafiði (Yeni/Devreden)"""
        try:
            # Sadece geçerli vakalarý al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(f"Vaka tipi için geçerli vaka bulunamadý: {grup_adi}")
                return None

            # Vaka tipi sayýmlarý
            vaka_tipi_sayimlari = gecerli_vakalar["vaka_tipi"].value_counts()

            # Grup adýný Türkçe'ye çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            baslik = f"Vaka Tipi Daðýlýmý - {bolge_adi}"
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            dosya_adi = f"il-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"

            # Pasta grafik oluþtur
            self.pasta_grafik_olustur(vaka_tipi_sayimlari, baslik, dosya_adi)

            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Vaka tipi pasta grafiði hatasý: {e}")
            return None

    def il_dagilim_pasta_grafigi(self, il_gruplari: dict, gun_tarihi: str):
        """Bölge daðýlýmý çubuk grafiði (Ýl Ýçi/Ýl Dýþý)"""
        try:
            # Sadece Ýl Ýçi ve Ýl Dýþý'ný kullan (Butun_Bolgeler hariç)
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

            # Ýl daðýlýmý dictionary'sini oluþtur
            il_dagilim = {"Ýl Ýçi": il_ici_sayisi, "Ýl Dýþý": il_disi_sayisi}

            if not il_dagilim or sum(il_dagilim.values()) == 0:
                logger.warning("Bölge daðýlýmý için geçerli vaka bulunamadý")
                return None

            # Pandas Series'e çevir
            import pandas as pd

            il_dagilim_series = pd.Series(il_dagilim)

            baslik = "Bölge Daðýlýmý"
            dosya_adi = f"il-dagilimi_Butun_Vakalar_{gun_tarihi}.png"

            # Pasta grafik oluþtur
            self.pasta_grafik_olustur(il_dagilim_series, baslik, dosya_adi)

            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Bölge daðýlýmý çubuk grafiði hatasý: {e}")
            return None

    def solunum_islemi_pasta_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str
    ):
        """Solunum iþlemi daðýlýmý pasta grafiði"""
        try:
            # Sadece geçerli vakalarý al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(
                    f"Solunum iþlemi için geçerli vaka bulunamadý: {grup_adi}"
                )
                return None

            # Solunum iþlemi sütununu kontrol et
            solunum_sutun = None
            for sutun in ["solunum iþlemi", "solunum_islemi", "Solunum Ýþlemi"]:
                if sutun in gecerli_vakalar.columns:
                    solunum_sutun = sutun
                    break

            if solunum_sutun is None:
                logger.warning(f"Solunum iþlemi sütunu bulunamadý: {grup_adi}")
                return None

            # Solunum iþlemi sayýmlarý (boþ deðerleri hariç tut)
            solunum_sayimlari = gecerli_vakalar[solunum_sutun].dropna().value_counts()

            if len(solunum_sayimlari) == 0:
                logger.warning(f"Solunum iþlemi verisi bulunamadý: {grup_adi}")
                return None

            # Grup adýný Türkçe'ye çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            baslik = f"Solunum Ýþlemi Daðýlýmý - {bolge_adi}"
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            dosya_adi = f"solunum-islemi-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"

            # Pasta grafik oluþtur
            self.pasta_grafik_olustur(solunum_sayimlari, baslik, dosya_adi)

            # Dosya yolunu döndür
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Solunum iþlemi pasta grafiði hatasý: {e}")
            return None

    def iptal_nedenleri_cubuk_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str, vaka_tipi: str
    ):
        """Ýptal nedenleri çubuk grafiði"""
        try:
            # Sadece geçerli vakalarý al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(
                    f"Ýptal nedenleri için geçerli vaka bulunamadý: {grup_adi}"
                )
                return None

            # Ýptal edilmiþ vakalarý al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("Ýptal", na=False)
            ]

            if len(iptal_vakalar) == 0:
                logger.warning(f"Ýptal edilmiþ vaka bulunamadý: {grup_adi}")
                return None

            # Ýptal nedeni sütununu kontrol et
            iptal_nedeni_sutun = None
            for sutun in ["iptal nedeni", "iptal_nedeni", "Ýptal Nedeni"]:
                if sutun in iptal_vakalar.columns:
                    iptal_nedeni_sutun = sutun
                    break

            if iptal_nedeni_sutun is None:
                logger.warning(f"Ýptal nedeni sütunu bulunamadý: {grup_adi}")
                return None

            # Ýptal nedeni sayýmlarý (boþ deðerleri hariç tut)
            iptal_nedeni_sayimlari = (
                iptal_vakalar[iptal_nedeni_sutun].dropna().value_counts()
            )

            if len(iptal_nedeni_sayimlari) == 0:
                logger.warning(f"Ýptal nedeni verisi bulunamadý: {grup_adi}")
                return None

            # Çubuk grafik oluþtur
            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)
            renkler = PASTA_GRAFIK_RENK_PALETI[: len(iptal_nedeni_sayimlari)]

            bars = plt.bar(
                range(len(iptal_nedeni_sayimlari)),
                iptal_nedeni_sayimlari.values,
                color=renkler,
            )

            # Sayýlarý çubuklarýn üzerinde göster
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
            plt.ylabel("Vaka Sayýsý", fontsize=12, fontweight="bold")
            plt.grid(axis="y", alpha=0.3)

            # Grup adýný Türkçe'ye çevir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            vaka_tipi_adi = GRUP_ADI_CEVIRI.get(vaka_tipi, vaka_tipi)

            plt.title(
                f"Ýptal Nedenleri - {bolge_adi} - {vaka_tipi_adi}\n"
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

            logger.info(f"Ýptal nedenleri çubuk grafiði oluþturuldu: {dosya_adi}")
            return dosya_adi

        except Exception as e:
            logger.error(f"Ýptal nedenleri çubuk grafiði hatasý: {e}")
            if "plt" in locals():
                plt.close()
            return None

    def _grafige_metin_ekle(self, plt_obj, dosya_adi: str, gun_tarihi: str):
        """Grafiklere config'den gelen metinleri ekler"""
        try:
            # PDF config dosyasýný oku
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

            # Dosya adýndan grafik tipini belirle
            dosya_adi_base = Path(dosya_adi).stem

            # Özel metin var mý kontrol et
            ozel_metinler = metin_ayarlari.get("ozel_metinler", {})
            metin_config = None

            for desen, config_item in ozel_metinler.items():
                # Basit wildcard eþleþmesi
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

            # Font aðýrlýðý
            fontweight = "bold" if font_kalin else "normal"

            # Metin rengini al
            metin_rengi = metin_ayarlari.get("metin_rengi", "#333333")

            # Grafik boyutlarýný al
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
            logger.warning(f"Grafik metin ekleme hatasý: {e}")

    def iptal_eden_karsilastirma_grafigi_eski(
        self, il_gruplari: Dict[str, pd.DataFrame], gun_tarihi: str
    ):
        """Eski fonksiyon - devre dýþý býrakýldý"""
        return None

    def iptal_eden_karsilastirma_grafigi(
        self, il_gruplari: Dict[str, pd.DataFrame], gun_tarihi: str
    ):
        """Ä°l iÃ§i ve il dÄ±ÅŸÄ± iptal eden kurumlarÄ± karÅŸÄ±laÅŸtÄ±rma grafiÄŸi - Yatay Stacked Bar"""
        try:
            # Ä°l iÃ§i ve il dÄ±ÅŸÄ± verilerini al
            il_ici_df = il_gruplari.get("Il_Ici", pd.DataFrame())
            il_disi_df = il_gruplari.get("Il_Disi", pd.DataFrame())
            if il_ici_df.empty and il_disi_df.empty:
                logger.warning("Ä°l iÃ§i veya il dÄ±ÅŸÄ± verisi bulunamadÄ±")
                return None

            # Ä°ptal eden veri toplama fonksiyonu
            def iptal_eden_sayisi_al(df):
                if df.empty:
                    return {"KKM": 0, "GÃ¶nderen": 0}
                # GeÃ§erli vakalarÄ± al
                gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
                if len(gecerli_vakalar) == 0:
                    return {"KKM": 0, "GÃ¶nderen": 0}
                # Ä°ptal edilmiÅŸ vakalarÄ± al
                iptal_vakalar = gecerli_vakalar[
                    gecerli_vakalar["durum"].str.contains("Ä°ptal", na=False)
                ]
                if len(iptal_vakalar) == 0:
                    return {"KKM": 0, "GÃ¶nderen": 0}
                # Ä°ptal eden sÃ¼tununu kontrol et
                if "iÌ‡ptal eden" not in iptal_vakalar.columns:
                    return {"KKM": 0, "GÃ¶nderen": 0}
                # Ä°ptal eden sayÄ±mlarÄ±
                iptal_eden_sayimlari = iptal_vakalar["iÌ‡ptal eden"].dropna().value_counts()
                # KKM ve GÃ¶nderen sayÄ±larÄ±nÄ± hesapla
                kkm_sayi = iptal_eden_sayimlari.get("KKM", 0)
                gonderen_sayi = sum(
                    count for kurum, count in iptal_eden_sayimlari.items()
                    if kurum != "KKM"
                )
                return {"KKM": kkm_sayi, "GÃ¶nderen": gonderen_sayi}

            # Ä°l iÃ§i ve il dÄ±ÅŸÄ± verilerini topla
            il_ici_veriler = iptal_eden_sayisi_al(il_ici_df)
            il_disi_veriler = iptal_eden_sayisi_al(il_disi_df)

            # Veri kontrolÃ¼
            toplam_veri = sum(il_ici_veriler.values()) + sum(il_disi_veriler.values())
            if toplam_veri == 0:
                logger.warning("Ä°ptal eden veri bulunamadÄ±")
                return None

            # Grafik oluÅŸtur - GERÃ‡EK STACKED BAR MANTIGI
            fig, ax = plt.subplots(figsize=(12, 6))

            # Kategoriler ve veriler - STACKED BAR MANTIGI  
            kategoriler = ['Ä°l DÄ±ÅŸÄ±', 'Ä°l Ä°Ã§i']  # Y ekseninde yukarÄ±dan aÅŸaÄŸÄ±ya
            
            # Her kategori iÃ§in KKM ve GÃ¶nderen deÄŸerleri
            il_ici_kkm = il_ici_veriler["KKM"]
            il_ici_gonderen = il_ici_veriler["GÃ¶nderen"] 
            il_disi_kkm = il_disi_veriler["KKM"]
            il_disi_gonderen = il_disi_veriler["GÃ¶nderen"]

            # Y pozisyonlarÄ±
            y_pos = [0, 1]  # Ä°l DÄ±ÅŸÄ±: 0, Ä°l Ä°Ã§i: 1
            bar_height = 0.6

            # Stacked bar - KKM deÄŸerleri (sol taraf)
            bars_kkm = ax.barh(y_pos, [il_disi_kkm, il_ici_kkm], bar_height,
                              label='KKM', color='#2E86AB', alpha=0.8)

            # Stacked bar - GÃ¶nderen deÄŸerleri (KKM'nin Ã¼zerine) 
            bars_gonderen = ax.barh(y_pos, [il_disi_gonderen, il_ici_gonderen], 
                                   bar_height, left=[il_disi_kkm, il_ici_kkm], 
                                   label='GÃ¶nderen', color='#A23B72', alpha=0.8)

            # DeÄŸerleri Ã§ubuklarÄ±n Ã¼zerine yaz
            # KKM deÄŸerleri
            if il_disi_kkm > 0:
                ax.text(il_disi_kkm/2, y_pos[0], str(il_disi_kkm),
                       ha='center', va='center', fontweight='bold', fontsize=10)
            if il_ici_kkm > 0:
                ax.text(il_ici_kkm/2, y_pos[1], str(il_ici_kkm),
                       ha='center', va='center', fontweight='bold', fontsize=10)

            # GÃ¶nderen deÄŸerleri
            if il_disi_gonderen > 0:
                ax.text(il_disi_kkm + il_disi_gonderen/2, y_pos[0], 
                       str(il_disi_gonderen), ha='center', va='center', 
                       fontweight='bold', fontsize=10)
            if il_ici_gonderen > 0:
                ax.text(il_ici_kkm + il_ici_gonderen/2, y_pos[1], 
                       str(il_ici_gonderen), ha='center', va='center',
                       fontweight='bold', fontsize=10)

            # Eksen ayarlarÄ±
            ax.set_yticks(y_pos)
            ax.set_yticklabels(kategoriler, fontsize=12)
            ax.set_xlabel('Ä°ptal Vaka SayÄ±sÄ±', fontweight='bold', fontsize=12)
            ax.set_title('Ä°ptal Eden Kurumlar', fontsize=16, 
                        fontweight='bold', pad=20)

            # Legend
            ax.legend(loc='lower right', fontsize=11)

            # Grid
            ax.grid(axis='x', alpha=0.3)

            plt.tight_layout()

            # Dosya kayÄ±t
            dosya_adi = f"iptal-eden-kurumlar_{gun_tarihi}.png"
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi
            plt.savefig(dosya_yolu, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"Ä°ptal eden karÅŸÄ±laÅŸtÄ±rma grafiÄŸi oluÅŸturuldu: {dosya_yolu}")
            return dosya_yolu

        except Exception as e:
            logger.error(f"Ä°ptal eden karÅŸÄ±laÅŸtÄ±rma grafiÄŸi oluÅŸturma hatasÄ±: {e}")
            return None
            return None

    def _grafige_tarih_ekle_eski(self, plt_obj, gun_tarihi: str):
        """Eski tarih ekleme fonksiyonu - kullanýlmýyor artýk"""
        pass

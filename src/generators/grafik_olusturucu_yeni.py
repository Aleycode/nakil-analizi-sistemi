"""
Grafik olu�turucu mod�l� - T�m grafik olu�turma fonksiyonlar�
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

# Logger yap�land�rmas�
logger = logging.getLogger(__name__)

# Grafik ayarlar�
plt.style.use("default")
sns.set_palette("husl")


class GrafikOlusturucu:
    """T�m grafik olu�turma i�lemleri"""

    def __init__(self):
        """Grafik olu�turucu ba�latma"""
        # Grafik klas�r� olu�tur
        RAPOR_DIZIN.mkdir(parents=True, exist_ok=True)

    def _grafik_baslik_olustur(self, sablon_adi: str, **kwargs) -> str:
        """
        Config'den grafik ba�l�k �ablonunu kullanarak ba�l�k olu�turur
        """
        try:
            if sablon_adi in GRAFIK_BASLIK_SABLONLARI:
                sablon = GRAFIK_BASLIK_SABLONLARI[sablon_adi]
                baslik = sablon.format(**kwargs)
            else:
                # Varsay�lan �ablon
                sablon = GRAFIK_BASLIK_SABLONLARI.get("genel", "{analiz_tipi}")
                baslik = sablon.format(**kwargs)

            # Grup adlar�n� �evir
            for kod, turkce in GRUP_ADI_CEVIRI.items():
                baslik = baslik.replace(kod, turkce)

            return baslik
        except Exception as e:
            logger.warning(
                f"Ba�l�k olu�turma hatas�: {e}, varsay�lan ba�l�k kullan�l�yor"
            )
            return kwargs.get("analiz_tipi", "Grafik")

    def _tarih_klasoru_olustur(self, gun_tarihi: str) -> Path:
        """Verilen tarih i�in klas�r olu�turur ve path d�ner"""
        tarih_klasor = RAPOR_DIZIN / gun_tarihi
        tarih_klasor.mkdir(parents=True, exist_ok=True)
        return tarih_klasor

    def iptal_eden_cubuk_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str
    ):
        """�ptal eden da��l�m� tek �ubuk stacked grafik"""
        try:
            # �nce sadece ge�erli vakalar� al (Analiz d��� hari�)
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
            if len(gecerli_vakalar) == 0:
                logger.warning(f"Ge�erli vaka bulunamad�: {grup_adi}")
                return None

            # Ge�erli vakalar i�inden iptal edilmi� olanlar� al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("�ptal", na=False)
            ]
            if len(iptal_vakalar) == 0:
                mesaj = (
                    f"Ge�erli vakalar i�inde iptal edilmi� vaka bulunamad�, "
                    f"iptal eden �ubuk grafi�i olu�turulamad�: {grup_adi}"
                )
                logger.warning(mesaj)
                return None

            # �ptal Eden s�tununu kontrol et
            if "i�ptal eden" not in iptal_vakalar.columns:
                logger.warning(f"'i�ptal eden' s�tunu bulunamad�: {grup_adi}")
                return None

            # �ptal eden say�mlar� (bo� de�erleri hari� tut)
            iptal_eden_sayimlari = iptal_vakalar["i�ptal eden"].dropna().value_counts()

            if iptal_eden_sayimlari.empty:
                logger.warning(f"�ptal eden verisi bulunamad�: {grup_adi}")
                return None

            # En �ok iptal eden ilk 10'u al
            top_iptal_eden = iptal_eden_sayimlari.head(10)

            # Renk paleti - her kuruma farkl� renk
            import matplotlib.cm as cm

            colors = cm.Set3(range(len(top_iptal_eden)))

            # Tek �ubuk stacked grafik olu�tur
            fig, ax = plt.subplots(figsize=(12, 6))

            # K�m�latif de�erler i�in ba�lang��
            left = 0

            # Her kurum i�in stacked bar ekle (horizontal)
            for i, (kurum, sayi) in enumerate(top_iptal_eden.items()):
                ax.barh(
                    ["�ptal Eden Kurumlar"],
                    [sayi],
                    left=left,
                    color=colors[i],
                    label=f"{kurum} ({sayi})",
                )
                left += sayi  # B�lge ad�n� d�zenle
            if grup_adi == "Il_Ici":
                bolge_adi = "�l ��i"
            elif grup_adi == "Il_Disi":
                bolge_adi = "�l D���"
            elif grup_adi == "Butun_Bolgeler":
                bolge_adi = "B�t�n B�lgeler"
            else:
                bolge_adi = grup_adi

            # Ba�l�k ve etiketler
            ax.set_title(
                f"�ptal Eden Kurumlar - {bolge_adi}",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )
            ax.set_xlabel("Vaka Say�s�", fontweight="bold")
            ax.set_ylabel("")

            # Legend'� sa� tarafa yerle�tir
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

            # Grid
            ax.grid(True, alpha=0.3)
            ax.set_axisbelow(True)

            # Layout ayarla
            plt.tight_layout()

            # Dosya ad�n� olu�tur ve kaydet
            dosya_adi = f"iptal-eden-dagilimi_{bolge_adi}_{gun_tarihi}.png"
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi
            plt.savefig(dosya_yolu, dpi=300, bbox_inches="tight")
            plt.close()

            logger.info(f"�ptal eden stacked �ubuk grafi�i olu�turuldu: {dosya_yolu}")
            return dosya_yolu

        except Exception as e:
            logger.error(f"�ptal eden stacked �ubuk grafi�i olu�turma hatas�: {e}")
            return None
        try:
            # �nce sadece ge�erli vakalar� al (Analiz d��� hari�)
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(f"Ge�erli vaka bulunamad�: {grup_adi}")
                return None

            # Ge�erli vakalar i�inden iptal edilmi� olanlar� al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("�ptal", na=False)
            ]

            if len(iptal_vakalar) == 0:
                mesaj = (
                    f"Ge�erli vakalar i�inde iptal edilmi� vaka bulunamad�, "
                    f"iptal eden �ubuk grafi�i olu�turulamad�: {grup_adi}"
                )
                logger.warning(mesaj)
                return None

            # �ptal Eden s�tununu kontrol et
            if "i�ptal eden" not in iptal_vakalar.columns:
                logger.warning(f"'i�ptal eden' s�tunu bulunamad�: {grup_adi}")
                return None

            # �ptal eden say�mlar� (bo� de�erleri hari� tut)
            iptal_eden_sayimlari = iptal_vakalar["i�ptal eden"].dropna().value_counts()

            if len(iptal_eden_sayimlari) == 0:
                logger.warning(f"�ptal eden verisi bulunamad�: {grup_adi}")
                return None

            # Minimum vaka say�s� kontrol�
            if iptal_eden_sayimlari.sum() < 3:
                logger.warning(
                    f"Yetersiz iptal vakas� ({iptal_eden_sayimlari.sum()}), "
                    f"�ubuk grafi�i olu�turulamad�: {grup_adi}"
                )
                return None

            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)

            # Yatay �ubuk grafi�i olu�tur
            bars = plt.barh(
                range(len(iptal_eden_sayimlari)),
                iptal_eden_sayimlari.values,
                color=PASTA_GRAFIK_RENK_PALETI[: len(iptal_eden_sayimlari)],
            )

            # Y ekseni etiketlerini ayarla
            plt.yticks(range(len(iptal_eden_sayimlari)), iptal_eden_sayimlari.index)

            # �ubuklar�n �zerine say�lar� yaz
            for i, (kurum, sayi) in enumerate(iptal_eden_sayimlari.items()):
                plt.text(sayi + 0.1, i, str(sayi), va="center", fontweight="bold")

            # Grup ad�n� �evir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            plt.title(
                f"�ptal Eden Kurumlar - {bolge_adi}\n"
                f"Toplam: {iptal_eden_sayimlari.sum()} vaka",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )

            plt.xlabel("Vaka Say�s�", fontweight="bold")
            plt.ylabel("�ptal Eden Kurum", fontweight="bold")
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

            logger.info(f"�ptal eden �ubuk grafi�i olu�turuldu: {dosya_adi}")
            return dosya_adi

        except Exception as e:
            logger.error(f"�ptal eden �ubuk grafi�i olu�turma hatas�: {e}")
            return None

    def pasta_grafik_olustur(self, veriler: pd.Series, baslik: str, dosya_adi: str):
        """Pasta grafi�i olu�turur - hem say� hem y�zde g�sterir"""
        try:
            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)

            # En �ok 10 kategori g�ster
            if len(veriler) > 10:
                top_10 = veriler.head(10)
                diger_toplam = veriler.iloc[10:].sum()
                if diger_toplam > 0:
                    top_10["Di�er"] = diger_toplam
                veriler = top_10

            # Ba�l�ktaki grup adlar�n� �evir
            for kod, turkce in GRUP_ADI_CEVIRI.items():
                baslik = baslik.replace(kod, turkce)

            # Hem say� hem y�zde g�stermek i�in �zel etiket fonksiyonu
            def autopct_format(pct):
                absolute = int(round(pct / 100.0 * veriler.sum()))
                return f"{pct:.1f}%\n({absolute:,})"

            # Geli�mi� renk paleti kullan
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

            # Tarih bilgisini dosya ad�ndan ��kar
            gun_tarihi = dosya_adi.split("_")[-1].replace(".png", "")

            # Tarih klas�r� olu�tur ve dosyaya kaydet
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            dosya_yolu = tarih_klasor / dosya_adi

            # Metin ekle (config'den)
            self._grafige_metin_ekle(plt, str(dosya_yolu), gun_tarihi)

            plt.savefig(dosya_yolu, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

        except Exception as e:
            logger.error(f"Pasta grafi�i olu�turma hatas�: {e}")

    def _grafige_tarih_ekle(self, plt_obj, gun_tarihi: str):
        """Grafiklere tarih bilgisi ekler"""
        try:
            if not GRAFIK_GORUNUM_AYARLARI.get("tarih_goster", True):
                return

            konum = GRAFIK_GORUNUM_AYARLARI.get("tarih_konum", "alt_sag")
            boyut = GRAFIK_GORUNUM_AYARLARI.get("tarih_boyut", 8)

            # Tarih format�n� d�zenle
            tarih_obj = datetime.strptime(gun_tarihi, "%Y-%m-%d")
            tarih_text = tarih_obj.strftime("%d.%m.%Y")

            # Konum ayarlar�
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
            logger.warning(f"Tarih ekleme hatas�: {e}")

    def _tarih_klasoru_olustur(self, gun_tarihi: str) -> Path:
        """Verilen tarih i�in rapor klas�r� olu�turur"""
        tarih_klasor = RAPOR_DIZIN / gun_tarihi
        tarih_klasor.mkdir(parents=True, exist_ok=True)
        return tarih_klasor

    def threshold_pasta_grafik(self, threshold_data: dict, baslik: str, dosya_adi: str):
        """Bekleme s�resi threshold pasta grafi�i"""
        try:
            if not threshold_data:
                return None

            # Dictionary'yi Series'e �evir
            import pandas as pd

            veriler = pd.Series(threshold_data)

            # Pasta grafik olu�tur
            self.pasta_grafik_olustur(veriler, baslik, dosya_adi)
        except Exception as e:
            logger.error(f"Threshold pasta grafik hatas�: {e}")

    def vaka_tipi_pasta_grafigi(self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str):
        """Vaka tipi da��l�m� pasta grafi�i (Yeni/Devreden)"""
        try:
            # Sadece ge�erli vakalar� al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(f"Vaka tipi i�in ge�erli vaka bulunamad�: {grup_adi}")
                return None

            # Vaka tipi say�mlar�
            vaka_tipi_sayimlari = gecerli_vakalar["vaka_tipi"].value_counts()

            # Grup ad�n� T�rk�e'ye �evir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            baslik = f"Vaka Tipi Da��l�m� - {bolge_adi}"
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            dosya_adi = f"il-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"

            # Pasta grafik olu�tur
            self.pasta_grafik_olustur(vaka_tipi_sayimlari, baslik, dosya_adi)

            # Dosya yolunu d�nd�r
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Vaka tipi pasta grafi�i hatas�: {e}")
            return None

    def il_dagilim_pasta_grafigi(self, il_gruplari: dict, gun_tarihi: str):
        """B�lge da��l�m� �ubuk grafi�i (�l ��i/�l D���)"""
        try:
            # Sadece �l ��i ve �l D���'n� kullan (Butun_Bolgeler hari�)
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

            # �l da��l�m� dictionary'sini olu�tur
            il_dagilim = {"�l ��i": il_ici_sayisi, "�l D���": il_disi_sayisi}

            if not il_dagilim or sum(il_dagilim.values()) == 0:
                logger.warning("B�lge da��l�m� i�in ge�erli vaka bulunamad�")
                return None

            # Pandas Series'e �evir
            import pandas as pd

            il_dagilim_series = pd.Series(il_dagilim)

            baslik = "B�lge Da��l�m�"
            dosya_adi = f"il-dagilimi_Butun_Vakalar_{gun_tarihi}.png"

            # Pasta grafik olu�tur
            self.pasta_grafik_olustur(il_dagilim_series, baslik, dosya_adi)

            # Dosya yolunu d�nd�r
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"B�lge da��l�m� �ubuk grafi�i hatas�: {e}")
            return None

    def solunum_islemi_pasta_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str
    ):
        """Solunum i�lemi da��l�m� pasta grafi�i"""
        try:
            # Sadece ge�erli vakalar� al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(
                    f"Solunum i�lemi i�in ge�erli vaka bulunamad�: {grup_adi}"
                )
                return None

            # Solunum i�lemi s�tununu kontrol et
            solunum_sutun = None
            for sutun in ["solunum i�lemi", "solunum_islemi", "Solunum ��lemi"]:
                if sutun in gecerli_vakalar.columns:
                    solunum_sutun = sutun
                    break

            if solunum_sutun is None:
                logger.warning(f"Solunum i�lemi s�tunu bulunamad�: {grup_adi}")
                return None

            # Solunum i�lemi say�mlar� (bo� de�erleri hari� tut)
            solunum_sayimlari = gecerli_vakalar[solunum_sutun].dropna().value_counts()

            if len(solunum_sayimlari) == 0:
                logger.warning(f"Solunum i�lemi verisi bulunamad�: {grup_adi}")
                return None

            # Grup ad�n� T�rk�e'ye �evir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)

            baslik = f"Solunum ��lemi Da��l�m� - {bolge_adi}"
            turkce_dosya_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            dosya_adi = f"solunum-islemi-dagilimi_{turkce_dosya_adi}_{gun_tarihi}.png"

            # Pasta grafik olu�tur
            self.pasta_grafik_olustur(solunum_sayimlari, baslik, dosya_adi)

            # Dosya yolunu d�nd�r
            tarih_klasor = self._tarih_klasoru_olustur(gun_tarihi)
            return tarih_klasor / dosya_adi

        except Exception as e:
            logger.error(f"Solunum i�lemi pasta grafi�i hatas�: {e}")
            return None

    def iptal_nedenleri_cubuk_grafigi(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str, vaka_tipi: str
    ):
        """�ptal nedenleri �ubuk grafi�i"""
        try:
            # Sadece ge�erli vakalar� al
            gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]

            if len(gecerli_vakalar) == 0:
                logger.warning(
                    f"�ptal nedenleri i�in ge�erli vaka bulunamad�: {grup_adi}"
                )
                return None

            # �ptal edilmi� vakalar� al
            iptal_vakalar = gecerli_vakalar[
                gecerli_vakalar["durum"].str.contains("�ptal", na=False)
            ]

            if len(iptal_vakalar) == 0:
                logger.warning(f"�ptal edilmi� vaka bulunamad�: {grup_adi}")
                return None

            # �ptal nedeni s�tununu kontrol et
            iptal_nedeni_sutun = None
            for sutun in ["iptal nedeni", "iptal_nedeni", "�ptal Nedeni"]:
                if sutun in iptal_vakalar.columns:
                    iptal_nedeni_sutun = sutun
                    break

            if iptal_nedeni_sutun is None:
                logger.warning(f"�ptal nedeni s�tunu bulunamad�: {grup_adi}")
                return None

            # �ptal nedeni say�mlar� (bo� de�erleri hari� tut)
            iptal_nedeni_sayimlari = (
                iptal_vakalar[iptal_nedeni_sutun].dropna().value_counts()
            )

            if len(iptal_nedeni_sayimlari) == 0:
                logger.warning(f"�ptal nedeni verisi bulunamad�: {grup_adi}")
                return None

            # �ubuk grafik olu�tur
            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)
            renkler = PASTA_GRAFIK_RENK_PALETI[: len(iptal_nedeni_sayimlari)]

            bars = plt.bar(
                range(len(iptal_nedeni_sayimlari)),
                iptal_nedeni_sayimlari.values,
                color=renkler,
            )

            # Say�lar� �ubuklar�n �zerinde g�ster
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
            plt.ylabel("Vaka Say�s�", fontsize=12, fontweight="bold")
            plt.grid(axis="y", alpha=0.3)

            # Grup ad�n� T�rk�e'ye �evir
            bolge_adi = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            vaka_tipi_adi = GRUP_ADI_CEVIRI.get(vaka_tipi, vaka_tipi)

            plt.title(
                f"�ptal Nedenleri - {bolge_adi} - {vaka_tipi_adi}\n"
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

            logger.info(f"�ptal nedenleri �ubuk grafi�i olu�turuldu: {dosya_adi}")
            return dosya_adi

        except Exception as e:
            logger.error(f"�ptal nedenleri �ubuk grafi�i hatas�: {e}")
            if "plt" in locals():
                plt.close()
            return None

    def _grafige_metin_ekle(self, plt_obj, dosya_adi: str, gun_tarihi: str):
        """Grafiklere config'den gelen metinleri ekler"""
        try:
            # PDF config dosyas�n� oku
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

            # Dosya ad�ndan grafik tipini belirle
            dosya_adi_base = Path(dosya_adi).stem

            # �zel metin var m� kontrol et
            ozel_metinler = metin_ayarlari.get("ozel_metinler", {})
            metin_config = None

            for desen, config_item in ozel_metinler.items():
                # Basit wildcard e�le�mesi
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

            # Font a��rl���
            fontweight = "bold" if font_kalin else "normal"

            # Metin rengini al
            metin_rengi = metin_ayarlari.get("metin_rengi", "#333333")

            # Grafik boyutlar�n� al
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
            logger.warning(f"Grafik metin ekleme hatas�: {e}")

    def iptal_eden_karsilastirma_grafigi_eski(
        self, il_gruplari: Dict[str, pd.DataFrame], gun_tarihi: str
    ):
        """Eski fonksiyon - devre d��� b�rak�ld�"""
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
                gecerli_vakalar = df[df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
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
                iptal_eden_sayimlari = iptal_vakalar["i̇ptal eden"].dropna().value_counts()
                # KKM ve Gönderen sayılarını hesapla
                kkm_sayi = iptal_eden_sayimlari.get("KKM", 0)
                gonderen_sayi = sum(
                    count for kurum, count in iptal_eden_sayimlari.items()
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

            # Grafik oluştur - GERÇEK STACKED BAR MANTIGI
            fig, ax = plt.subplots(figsize=(12, 6))

            # Kategoriler ve veriler - STACKED BAR MANTIGI  
            kategoriler = ['İl Dışı', 'İl İçi']  # Y ekseninde yukarıdan aşağıya
            
            # Her kategori için KKM ve Gönderen değerleri
            il_ici_kkm = il_ici_veriler["KKM"]
            il_ici_gonderen = il_ici_veriler["Gönderen"] 
            il_disi_kkm = il_disi_veriler["KKM"]
            il_disi_gonderen = il_disi_veriler["Gönderen"]

            # Y pozisyonları
            y_pos = [0, 1]  # İl Dışı: 0, İl İçi: 1
            bar_height = 0.6

            # Stacked bar - KKM değerleri (sol taraf)
            bars_kkm = ax.barh(y_pos, [il_disi_kkm, il_ici_kkm], bar_height,
                              label='KKM', color='#2E86AB', alpha=0.8)

            # Stacked bar - Gönderen değerleri (KKM'nin üzerine) 
            bars_gonderen = ax.barh(y_pos, [il_disi_gonderen, il_ici_gonderen], 
                                   bar_height, left=[il_disi_kkm, il_ici_kkm], 
                                   label='Gönderen', color='#A23B72', alpha=0.8)

            # Değerleri çubukların üzerine yaz
            # KKM değerleri
            if il_disi_kkm > 0:
                ax.text(il_disi_kkm/2, y_pos[0], str(il_disi_kkm),
                       ha='center', va='center', fontweight='bold', fontsize=10)
            if il_ici_kkm > 0:
                ax.text(il_ici_kkm/2, y_pos[1], str(il_ici_kkm),
                       ha='center', va='center', fontweight='bold', fontsize=10)

            # Gönderen değerleri
            if il_disi_gonderen > 0:
                ax.text(il_disi_kkm + il_disi_gonderen/2, y_pos[0], 
                       str(il_disi_gonderen), ha='center', va='center', 
                       fontweight='bold', fontsize=10)
            if il_ici_gonderen > 0:
                ax.text(il_ici_kkm + il_ici_gonderen/2, y_pos[1], 
                       str(il_ici_gonderen), ha='center', va='center',
                       fontweight='bold', fontsize=10)

            # Eksen ayarları
            ax.set_yticks(y_pos)
            ax.set_yticklabels(kategoriler, fontsize=12)
            ax.set_xlabel('İptal Vaka Sayısı', fontweight='bold', fontsize=12)
            ax.set_title('İptal Eden Kurumlar', fontsize=16, 
                        fontweight='bold', pad=20)

            # Legend
            ax.legend(loc='lower right', fontsize=11)

            # Grid
            ax.grid(axis='x', alpha=0.3)

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
            return None

    def _grafige_tarih_ekle_eski(self, plt_obj, gun_tarihi: str):
        """Eski tarih ekleme fonksiyonu - kullan�lm�yor art�k"""
        pass

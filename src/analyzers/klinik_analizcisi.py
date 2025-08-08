"""
Klinik analizcisi modülü - Klinik analizi işlemleri
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional

from ..core.config import (
    KLINIK_SUTUN_ADI,
    KLINIK_ANALIZ_AYARLARI,
    VARSAYILAN_GRAFIK_BOYUTU,
    VARSAYILAN_DPI,
    GRAFIK_GORUNUM_AYARLARI,
    GRAFIK_AYARLARI,
    PASTA_GRAFIK_RENK_PALETI,
    GRUP_ADI_CEVIRI,
)

# Logger yapılandırması
logger = logging.getLogger(__name__)


class KlinikAnalizcisi:
    """Klinik analizi işlemleri"""

    def __init__(self, grafik_olusturucu):
        """Klinik analizcisi başlatma"""
        self.grafik_olusturucu = grafik_olusturucu

    def klinik_filtrele(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Klinik verilerini config ayarlarına göre filtreler
        """
        try:
            if KLINIK_SUTUN_ADI not in df.columns:
                logger.warning(f"Klinik sütunu bulunamadı: {KLINIK_SUTUN_ADI}")
                return df

            # Boş klinik değerlerini temizle
            df_temiz = df[
                df[KLINIK_SUTUN_ADI].notna() & (df[KLINIK_SUTUN_ADI] != "")
            ].copy()

            # Klinik sayımlarını al
            klinik_sayimlari = df_temiz[KLINIK_SUTUN_ADI].value_counts()

            # Minimum giriş barajı filtresi
            if (
                KLINIK_ANALIZ_AYARLARI["minimum_giris_baraj"]["aktif"]
                and KLINIK_ANALIZ_AYARLARI["minimum_giris_baraj"]["deger"] > 0
            ):

                min_baraj = KLINIK_ANALIZ_AYARLARI["minimum_giris_baraj"]["deger"]
                klinik_sayimlari = klinik_sayimlari[klinik_sayimlari >= min_baraj]

            # En çok klinik sayısı filtresi
            if (
                KLINIK_ANALIZ_AYARLARI["en_cok_klinik_sayisi"]["aktif"]
                and KLINIK_ANALIZ_AYARLARI["en_cok_klinik_sayisi"]["deger"] > 0
            ):

                max_klinik = KLINIK_ANALIZ_AYARLARI["en_cok_klinik_sayisi"]["deger"]
                klinik_sayimlari = klinik_sayimlari.head(max_klinik)

            # Filtrelenmiş klinikleri al
            gecerli_klinikler = klinik_sayimlari.index.tolist()
            df_filtreli = df_temiz[
                df_temiz[KLINIK_SUTUN_ADI].isin(gecerli_klinikler)
            ].copy()

            return df_filtreli

        except Exception as e:
            logger.error(f"Klinik filtreleme hatası: {e}")
            return df

    def klinik_dagilim_analizi(
        self, df: pd.DataFrame, grup_adi: str = "Genel"
    ) -> Dict[str, Any]:
        """
        Klinik dağılım analizi yapar
        """
        try:
            # Klinik verilerini filtrele
            df_filtreli = self.klinik_filtrele(df)

            if len(df_filtreli) == 0:
                return {"hata": "Filtrelenmiş veri yok"}

            # Klinik dağılımı
            klinik_sayimlari = df_filtreli[KLINIK_SUTUN_ADI].value_counts()
            klinik_yuzdeleri = (
                df_filtreli[KLINIK_SUTUN_ADI].value_counts(normalize=True) * 100
            )

            # Her klinik için vaka durumu analizi
            vaka_durum_analizi = {}
            if "vaka_tipi" in df_filtreli.columns:
                for klinik in klinik_sayimlari.index:
                    klinik_df = df_filtreli[df_filtreli[KLINIK_SUTUN_ADI] == klinik]
                    vaka_durumlari = klinik_df["vaka_tipi"].value_counts().to_dict()
                    vaka_durum_analizi[klinik] = vaka_durumlari

            # Bekleme süresi analizi (tarih farkından hesapla)
            bekleme_analizi = {}
            if (
                "talep tarihi" in df_filtreli.columns
                and "yer bulunma tarihi" in df_filtreli.columns
            ):
                for klinik in klinik_sayimlari.index:
                    klinik_df = df_filtreli[df_filtreli[KLINIK_SUTUN_ADI] == klinik]

                    # Klinik için bekleme sürelerini hesapla
                    mask = (
                        klinik_df["talep tarihi"].notna()
                        & klinik_df["yer bulunma tarihi"].notna()
                    )
                    klinik_temiz = klinik_df[mask]

                    if len(klinik_temiz) > 0:
                        # Saat cinsinden bekleme süresi hesapla
                        bekleme_delta = (
                            klinik_temiz["yer bulunma tarihi"]
                            - klinik_temiz["talep tarihi"]
                        )
                        bekleme_saat = bekleme_delta.dt.total_seconds() / 3600

                        # Negatif değerleri filtrele
                        gecerli_beklemeler = bekleme_saat[bekleme_saat >= 0]

                        if len(gecerli_beklemeler) > 0:
                            bekleme_analizi[klinik] = {
                                "ortalama": float(gecerli_beklemeler.mean()),
                                "medyan": float(gecerli_beklemeler.median()),
                                "min": float(gecerli_beklemeler.min()),
                                "max": float(gecerli_beklemeler.max()),
                                "vaka_sayisi": len(gecerli_beklemeler),
                            }

            analiz_sonucu = {
                "grup_adi": grup_adi,
                "toplam_vaka": len(df_filtreli),
                "toplam_klinik": len(klinik_sayimlari),
                "klinik_sayimlari": klinik_sayimlari.to_dict(),
                "klinik_yuzdeleri": klinik_yuzdeleri.to_dict(),
                "vaka_durum_analizi": vaka_durum_analizi,
                "bekleme_analizi": bekleme_analizi,
                "filtrelenmis_veri": df_filtreli,
            }

            return analiz_sonucu

        except Exception as e:
            logger.error(f"Klinik dağılım analizi hatası: {e}")
            return {"hata": str(e)}

    def klinik_grafikleri_olustur(
        self, df: pd.DataFrame, gun_tarihi: str, grup_adi: str = "Genel"
    ) -> Optional[List[str]]:
        """
        Klinik analizi için grafikler oluşturur
        """
        try:
            # Klinik analizini yap
            analiz = self.klinik_dagilim_analizi(df, grup_adi)

            if "hata" in analiz:
                logger.warning(f"Klinik analizi başarısız: {analiz['hata']}")
                return []

            df_filtreli = analiz["filtrelenmis_veri"]

            if df_filtreli.empty:
                logger.warning(f"Filtreli veri boş, grafik oluşturulamadı: {grup_adi}")
                return []

            # Grafik dosyalarını tutar
            grafik_dosyalari = []

            # 1. Klinik dağılım pasta grafiği
            if GRAFIK_AYARLARI.get("klinik_pasta_grafik", True):
                pasta_dosya = self._klinik_pasta_grafigi(analiz, gun_tarihi, grup_adi)
                if pasta_dosya:
                    grafik_dosyalari.append(pasta_dosya)

            # 2. Klinik başına vaka durumu grafiği
            if GRAFIK_AYARLARI.get("klinik_vaka_durum_grafik", True):
                durum_dosya = self._klinik_vaka_durum_grafigi(
                    analiz, gun_tarihi, grup_adi
                )
                if durum_dosya:
                    grafik_dosyalari.append(durum_dosya)

            # 3. Klinik bekleme süreleri grafiği (eğer veri varsa)
            if analiz["bekleme_analizi"] and GRAFIK_AYARLARI.get(
                "klinik_bekleme_grafik", True
            ):
                bekleme_dosya = self._klinik_bekleme_grafigi(
                    analiz, gun_tarihi, grup_adi
                )
                if bekleme_dosya:
                    grafik_dosyalari.append(bekleme_dosya)

            # 4. İptal nedenleri çubuk grafiği
            if GRAFIK_AYARLARI.get("iptal_nedenleri_grafik", True):
                iptal_dosya = self.grafik_olusturucu.iptal_nedenleri_cubuk_grafigi(
                    df_filtreli, gun_tarihi, grup_adi, "Butun_Vakalar"
                )
                if iptal_dosya:
                    grafik_dosyalari.append(iptal_dosya)

            logger.info(f"Klinik grafikleri oluşturuldu: {grup_adi}")
            return grafik_dosyalari

        except Exception as e:
            logger.error(f"Klinik grafik oluşturma hatası: {e}")
            return []

    def _klinik_pasta_grafigi(
        self, analiz: Dict[str, Any], gun_tarihi: str, grup_adi: str
    ):
        """Klinik dağılım pasta grafiği"""
        try:
            import matplotlib

            matplotlib.use("Agg")

            plt.figure(figsize=VARSAYILAN_GRAFIK_BOYUTU)

            klinik_sayimlari = analiz["klinik_sayimlari"]
            klinik_yuzdeleri = analiz["klinik_yuzdeleri"]

            # Pasta grafiği için etiket formatı
            etiket_format = GRAFIK_GORUNUM_AYARLARI.get(
                "pasta_etiket_format", "isim_yuzde_sayi"
            )

            labels = []
            for klinik, sayim in klinik_sayimlari.items():
                if etiket_format == "isim":
                    label = klinik
                elif etiket_format == "yuzde":
                    label = f"%{klinik_yuzdeleri[klinik]:.1f}"
                elif etiket_format == "sayi":
                    label = f"{sayim}"
                elif etiket_format == "isim_yuzde":
                    label = f"{klinik}\n%{klinik_yuzdeleri[klinik]:.1f}"
                elif etiket_format == "isim_sayi":
                    label = f"{klinik}\n{sayim}"
                elif etiket_format == "isim_yuzde_sayi_yanli":
                    # Klinik adını pasta yanında, sayısal veriyi pasta içinde
                    label = klinik
                else:  # isim_yuzde_sayi (default)
                    label = f"{klinik}\n{sayim} (%{klinik_yuzdeleri[klinik]:.1f})"
                labels.append(label)

            # Autopct fonksiyonu (yeni format için)
            def autopct_format(pct):
                if etiket_format == "isim_yuzde_sayi_yanli":
                    # Pasta içinde sayı ve yüzde göster
                    absolute = int(round(pct / 100.0 * sum(klinik_sayimlari.values())))
                    return f"{absolute}\n({pct:.1f}%)"
                return ""

            # Gelişmiş renk paleti kullan
            colors = PASTA_GRAFIK_RENK_PALETI[: len(klinik_sayimlari)]

            plt.pie(
                list(klinik_sayimlari.values()),
                labels=labels,
                autopct=autopct_format,
                startangle=90,
                labeldistance=1.1 if etiket_format == "isim_yuzde_sayi_yanli" else None,
                colors=colors,
            )

            baslik = f"Klinik Dağılımı - {grup_adi}"

            # Başlıktaki grup adlarını çevir
            for kod, turkce in GRUP_ADI_CEVIRI.items():
                baslik = baslik.replace(kod, turkce)

            plt.title(baslik, fontsize=14, fontweight="bold")
            plt.axis("equal")

            # Tarih ekleme (config'e göre)
            if GRAFIK_GORUNUM_AYARLARI.get("tarih_goster", True):
                self.grafik_olusturucu._grafige_tarih_ekle(plt, gun_tarihi)

            # Tarih klasörü oluştur ve dosyaya kaydet
            tarih_klasor = self.grafik_olusturucu._tarih_klasoru_olustur(gun_tarihi)
            dosya_adi = tarih_klasor / f"klinik-dagilim_{grup_adi}_{gun_tarihi}.png"
            plt.savefig(dosya_adi, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

            return str(dosya_adi)

        except Exception as e:
            logger.error(f"Klinik pasta grafiği hatası: {e}")
            if "plt" in locals():
                plt.close()
            return None

    def _klinik_vaka_durum_grafigi(
        self, analiz: Dict[str, Any], gun_tarihi: str, grup_adi: str
    ):
        """Her klinik için vaka durumu grafiği"""
        try:
            import matplotlib

            matplotlib.use("Agg")

            # Analiz verisinden DataFrame'i al
            df = analiz["filtrelenmis_veri"]

            if df.empty:
                logger.warning("Boş veri, klinik vaka durum grafiği oluşturulamadı")
                return None

            # Sadece analiz kapsamındaki vakaları al
            if "vaka_tipi" in df.columns:
                analiz_kapsamindaki_vakalar = df[
                    df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])
                ]
                if not analiz_kapsamindaki_vakalar.empty:
                    df = analiz_kapsamindaki_vakalar
                else:
                    logger.warning("Analiz kapsamında vaka bulunamadı")
                    return None

            # Klinik bazında durum analizi
            klinik_durum_analizi = {}

            # Her klinik için durum sayılarını hesapla
            for klinik_adi in df[KLINIK_SUTUN_ADI].unique():
                klinik_df = df[df[KLINIK_SUTUN_ADI] == klinik_adi]
                durum_sayilari = klinik_df["durum"].value_counts().to_dict()
                klinik_durum_analizi[klinik_adi] = durum_sayilari

            if not klinik_durum_analizi:
                return None

            # Veri hazırlama
            klinikler = list(klinik_durum_analizi.keys())
            durum_tipleri = set()
            for durum_dict in klinik_durum_analizi.values():
                durum_tipleri.update(durum_dict.keys())
            durum_tipleri = sorted(list(durum_tipleri))

            # DataFrame oluştur
            veri_matrisi = []
            for klinik in klinikler:
                satir = []
                for durum_tipi in durum_tipleri:
                    sayim = klinik_durum_analizi[klinik].get(durum_tipi, 0)
                    satir.append(sayim)
                veri_matrisi.append(satir)

            # Grafik
            fig, ax = plt.subplots(figsize=(14, 8))

            x = range(len(klinikler))
            width = 0.25

            # Durum tipine özel renk tanımları
            durum_renkleri = {
                "Yer Ayarlandı": "#2ecc71",
                "Nakil Talebi İptal Edildi": "#e74c3c",
                "Yer Aranıyor": "#f39c12",
                "Yeni Talep": "#3498db",
            }

            for i, durum_tipi in enumerate(durum_tipleri):
                values = [veri_matrisi[j][i] for j in range(len(klinikler))]
                x_pos = [xi + i * width for xi in x]

                # Durum tipine göre renk seç
                renk = durum_renkleri.get(durum_tipi, "#7f8c8d")

                bars = ax.bar(
                    x_pos, values, width, label=durum_tipi, color=renk, alpha=0.8
                )

                # Bar üzerinde sayı göster (eğer 0'dan büyükse)
                for bar, value in zip(bars, values):
                    if value > 0:
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height + 0.1,
                            f"{value}",
                            ha="center",
                            va="bottom",
                            fontsize=8,
                        )

            ax.set_xlabel("Klinikler")
            ax.set_ylabel("Vaka Sayısı")

            # Grup adını çevir
            grup_adi_tr = GRUP_ADI_CEVIRI.get(grup_adi, grup_adi)
            title = f"Klinik Vaka Durumu - {grup_adi_tr}"
            ax.set_title(title)

            ax.set_xticks([xi + width * (len(durum_tipleri) - 1) / 2 for xi in x])
            ax.set_xticklabels(klinikler, rotation=45, ha="right")
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

            # Tarih ekleme (config'e göre)
            if GRAFIK_GORUNUM_AYARLARI.get("tarih_goster", True):
                self.grafik_olusturucu._grafige_tarih_ekle(plt, gun_tarihi)

            # Tarih klasörü oluştur ve dosyaya kaydet
            tarih_klasor = self.grafik_olusturucu._tarih_klasoru_olustur(gun_tarihi)
            dosya_adi = tarih_klasor / f"klinik_vaka_durum_{grup_adi}_{gun_tarihi}.png"
            plt.tight_layout()
            plt.savefig(dosya_adi, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

            logger.info(f"Klinik vaka durum grafiği oluşturuldu: {grup_adi}")
            return str(dosya_adi)

        except Exception as e:
            logger.error(f"Klinik vaka durum grafiği hatası: {e}")
            if "plt" in locals():
                plt.close()
            return None

    def _klinik_bekleme_grafigi(
        self, analiz: Dict[str, Any], gun_tarihi: str, grup_adi: str
    ):
        """Klinik başına bekleme süreleri grafiği"""
        try:
            import matplotlib

            matplotlib.use("Agg")

            bekleme_analizi = analiz["bekleme_analizi"]

            if not bekleme_analizi:
                return None

            klinikler = list(bekleme_analizi.keys())
            ortalama_list = [bekleme_analizi[k]["ortalama"] for k in klinikler]

            plt.figure(figsize=(12, 6))
            bars = plt.bar(range(len(klinikler)), ortalama_list)

            plt.xlabel("Klinikler")
            plt.ylabel("Ortalama Bekleme Süresi (Saat)")
            title = f"{grup_adi} - Klinik Başına Ortalama Bekleme Süreleri"
            plt.title(title)
            plt.xticks(range(len(klinikler)), klinikler, rotation=45, ha="right")

            # Bar üzerine değerleri yaz
            for bar, deger in zip(bars, ortalama_list):
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(ortalama_list) * 0.01,
                    f"{deger:.1f}h",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )

            plt.tight_layout()

            # Tarih ekleme (config'e göre)
            if GRAFIK_GORUNUM_AYARLARI.get("tarih_goster", True):
                self.grafik_olusturucu._grafige_tarih_ekle(plt, gun_tarihi)

            # Tarih klasörü oluştur ve dosyaya kaydet
            tarih_klasor = self.grafik_olusturucu._tarih_klasoru_olustur(gun_tarihi)
            dosya_adi = tarih_klasor / f"klinik-bekleme_{grup_adi}_{gun_tarihi}.png"
            plt.savefig(dosya_adi, dpi=VARSAYILAN_DPI, bbox_inches="tight")
            plt.close()

            return str(dosya_adi)

        except Exception as e:
            logger.error(f"Klinik bekleme grafiği hatası: {e}")
            if "plt" in locals():
                plt.close()
            return None

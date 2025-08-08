"""
Analiz motoru modülü - Ana analiz mantığı ve istatistikler
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

# Logger yapılandırması
logger = logging.getLogger(__name__)


class AnalizMotoru:
    """Ana analiz mantığı ve istatistiksel hesaplamalar"""

    def vaka_durumu_analizi(
        self, df: pd.DataFrame, grup_adi: str, vaka_tipi: str
    ) -> Dict[str, Any]:
        """
        Vaka durumu dağılımını analiz eder
        """
        try:
            sonuc = {}

            if "durum" in df.columns and len(df) > 0:
                durum_sayilari = df["durum"].value_counts()
                durum_yuzdeleri = df["durum"].value_counts(normalize=True) * 100

                sonuc = {
                    "toplam_vaka": len(df),
                    "durum_sayilari": durum_sayilari.to_dict(),
                    "durum_yuzdeleri": durum_yuzdeleri.to_dict(),
                }

            return sonuc

        except Exception as e:
            logger.error(f"Vaka durumu analizi hatası: {e}")
            return {}

    def bekleme_suresi_analizi(
        self,
        df: pd.DataFrame,
        grup_adi: str,
        vaka_tipi: str,
        durum_filtre: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bekleme süresi analizini yapar
        """
        try:
            if durum_filtre:
                df_filtered = df[df["durum"] == durum_filtre].copy()
            else:
                df_filtered = df.copy()

            if len(df_filtered) == 0:
                return {}

            # Bekleme süresini hesapla
            bekleme_suresi_saat = self._bekleme_suresi_hesapla(df_filtered)

            if len(bekleme_suresi_saat) == 0:
                return {}

            sonuc = {
                "vaka_sayisi": len(df_filtered),
                "ortalama_saat": float(np.mean(bekleme_suresi_saat)),
                "medyan_saat": float(np.median(bekleme_suresi_saat)),
                "min_saat": float(np.min(bekleme_suresi_saat)),
                "max_saat": float(np.max(bekleme_suresi_saat)),
            }

            # Sadece "Yer Ayarlandı" için threshold analizi yap
            if durum_filtre == "Yer Ayarlandı":
                threshold_analizi = self._threshold_analizi(bekleme_suresi_saat)
                sonuc["threshold_analizi"] = threshold_analizi

            return sonuc

        except Exception as e:
            logger.error(f"Bekleme süresi analizi hatası: {e}")
            return {}

    def _bekleme_suresi_hesapla(self, df: pd.DataFrame) -> np.ndarray:
        """Bekleme süresini saat cinsinden hesaplar"""
        try:
            if "talep tarihi" in df.columns and "yer bulunma tarihi" in df.columns:
                # Boş olmayan değerleri filtrele
                mask = df["talep tarihi"].notna() & df["yer bulunma tarihi"].notna()
                df_temiz = df[mask]

                if len(df_temiz) > 0:
                    # Saat cinsinden fark hesapla
                    bekleme_delta = (
                        df_temiz["yer bulunma tarihi"] - df_temiz["talep tarihi"]
                    )
                    bekleme_saat = bekleme_delta.dt.total_seconds() / 3600

                    # Negatif değerleri filtrele
                    return bekleme_saat[bekleme_saat >= 0].values

            return np.array([])

        except Exception as e:
            logger.error(f"Bekleme süresi hesaplama hatası: {e}")
            return np.array([])

    def _threshold_analizi(self, bekleme_suresi_saat: np.ndarray) -> Dict[str, int]:
        """Bekleme süresi threshold analizini yapar"""
        try:
            thresholds = {
                "0-30 dakika": 0.5,
                "30 dakika - 1 saat": 1,
                "1-2 saat": 2,
                "2-4 saat": 4,
                "4-8 saat": 8,
                "8-24 saat": 24,
                "24+ saat": float("inf"),
            }

            sonuc = {}
            for etiket, limit in thresholds.items():
                if etiket == "0-30 dakika":
                    count = np.sum(bekleme_suresi_saat <= limit)
                elif etiket == "24+ saat":
                    count = np.sum(bekleme_suresi_saat > 24)
                elif etiket == "30 dakika - 1 saat":
                    count = np.sum(
                        (bekleme_suresi_saat > 0.5) & (bekleme_suresi_saat <= 1)
                    )
                elif etiket == "1-2 saat":
                    count = np.sum(
                        (bekleme_suresi_saat > 1) & (bekleme_suresi_saat <= 2)
                    )
                elif etiket == "2-4 saat":
                    count = np.sum(
                        (bekleme_suresi_saat > 2) & (bekleme_suresi_saat <= 4)
                    )
                elif etiket == "4-8 saat":
                    count = np.sum(
                        (bekleme_suresi_saat > 4) & (bekleme_suresi_saat <= 8)
                    )
                elif etiket == "8-24 saat":
                    count = np.sum(
                        (bekleme_suresi_saat > 8) & (bekleme_suresi_saat <= 24)
                    )

                sonuc[etiket] = int(count)

            return sonuc

        except Exception as e:
            logger.error(f"Threshold analizi hatası: {e}")
            return {}

    def genel_istatistik_hesapla(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Genel istatistikleri hesaplar
        """
        try:
            if len(df) == 0:
                return {}

            toplam_yeni = len(df[df["vaka_tipi"] == "Yeni Vaka"])
            toplam_devreden = len(df[df["vaka_tipi"] == "Devreden Vaka"])
            toplam_gecerli = toplam_yeni + toplam_devreden

            if toplam_gecerli > 0:
                return {
                    "yeni_vaka_sayisi": toplam_yeni,
                    "devreden_vaka_sayisi": toplam_devreden,
                    "yeni_vaka_yuzde": round((toplam_yeni / toplam_gecerli) * 100, 1),
                    "devreden_vaka_yuzde": round(
                        (toplam_devreden / toplam_gecerli) * 100, 1
                    ),
                    "toplam_gecerli_vaka": toplam_gecerli,
                }
            return {}

        except Exception as e:
            logger.error(f"Genel istatistik hesaplama hatası: {e}")
            return {}

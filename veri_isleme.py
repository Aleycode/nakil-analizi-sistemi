"""
Veri işleme modülü - Veri okuma, filtreleme ve sınıflandırma
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from config import (
    ISLENMIŞ_VERI_DIZIN,
    TARIH_SUTUNLARI,
)

# Logger yapılandırması
logger = logging.getLogger(__name__)


class VeriIsleme:
    """Veri okuma, filtreleme ve sınıflandırma işlemleri"""

    def __init__(self):
        """Veri işleme sınıfı başlatma"""
        self.ana_veri_dosya = ISLENMIŞ_VERI_DIZIN / "ana_veri.parquet"

    def veriyi_oku(self) -> pd.DataFrame:
        """Ana veri dosyasını okur ve tarih sütunlarını düzeltir"""
        try:
            if not self.ana_veri_dosya.exists():
                raise FileNotFoundError("Ana veri dosyası bulunamadı")

            df = pd.read_parquet(self.ana_veri_dosya)

            # Gerçek sütun adlarını kullan (küçük harf)
            tarih_sutunlari_gercek = [
                "talep tarihi",
                "oluşturma tarihi",
                "yer aramaya başlama tarihi",
                "yer bulunma tarihi",
                "ekip talep tarihi",
                "ekip belirlenme tarihi",
                "vakanın ekibe veriliş tarihi",
            ]

            # Tarih sütunlarını datetime'a çevir
            for col in tarih_sutunlari_gercek:
                if col in df.columns:
                    # Önce NaN olmayan değerleri string'e çevir
                    df[col] = df[col].astype(str)
                    # Türkçe tarih formatını datetime'a çevir
                    df[col] = pd.to_datetime(
                        df[col], format="%d-%m-%Y %H:%M:%S", errors="coerce"
                    )

            # Veri düzenleme ayarlarını uygula
            df = self._veri_duzenleme_uygula(df)

            logger.info(f"Veri okundu: {len(df)} satır, {len(df.columns)} sütun")
            return df

        except Exception as e:
            logger.error(f"Veri okuma hatası: {e}")
            raise

    def _veri_duzenleme_uygula(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Config ayarlarına göre veri düzenlemelerini uygular
        """
        try:
            from config import VERI_DUZENLEME_AYARLARI

            # Klinik adı dönüştürmeleri (en başta yapılır)
            klinik_ayarlari = VERI_DUZENLEME_AYARLARI.get(
                "klinik_adi_donusturmeler", {}
            )
            if klinik_ayarlari.get("aktif", True):
                donusumler = klinik_ayarlari.get("donusumler", {})
                klinik_sutun = "nakledilmesi i̇stenen klinik"
                if donusumler and klinik_sutun in df.columns:
                    toplam_donusum = 0
                    for eski_ad, yeni_ad in donusumler.items():
                        mask = df[klinik_sutun] == eski_ad
                        donusum_sayisi = mask.sum()
                        if donusum_sayisi > 0:
                            df.loc[mask, klinik_sutun] = yeni_ad
                            toplam_donusum += donusum_sayisi
                            logger.info(
                                f"Klinik dönüştürme: {donusum_sayisi} "
                                f"'{eski_ad}' → '{yeni_ad}'"
                            )

                    if toplam_donusum > 0:
                        logger.info(f"Toplam {toplam_donusum} klinik adı dönüştürüldü")

            # Solunum işlemi dönüştürmeleri
            solunum_ayarlari = VERI_DUZENLEME_AYARLARI.get(
                "solunum_islemi_donusturmeler", {}
            )
            if solunum_ayarlari.get("aktif", True):
                donusumler = solunum_ayarlari.get("donusumler", {})
                solunum_sutun = "solunum i̇şlemi"
                if donusumler and solunum_sutun in df.columns:
                    toplam_donusum = 0
                    for eski_ad, yeni_ad in donusumler.items():
                        mask = df[solunum_sutun] == eski_ad
                        donusum_sayisi = mask.sum()
                        if donusum_sayisi > 0:
                            df.loc[mask, solunum_sutun] = yeni_ad
                            toplam_donusum += donusum_sayisi
                            logger.info(
                                f"Solunum dönüştürme: {donusum_sayisi} "
                                f"'{eski_ad}' → '{yeni_ad}'"
                            )

                    if toplam_donusum > 0:
                        logger.info(
                            f"Toplam {toplam_donusum} solunum işlemi dönüştürüldü"
                        )

            # "Yeni Talep" → "Yer Aranıyor" dönüşümü
            yeni_talep_donusum = VERI_DUZENLEME_AYARLARI.get(
                "yeni_talep_yer_araniyor_donusum", True
            )
            if yeni_talep_donusum:
                if "durum" in df.columns:
                    onceki_sayisi = (df["durum"] == "Yeni Talep").sum()
                    df.loc[df["durum"] == "Yeni Talep", "durum"] = "Yer Aranıyor"
                    if onceki_sayisi > 0:
                        logger.info(
                            f"Veri düzenleme: {onceki_sayisi} "
                            f"'Yeni Talep' → 'Yer Aranıyor' dönüştürüldü"
                        )

            return df

        except Exception as e:
            logger.warning(f"Veri düzenleme hatası: {e}")
            return df

    def gunluk_zaman_araligi_filtrele(
        self, df: pd.DataFrame, gun_tarihi: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Günlük analiz için doğru zaman aralığında filtrele
        İki tip vaka dahil edilir:
        1. O gün yeni oluşturulan vakalar (dün 08:00 - bugün 08:00)
        2. Önceki günlerde oluşturulmuş ama hala aktif vakalar (yer bulunmamış)
        """
        try:
            if gun_tarihi is None:
                gun_tarihi = datetime.now().strftime("%Y-%m-%d")

            # Bugün 08:00
            bugun_08 = pd.to_datetime(f"{gun_tarihi} 08:00:00")
            # Dün 08:00
            dun_08 = bugun_08 - timedelta(days=1)

            logger.info(f"Zaman aralığı: {dun_08} - {bugun_08}")

            if "oluşturma tarihi" not in df.columns:
                logger.warning("oluşturma tarihi sütunu bulunamadı")
                return df

            # 1. O gün yeni oluşturulmuş vakalar
            yeni_vakalar_mask = (df["oluşturma tarihi"] >= dun_08) & (
                df["oluşturma tarihi"] < bugun_08
            )

            # 2. Eski ama hala aktif vakalar VEYA yer bulma tarihi analiz aralığında olanlar
            if "yer bulunma tarihi" in df.columns:
                # Eski tarihli + yer bulunma tarihi boş = hala aktif
                eski_aktif_mask = (df["oluşturma tarihi"] < dun_08) & (
                    df["yer bulunma tarihi"].isna()
                )

                # Eski tarihli + yer bulma tarihi analiz aralığında = devreden ama tamamlanmış
                yer_bulunma_dt = pd.to_datetime(
                    df["yer bulunma tarihi"], errors="coerce"
                )
                eski_tamamlanmis_mask = (
                    (df["oluşturma tarihi"] < dun_08)
                    & (yer_bulunma_dt >= dun_08)
                    & (yer_bulunma_dt < bugun_08)
                )

                # Kombinasyon: Eski aktif VEYA eski tamamlanmış (analiz aralığında)
                eski_kombinasyon_mask = eski_aktif_mask | eski_tamamlanmis_mask
            else:
                # Yer bulunma tarihi sütunu yoksa sadece eski olanları al
                eski_kombinasyon_mask = df["oluşturma tarihi"] < dun_08

            # Toplam: Yeni + Eski kombinasyon
            toplam_mask = yeni_vakalar_mask | eski_kombinasyon_mask
            filtered_df = df[toplam_mask].copy()

            yeni_sayi = yeni_vakalar_mask.sum()
            if "yer bulunma tarihi" in df.columns:
                eski_aktif_sayi = eski_aktif_mask.sum()
                eski_tamamlanmis_sayi = eski_tamamlanmis_mask.sum()
                logger.info(
                    f"Zaman aralığında {len(filtered_df)} vaka bulundu "
                    f"(Yeni: {yeni_sayi}, Eski aktif: {eski_aktif_sayi}, "
                    f"Eski tamamlanmış: {eski_tamamlanmis_sayi})"
                )
            else:
                eski_kombinasyon_sayi = eski_kombinasyon_mask.sum()
                logger.info(
                    f"Zaman aralığında {len(filtered_df)} vaka bulundu "
                    f"(Yeni: {yeni_sayi}, Eski: {eski_kombinasyon_sayi})"
                )

            return filtered_df

        except Exception as e:
            logger.error(f"Zaman aralığı filtreleme hatası: {e}")
            return df

    def _bekleme_suresi_parse(self, bekleme_str: str) -> timedelta:
        """
        Bekleme süresi string'ini timedelta'ya çevirir
        Format: "x gün x saat x dakika"
        """
        try:
            if pd.isna(bekleme_str) or not isinstance(bekleme_str, str):
                return timedelta(0)

            gun = 0
            saat = 0
            dakika = 0

            # "gün" kelimesini ara
            if "gün" in bekleme_str:
                gun_part = bekleme_str.split("gün")[0].strip()
                try:
                    gun = int(gun_part.split()[-1])
                except:
                    gun = 0

            # "saat" kelimesini ara
            if "saat" in bekleme_str:
                saat_part = bekleme_str.split("saat")[0]
                if "gün" in saat_part:
                    saat_part = saat_part.split("gün")[1]
                saat_part = saat_part.strip()
                try:
                    saat = int(saat_part.split()[-1])
                except:
                    saat = 0

            # "dakika" kelimesini ara
            if "dakika" in bekleme_str:
                dakika_part = bekleme_str.split("dakika")[0]
                if "saat" in dakika_part:
                    dakika_part = dakika_part.split("saat")[1]
                elif "gün" in dakika_part:
                    dakika_part = dakika_part.split("gün")[1]
                    if "saat" in dakika_part:
                        dakika_part = dakika_part.split("saat")[1]
                dakika_part = dakika_part.strip()
                try:
                    dakika = int(dakika_part.split()[-1])
                except:
                    dakika = 0

            return timedelta(days=gun, hours=saat, minutes=dakika)

        except Exception as e:
            logger.warning(f"Bekleme süresi parse hatası: {bekleme_str} -> {e}")
            return timedelta(0)

    def vaka_tipi_belirle(
        self, df: pd.DataFrame, gun_tarihi: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Düzeltilmiş filtreleme ve sınıflandırma mantığı:
        1. Filtreleme (analiz dışı):
           - "Yer Bulunma Tarihi" DOLU ve dün 08:00'dan eski olanlar
           - "Durum" = "Nakil Talebi İptal Edildi" + (Oluşturma + Bekleme) dün 08:00'dan eski
        2. Geriye kalanlar (Yer Bulunma Tarihi boş olanlar dahil):
           - "Oluşturma Tarihi" dün 08:00'den yeni → Yeni Vaka
           - "Oluşturma Tarihi" dün 08:00'den eski → Devreden Vaka
        """
        try:
            if gun_tarihi is None:
                gun_tarihi = datetime.now().strftime("%Y-%m-%d")

            # Dün 08:00 referans noktası
            dun_08 = pd.to_datetime(f"{gun_tarihi} 08:00:00") - timedelta(days=1)

            df = df.copy()
            df["vaka_tipi"] = "Analiz_Disi"  # Başlangıçta hepsi analiz dışı

            logger.info(f"Filtreleme referans noktası: {dun_08}")

            # 1. FILTRELEME AŞAMASI
            # 1a. Yer Bulunma Tarihi filtrelemesi - Sadece çok eski tamamlanmış vakaları çıkar
            yer_bulunma_filtre = pd.Series([True] * len(df), index=df.index)
            if "yer bulunma tarihi" in df.columns:
                # Analiz başlangıcından 1 gün önce tamamlanmış vakaları çıkar
                cok_eski_tamamlanmis = df["yer bulunma tarihi"].notna() & (
                    df["yer bulunma tarihi"] < (dun_08 - timedelta(days=1))
                )
                yer_bulunma_filtre = ~cok_eski_tamamlanmis

                filtrelenen_yer = cok_eski_tamamlanmis.sum()
                logger.info(
                    f"Yer bulunma tarihi filtrelemesi: {filtrelenen_yer} vaka "
                    f"çıkarıldı (çok eski tamamlanmış)"
                )
                bos_yer_sayisi = df["yer bulunma tarihi"].isna().sum()
                yakın_tamamlanmis = (
                    df["yer bulunma tarihi"].notna()
                    & (df["yer bulunma tarihi"] >= (dun_08 - timedelta(days=1)))
                ).sum()
                logger.info(
                    f"Analiz kapsamı: BOŞ yer {bos_yer_sayisi} + yakın tamamlanmış {yakın_tamamlanmis}"
                )

            # 1b. İptal edilmiş vakalar filtrelemesi
            iptal_filtre = pd.Series([True] * len(df), index=df.index)
            if (
                "durum" in df.columns
                and "oluşturma tarihi" in df.columns
                and "bekleme süresi" in df.columns
            ):
                iptal_mask = df["durum"] == "Nakil Talebi İptal Edildi"

                for idx in df[iptal_mask].index:
                    try:
                        olusturma = df.loc[idx, "oluşturma tarihi"]
                        bekleme_str = df.loc[idx, "bekleme süresi"]

                        if pd.notna(olusturma) and pd.notna(bekleme_str):
                            bekleme_delta = self._bekleme_suresi_parse(str(bekleme_str))
                            iptal_zamani = pd.to_datetime(olusturma) + bekleme_delta

                            if iptal_zamani < dun_08:
                                iptal_filtre.loc[idx] = False
                    except Exception as e:
                        logger.warning(f"İptal vakası işleme hatası (idx={idx}): {e}")

                filtrelenen_iptal = (~iptal_filtre & iptal_mask).sum()
                logger.info(
                    f"İptal vakası filtrelemesi: {filtrelenen_iptal} vaka çıkarıldı"
                )

            # Genel filtre: Her iki filtreyi de geçenler
            genel_filtre = yer_bulunma_filtre & iptal_filtre

            # 2. SINIFLANDIRMA AŞAMASI (Filtreyi geçenler için)
            if "oluşturma tarihi" in df.columns:
                olusturma_mask = df["oluşturma tarihi"].notna()

                # Yeni vakalar: Oluşturma tarihi dün 08:00'den sonra
                yeni_vaka_mask = (
                    genel_filtre & olusturma_mask & (df["oluşturma tarihi"] >= dun_08)
                )

                # Devreden vakalar: Oluşturma tarihi dün 08:00'den önce
                # ANCAK oluşturma_tarihi + bekleme_süresi > dün 08:00 olanlar
                # VEYA yer bulma tarihi dün 08:00 - bugün 08:00 arasında olanlar
                devreden_vaka_mask = pd.Series([False] * len(df), index=df.index)

                # Bugün 08:00 (bitiş noktası)
                bugun_08 = pd.to_datetime(f"{gun_tarihi} 08:00:00")

                if "bekleme süresi" in df.columns:
                    for idx in df[
                        genel_filtre
                        & olusturma_mask
                        & (df["oluşturma tarihi"] < dun_08)
                    ].index:
                        try:
                            olusturma = df.loc[idx, "oluşturma tarihi"]
                            bekleme_str = df.loc[idx, "bekleme süresi"]
                            durum = (
                                df.loc[idx, "durum"] if "durum" in df.columns else ""
                            )
                            yer_bulunma = (
                                df.loc[idx, "yer bulunma tarihi"]
                                if "yer bulunma tarihi" in df.columns
                                else None
                            )

                            is_devreden = False

                            # Kontrol 1: Bekleme süresi bazlı kontrol
                            if pd.notna(olusturma) and pd.notna(bekleme_str):
                                bekleme_delta = self._bekleme_suresi_parse(
                                    str(bekleme_str)
                                )
                                vaka_bitis_zamani = (
                                    pd.to_datetime(olusturma) + bekleme_delta
                                )

                                # Eğer vaka bitiş zamanı dün 08:00'dan sonraysa, devreden vaka olabilir
                                if vaka_bitis_zamani > dun_08:
                                    is_devreden = True

                            # Kontrol 2: Yer Ayarlandı vakaları için özel kontrol
                            if durum == "Yer Ayarlandı" and pd.notna(yer_bulunma):
                                yer_bulunma_dt = pd.to_datetime(yer_bulunma)
                                # Yer bulma tarihi analiz aralığında mı? (dün 08:00 - bugün 08:00)
                                if dun_08 <= yer_bulunma_dt < bugun_08:
                                    is_devreden = True

                            if is_devreden:
                                devreden_vaka_mask.loc[idx] = True

                        except Exception as e:
                            logger.warning(
                                f"Devreden vaka kontrolü hatası (idx={idx}): {e}"
                            )
                else:
                    # Bekleme süresi yoksa eski mantık (oluşturma tarihi bazlı)
                    devreden_vaka_mask = (
                        genel_filtre
                        & olusturma_mask
                        & (df["oluşturma tarihi"] < dun_08)
                    )

                # Sınıflandırma uygula
                df.loc[yeni_vaka_mask, "vaka_tipi"] = "Yeni Vaka"
                df.loc[devreden_vaka_mask, "vaka_tipi"] = "Devreden Vaka"

                # İstatistikleri logla
                yeni_vaka_sayisi = yeni_vaka_mask.sum()
                devreden_vaka_sayisi = devreden_vaka_mask.sum()
                analiz_disi_sayisi = (df["vaka_tipi"] == "Analiz_Disi").sum()
                toplam_gecerli = yeni_vaka_sayisi + devreden_vaka_sayisi

                if toplam_gecerli > 0:
                    yeni_yuzde = (yeni_vaka_sayisi / toplam_gecerli) * 100
                    devreden_yuzde = (devreden_vaka_sayisi / toplam_gecerli) * 100

                    logger.info(f"Vaka sınıflandırması:")
                    logger.info(
                        f"  - Yeni Vaka: {yeni_vaka_sayisi} (%{yeni_yuzde:.1f})"
                    )
                    logger.info(
                        f"  - Devreden Vaka: {devreden_vaka_sayisi} (%{devreden_yuzde:.1f})"
                    )
                    logger.info(f"  - Analiz Dışı: {analiz_disi_sayisi}")
                    logger.info(f"  - Toplam Geçerli: {toplam_gecerli}")

            return df

        except Exception as e:
            logger.error(f"Vaka tipi belirleme hatası: {e}")
            df["vaka_tipi"] = "Hata"
            return df

    def il_bazinda_grupla(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Verileri il içi, il dışı ve bütün bölgeler olarak gruplar
        İl dışı: Talep Kaynağı != "İl İçi"
        """
        try:
            gruplar = {}

            if "talep kaynağı" in df.columns:
                # İl dışı: Talep Kaynağı sütunu "İl İçi" olmayan vakalar
                il_disi_mask = (df["talep kaynağı"] != "İl İçi") & df[
                    "talep kaynağı"
                ].notna()

                gruplar["Il_Disi"] = df[il_disi_mask].copy()
                gruplar["Il_Ici"] = df[~il_disi_mask].copy()
            else:
                # Talep Kaynağı sütunu yoksa tümü il içi sayılır
                gruplar["Il_Ici"] = df.copy()
                gruplar["Il_Disi"] = pd.DataFrame()

            gruplar["Butun_Bolgeler"] = df.copy()

            # İstatistikleri logla
            for grup_adi, grup_df in gruplar.items():
                logger.info(f"{grup_adi}: {len(grup_df)} vaka")

            return gruplar

        except Exception as e:
            logger.error(f"İl bazında gruplama hatası: {e}")
            return {"Butun_Bolgeler": df}

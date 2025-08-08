"""
Excel veri işleme ve parquet dönüştürme modülü
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import xlrd

from ..core.config import (
    HAM_VERI_DIZIN,
    ISLENMIŞ_VERI_DIZIN,
    EXCEL_MOTOR,
    PARQUET_MOTOR,
    PARQUET_SIKISTIRMA,
    TARIH_KOLON_ADI,
)

# Logger yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Veriİşleyici:
    """Excel dosyalarını okuyup parquet formatına dönüştüren sınıf"""

    def __init__(self):
        """Veri işleyici başlatma"""
        self.ana_parquet_dosya = ISLENMIŞ_VERI_DIZIN / "ana_veri.parquet"

    def excel_oku(self, dosya_yolu: str) -> pd.DataFrame:
        """
        Excel dosyasını xlrd 1.2.0 ile okur

        Args:
            dosya_yolu: Excel dosyasının yolu

        Returns:
            DataFrame: Okunan veriler
        """
        try:
            dosya_path = Path(dosya_yolu)

            if not dosya_path.exists():
                raise FileNotFoundError(f"Dosya bulunamadı: {dosya_yolu}")

            # İlk olarak xlrd ile deneme (.xls dosyaları için)
            try:
                if dosya_path.suffix.lower() == ".xls":
                    df = pd.read_excel(dosya_yolu, engine="xlrd")
                else:
                    # .xlsx dosyalar için openpyxl kullan
                    df = pd.read_excel(dosya_yolu, engine="openpyxl")
            except Exception as xlrd_error:
                # xlrd başarısız olursa openpyxl dene
                logger.debug(
                    f"xlrd ile okuma başarısız, openpyxl deneniyor: {xlrd_error}"
                )
                try:
                    df = pd.read_excel(dosya_yolu, engine="openpyxl")
                except Exception as openpyxl_error:
                    # Her ikisi de başarısız olursa varsayılan engine'i dene
                    logger.warning(
                        f"openpyxl ile okuma başarısız, varsayılan engine deneniyor: {openpyxl_error}"
                    )
                    df = pd.read_excel(dosya_yolu)

            logger.info(f"Excel dosyası başarıyla okundu: {dosya_yolu}")
            logger.info(f"Satır sayısı: {len(df)}, Sütun sayısı: {len(df.columns)}")

            return df

        except Exception as e:
            logger.error(f"Excel dosyası okuma hatası: {e}")
            raise

    def veri_temizle(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Veriyi temizler ve standartlaştırır

        Args:
            df: Ham veri DataFrame'i

        Returns:
            DataFrame: Temizlenmiş veri
        """
        try:
            # Boş satırları kaldır
            df_temiz = df.dropna(how="all")

            # Bugünün tarihini ekle
            df_temiz[TARIH_KOLON_ADI] = datetime.now().date()

            # Sütun isimlerini temizle
            df_temiz.columns = df_temiz.columns.str.strip().str.lower()

            logger.info(f"Veri temizlendi. Kalan satır sayısı: {len(df_temiz)}")

            return df_temiz

        except Exception as e:
            logger.error(f"Veri temizleme hatası: {e}")
            raise

    def parquet_kaydet(self, df: pd.DataFrame, dosya_adi: Optional[str] = None) -> str:
        """
        DataFrame'i parquet formatında kaydeder

        Args:
            df: Kaydedilecek DataFrame
            dosya_adi: İsteğe bağlı dosya adı

        Returns:
            str: Kaydedilen dosyanın yolu
        """
        try:
            if dosya_adi is None:
                tarih_str = datetime.now().strftime("%Y%m%d")
                dosya_adi = f"gunluk_veri_{tarih_str}.parquet"

            dosya_yolu = ISLENMIŞ_VERI_DIZIN / dosya_adi

            df.to_parquet(
                dosya_yolu,
                engine=PARQUET_MOTOR,
                compression=PARQUET_SIKISTIRMA,
                index=False,
            )

            logger.info(f"Parquet dosyası kaydedildi: {dosya_yolu}")
            return str(dosya_yolu)

        except Exception as e:
            logger.error(f"Parquet kaydetme hatası: {e}")
            raise

    def ana_veriyi_guncelle(self, yeni_df: pd.DataFrame) -> None:
        """
        Ana parquet dosyasını yeni verilerle günceller (duplicate kontrolü ile)

        Args:
            yeni_df: Eklenecek yeni veriler
        """
        try:
            if self.ana_parquet_dosya.exists():
                # Mevcut veriyi oku
                mevcut_df = pd.read_parquet(self.ana_parquet_dosya)

                # Orijinal satır sayıları
                mevcut_satir_sayisi = len(mevcut_df)
                yeni_satir_sayisi = len(yeni_df)

                # Yeni veriyle birleştir
                birleşik_df = pd.concat([mevcut_df, yeni_df], ignore_index=True)

                # Duplicate'leri kaldır (tüm sütunlara göre)
                birleşik_df = birleşik_df.drop_duplicates()

                # Tarih sütununa göre sırala
                if TARIH_KOLON_ADI in birleşik_df.columns:
                    birleşik_df = birleşik_df.sort_values(TARIH_KOLON_ADI)

                # İstatistikleri logla
                son_satir_sayisi = len(birleşik_df)
                eklenen_yeni_satirlar = son_satir_sayisi - mevcut_satir_sayisi
                duplicate_satirlar = yeni_satir_sayisi - eklenen_yeni_satirlar

                logger.info(f"Veri güncelleme istatistikleri:")
                logger.info(f"  - Mevcut satır sayısı: {mevcut_satir_sayisi}")
                logger.info(f"  - Yeni dosyadaki satır sayısı: {yeni_satir_sayisi}")
                logger.info(f"  - Eklenen yeni satır sayısı: {eklenen_yeni_satirlar}")
                logger.info(f"  - Duplicate/Skip edilen satır: {duplicate_satirlar}")
                logger.info(f"  - Toplam satır sayısı: {son_satir_sayisi}")

            else:
                birleşik_df = yeni_df.drop_duplicates()
                logger.info(
                    f"Yeni ana veri dosyası oluşturuldu: {len(birleşik_df)} satır"
                )

            # Ana dosyayı güncelle
            birleşik_df.to_parquet(
                self.ana_parquet_dosya,
                engine=PARQUET_MOTOR,
                compression=PARQUET_SIKISTIRMA,
                index=False,
            )

        except Exception as e:
            logger.error(f"Ana veri güncelleme hatası: {e}")
            raise

    def gunluk_islem(self, excel_dosya_yolu: str) -> Dict[str, Any]:
        """
        Günlük veri işleme operasyonu

        Args:
            excel_dosya_yolu: İşlenecek Excel dosyasının yolu

        Returns:
            Dict: İşlem sonuç bilgileri
        """
        try:
            # Excel dosyasını oku
            ham_df = self.excel_oku(excel_dosya_yolu)

            # Veriyi temizle
            temiz_df = self.veri_temizle(ham_df)

            # Günlük parquet dosyası kaydet
            gunluk_dosya = self.parquet_kaydet(temiz_df)

            # Ana veriyi güncelle
            self.ana_veriyi_guncelle(temiz_df)

            sonuc = {
                "durum": "başarılı",
                "kaynak_dosya": excel_dosya_yolu,
                "gunluk_parquet": gunluk_dosya,
                "işlenen_satir_sayisi": len(temiz_df),
                "işlem_tarihi": datetime.now().isoformat(),
            }

            logger.info(f"Günlük işlem tamamlandı: {sonuc}")
            return sonuc

        except Exception as e:
            logger.error(f"Günlük işlem hatası: {e}")
            raise


def parquet_oku(dosya_yolu: str) -> pd.DataFrame:
    """
    Parquet dosyasını okur

    Args:
        dosya_yolu: Parquet dosyasının yolu

    Returns:
        DataFrame: Okunan veriler
    """
    try:
        return pd.read_parquet(dosya_yolu)
    except Exception as e:
        logger.error(f"Parquet okuma hatası: {e}")
        raise

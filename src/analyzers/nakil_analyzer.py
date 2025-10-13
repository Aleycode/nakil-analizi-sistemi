"""
Ana nakil analizcisi - Modüler koordinatör sınıf
"""

import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from ..processors.veri_isleme import VeriIsleme
from .analiz_motoru import AnalizMotoru
from ..generators.grafik_olusturucu import GrafikOlusturucu
from .klinik_analizcisi import KlinikAnalizcisi
from ..generators.pdf_olusturucu import PDFOlusturucu

# Logger yapılandırması
logger = logging.getLogger(__name__)


class NakilAnalizcisi:
    """Ana nakil analizcisi - Modüler koordinatör sınıf"""

    def __init__(self):
        """Nakil analizcisi başlatma"""
        # Alt modülleri başlat
        self.veri_isleme = VeriIsleme()
        self.analiz_motoru = AnalizMotoru()
        self.grafik_olusturucu = GrafikOlusturucu()
        self.klinik_analizcisi = KlinikAnalizcisi(self.grafik_olusturucu)
        self.pdf_olusturucu = PDFOlusturucu()

    def kapsamli_gunluk_analiz(
        self, gun_tarihi: Optional[str] = None, unique_id: str = None
    ) -> Dict[str, Any]:
        """
        Kapsamlı günlük analiz yapar - Modüler yaklaşım
        """
        try:
            if gun_tarihi is None:
                gun_tarihi = datetime.now().strftime("%Y-%m-%d")

            logger.info(f"Kapsamlı günlük analiz başlatılıyor: {gun_tarihi}")

            # 1. Veri işleme - son işlenen günlük veriyi kullan
            from ..core.config import ISLENMIŞ_VERI_DIZIN
            
            # Tarih bazlı klasörleri bul
            tarih_format = gun_tarihi.replace('-', '')  # 20251013
            tarih_klasorleri = [k for k in ISLENMIŞ_VERI_DIZIN.glob(f"günlük_{tarih_format}*") if k.is_dir()]
            
            if not tarih_klasorleri:
                logger.error(f"Tarih için klasör bulunamadı: {tarih_format}")
                return {"durum": "hata", "mesaj": f"Tarih için klasör bulunamadı: {tarih_format}"}
            
            # En son modifiye edilen klasörü al
            gunluk_klasor = max(tarih_klasorleri, key=lambda x: x.stat().st_mtime)
            gunluk_dosya = gunluk_klasor / "veriler.parquet"
            
            logger.info(f"Son işlenen günlük dosya kullanılıyor: {gunluk_dosya}")
            
            if gunluk_dosya.exists():
                logger.info(f"Günlük dosya okunuyor: {gunluk_dosya}")
                df_gunluk = pd.read_parquet(gunluk_dosya)
                # KRİTİK: Tarih sütunlarını datetime'a çevir
                logger.info("Tarih sütunları datetime'a dönüştürülüyor...")
                df_gunluk = self.veri_isleme.ensure_datetime_columns(df_gunluk)
                logger.info(f"Datetime dönüşümü tamamlandı. Veri boyutu: {len(df_gunluk)}")
                
                # Bu dosya zaten günlük filtreli, vaka tipi belirleme yap
                df_gunluk = self.veri_isleme.vaka_tipi_belirle(df_gunluk, gun_tarihi)
            else:
                logger.error(f"Günlük dosya bulunamadı: {gunluk_dosya}")
                return {"durum": "hata", "mesaj": f"Günlük dosya bulunamadı: {gunluk_dosya}"}
            
            # Süre hesaplamalarını ekle ve durum_kategori oluştur
            gun_datetime = datetime.strptime(gun_tarihi, "%Y-%m-%d")
            logger.info(f"Süre hesaplamaları ekleniyor... (gun_datetime: {gun_datetime})")
            df_gunluk = self.veri_isleme.sure_hesaplama_ekle(df_gunluk, gun_datetime)
            
            # Durum kategori kontrolü
            if 'durum_kategori' not in df_gunluk.columns:
                logger.warning("durum_kategori sütunu bulunamadı! Manuel olarak ekleniyor...")
                df_gunluk['durum_kategori'] = 'Bilinmiyor'
            
            logger.info(f"Veri hazırlığı tamamlandı. Sütunlar: {df_gunluk.columns.tolist()}")
            
            il_gruplari = self.veri_isleme.il_bazinda_grupla(df_gunluk)

            # 2. Ana rapor objesi
            gecerli_vakalar = df_gunluk[df_gunluk["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])]
            rapor = {
                "analiz_tarihi": gun_tarihi,
                "analiz_zamani": datetime.now().isoformat(),
                "toplam_vaka_sayisi": len(gecerli_vakalar),
                "il_gruplari": {},
                "genel_istatistikler": {},
                "oluşturulan_grafikler": [],
            }

            # Rapor klasörü ve PDF adı için unique_id kullan
            rapor_klasor_adi = gun_tarihi
            if unique_id:
                rapor_klasor_adi = f"{gun_tarihi}_{unique_id}"
            rapor_dizin = Path("data/reports") / rapor_klasor_adi
            rapor_dizin.mkdir(parents=True, exist_ok=True)
            rapor["rapor_dizin"] = str(rapor_dizin)
            
            # GrafikOlusturucu'ya rapor dizinini set et (tüm grafikler buraya kaydedilecek)
            self.grafik_olusturucu._rapor_dizin_override = rapor_dizin

            # 3. Genel istatistikler
            if len(df_gunluk) > 0:
                genel_stats = self.analiz_motoru.genel_istatistik_hesapla(df_gunluk)
                rapor["genel_istatistikler"] = genel_stats
                
                # Süre istatistiklerini ekle
                sure_istatistikleri = self.veri_isleme.sure_istatistiklerini_hesapla(df_gunluk)
                rapor["sure_analizleri"] = sure_istatistikleri

            # 4. Her il grubu için analiz
            for il_grup_adi, il_df in il_gruplari.items():
                if len(il_df) == 0:
                    continue

                rapor["il_gruplari"][il_grup_adi] = {}

                # Vaka tiplerine göre grupla
                vaka_tipleri = ["Yeni Vaka", "Devreden Vaka", "Butun_Vakalar"]

                for vaka_tipi in vaka_tipleri:
                    if vaka_tipi == "Butun_Vakalar":
                        # Bütün Vakalar = Yeni Vaka + Devreden Vaka (Analize Dahil Edilmeyecekler hariç)
                        vaka_df = il_df[
                            il_df["vaka_tipi"].isin(["Yeni Vaka", "Devreden Vaka"])
                        ].copy()
                    else:
                        vaka_df = il_df[il_df["vaka_tipi"] == vaka_tipi].copy()

                    if len(vaka_df) == 0:
                        continue

                    rapor["il_gruplari"][il_grup_adi][vaka_tipi] = {}

                    # 1. Vaka durumu analizi
                    durum_analizi = self.analiz_motoru.vaka_durumu_analizi(
                        vaka_df, il_grup_adi, vaka_tipi
                    )
                    rapor["il_gruplari"][il_grup_adi][vaka_tipi][
                        "vaka_durumu"
                    ] = durum_analizi
                    
                    # 1.1. Süre analizi
                    sure_analizi = self.veri_isleme.sure_istatistiklerini_hesapla(vaka_df)
                    rapor["il_gruplari"][il_grup_adi][vaka_tipi][
                        "sure_analizleri"
                    ] = sure_analizi

                    # Grafik oluştur (vaka durumu)
                    try:
                        if durum_analizi and "durum_sayilari" in durum_analizi:
                            baslik = self.grafik_olusturucu._grafik_baslik_olustur(
                                "vaka_durumu", grup_adi=il_grup_adi, vaka_tipi=vaka_tipi
                            )
                            # Dict'i pandas Series'e çevir (pd zaten global import edilmiş)
                            durum_series = pd.Series(durum_analizi["durum_sayilari"])
                            grafik_path = f"vaka_durumu_{il_grup_adi}_{vaka_tipi}_{gun_tarihi}.png"
                            grafik_path_str = str(self.grafik_olusturucu.pasta_grafik_olustur(
                                durum_series,
                                baslik,
                                grafik_path,
                                gun_tarihi
                            ))
                            if grafik_path_str:
                                rapor["oluşturulan_grafikler"].append(grafik_path_str)
                            else:
                                logger.warning(f"Grafik oluşturulamadı: {grafik_path} (veri: {len(durum_series)})")
                    except Exception as grafik_hata:
                        logger.error(f"Vaka durumu grafiği oluşturma hatası: {grafik_hata}")

                    # 2. İptal vakalar için bekleme süresi
                    iptal_analizi = self.analiz_motoru.bekleme_suresi_analizi(
                        vaka_df, il_grup_adi, vaka_tipi, "İptal"
                    )
                    if iptal_analizi:
                        rapor["il_gruplari"][il_grup_adi][vaka_tipi][
                            "iptal_bekleme_suresi"
                        ] = iptal_analizi

                    # 3. Yer Ayarlandı için bekleme süresi ve threshold analizi
                    yer_analizi = self.analiz_motoru.bekleme_suresi_analizi(
                        vaka_df, il_grup_adi, vaka_tipi, "Yer Ayarlandı"
                    )
                    if yer_analizi:
                        rapor["il_gruplari"][il_grup_adi][vaka_tipi][
                            "yer_ayarlandi_bekleme_suresi"
                        ] = yer_analizi

                        # Threshold pasta grafiği
                        try:
                            if "threshold_analizi" in yer_analizi:
                                baslik = self.grafik_olusturucu._grafik_baslik_olustur(
                                    "bekleme_threshold",
                                    grup_adi=il_grup_adi,
                                    vaka_tipi=vaka_tipi,
                                )
                                grafik_path = f"bekleme_threshold_{il_grup_adi}_{vaka_tipi}_{gun_tarihi}.png"
                                grafik_path_str = str(self.grafik_olusturucu.threshold_pasta_grafik(
                                    yer_analizi["threshold_analizi"],
                                    baslik,
                                    grafik_path,
                                ))
                                if grafik_path_str:
                                    rapor["oluşturulan_grafikler"].append(grafik_path_str)
                                else:
                                    logger.warning(f"Threshold grafik oluşturulamadı: {grafik_path} (veri: {yer_analizi['threshold_analizi']})")
                        except Exception as grafik_hata:
                            logger.error(f"Threshold grafiği oluşturma hatası: {grafik_hata}")

                    # 4. Klinik dağılım analizi
                    klinik_analizi = self.klinik_analizcisi.klinik_dagilim_analizi(
                        vaka_df, f"{il_grup_adi}_{vaka_tipi}"
                    )
                    if klinik_analizi and "hata" not in klinik_analizi:
                        rapor["il_gruplari"][il_grup_adi][vaka_tipi][
                            "klinik_analizi"
                        ] = klinik_analizi

                        # Klinik grafiklerini oluştur
                        try:
                            grafik_dosyalari = (
                                self.klinik_analizcisi.klinik_grafikleri_olustur(
                                    vaka_df, gun_tarihi, f"{il_grup_adi}_{vaka_tipi}"
                                )
                            )
                            import os
                            for grafik_path in grafik_dosyalari or []:
                                if not os.path.exists(grafik_path):
                                    logger.warning(f"Klinik grafik oluşturulamadı: {grafik_path}")
                            if grafik_dosyalari:
                                rapor["oluşturulan_grafikler"].extend(grafik_dosyalari)
                        except Exception as grafik_hata:
                            logger.error(f"Klinik grafikleri oluşturma hatası: {grafik_hata}")

            # 5. Yeni pasta grafikleri oluştur (her il grubu için)
            from ..core.config import GRAFIK_AYARLARI

            # Vaka tipi pasta grafikleri
            try:
                if GRAFIK_AYARLARI.get("vaka_tipi_pasta_grafigi", True):
                    for il_grup_adi, il_df in il_gruplari.items():
                        if len(il_df) > 0:
                            vaka_tipi_dosya = (
                                self.grafik_olusturucu.vaka_tipi_pasta_grafigi(
                                    il_df, gun_tarihi, il_grup_adi
                                )
                            )
                            if vaka_tipi_dosya:
                                grafik_dosya_str = str(vaka_tipi_dosya)
                                grafik_listesi = rapor["oluşturulan_grafikler"]
                                grafik_listesi.append(grafik_dosya_str)
            except Exception as grafik_hata:
                logger.error(f"Vaka tipi pasta grafikleri oluşturma hatası: {grafik_hata}")

            # İl dağılımı pasta grafiği (genel)
            try:
                if GRAFIK_AYARLARI.get("il_dagilim_pasta_grafigi", True):
                    il_dagilim_dosya = self.grafik_olusturucu.il_dagilim_pasta_grafigi(
                        il_gruplari, gun_tarihi
                    )
                    if il_dagilim_dosya:
                        grafik_dosya_str = str(il_dagilim_dosya)
                        grafik_listesi = rapor["oluşturulan_grafikler"]
                        grafik_listesi.append(grafik_dosya_str)
            except Exception as grafik_hata:
                logger.error(f"İl dağılımı pasta grafiği oluşturma hatası: {grafik_hata}")

            # İptal eden karşılaştırma grafiği (il içi vs il dışı)
            try:
                if GRAFIK_AYARLARI.get("iptal_eden_karsilastirma_grafigi", True):
                    karsilastirma_dosya = (
                        self.grafik_olusturucu.iptal_eden_karsilastirma_grafigi(
                            il_gruplari, gun_tarihi
                        )
                    )
                    if karsilastirma_dosya:
                        grafik_dosya_str = str(karsilastirma_dosya)
                        grafik_listesi = rapor["oluşturulan_grafikler"]
                        grafik_listesi.append(grafik_dosya_str)
            except Exception as grafik_hata:
                logger.error(f"İptal eden karşılaştırma grafiği oluşturma hatası: {grafik_hata}")

            # Solunum işlemi pasta grafikleri (her il grubu için)
            try:
                if GRAFIK_AYARLARI.get("solunum_islemi_pasta_grafigi", True):
                    solunum_grafik_dosyasi = (
                        self.grafik_olusturucu.solunum_islemi_pasta_grafigi(
                            il_gruplari["Butun_Bolgeler"], gun_tarihi, "Butun_Bolgeler"
                        )
                    )
                    if solunum_grafik_dosyasi:
                        grafik_listesi = rapor["oluşturulan_grafikler"]
                        grafik_listesi.append(str(solunum_grafik_dosyasi))
            except Exception as grafik_hata:
                logger.error(f"Solunum işlemi pasta grafikleri oluşturma hatası: {grafik_hata}")

            # Süre analizi grafikleri
            try:
                if df_gunluk is not None and len(df_gunluk) > 0:
                    # Yer bulma süresi histogramı 
                    histogram_dosya = self.grafik_olusturucu.sure_dagilimi_histogram(
                        df_gunluk, gun_tarihi
                    )
                    if histogram_dosya:
                        grafik_listesi = rapor["oluşturulan_grafikler"]
                        grafik_listesi.append(histogram_dosya)
                    
                    # Klinik bazında süre karşılaştırması
                    klinik_sure_dosya = self.grafik_olusturucu.klinik_sure_karsilastirma(
                        df_gunluk, gun_tarihi
                    )
                    if klinik_sure_dosya:
                        grafik_listesi = rapor["oluşturulan_grafikler"] 
                        grafik_listesi.append(klinik_sure_dosya)
                    
                    # Bekleme durumu analizi
                    bekleme_dosya = self.grafik_olusturucu.bekleme_durumu_analizi(
                        df_gunluk, gun_tarihi
                    )
                    if bekleme_dosya:
                        grafik_listesi = rapor["oluşturulan_grafikler"]
                        grafik_listesi.append(bekleme_dosya)
            except Exception as grafik_hata:
                logger.error(f"Süre analizi grafikleri oluşturma hatası: {grafik_hata}")

            # Nakil bekleyen raporu oluştur (txt)
            if GRAFIK_AYARLARI.get("nakil_bekleyen_raporu", True):
                try:
                    rapor_dosya = self._nakil_bekleyen_raporu_olustur(
                        il_gruplari, gun_tarihi, rapor_dizin
                    )
                    if rapor_dosya:
                        grafik_listesi = rapor["oluşturulan_grafikler"]
                        grafik_listesi.append(str(rapor_dosya))
                except Exception as e:
                    logger.error(f"Nakil bekleyen rapor hatası: {e}")

            # 6. Raporu kaydet
            # Rapor klasörünü unique_id ile al (önceden oluşturulmuştu)
            tarih_klasor = Path(rapor["rapor_dizin"])
            rapor_dosya = tarih_klasor / f"kapsamli_gunluk_analiz_{gun_tarihi}.json"
            with open(rapor_dosya, "w", encoding="utf-8") as f:
                json.dump(rapor, f, ensure_ascii=False, indent=2, default=str)

            # 7. PDF raporu oluşturulmadan ÖNCE: Grafiklerin hepsi unique_id klasöründe dursun
            # Böylece PDF içine tüm PNG'ler dahil edilecek
            try:
                import shutil
                from ..core.config import RAPOR_DIZIN

                # Tarih bazlı klasör (standart günlük klasör)
                tarih_bazli_klasor = RAPOR_DIZIN / gun_tarihi
                # PDF'in kaydedileceği klasör
                unique_id_klasor = tarih_klasor
                
                # Durumu göster
                logger.info(f"Tarih klasörü: {tarih_bazli_klasor}, mevcutmu: {tarih_bazli_klasor.exists()}")
                logger.info(f"PDF klasörü: {unique_id_klasor}, mevcutmu: {unique_id_klasor.exists()}")
                
                if tarih_bazli_klasor.exists():
                    # Tarih bazlı klasördeki PNG sayısını gör
                    png_listesi = list(tarih_bazli_klasor.glob("*.png"))
                    logger.info(f"Tarih klasöründe {len(png_listesi)} PNG dosyası mevcut")
                    
                    # Klasör farklıysa kopyala, aynı klasörse atla
                    if tarih_bazli_klasor != unique_id_klasor and unique_id_klasor.exists():
                        kopya_sayisi = 0
                        for grafik_dosya in png_listesi:
                            hedef = unique_id_klasor / grafik_dosya.name
                            if not hedef.exists():
                                shutil.copy2(grafik_dosya, hedef)
                                kopya_sayisi += 1
                        
                        if kopya_sayisi > 0:
                            logger.info(f"📄 PDF öncesi {kopya_sayisi} grafik unique klasöre kopyalandı: {tarih_bazli_klasor} → {unique_id_klasor}")
                    else:
                        if tarih_bazli_klasor == unique_id_klasor:
                            logger.info("Klasörler aynı, kopya işlemi atlanıyor")
                        else:
                            logger.info(f"Hedef klasör mevcut değil, oluşturuluyor: {unique_id_klasor}")
                            unique_id_klasor.mkdir(parents=True, exist_ok=True)
                            # Grafikleri kopyala
                            kopya_sayisi = 0
                            for grafik_dosya in png_listesi:
                                hedef = unique_id_klasor / grafik_dosya.name
                                shutil.copy2(grafik_dosya, hedef)
                                kopya_sayisi += 1
                            
                            logger.info(f"📄 PDF öncesi {kopya_sayisi} grafik yeni klasöre kopyalandı: {tarih_bazli_klasor} → {unique_id_klasor}")
                else:
                    logger.warning(f"Tarih klasörü mevcut değil, grafik kopyalanamıyor: {tarih_bazli_klasor}")
            except Exception as pre_copy_err:
                logger.warning(f"PDF öncesi grafik kopyalama hatası (kritik değil): {pre_copy_err}")

            # 8. PDF raporu oluştur - unique_id parametresini ekle
            try:
                pdf_dosya = self.pdf_olusturucu.pdf_olustur(tarih_klasor, gun_tarihi, rapor, unique_id)
                if pdf_dosya:
                    rapor["pdf_raporu"] = str(pdf_dosya)
                    logger.info(f"PDF raporu oluşturuldu: {pdf_dosya}")
            except Exception as e:
                logger.error(f"PDF rapor oluşturma hatası: {e}")
            
            # Grafik oluşturucu override'ını temizle
            self.grafik_olusturucu._rapor_dizin_override = None

            # ÖNEMLİ: Grafikleri unique_id klasörüne kopyala (Rapor Arşivi için) - PDF sonrası yine güvence
            try:
                import shutil
                
                # Tarih bazlı klasör (grafiklerin olduğu yer)
                from ..core.config import RAPOR_DIZIN
                tarih_bazli_klasor = RAPOR_DIZIN / gun_tarihi
                
                # unique_id'li klasör (PDF'in olduğu yer)
                unique_id_klasor = tarih_klasor  # Bu zaten Path objesi
                
                if tarih_bazli_klasor.exists() and unique_id_klasor.exists():
                    grafik_sayisi = 0
                    for grafik_dosya in tarih_bazli_klasor.glob("*.png"):
                        hedef = unique_id_klasor / grafik_dosya.name
                        if not hedef.exists():
                            shutil.copy2(grafik_dosya, hedef)
                            grafik_sayisi += 1
                    
                    if grafik_sayisi > 0:
                        logger.info(f"✅ {grafik_sayisi} grafik kopyalandı: {tarih_bazli_klasor} → {unique_id_klasor}")
                    else:
                        logger.warning(f"⚠️ Kopyalanacak grafik bulunamadı: {tarih_bazli_klasor}")
                else:
                    logger.warning(f"⚠️ Klasörlerden biri mevcut değil. Tarih: {tarih_bazli_klasor.exists()}, Unique: {unique_id_klasor.exists()}")
            except Exception as copy_error:
                logger.warning(f"Grafik kopyalama hatası (kritik değil): {copy_error}")

            logger.info(f"Kapsamlı analiz tamamlandı: {rapor_dosya}")
            
            # Başarı durumunu ekle
            rapor["durum"] = "basarili"
            rapor["mesaj"] = "Analiz başarıyla tamamlandı"
            
            return rapor

        except Exception as e:
            logger.error(f"Kapsamlı günlük analiz hatası: {e}")
            # Hata durumunda da override'ı temizle
            self.grafik_olusturucu._rapor_dizin_override = None
            raise

    def _nakil_bekleyen_raporu_olustur(self, il_gruplari: dict, gun_tarihi: str, rapor_dizin: Path):
        """
        Nakil bekleyen talep raporu oluşturur (txt formatında)

        Args:
            il_gruplari: İl gruplarına göre ayrılmış veriler
            gun_tarihi: Analiz tarihi
            rapor_dizin: Raporun kaydedileceği dizin

        Returns:
            str: Oluşturulan dosyanın yolu
        """
        try:
            # Verilen rapor dizinini kullan (unique_id'li)
            rapor_dosya = rapor_dizin / f"nakil_bekleyen_raporu_{gun_tarihi}.txt"

            rapor_icerigi = []
            rapor_icerigi.append("NAKİL BEKLEYEN TALEP RAPORU")
            rapor_icerigi.append("=" * 40)
            rapor_icerigi.append(f"Tarih: {gun_tarihi}")
            rapor_icerigi.append("")

            # Tüm verileri birleştir (Butun_Bolgeler)
            if "Butun_Bolgeler" in il_gruplari:
                tum_veri = il_gruplari["Butun_Bolgeler"]

                # Nakil bekleyen vakaları filtrele (Yer Aranıyor durumunda olanlar)
                bekleyen_vakalar = tum_veri[tum_veri["durum"].isin(["Yer Aranıyor"])]

                # Toplam nakil bekleyen talep
                toplam_bekleyen = len(bekleyen_vakalar)
                rapor_icerigi.append(f"Nakil Bekleyen Toplam Talep: {toplam_bekleyen}")

                # İl içi/dışı dağılımı
                if "Il_Ici" in il_gruplari and "Il_Disi" in il_gruplari:
                    il_ici_bekleyen = len(
                        il_gruplari["Il_Ici"][
                            il_gruplari["Il_Ici"]["durum"].isin(["Yer Aranıyor"])
                        ]
                    )
                    il_disi_bekleyen = len(
                        il_gruplari["Il_Disi"][
                            il_gruplari["Il_Disi"]["durum"].isin(["Yer Aranıyor"])
                        ]
                    )

                    rapor_icerigi.append(f"İl İçi Talep: {il_ici_bekleyen}")
                    rapor_icerigi.append(f"İl Dışı Talep: {il_disi_bekleyen}")

                rapor_icerigi.append("")
                rapor_icerigi.append("-" * 13)
                rapor_icerigi.append("")

                # Yoğun bakım talepleri
                yb_bekleyen = bekleyen_vakalar[
                    bekleyen_vakalar["nakledilmesi i̇stenen klinik"].str.contains(
                        "YOĞUN BAKIM", case=False, na=False
                    )
                ]

                toplam_yb_bekleyen = len(yb_bekleyen)
                rapor_icerigi.append(
                    f"Nakil Bekleyen Yoğun Bakım Toplam Talep: {toplam_yb_bekleyen}"
                )

                # İl içi/dışı yoğun bakım talepleri
                if "Il_Ici" in il_gruplari and "Il_Disi" in il_gruplari:
                    # İl içi YB
                    il_ici_yb = il_gruplari["Il_Ici"][
                        (il_gruplari["Il_Ici"]["durum"].isin(["Yer Aranıyor"]))
                        & (
                            il_gruplari["Il_Ici"][
                                "nakledilmesi i̇stenen klinik"
                            ].str.contains("YOĞUN BAKIM", case=False, na=False)
                        )
                    ]

                    # İl dışı YB
                    il_disi_yb = il_gruplari["Il_Disi"][
                        (il_gruplari["Il_Disi"]["durum"].isin(["Yer Aranıyor"]))
                        & (
                            il_gruplari["Il_Disi"][
                                "nakledilmesi i̇stenen klinik"
                            ].str.contains("YOĞUN BAKIM", case=False, na=False)
                        )
                    ]

                    rapor_icerigi.append(f"İl İçi Yb Talep: {len(il_ici_yb)}")
                    rapor_icerigi.append(f"İl Dışı Yb Talep: {len(il_disi_yb)}")
                    rapor_icerigi.append("")

                    # Solunum işlemine göre ayrım (İl İçi)
                    if len(il_ici_yb) > 0 and "solunum i̇şlemi" in il_ici_yb.columns:
                        il_ici_entube = il_ici_yb[
                            ~il_ici_yb["solunum i̇şlemi"].isin(["Non-Entübe"])
                        ]
                        il_ici_non_entube = il_ici_yb[
                            il_ici_yb["solunum i̇şlemi"].isin(["Non-Entübe"])
                        ]

                        rapor_icerigi.append(
                            f"İl İçi Entübe Yb Talep: {len(il_ici_entube)}"
                        )
                        rapor_icerigi.append(
                            f"İl İçi Non-Entübe Yb Talep: {len(il_ici_non_entube)}"
                        )
                        rapor_icerigi.append("")

                    # Solunum işlemine göre ayrım (İl Dışı)
                    if len(il_disi_yb) > 0 and "solunum i̇şlemi" in il_disi_yb.columns:
                        il_disi_entube = il_disi_yb[
                            ~il_disi_yb["solunum i̇şlemi"].isin(["Non-Entübe"])
                        ]
                        il_disi_non_entube = il_disi_yb[
                            il_disi_yb["solunum i̇şlemi"].isin(["Non-Entübe"])
                        ]

                        rapor_icerigi.append(
                            f"İl Dışı Entübe Yb Talep: {len(il_disi_entube)}"
                        )
                        rapor_icerigi.append(
                            f"İl Dışı Non-Entübe Yb Talep: {len(il_disi_non_entube)}"
                        )

            # Raporu dosyaya yaz
            with open(rapor_dosya, "w", encoding="utf-8") as f:
                f.write("\n".join(rapor_icerigi))

            logger.info(f"Nakil bekleyen raporu oluşturuldu: {rapor_dosya}")
            return rapor_dosya

        except Exception as e:
            logger.error(f"Nakil bekleyen rapor hatası: {e}")
            return None

    # Geriye uyumluluk için eski metodları yönlendir
    def veriyi_oku(self):
        """Geriye uyumluluk için veri okuma"""
        return self.veri_isleme.veriyi_oku()

    def gunluk_zaman_araligi_filtrele(self, df, gun_tarihi=None):
        """Geriye uyumluluk için zaman aralığı filtreleme"""
        return self.veri_isleme.gunluk_zaman_araligi_filtrele(df, gun_tarihi)

    def vaka_tipi_belirle(self, df, gun_tarihi=None):
        """Geriye uyumluluk için vaka tipi belirleme"""
        return self.veri_isleme.vaka_tipi_belirle(df, gun_tarihi)

    def il_bazinda_grupla(self, df):
        """Geriye uyumluluk için il bazında gruplama"""
        return self.veri_isleme.il_bazinda_grupla(df)

    def klinik_dagilim_analizi(self, df, grup_adi="Genel"):
        """Geriye uyumluluk için klinik dağılım analizi"""
        return self.klinik_analizcisi.klinik_dagilim_analizi(df, grup_adi)

    def klinik_grafikleri_olustur(self, df, gun_tarihi, grup_adi="Genel"):
        """Geriye uyumluluk için klinik grafikleri oluşturma"""
        return self.klinik_analizcisi.klinik_grafikleri_olustur(
            df, gun_tarihi, grup_adi
        )

    def klinik_filtrele(self, df):
        """Geriye uyumluluk için klinik filtreleme"""
        return self.klinik_analizcisi.klinik_filtrele(df)

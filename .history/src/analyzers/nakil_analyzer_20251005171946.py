"""
Ana nakil analizcisi - Modüler koordinatör sınıf
"""

import logging
import json
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

            # 1. Veri işleme - unique_id varsa o dosyayı oku
            if unique_id:
                # Unique_id'li günlük dosyayı oku
                from ..core.config import ISLENMIŞ_VERI_DIZIN
                tarih_str = gun_tarihi.replace("-", "")
                gunluk_klasor = ISLENMIŞ_VERI_DIZIN / f"günlük_{tarih_str}_{unique_id}"
                gunluk_dosya = gunluk_klasor / "veriler.parquet"
                
                if gunluk_dosya.exists():
                    logger.info(f"Unique_id'li günlük dosya okunuyor: {gunluk_dosya}")
                    df_gunluk = pd.read_parquet(gunluk_dosya)
                else:
                    logger.error(f"Unique_id'li günlük dosya bulunamadı: {gunluk_dosya}")
                    return {}
                    
                # Bu dosya zaten günlük filtreli, vaka tipi belirleme yap
                df_gunluk = self.veri_isleme.vaka_tipi_belirle(df_gunluk, gun_tarihi)
            else:
                # Normal akış: ana veriyi oku ve filtrele
                df = self.veri_isleme.veriyi_oku()
                if df.empty:
                    logger.warning("Ana veri boş, analiz yapılamıyor.")
                    return {} # veya hata yönetimi
                
                df_gunluk = self.veri_isleme.gunluk_zaman_araligi_filtrele(df, gun_tarihi)
                df_gunluk = self.veri_isleme.vaka_tipi_belirle(df_gunluk, gun_tarihi)
            
            # Süre hesaplamalarını ekle
            gun_datetime = datetime.strptime(gun_tarihi, "%Y-%m-%d")
            df_gunluk = self.veri_isleme.sure_hesaplama_ekle(df_gunluk, gun_datetime)
            
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
                    if durum_analizi and "durum_sayilari" in durum_analizi:
                        baslik = self.grafik_olusturucu._grafik_baslik_olustur(
                            "vaka_durumu", grup_adi=il_grup_adi, vaka_tipi=vaka_tipi
                        )
                        # Dict'i pandas Series'e çevir
                        import pandas as pd

                        durum_series = pd.Series(durum_analizi["durum_sayilari"])
                        grafik_path = f"vaka_durumu_{il_grup_adi}_{vaka_tipi}_{gun_tarihi}.png"
                        self.grafik_olusturucu.pasta_grafik_olustur(
                            durum_series,
                            baslik,
                            grafik_path,
                        )
                        import os
                        if not os.path.exists(grafik_path):
                            logger.warning(f"Grafik oluşturulamadı: {grafik_path} (veri: {len(durum_series)})")

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
                        if "threshold_analizi" in yer_analizi:
                            baslik = self.grafik_olusturucu._grafik_baslik_olustur(
                                "bekleme_threshold",
                                grup_adi=il_grup_adi,
                                vaka_tipi=vaka_tipi,
                            )
                            grafik_path = f"bekleme_threshold_{il_grup_adi}_{vaka_tipi}_{gun_tarihi}.png"
                            self.grafik_olusturucu.threshold_pasta_grafik(
                                yer_analizi["threshold_analizi"],
                                baslik,
                                grafik_path,
                            )
                            import os
                            if not os.path.exists(grafik_path):
                                logger.warning(f"Threshold grafik oluşturulamadı: {grafik_path} (veri: {yer_analizi['threshold_analizi']})")

                    # 4. Klinik dağılım analizi
                    klinik_analizi = self.klinik_analizcisi.klinik_dagilim_analizi(
                        vaka_df, f"{il_grup_adi}_{vaka_tipi}"
                    )
                    if klinik_analizi and "hata" not in klinik_analizi:
                        rapor["il_gruplari"][il_grup_adi][vaka_tipi][
                            "klinik_analizi"
                        ] = klinik_analizi

                        # Klinik grafiklerini oluştur
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

            # 5. Yeni pasta grafikleri oluştur (her il grubu için)
            from ..core.config import GRAFIK_AYARLARI

            # Vaka tipi pasta grafikleri
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

            # İl dağılımı pasta grafiği (genel)
            if GRAFIK_AYARLARI.get("il_dagilim_pasta_grafigi", True):
                il_dagilim_dosya = self.grafik_olusturucu.il_dagilim_pasta_grafigi(
                    il_gruplari, gun_tarihi
                )
                if il_dagilim_dosya:
                    grafik_dosya_str = str(il_dagilim_dosya)
                    grafik_listesi = rapor["oluşturulan_grafikler"]
                    grafik_listesi.append(grafik_dosya_str)

            # İptal eden karşılaştırma grafiği (il içi vs il dışı)
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

            # Solunum işlemi pasta grafikleri (her il grubu için)
            if GRAFIK_AYARLARI.get("solunum_islemi_pasta_grafigi", True):
                solunum_grafik_dosyasi = (
                    self.grafik_olusturucu.solunum_islemi_pasta_grafigi(
                        il_gruplari["Butun_Bolgeler"], gun_tarihi, "Butun_Bolgeler"
                    )
                )
                if solunum_grafik_dosyasi:
                    grafik_listesi = rapor["oluşturulan_grafikler"]
                    grafik_listesi.append(str(solunum_grafik_dosyasi))

            # Süre analizi grafikleri
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

            # 7. PDF raporu oluştur - unique_id parametresini ekle
            try:
                pdf_dosya = self.pdf_olusturucu.pdf_olustur(tarih_klasor, gun_tarihi, rapor, unique_id)
                if pdf_dosya:
                    rapor["pdf_raporu"] = str(pdf_dosya)
                    logger.info(f"PDF raporu oluşturuldu: {pdf_dosya}")
            except Exception as e:
                logger.error(f"PDF rapor oluşturma hatası: {e}")
            
            # Grafik oluşturucu override'ını temizle
            self.grafik_olusturucu._rapor_dizin_override = None

            logger.info(f"Kapsamlı analiz tamamlandı: {rapor_dosya}")
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

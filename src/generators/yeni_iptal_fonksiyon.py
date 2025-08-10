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

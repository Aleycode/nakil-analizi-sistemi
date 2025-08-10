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

            # Grafik oluştur
            fig, ax = plt.subplots(figsize=(12, 6))

            # Kategoriler ve veriler
            kategoriler = ['İl Dışı', 'İl İçi']  # Ters sırada (Y ekseninde yukarıdan aşağı)
            
            # İl İçi veriler
            il_ici_kkm = il_ici_veriler["KKM"]
            il_ici_gonderen = il_ici_veriler["Gönderen"]
            
            # İl Dışı veriler  
            il_disi_kkm = il_disi_veriler["KKM"]
            il_disi_gonderen = il_disi_veriler["Gönderen"]

            # Her kategori için büyük değer sol (alt), küçük değer sağ (üst) mantığı
            # İl İçi için
            if il_ici_kkm >= il_ici_gonderen:
                il_ici_left_values = [il_ici_kkm]
                il_ici_right_values = [il_ici_gonderen]
                il_ici_left_labels = ["KKM"]
                il_ici_right_labels = ["Gönderen"]
                il_ici_left_colors = ['#2E86AB']
                il_ici_right_colors = ['#A23B72']
            else:
                il_ici_left_values = [il_ici_gonderen]
                il_ici_right_values = [il_ici_kkm]
                il_ici_left_labels = ["Gönderen"]
                il_ici_right_labels = ["KKM"]
                il_ici_left_colors = ['#A23B72']
                il_ici_right_colors = ['#2E86AB']

            # İl Dışı için
            if il_disi_kkm >= il_disi_gonderen:
                il_disi_left_values = [il_disi_kkm]
                il_disi_right_values = [il_disi_gonderen]
                il_disi_left_labels = ["KKM"]
                il_disi_right_labels = ["Gönderen"]
                il_disi_left_colors = ['#2E86AB']
                il_disi_right_colors = ['#A23B72']
            else:
                il_disi_left_values = [il_disi_gonderen]
                il_disi_right_values = [il_disi_kkm]
                il_disi_left_labels = ["Gönderen"]
                il_disi_right_labels = ["KKM"]
                il_disi_left_colors = ['#A23B72']
                il_disi_right_colors = ['#2E86AB']

            # Y pozisyonları
            y_pos = [0, 1]  # İl Dışı: 0, İl İçi: 1
            bar_height = 0.6

            # Sol çubuklar (büyük değerler)
            bars_left_0 = ax.barh(y_pos[0], il_disi_left_values[0], bar_height, 
                                 label=il_disi_left_labels[0], color=il_disi_left_colors[0], alpha=0.8)
            bars_left_1 = ax.barh(y_pos[1], il_ici_left_values[0], bar_height, 
                                 color=il_ici_left_colors[0], alpha=0.8)

            # Sağ çubuklar (küçük değerler) - sol çubukların üzerine eklenir
            bars_right_0 = ax.barh(y_pos[0], il_disi_right_values[0], bar_height, 
                                  left=il_disi_left_values[0], label=il_disi_right_labels[0], 
                                  color=il_disi_right_colors[0], alpha=0.8)
            bars_right_1 = ax.barh(y_pos[1], il_ici_right_values[0], bar_height, 
                                  left=il_ici_left_values[0], 
                                  color=il_ici_right_colors[0], alpha=0.8)

            # Değerleri çubukların üzerine yaz
            # İl Dışı değerleri
            if il_disi_left_values[0] > 0:
                ax.text(il_disi_left_values[0]/2, y_pos[0], str(il_disi_left_values[0]), 
                       ha='center', va='center', fontweight='bold', fontsize=10)
            if il_disi_right_values[0] > 0:
                ax.text(il_disi_left_values[0] + il_disi_right_values[0]/2, y_pos[0], 
                       str(il_disi_right_values[0]), ha='center', va='center', 
                       fontweight='bold', fontsize=10)

            # İl İçi değerleri  
            if il_ici_left_values[0] > 0:
                ax.text(il_ici_left_values[0]/2, y_pos[1], str(il_ici_left_values[0]), 
                       ha='center', va='center', fontweight='bold', fontsize=10)
            if il_ici_right_values[0] > 0:
                ax.text(il_ici_left_values[0] + il_ici_right_values[0]/2, y_pos[1], 
                       str(il_ici_right_values[0]), ha='center', va='center', 
                       fontweight='bold', fontsize=10)

            # Eksen ayarları
            ax.set_yticks(y_pos)
            ax.set_yticklabels(kategoriler, fontsize=12)
            ax.set_xlabel('İptal Vaka Sayısı', fontweight='bold', fontsize=12)
            ax.set_title('İptal Eden Kurumlar', fontsize=16, fontweight='bold', pad=20)

            # Legend - sadece KKM ve Gönderen için
            handles = []
            labels = []
            
            # KKM için legend
            kkm_color = '#2E86AB'
            gonderen_color = '#A23B72'
            
            handles.append(plt.Rectangle((0,0),1,1, color=kkm_color, alpha=0.8))
            labels.append('KKM')
            handles.append(plt.Rectangle((0,0),1,1, color=gonderen_color, alpha=0.8))
            labels.append('Gönderen')
            
            ax.legend(handles, labels, loc='lower right', fontsize=11)

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

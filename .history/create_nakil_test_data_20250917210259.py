import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def create_test_data():
    # Test verisi için parametreler
    n_rows = 100
    baslangic_tarihi = datetime(2025, 9, 1)
    bitis_tarihi = datetime(2025, 9, 17)
    
    # İller ve klinikler
    iller = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Gaziantep"]
    klinikler = [
        "KORONER YOĞUN BAKIM", "GENEL YOĞUN BAKIM", "YENİDOĞAN YOĞUN BAKIM",
        "KARDİYOLOJİ", "NÖROLOJİ", "GENEL CERRAHİ", "ACİL SERVİS",
        "GÖĞÜS HASTALIKLARI", "İÇ HASTALIKLARI"
    ]
    nakil_turleri = ["İl İçi", "İl Dışı"]
    durumlar = ["Yer Aranıyor", "Yer Ayarlandı", "İptal"]
    iptal_nedenleri = ["Hasta İsteği", "Tıbbi Endikasyon", "Hastane Kapasitesi", "Diğer", ""]
    solunum_islemleri = ["Entübe", "Non-Entübe", "SPONTAN", "NON-INVASIVE"]
    iptal_edenler = ["Hasta", "Hekim", "Sistem", ""]
    
    # Rastgele tarihler oluştur
    tarihler = [baslangic_tarihi + timedelta(
        days=np.random.randint((bitis_tarihi - baslangic_tarihi).days),
        hours=np.random.randint(24),
        minutes=np.random.randint(60)
    ) for _ in range(n_rows)]
    
    # Yer bulunma tarihleri (bazı vakalar için)
    yer_tarihleri = []
    for i in range(n_rows):
        if np.random.random() < 0.3:  # %30 ihtimalle yer bulunmuş
            yer_tarihi = tarihler[i] + timedelta(
                hours=np.random.randint(1, 72),  # 1-72 saat arası
                minutes=np.random.randint(60)
            )
            yer_tarihleri.append(yer_tarihi)
        else:
            yer_tarihleri.append(pd.NaT)
    
    # Veri çerçevesi oluştur (gerçek sütun adlarıyla)
    df = pd.DataFrame({
        "oluşturma tarihi": tarihler,
        "hasta tc": [f"{np.random.randint(10000000000, 99999999999)}" for _ in range(n_rows)],
        "il": np.random.choice(iller, n_rows),
        "nakledilmesi i̇stenen klinik": np.random.choice(klinikler, n_rows),
        "durum": np.random.choice(durumlar, n_rows, p=[0.5, 0.3, 0.2]),
        "solunum i̇şlemi": np.random.choice(solunum_islemleri, n_rows),
        "yer bulunma tarihi": yer_tarihleri,
        "i̇ptal nedeni": "",
        "i̇ptal eden": ""
    })
    
    # İl bazında nakil türü belirle
    df["nakil türü"] = df["il"].apply(lambda x: "İl Dışı" if np.random.random() < 0.3 else "İl İçi")
    
    # İptal edilmiş vakalar için nedenleri ekle
    iptal_mask = df["durum"] == "İptal"
    if iptal_mask.sum() > 0:
        df.loc[iptal_mask, "i̇ptal nedeni"] = np.random.choice(
            [x for x in iptal_nedenleri if x != ""], iptal_mask.sum()
        )
        df.loc[iptal_mask, "i̇ptal eden"] = np.random.choice(
            [x for x in iptal_edenler if x != ""], iptal_mask.sum()
        )
    
    # Yer ayarlananlar için yer bulunma tarihi ekle
    yer_ayarlandi_mask = df["durum"] == "Yer Ayarlandı"
    if yer_ayarlandi_mask.sum() > 0:
        for idx in df[yer_ayarlandi_mask].index:
            if pd.isna(df.loc[idx, "yer bulunma tarihi"]):
                df.loc[idx, "yer bulunma tarihi"] = df.loc[idx, "oluşturma tarihi"] + timedelta(
                    hours=np.random.randint(1, 48),
                    minutes=np.random.randint(60)
                )
    
    # Tarihleri string formatına çevir (Excel formatı)
    df["oluşturma tarihi"] = df["oluşturma tarihi"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["yer bulunma tarihi"] = df["yer bulunma tarihi"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # NaN değerlerini boş string yap
    df = df.fillna("")
    
    # Dizini oluştur ve kaydet
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/nakil_test_veri.xlsx"
    df.to_excel(output_path, index=False)
    
    print(f"Gerçekçi test verisi oluşturuldu: {output_path}")
    print(f"Veri özeti:")
    print(f"- Toplam vaka: {len(df)}")
    print(f"- Yer Aranıyor: {(df['durum'] == 'Yer Aranıyor').sum()}")
    print(f"- Yer Ayarlandı: {(df['durum'] == 'Yer Ayarlandı').sum()}")
    print(f"- İptal: {(df['durum'] == 'İptal').sum()}")
    print(f"- İl İçi: {(df['nakil türü'] == 'İl İçi').sum()}")
    print(f"- İl Dışı: {(df['nakil türü'] == 'İl Dışı').sum()}")

if __name__ == "__main__":
    create_test_data()
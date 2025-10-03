import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def create_test_data():
    # Test verisi için parametreler
    n_rows = 100
    baslangic_tarihi = datetime(2025, 8, 1)
    bitis_tarihi = datetime(2025, 9, 30)
    
    # İller ve klinikler
    iller = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"]
    klinikler = ["Kardiyoloji", "Nöroloji", "Genel Cerrahi", "Acil Servis"]
    nakil_turleri = ["İl İçi", "İl Dışı"]
    durumlar = ["Beklemede", "Tamamlandı", "İptal Edildi"]
    iptal_nedenleri = ["Hasta İsteği", "Tıbbi Endikasyon", "Hastane Kapasitesi", "Diğer"]
    
    # Rastgele tarihler oluştur
    tarihler = [baslangic_tarihi + timedelta(
        days=np.random.randint((bitis_tarihi - baslangic_tarihi).days)
    ) for _ in range(n_rows)]
    
    # Veri çerçevesi oluştur
    df = pd.DataFrame({
        "Tarih": tarihler,
        "İl": np.random.choice(iller, n_rows),
        "Klinik": np.random.choice(klinikler, n_rows),
        "Nakil Türü": np.random.choice(nakil_turleri, n_rows),
        "Durum": np.random.choice(durumlar, n_rows, p=[0.4, 0.4, 0.2]),
        "İptal Nedeni": np.nan
    })
    
    # İptal edilmiş vakalar için nedenleri ekle
    iptal_mask = df["Durum"] == "İptal Edildi"
    df.loc[iptal_mask, "İptal Nedeni"] = np.random.choice(iptal_nedenleri, sum(iptal_mask))
    
    # Tarihi datetime tipinde tut
    df["Tarih"] = pd.to_datetime(df["Tarih"]).dt.date
    
    # Dizini oluştur ve kaydet
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/nakil_test_veri.xlsx"
    df.to_excel(output_path, index=False)
    print(f"Test verisi oluşturuldu: {output_path}")

if __name__ == "__main__":
    create_test_data()
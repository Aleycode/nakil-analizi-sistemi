"""Menü işlemleri için yardımcı fonksiyonlar"""

from pathlib import Path
from typing import Optional
import os

def excel_dosyasi_sec() -> Optional[str]:
    """
    Kullanıcıdan Excel dosyası seçmesini ister

    Returns:
        str: Seçilen Excel dosyasının yolu veya None
    """
    while True:
        print("\n📂 Excel dosyası seçimi:")
        print("1. Raw klasöründeki son dosyayı kullan")
        print("2. Dosya yolu gir")
        print("3. İptal")
        
        secim = input("\nSeçiminiz (1-3): ").strip()
        
        if secim == "1":
            raw_klasor = Path("data/raw")
            if not raw_klasor.exists():
                print("❌ Raw klasörü bulunamadı!")
                continue
                
            excel_dosyalari = [f for f in raw_klasor.glob("*.xls*")]
            if not excel_dosyalari:
                print("❌ Raw klasöründe Excel dosyası bulunamadı!")
                continue
                
            # En son değiştirilen dosyayı seç
            son_dosya = max(excel_dosyalari, key=os.path.getmtime)
            print(f"✅ Seçilen dosya: {son_dosya}")
            return str(son_dosya)
            
        elif secim == "2":
            dosya_yolu = input("Excel dosyasının tam yolunu girin: ").strip()
            dosya = Path(dosya_yolu)
            
            if not dosya.exists():
                print("❌ Dosya bulunamadı!")
                continue
                
            if not dosya.suffix.lower() in ['.xls', '.xlsx']:
                print("❌ Geçersiz dosya türü! .xls veya .xlsx olmalı")
                continue
                
            return str(dosya)
            
        elif secim == "3":
            return None
            
        else:
            print("❌ Geçersiz seçim!")
            
def menu_basligi_goster(baslik: str) -> None:
    """Menü başlığını gösterir"""
    print("\n" + "=" * 50)
    print(baslik.center(50))
    print("=" * 50)
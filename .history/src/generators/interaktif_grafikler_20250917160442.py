from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import logging
from typing import Dict, Any, Optional

from ..core.config import RAPOR_DIZIN
from ..utils.grafik_sabitleri import GRAFIK_RENK_PALETI, PLOTLY_TEMA

logger = logging.getLogger(__name__)

class InteraktifGrafikOlusturucu:
    """İnteraktif grafik oluşturma sınıfı"""
    
    def __init__(self):
        self.rapor_dizin = RAPOR_DIZIN
        # Plotly temasını ayarla
        pio.templates["custom"] = go.layout.Template(layout=PLOTLY_TEMA["layout"])
        pio.templates.default = "custom"
    
    def pasta_grafik_olustur(
        self,
        veriler: pd.Series,
        baslik: str,
        dosya_adi: str,
        aciklama: Optional[str] = None,
        min_yuzde: float = 3.0
    ) -> str:
        """
        İnteraktif pasta grafik oluşturur
        
        Args:
            veriler: Grafik verileri (pandas Series)
            baslik: Grafik başlığı
            dosya_adi: Kaydedilecek dosya adı
            aciklama: Grafik açıklaması (opsiyonel)
            min_yuzde: Minimum gösterim yüzdesi
        
        Returns:
            str: Oluşturulan HTML dosyasının yolu
        """
        try:
            # Veri hazırlama
            degerler = veriler.values
            etiketler = veriler.index
            yuzdelikler = (degerler / degerler.sum()) * 100
            
            # Hover bilgisi için metin hazırla
            hover_metin = [
                f"Kategori: {etiket}<br>"
                f"Değer: {int(deger)}<br>"
                f"Yüzde: %{yuzde:.1f}"
                for etiket, deger, yuzde in zip(etiketler, degerler, yuzdelikler)
            ]
            
            # Grafik oluştur
            fig = go.Figure()
            
            fig.add_trace(
                go.Pie(
                    labels=etiketler,
                    values=degerler,
                    textinfo="percent+value",
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=hover_metin,
                    marker=dict(colors=GRAFIK_RENK_PALETI),
                    textposition="auto",
                    textfont=dict(size=14),
                )
            )
            
            # Başlık ve açıklama
            baslik_html = f"<b>{baslik}</b>"
            if aciklama:
                baslik_html += f"<br><span style='font-size:14px'>{aciklama}</span>"
            
            fig.update_layout(
                title=dict(
                    text=baslik_html,
                    x=0.5,
                    xanchor="center",
                ),
                width=800,
                height=600,
            )
            
            # Dosya yolları
            tarih_klasor = self._tarih_klasoru_olustur()
            html_dosya = tarih_klasor / f"{dosya_adi}.html"
            png_dosya = tarih_klasor / f"{dosya_adi}.png"
            
            # HTML ve PNG olarak kaydet
            fig.write_html(html_dosya)
            fig.write_image(png_dosya)
            
            logger.info(f"İnteraktif grafik oluşturuldu: {html_dosya}")
            return str(html_dosya)
            
        except Exception as e:
            logger.error(f"Pasta grafik oluşturma hatası: {e}")
            raise
    
    def _tarih_klasoru_olustur(self) -> Path:
        """Tarih klasörünü oluşturur ve yolunu döndürür"""
        from datetime import datetime
        
        tarih = datetime.now().strftime("%Y-%m-%d")
        klasor = self.rapor_dizin / tarih
        klasor.mkdir(parents=True, exist_ok=True)
        return klasor
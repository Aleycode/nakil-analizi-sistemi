#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Grafik oluşturma için sabit değerler ve yardımcı fonksiyonlar.
"""

from typing import List, Tuple, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns

# Temel matplotlib ayarları
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

# Renk paleti (color-blind friendly)
GRAFIK_RENK_PALETI: List[str] = [
    '#3498DB',  # Ana kategori - Mavi
    '#F1C40F',  # İkincil kategori - Sarı
    '#2ECC71',  # Olumlu durumlar - Yeşil
    '#E74C3C',  # Uyarılar - Kırmızı
    '#9B59B6',  # Özel durumlar - Mor
    '#1ABC9C',  # Nötr durumlar - Turkuaz
    '#E67E22',  # Önemli - Turuncu
    '#34495E'   # Diğer - Lacivert
]

# Matplotlib stil ayarları
GRAFIK_STIL: Dict[str, Any] = {
    'figure.facecolor': 'white',
    'axes.facecolor': '#F8F9FA',
    'axes.edgecolor': '#343A40',
    'axes.labelcolor': '#212529',
    'axes.grid': True,
    'grid.alpha': 0.2,
    'text.color': '#212529',
    'xtick.color': '#495057',
    'ytick.color': '#495057',
    'figure.titlesize': 14,
    'axes.titlesize': 14,
    'axes.labelsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'legend.framealpha': 0.8,
    'legend.edgecolor': '#DEE2E6'
}

def format_etiket(deger: float, toplam: float, min_yuzde: float = 3.0) -> str:
    """Pasta grafik etiketlerini akıllı şekilde formatlar.
    
    Args:
        deger: Dilimin değeri
        toplam: Toplam değer
        min_yuzde: Minimum gösterim yüzdesi
    
    Returns:
        str: Formatlanmış etiket metni
    """
    yuzde = (deger / toplam) * 100
    return f'{int(deger)}\n%{yuzde:.1f}' if yuzde < min_yuzde else f'{int(deger)}\n(%{yuzde:.1f})'

def renk_paleti_uret(n: int) -> List[str]:
    """Verilen sayıda renk üretir.
    
    Args:
        n: İhtiyaç duyulan renk sayısı
    
    Returns:
        List[str]: Renk kodları listesi
    """
    if n <= len(GRAFIK_RENK_PALETI):
        return GRAFIK_RENK_PALETI[:n]
    return GRAFIK_RENK_PALETI + GRAFIK_RENK_PALETI[:(n - len(GRAFIK_RENK_PALETI))]

def grafik_ayarlarini_uygula() -> None:
    """Tüm grafik ayarlarını uygular."""
    for key, value in GRAFIK_STIL.items():
        plt.rcParams[key] = value
    sns.set_palette(sns.color_palette(GRAFIK_RENK_PALETI))

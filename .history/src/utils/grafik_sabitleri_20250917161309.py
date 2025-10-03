#!/usr/bin/env python3# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-"""Grafik oluşturma için sabit değerler ve yardımcı fonksiyonlar."""



"""Grafik oluşturma için sabit değerler ve yardımcı fonksiyonlar."""from typing import List, Tuple

import matplotlib.pyplot as plt

from typing import List, Tuple, Dict, Any

import matplotlib.pyplot as plt# Temel ayarlar

import seaborn as snsplt.style.use("seaborn")

plt.rcParams["font.family"] = "sans-serif"

# Temel matplotlib ayarlarıplt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]

plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']# Ana renk paleti

GRAFIK_RENK_PALETI = [

# Seaborn stil ayarları    "#3498DB",  # Ana kategori - Mavi

sns.set_style("whitegrid")    "#F1C40F",  # İkincil kategori - Sarı

sns.set_context("notebook", font_scale=1.2)    "#2ECC71",  # Olumlu durumlar - Yeşil

    "#E74C3C",  # Uyarılar - Kırmızı

# Renk paleti (color-blind friendly)    "#9B59B6",  # Özel durumlar - Mor

GRAFIK_RENK_PALETI: List[str] = [    "#1ABC9C",  # Nötr durumlar - Turkuaz

    '#3498DB',  # Ana kategori - Mavi    "#E67E22",  # Önemli - Turuncu

    '#F1C40F',  # İkincil kategori - Sarı    "#34495E",  # Diğer - Lacivert

    '#2ECC71',  # Olumlu durumlar - Yeşil]

    '#E74C3C',  # Uyarılar - Kırmızı

    '#9B59B6',  # Özel durumlar - Mordef format_etiket(deger: float, toplam: float, min_yuzde: float = 3.0) -> str:

    '#1ABC9C',  # Nötr durumlar - Turkuaz    """Pasta grafik etiketlerini formatlar"""

    '#E67E22',  # Önemli - Turuncu    yuzde = (deger / toplam) * 100

    '#34495E',  # Diğer - Lacivert    if yuzde < min_yuzde:

]        return f"{int(deger)}

%{yuzde:.1f}"

# Grafik boyutları    return f"{int(deger)}

GRAFIK_BOYUTLARI: Dict[str, Tuple[int, int]] = {(%{yuzde:.1f})"

    'varsayilan': (10, 8),

    'buyuk': (12, 10),def renk_paleti_uret(n: int) -> List[str]:

    'kucuk': (8, 6)    """İstenilen sayıda renk üretir"""

}    return GRAFIK_RENK_PALETI[:n] + GRAFIK_RENK_PALETI[:(n - len(GRAFIK_RENK_PALETI))]



# Font boyutları# Grafik stil ayarları

FONT_BOYUTLARI: Dict[str, int] = {GRAFIK_STIL = {

    'baslik': 14,    "figure.facecolor": "white",

    'alt_baslik': 12,    "axes.facecolor": "#F8F9FA",

    'etiket': 10,    "axes.edgecolor": "#343A40",

    'lejant': 9    "axes.labelcolor": "#212529",

}    "axes.grid": True,

    "grid.alpha": 0.2,

# Matplotlib stil ayarları    "text.color": "#212529",

GRAFIK_STIL: Dict[str, Any] = {    "xtick.color": "#495057",

    'figure.facecolor': 'white',    "ytick.color": "#495057",

    'axes.facecolor': '#F8F9FA',    "figure.titlesize": 14,

    'axes.edgecolor': '#343A40',    "axes.titlesize": 14,

    'axes.labelcolor': '#212529',    "axes.labelsize": 10,

    'axes.grid': True,    "xtick.labelsize": 10,

    'grid.alpha': 0.2,    "ytick.labelsize": 10,

    'text.color': '#212529',    "legend.fontsize": 9,

    'xtick.color': '#495057',    "legend.framealpha": 0.8,

    'ytick.color': '#495057',    "legend.edgecolor": "#DEE2E6"

    'figure.titlesize': FONT_BOYUTLARI['baslik'],}

    'axes.titlesize': FONT_BOYUTLARI['alt_baslik'],

    'axes.labelsize': FONT_BOYUTLARI['etiket'],# Stil ayarlarını uygula

    'xtick.labelsize': FONT_BOYUTLARI['etiket'],plt.style.use(GRAFIK_STIL)

    'ytick.labelsize': FONT_BOYUTLARI['etiket'],
    'legend.fontsize': FONT_BOYUTLARI['lejant'],
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
    # Temel stil
    plt.style.use('seaborn')
    
    # Özel stil ayarları
    for key, value in GRAFIK_STIL.items():
        plt.rcParams[key] = value
    
    # Renk paleti
    sns.set_palette(sns.color_palette(GRAFIK_RENK_PALETI))

# Başlangıç ayarlarını uygula
grafik_ayarlarini_uygula()
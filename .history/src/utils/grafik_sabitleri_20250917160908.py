"""Grafik oluşturma için sabit değerler ve yardımcı fonksiyonlar.""""""Grafik oluşturma için sabit değerler ve yardımcı fonksiyonlar."""



from typing import List, Tuple, Dict, Anyfrom typing import List, Tuple, Dict, Any

import plotly.graph_objects as goimport plotly.graph_objects as go

import plotly.io as pioimport plotly.io as pio



# Erişilebilir ve kullanıcı dostu renk paleti (Color-blind friendly)# Temel renk paleti (Color-blind friendly)

GRAFIK_RENK_PALETI = [GRAFIK_RENK_PALETI = [

    '#3498DB',  # Ana kategori - Mavi    '#2E86C1',  # Mavi - Ana kategori

    '#F1C40F',  # İkincil kategori - Sarı    '#F39C12',  # Turuncu - İkincil kategori

    '#2ECC71',  # Olumlu durumlar - Yeşil    '#27AE60',  # Yeşil - Olumlu durumlar

    '#E74C3C',  # Uyarılar - Kırmızı    '#E74C3C',  # Kırmızı - Uyarılar

    '#9B59B6',  # Özel durumlar - Mor    '#8E44AD',  # Mor - Özel durumlar

    '#1ABC9C',  # Nötr durumlar - Turkuaz    '#16A085',  # Turkuaz - Nötr

    '#E67E22',  # Önemli - Turuncu    '#D35400',  # Koyu Turuncu - Önemli

    '#34495E',  # Diğer - Lacivert    '#2C3E50',  # Lacivert - Diğer

]]



# Grafik boyutları# Plotly tema ayarları

VARSAYILAN_GRAFIK_BOYUTU = (10, 8)PLOTLY_TEMA = {

BUYUK_GRAFIK_BOYUTU = (12, 10)    'layout': {

KUCUK_GRAFIK_BOYUTU = (8, 6)        'font': {'family': 'Arial, sans-serif', 'size': 12},

        'title': {'font': {'size': 20}},

# Font ayarları        'plot_bgcolor': 'white',

BASLIK_FONT_BOYUTU = 14        'paper_bgcolor': 'white',

ETIKET_FONT_BOYUTU = 10        'margin': {'t': 100, 'b': 80, 'l': 80, 'r': 80},

LEJANT_FONT_BOYUTU = 9        'showlegend': True,

        'legend': {

# Plotly tema ayarları            'orientation': 'h',

PLOTLY_TEMA = {            'yanchor': 'bottom',

    'layout': {            'y': -0.2,

        'font': {'family': 'Arial, sans-serif', 'size': 12},            'xanchor': 'center',

        'title': {'font': {'size': 20}},            'x': 0.5

        'plot_bgcolor': 'white',        },

        'paper_bgcolor': 'white',        'hoverlabel': {'bgcolor': 'white', 'font_size': 14},

        'margin': {'t': 100, 'b': 80, 'l': 80, 'r': 80},    }

        'showlegend': True,}urma için sabit değerler ve yardımcı fonksiyonlar."""

        'legend': {

            'orientation': 'h',from typing import List, Tuple

            'yanchor': 'bottom',

            'y': -0.2,# Erişilebilir ve kullanıcı dostu renk paleti (Color-blind friendly)

            'xanchor': 'center',GRAFIK_RENK_PALETI = [

            'x': 0.5    '#3498DB',  # Açık Mavi - Ana kategori

        },    '#E67E22',  # Turuncu - İkincil kategori

        'hoverlabel': {'bgcolor': 'white', 'font_size': 14},    '#2ECC71',  # Yeşil - Olumlu durumlar

    }    '#E74C3C',  # Kırmızı - Dikkat çekilmesi gereken durumlar

}    '#9B59B6',  # Mor - Özel durumlar

    '#1ABC9C',  # Turkuaz - Nötr durumlar

# Matplotlib stil ayarları    '#F1C40F',  # Sarı - Uyarı durumları

GRAFIK_STIL = {    '#34495E',  # Lacivert - Diğer

    'figure.facecolor': 'white',]

    'axes.facecolor': '#F8F9FA',

    'axes.edgecolor': '#343A40',# Pasta grafik opacity değerleri

    'axes.labelcolor': '#212529',PASTA_GRAFIK_OPACITY = {

    'axes.grid': True,    'ana_dilim': 0.9,

    'grid.alpha': 0.2,    'vurgulanan_dilim': 1.0,

    'text.color': '#212529',    'soluk_dilim': 0.7

    'xtick.color': '#495057',}

    'ytick.color': '#495057',

    'figure.titlesize': BASLIK_FONT_BOYUTU,# Grafik boyutları

    'axes.titlesize': BASLIK_FONT_BOYUTU,VARSAYILAN_GRAFIK_BOYUTU = (10, 8)

    'axes.labelsize': ETIKET_FONT_BOYUTU,BUYUK_GRAFIK_BOYUTU = (12, 10)

    'xtick.labelsize': ETIKET_FONT_BOYUTU,KUCUK_GRAFIK_BOYUTU = (8, 6)

    'ytick.labelsize': ETIKET_FONT_BOYUTU,

    'legend.fontsize': LEJANT_FONT_BOYUTU,# Font ayarları

    'legend.framealpha': 0.8,BASLIK_FONT_BOYUTU = 14

    'legend.edgecolor': '#DEE2E6'ETIKET_FONT_BOYUTU = 10

}LEJANT_FONT_BOYUTU = 9



def format_etiket(deger: float, toplam: float, min_yuzde: float = 3.0) -> str:# Grafik stil ayarları

    """Pasta grafik dilimlerindeki etiketleri akıllı şekilde formatlar.GRAFIK_STIL = {

        'figure.facecolor': 'white',

    Args:    'axes.facecolor': '#F8F9FA',  # Hafif gri arkaplan

        deger: Dilimin değeri    'axes.edgecolor': '#343A40',  # Koyu gri kenarlıklar

        toplam: Toplam değer    'axes.labelcolor': '#212529',  # Koyu metin rengi

        min_yuzde: Minimum gösterim yüzdesi (bu değerin altındaki dilimlerin etiketi dışarıda gösterilir)    'axes.grid': True,  # Izgara çizgileri

        'grid.alpha': 0.2,  # Izgara saydamlığı

    Returns:    'text.color': '#212529',

        str: Formatlanmış etiket    'xtick.color': '#495057',

    """    'ytick.color': '#495057',

    yuzde = (deger / toplam) * 100    'figure.titlesize': 16,

        'axes.titlesize': 14,

    if yuzde < min_yuzde:    'axes.labelsize': 12,

        return f'{int(deger)}\n%{yuzde:.1f}'    'xtick.labelsize': 10,

        'ytick.labelsize': 10,

    return f'{int(deger)}\n(%{yuzde:.1f})'    'legend.fontsize': 10,

    'legend.framealpha': 0.8,

def renk_paleti_uret(n: int) -> List[str]:    'legend.edgecolor': '#DEE2E6'

    """İstenilen sayıda renk üretir.}

    

    Args:def format_etiket(deger: float, toplam: float, min_yuzde: float = 3.0) -> str:

        n: İhtiyaç duyulan renk sayısı    """Pasta grafik dilimlerindeki etiketleri akıllı şekilde formatlar.

        

    Returns:    Args:

        List[str]: Renk kodları listesi        deger: Dilimin değeri

    """        toplam: Toplam değer

    return GRAFIK_RENK_PALETI[:n] + GRAFIK_RENK_PALETI[:(n - len(GRAFIK_RENK_PALETI))]        min_yuzde: Minimum gösterim yüzdesi (bu değerin altındaki dilimlerin etiketi dışarıda gösterilir)
    
    Returns:
        str: Formatlanmış etiket
    """
    yuzde = (deger / toplam) * 100
    
    # Küçük dilimler için kısa format
    if yuzde < min_yuzde:
        return f'{int(deger)}\n%{yuzde:.1f}'
    
    # Büyük dilimler için detaylı format
    return f'{int(deger)}\n(%{yuzde:.1f})'

def renk_paleti_uret(n: int) -> List[str]:
    """İstenilen sayıda renk üretir.
    
    Args:
        n: İhtiyaç duyulan renk sayısı
    
    Returns:
        List[str]: Renk kodları listesi
    """
    return GRAFIK_RENK_PALETI[:n] + GRAFIK_RENK_PALETI[:(n - len(GRAFIK_RENK_PALETI))]
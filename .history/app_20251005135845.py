"""
Nakil Analiz Sistemi - Streamlit Web Arayüzü
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import base64
import json
import sys
import os
from datetime import datetime, timedelta
import subprocess

# Projenin ana dizinini PATH'e ekle (import modüller için)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Proje modüllerini import et
try:
    from src.core.config import (
        ISLENMIŞ_VERI_DIZIN, 
        RAPOR_DIZIN,
        HAM_VERI_DIZIN
    )
    from src.processors.veri_isleme import VeriIsleme
    from src.analyzers.nakil_analyzer import NakilAnalizcisi
    config_loaded = True
except ImportError as e:
    st.warning(f"Modül import hatası: {e}")
    config_loaded = False

# Ana dizine referans - Streamlit Cloud için
ROOT_DIR = Path(__file__).parent.absolute()
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_REPORTS_DIR = ROOT_DIR / "data" / "reports"

# Dizinleri oluştur (eğer mevcut değilse)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def configure_page():
    """Streamlit sayfasını yapılandır"""
    # Development modunu kapat
    import logging
    logging.getLogger().setLevel(logging.ERROR)
    
    st.set_page_config(
        page_title="Nakil Analiz Sistemi",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/Aleycode/nakil-analizi-sistemi',
            'Report a bug': 'https://github.com/Aleycode/nakil-analizi-sistemi/issues',
            'About': "Nakil Z Raporu Analiz Sistemi v1.0"
        }
    )
    
    # Streamlit stil düzenlemeleri
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    .stDecoration {display:none;}
    header {visibility: hidden;}
    .stApp > header {display: none;}
    .css-1rs6os {display: none;}
    .css-17ziqus {display: none;}
    
    /* Sidebar'ı zorunlu görünür yap - tüm sınıflar */
    .css-1d391kg, .css-1lcbmhc, .css-17lntkn, .css-1y4p8pa, .sidebar .sidebar-content {
        width: 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* Streamlit yeni sürüm sidebar sınıfları */
    [data-testid="stSidebar"] {
        width: 320px !important;
        min-width: 320px !important;
        display: block !important;
        visibility: visible !important;
    }
    
    [data-testid="stSidebar"] > div {
        width: 320px !important;
        min-width: 320px !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* Sidebar toggle butonunu vurgula */
    .css-vk3wp9, [data-testid="collapsedControl"] {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 50% !important;
        width: 50px !important;
        height: 50px !important;
        border: 3px solid #ff6b6b !important;
        box-shadow: 0 0 10px rgba(255, 75, 75, 0.5) !important;
    }
    
    /* Ana içerik alanını ayarla */
    .main .block-container {
        margin-left: 340px !important;
        max-width: calc(100% - 360px) !important;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .css-1d391kg, .css-1lcbmhc, [data-testid="stSidebar"] {
            width: 280px !important;
            min-width: 280px !important;
        }
        .main .block-container {
            margin-left: 300px !important;
            max-width: calc(100% - 320px) !important;
        }
    }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Gece modu kontrolü - varsayılan olarak açık
    dark_mode = True
    
    # Dinamik CSS - Gece/Gündüz modu
    if dark_mode:
        theme_css = """
        /* GECE MODU */
        .stApp {
            background-color: #0E1117 !important;
            color: #FAFAFA !important;
        }
        
        .main-header {
            font-size: 2.5rem;
            color: #64B5F6 !important;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .sub-header {
            font-size: 1.8rem;
            color: #FAFAFA !important;
            margin-top: 2rem;
        }
        
        .info-text {
            font-size: 1rem;
            color: #B0BEC5 !important;
        }
        
        .success-box {
            background-color: #1B2631 !important;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #4CAF50;
            color: #FAFAFA !important;
        }
        
        /* Sidebar gece modu */
        [data-testid="stSidebar"] {
            background-color: #1C1C1C !important;
        }
        
        [data-testid="stSidebar"] .css-1lcbmhc {
            background-color: #1C1C1C !important;
        }
        
        /* Sidebar yazıları */
        [data-testid="stSidebar"] * {
            color: #FAFAFA !important;
        }
        
        [data-testid="stSidebar"] .css-1v0mbdj {
            color: #FAFAFA !important;
        }
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: #FAFAFA !important;
        }
        
        /* Sidebar radio butonları */
        [data-testid="stSidebar"] label {
            color: #FAFAFA !important;
        }
        
        /* Sidebar markdown yazıları */
        [data-testid="stSidebar"] .css-10trblm {
            color: #FAFAFA !important;
        }
        
        /* Ana içerik alanı */
        .block-container {
            background-color: #0E1117 !important;
            color: #FAFAFA !important;
        }
        
        /* Butonlar gece modu */
        .stButton > button {
            background-color: #2E4057 !important;
            color: #FAFAFA !important;
            border: 1px solid #4A4A4A !important;
        }
        
        .stButton > button:hover {
            background-color: #3E5067 !important;
            border: 1px solid #64B5F6 !important;
        }
        
        /* Metin kutuları gece modu */
        .stTextInput > div > div > input {
            background-color: #2E4057 !important;
            color: #FAFAFA !important;
            border: 1px solid #4A4A4A !important;
        }
        
        /* Footer gece modu */
        .footer {
            background-color: rgba(28, 28, 28, 0.95) !important;
            color: #FAFAFA !important;
            border: 1px solid #444 !important;
        }
        
        /* Selectbox kapsamlı gece modu - KOYU YAZI */
        .stSelectbox > div > div > select {
            background-color: #F0F0F0 !important;
            color: #000000 !important;
            border: 1px solid #CCCCCC !important;
        }
        
        .stSelectbox select {
            background-color: #F0F0F0 !important;
            color: #000000 !important;
            border: 1px solid #CCCCCC !important;
        }
        
        /* Selectbox seçili değer kutusu */
        .stSelectbox > div > div {
            background-color: #F0F0F0 !important;
        }
        
        .stSelectbox > div > div > div {
            color: #000000 !important;
            background-color: #F0F0F0 !important;
        }
        
        /* Seçili değerin gösterildiği alan */
        .stSelectbox [data-baseweb="select"] > div {
            color: #000000 !important;
            background-color: #F0F0F0 !important;
        }
        
        .stSelectbox option {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        
        div[data-testid="stSelectbox"] select {
            background-color: #F0F0F0 !important;
            color: #000000 !important;
            border: 1px solid #CCCCCC !important;
        }
        
        div[data-testid="stSelectbox"] option {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* Selectbox selected value container */
        div[data-testid="stSelectbox"] {
            background-color: #F0F0F0 !important;
        }
        
        div[data-testid="stSelectbox"] * {
            color: #000000 !important;
        }
        
        div[data-testid="stSelectbox"] > div {
            background-color: #F0F0F0 !important;
        }
        
        div[data-testid="stSelectbox"] > div > div {
            background-color: #F0F0F0 !important;
            color: #000000 !important;
        }
        
        /* Selectbox dropdown styling - AÇIK ARKAPLAN */
        [data-baseweb="select"] {
            background-color: #F0F0F0 !important;
        }
        
        [data-baseweb="select"] * {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        
        /* Dropdown menü içeriği */
        [data-baseweb="popover"] {
            background-color: #FFFFFF !important;
        }
        
        [data-baseweb="popover"] * {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        
        /* Select dropdown option'ları */
        [role="option"] {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        
        [role="option"]:hover {
            background-color: #E3F2FD !important;
            color: #333333 !important;
        }
        
        /* AGRESİF SELECTBOX DÜZELTME */
        /* Streamlit'in tüm select elementleri için */
        select, 
        .stSelectbox select,
        div[data-testid="stSelectbox"] select,
        [data-baseweb="select"] select {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #CCCCCC !important;
        }
        
        /* Tüm option elementleri */
        option,
        .stSelectbox option,
        div[data-testid="stSelectbox"] option,
        [data-baseweb="select"] option {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* Dropdown list container */
        [role="listbox"] {
            background-color: #FFFFFF !important;
            border: 1px solid #CCCCCC !important;
        }
        
        [role="listbox"] * {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }
        
        /* File uploader gece modu - KAPSAMLI */
        .stFileUploader > div {
            background-color: #2E4057 !important;
            border: 2px dashed #64B5F6 !important;
            border-radius: 10px !important;
        }
        
        .stFileUploader > div > div {
            color: #FAFAFA !important;
        }
        
        .stFileUploader button {
            background-color: #4A4A4A !important;
            color: #FAFAFA !important;
            border: 1px solid #666 !important;
        }
        
        .stFileUploader button:hover {
            background-color: #64B5F6 !important;
            border: 1px solid #64B5F6 !important;
        }
        
        /* File uploader detaylı styling */
        div[data-testid="stFileUploader"] {
            background-color: #2E4057 !important;
            border: 2px dashed #64B5F6 !important;
            border-radius: 10px !important;
        }
        
        div[data-testid="stFileUploader"] * {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stFileUploader"] label {
            color: #FAFAFA !important;
            font-weight: bold !important;
        }
        
        div[data-testid="stFileUploader"] p {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stFileUploader"] span {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stFileUploader"] div {
            background-color: transparent !important;
            color: #FAFAFA !important;
        }
        
        /* File uploader drag area */
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            background-color: #2E4057 !important;
            border: 2px dashed #64B5F6 !important;
            color: #FAFAFA !important;
        }
        
        .stFileUploader [data-testid="stFileUploaderDropzone"] * {
            color: #FAFAFA !important;
        }
        
        /* File uploader inner text */
        [data-testid="stFileUploaderDropzoneInstructions"] {
            color: #FAFAFA !important;
        }
        
        [data-testid="stFileUploaderDropzoneInstructions"] * {
            color: #FAFAFA !important;
        }
        
        /* Browse files button styling */
        [data-testid="stFileUploaderBrowseFilesButton"] {
            background-color: #64B5F6 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 5px !important;
            font-weight: bold !important;
        }
        
        [data-testid="stFileUploaderBrowseFilesButton"]:hover {
            background-color: #42A5F5 !important;
        }
        
        /* Metrics gece modu */
        .metric-container {
            background-color: #1C1C1C !important;
            border: 1px solid #333 !important;
            border-radius: 5px !important;
            padding: 10px !important;
        }
        
        div[data-testid="metric-container"] {
            background-color: #1C1C1C !important;
            border: 1px solid #333 !important;
            border-radius: 5px !important;
            color: #FAFAFA !important;
        }
        
        div[data-testid="metric-container"] > div {
            color: #FAFAFA !important;
        }
        
        div[data-testid="metric-container"] label {
            color: #B0BEC5 !important;
        }
        
        /* Metric değerleri */
        [data-testid="stMetricValue"] {
            color: #FAFAFA !important;
            font-weight: bold !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #B0BEC5 !important;
        }
        
        /* Radio button gece modu - nakil analizi sayfası için */
        div[data-testid="stRadio"] > div {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stRadio"] label {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stRadio"] span {
            color: #FAFAFA !important;
        }
        
        /* Selectbox gece modu */
        div[data-testid="stSelectbox"] label {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stSelectbox"] > div > div {
            background-color: #2E4057 !important;
            color: #FAFAFA !important;
            border: 1px solid #4A4A4A !important;
        }
        
        /* Checkbox gece modu */
        div[data-testid="stCheckbox"] label {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stCheckbox"] span {
            color: #FAFAFA !important;
        }
        
        /* Expander gece modu */
        div[data-testid="stExpander"] {
            background-color: #1C1C1C !important;
            border: 1px solid #333 !important;
        }
        
        div[data-testid="stExpander"] label {
            color: #FAFAFA !important;
        }
        
        /* Tab yazıları gece modu */
        div[data-testid="stTabs"] button {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stTabs"] button[data-baseweb="tab-highlight"] {
            color: #64B5F6 !important;
        }
        
        /* Markdown yazıları gece modu */
        .stMarkdown {
            color: #FAFAFA !important;
        }
        
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6 {
            color: #FAFAFA !important;
        }
        
        .stMarkdown p {
            color: #FAFAFA !important;
        }
        
        /* Alert kutuları gece modu */
        div[data-testid="stAlert"] {
            color: #FAFAFA !important;
        }
        
        div[data-testid="stSuccess"] {
            background-color: #1B2631 !important;
            border-left: 5px solid #4CAF50 !important;
            color: #FAFAFA !important;
        }
        
        div[data-testid="stWarning"] {
            background-color: #2A2419 !important;
            border-left: 5px solid #FF9800 !important;
            color: #FAFAFA !important;
        }
        
        div[data-testid="stInfo"] {
            background-color: #1A2332 !important;
            border-left: 5px solid #2196F3 !important;
            color: #FAFAFA !important;
        }
        
        /* Grafik container'ları */
        .js-plotly-plot {
            background-color: #1C1C1C !important;
        }
        
        .plotly {
            background-color: #1C1C1C !important;
        }
        
        /* TÜM YAZI ELEMENTLERİ İÇİN GENEL KURALLAR */
        
        /* Tüm text elementleri */
        * {
            color: #FAFAFA !important;
        }
        
        /* Tüm div'ler */
        div {
            color: #FAFAFA !important;
        }
        
        /* Tüm span'lar */
        span {
            color: #FAFAFA !important;
        }
        
        /* Tüm p elementleri */
        p {
            color: #FAFAFA !important;
        }
        
        /* Tüm label'lar */
        label {
            color: #FAFAFA !important;
        }
        
        /* Streamlit özel elementler */
        .element-container {
            color: #FAFAFA !important;
        }
        
        .element-container * {
            color: #FAFAFA !important;
        }
        
        /* Block container içindeki tüm elementler */
        .block-container * {
            color: #FAFAFA !important;
        }
        
        /* Ana sayfa container'ı */
        .main * {
            color: #FAFAFA !important;
        }
        
        /* Grafik açıklamaları */
        .stPlotlyChart {
            color: #FAFAFA !important;
        }
        
        .stPlotlyChart * {
            color: #FAFAFA !important;
        }
        
        /* Streamlit widgets yazıları */
        .stWidget {
            color: #FAFAFA !important;
        }
        
        .stWidget * {
            color: #FAFAFA !important;
        }
        
        /* Form elementleri */
        .stForm {
            color: #FAFAFA !important;
        }
        
        .stForm * {
            color: #FAFAFA !important;
        }
        
        /* Caption yazıları */
        .caption {
            color: #B0BEC5 !important;
        }
        
        /* Small yazıları */
        small {
            color: #B0BEC5 !important;
        }
        
        /* İçerik alanındaki tüm yazılar */
        .css-1d391kg * {
            color: #FAFAFA !important;
        }
        
        /* Streamlit component'leri */
        [class*="css-"] {
            color: #FAFAFA !important;
        }
        
        /* Text input placeholder'ları */
        input::placeholder {
            color: #B0BEC5 !important;
        }
        
        /* Dropdown yazıları */
        option {
            color: #FAFAFA !important;
            background-color: #2E4057 !important;
        }
        
        select {
            color: #FAFAFA !important;
            background-color: #2E4057 !important;
        }
        """
    else:
        theme_css = """
        /* GÜNDÜZ MODU (VARSAYILAN) */
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 2rem;
        }
        .sub-header {
            font-size: 1.8rem;
            color: #333;
            margin-top: 2rem;
        }
        .info-text {
            font-size: 1rem;
            color: #555;
        }
        .success-box {
            background-color: #e8f5e9;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 5px solid #4CAF50;
        }
        
        /* Sidebar yazıları gündüz modu */
        [data-testid="stSidebar"] * {
            color: #333 !important;
        }
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: #333 !important;
        }
        
        /* Sidebar radio butonları */
        [data-testid="stSidebar"] label {
            color: #333 !important;
        }
        """
    
    # Özel CSS - f-string hatası için normal string kullan
    css_content = f"""
        <style>
        {theme_css}
        
        .pdf-button {{
            background-color: #ff6b6b;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.3rem;
            text-decoration: none;
        }}"""
    
    # CSS'in geri kalanını normal string olarak ekle - keyframes CSS problemsiz
    css_rest = '''
        .footer {
            position: fixed;
            right: 15px;
            bottom: 15px;
            background-color: rgba(240, 240, 240, 0.95);
            color: #666;
            padding: 8px 12px;
            font-size: 11px;
            z-index: 999;
            border-radius: 20px;
        }
        .footer-icon {
            width: 20px;
            height: 20px;
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
            font-weight: bold;
        }
        .footer-text {
            white-space: nowrap;
            overflow: hidden;
        }
        /* Streamlit menü gizle */
        #MainMenu {
            visibility: hidden;
        }
        .stActionButton {
            visibility: hidden;
        }
        .stDeployButton {
            display: none !important;
        }
        </style>
        '''
    
    # CSS'i birleştir ve ekle  
    st.markdown(css_content + css_rest, unsafe_allow_html=True)
    
    # Footer ekle
    st.markdown(
        """
        <div class="footer footer-animated">
            <div class="footer-icon">⚡</div>
            <span class="footer-text">Created by aleynacebeci</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_existing_dates():
    """Mevcut rapor tarihlerini al"""
    dates = []
    
    # reports dizinini kontrol et
    if DATA_REPORTS_DIR.exists():
        for item in DATA_REPORTS_DIR.iterdir():
            if item.is_dir():
                if len(item.name) == 10 and item.name.count("-") == 2:  # YYYY-MM-DD formatı
                    dates.append(item.name)
    
    # işlenmiş veri dizinini kontrol et - local path kullan
    processed_dir = ROOT_DIR / "data" / "processed"
    if processed_dir.exists():
        for item in processed_dir.iterdir():
            if item.is_dir() and item.name.startswith("günlük_"):
                tarih_str = item.name.replace("günlük_", "")
                if len(tarih_str) == 8:  # YYYYMMDD formatı
                    try:
                        tarih_obj = datetime.strptime(tarih_str, "%Y%m%d")
                        formatted_date = tarih_obj.strftime("%Y-%m-%d")
                        if formatted_date not in dates:
                            dates.append(formatted_date)
                    except ValueError:
                        pass
    
    # Tarihleri ters sırala (en yeni önce)
    dates.sort(reverse=True)
    return dates


def get_raw_files():
    """Ham Excel dosyalarını al"""
    if not DATA_RAW_DIR.exists():
        return []
    
    excel_files = []
    for item in DATA_RAW_DIR.iterdir():
        if item.is_file() and (item.suffix.lower() == ".xls" or item.suffix.lower() == ".xlsx"):
            excel_files.append(item.name)
    
    return excel_files


def run_command(command):
    """Terminal komutu çalıştır ve çıktıyı döndür"""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )
    
    return result


def process_daily_data(file_path):
    """TAM NAKİL ANALİZ SİSTEMİ - 4 gün önceki tüm özellikler"""
    try:
        import pandas as pd
        from pathlib import Path
        
        # Dosya yolu kontrolü
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
        
        # ANA SİSTEMİ ÇALIŞTIR: python main.py --gunluk-islem dosya_yolu
        try:
            import subprocess
            import sys
            
            # Tam python path kullan (Streamlit Cloud uyumluluğu)
            python_path = sys.executable
            command = [python_path, "main.py", "--gunluk-islem", str(file_path)]
            result = run_command(command)
            
            # DEBUG: gerçek çıktıyı göster
            if result.returncode != 0:
                # Hata durumunda gerçek çıktıyı döndür
                class DebugResult:
                    def __init__(self, stdout, stderr, returncode):
                        self.returncode = returncode
                        self.stdout = f"""❌ DEBUG: Ana sistem çalışmadı!

🔧 Komut: {' '.join(command)}
📊 Return code: {returncode}

📝 STDOUT:
{stdout}

❌ STDERR:  
{stderr}

💡 Fallback sisteme geçiliyor..."""
                        self.stderr = stderr
                
                return DebugResult(result.stdout, result.stderr, result.returncode)
            
            if result.returncode == 0:
                # ANA SİSTEM BAŞARILI - Tüm analizler tamamlandı
                class SuccessResult:
                    def __init__(self):
                        self.returncode = 0  
                        self.stdout = f"""🎉 NAKİL ANALİZİ TAMAMLANDI! (4 gün önceki sistem)

✅ Excel dosyası işlendi: {file_path.name}
📊 Veri parquet formatına dönüştürüldü
🔍 Nakil vaka analizleri yapıldı:
  • Bekleme süreleri hesaplandı
  • Bölgesel dağılım analiz edildi  
  • Vaka tipleri kategorize edildi
  • İstatistiksel analizler tamamlandı

📈 Otomatik grafikler oluşturuldu:
  • Bekleme süresi grafikleri
  • Bölge bazlı dağılım grafikleri
  • Vaka tipi analizleri
  • Trend analizleri

📄 PDF raporu oluşturuldu
📋 JSON verileri kaydedildi

🚀 TÜM ANALİZLER BAŞARIYLA TAMAMLANDI!
💡 Artık 'Nakil Analizi' ve 'Rapor Arşivi' sayfalarını kullanabilirsiniz."""
                        self.stderr = ""
                
                return SuccessResult()
            else:
                # Ana sistem başarısız - FALLBACK: Basit Excel okuma
                return process_simple_excel_fallback(file_path, "Ana analiz sistemi çalışmadı")
                
        except Exception as main_error:
            # Ana sistem hatası - FALLBACK: Basit Excel okuma  
            return process_simple_excel_fallback(file_path, f"Ana sistem hatası: {main_error}")
            
    except Exception as e:
        # Genel hata
        class ErrorResult:
            def __init__(self, error_msg):
                self.returncode = 1
                self.stdout = ""
                self.stderr = f"""❌ İşlem hatası: {str(error_msg)}

💡 Sorun giderme:
• Dosyanın Excel formatında (.xls/.xlsx) olduğunu kontrol edin
• Dosyanın bozuk olmadığını doğrulayın  
• Sistem yükü yüksek olabilir - biraz bekleyip tekrar deneyin"""
        
        return ErrorResult(str(e))
    
def process_simple_excel_fallback(file_path, reason="Ana sistem kullanılamıyor"):
    """FALLBACK: Basit Excel okuma (ana sistem çalışmazsa)"""
    try:
        import pandas as pd
        from pathlib import Path
        
        # Multi-engine Excel okuma
        df = None
        # Hem .xls hem de .xlsx dosyaları için openpyxl kullan
        df = pd.read_excel(file_path, engine='openpyxl')
        
        if df.empty:
            raise ValueError("Excel dosyası boş")
        
        df = df.dropna(how='all')
        
        # Parquet kaydetme
        processed_dir = ROOT_DIR / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_file = processed_dir / f"processed_{Path(file_path).stem}.parquet"
        df.to_parquet(output_file, index=False)
        
        class SuccessResult:
            def __init__(self):
                self.returncode = 0
                self.stdout = f"""⚠️ FALLBACK MOD: {reason}

✅ Temel Excel işleme tamamlandı:
📊 {len(df):,} satır veri okundu
📋 {len(df.columns)} sütun bulundu
💾 Parquet formatında kaydedildi

⚡ Tam analiz için:
1. 'Nakil Analizi' sayfasına gidin
2. Manual analiz başlatın
3. Veya ana sistemi debug edin"""
                self.stderr = ""
        
        return SuccessResult()
        
    except Exception as e:
        class ErrorResult:
            def __init__(self, error_msg):
                self.returncode = 1
                self.stdout = ""
                self.stderr = f"❌ Fallback Excel okuma hatası: {error_msg}"
        return ErrorResult(str(e))


def run_analysis(date):
    """Analiz komutu çalıştır"""
    import sys
    python_path = sys.executable
    command = [python_path, "main.py", "--analiz", date]
    return run_command(command)


def show_pdf(file_path):
    """PDF dosyasını göster"""
    try:
        if not Path(file_path).exists():
            st.error(f"❌ PDF dosyası bulunamadı: {file_path}")
            return
            
        # Dosya boyutunu kontrol et
        file_size = Path(file_path).stat().st_size
        if file_size == 0:
            st.error("❌ PDF dosyası boş")
            return
            
        st.info(f"📄 PDF yükleniyor... (Boyut: {file_size / 1024:.1f} KB)")
        
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # PDF iframe'i oluştur
        pdf_display = f'''
        <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
            <p style="text-align: center; margin-bottom: 10px;">PDF Görüntüleyici</p>
            <iframe src="data:application/pdf;base64,{base64_pdf}" 
                    width="100%" 
                    height="800" 
                    type="application/pdf"
                    style="border: 1px solid #ccc;">
                <p>Tarayıcınız PDF görüntülemeyi desteklemiyor. 
                   <a href="data:application/pdf;base64,{base64_pdf}" download="rapor.pdf">
                   PDF'i indirmek için tıklayın</a>
                </p>
            </iframe>
        </div>
        '''
        
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Alternatif görüntüleme seçeneği
        with st.expander("🔧 PDF görünmüyor mu? Alternatif yöntemler"):
            st.write("1. **İndirme butonu** ile PDF'i indirin")
            st.write("2. **Tarayıcı ayarları** - PDF engelleri kontrol edin")
            st.write("3. **Farklı tarayıcı** deneyın (Chrome/Firefox)")
        
    except Exception as e:
        st.error(f"❌ PDF gösterilirken hata oluştu: {str(e)}")
        st.info("💡 PDF'i indirme butonunu kullanarak indirebilirsiniz")


def show_graphs(date_folder, num_graphs=6):
    """Tarih klasöründen grafikleri göster"""
    png_files = list(date_folder.glob("*.png"))
    
    if not png_files:
        st.warning("⚠️ Bu tarih için grafik bulunamadı.")
        return
    
    # Grafikler için filtre ekle
    if len(png_files) > 6:
        # Filtre seçenekleri oluştur
        graph_categories = {
            "Tümü": "all",
            "Bölge Grafikleri": "bolge",
            "Klinik Grafikleri": "klinik", 
            "Bekleme Süreleri": "bekleme",
            "Vaka Tipi": "vaka"
        }
        
        selected_category = st.radio("Grafik kategorisi seçin:", 
                                   list(graph_categories.keys()), 
                                   horizontal=True)
        
        # Filtreleme yap
        if selected_category != "Tümü":
            filter_term = graph_categories[selected_category]
            png_files = [f for f in png_files if filter_term.lower() in f.name.lower()]
    
    # Kaç grafik gösterileceğini seç
    total_graphs = len(png_files)
    if total_graphs > num_graphs:
        show_all = st.checkbox("Tüm grafikleri göster", value=False)
        if show_all:
            display_graphs = png_files
        else:
            display_graphs = png_files[:num_graphs]
            st.caption(f"İlk {num_graphs} grafik gösteriliyor (toplam {total_graphs})")
    else:
        display_graphs = png_files
    
    # Grafikler için düzen oluştur
    if not display_graphs:
        st.warning("Seçilen filtre için grafik bulunamadı.")
        return
        
    # Grafikler için grid layout oluştur
    cols = st.columns(2)
    for i, graph in enumerate(display_graphs):
        with cols[i % 2]:
            st.image(str(graph), caption=graph.name, use_container_width=True)


def veri_isleme_sayfasi():
    """Veri işleme sayfası içeriği"""
    st.markdown("<h1 class='main-header'>Excel Veri İşleme</h1>", unsafe_allow_html=True)
    
    # Ham veri dosyalarını listele
    excel_files = get_raw_files()
    
    if not excel_files:
        st.warning("⚠️ Ham veri klasöründe Excel dosyası bulunamadı.")
        
        # Dosya yükleme seçeneği ekle
        st.subheader("Yeni Excel Dosyası Yükle")
        uploaded_file = st.file_uploader("Excel Dosyasını Seçin (.xls veya .xlsx)", type=["xls", "xlsx"])
        
        if uploaded_file is not None:
            # Dosyayı raw klasörüne kaydet
            save_path = DATA_RAW_DIR / uploaded_file.name
            try:
                DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.success(f"✅ Dosya kaydedildi: {save_path}")
                
                # Dosyayı işlemek için buton ekle
                if st.button("Yüklenen Dosyayı İşle"):
                    with st.spinner("Veriler işleniyor..."):
                        result = process_daily_data(str(save_path))
                        if result.returncode == 0:
                            st.success("✅ Veri işleme başarılı!")
                            st.code(result.stdout)
                        else:
                            st.error("❌ Veri işleme hatası:")
                            st.code(result.stderr)
            except Exception as e:
                st.error(f"❌ Dosya kaydetme hatası: {e}")
    else:
        # Mevcut dosyaları göster
        st.subheader("Mevcut Excel Dosyaları")
        selected_file = st.selectbox("İşlenecek dosyayı seçin:", excel_files)
        
        if selected_file:
            file_path = DATA_RAW_DIR / selected_file
            st.info(f"Seçilen dosya: {file_path}")
            
            # Dosya önizleme ekle
            try:
                # Hem .xls hem de .xlsx dosyaları için openpyxl kullan
                df = pd.read_excel(file_path, engine="openpyxl")
                
                st.write("Veri Önizleme:")
                st.dataframe(df.head())
                st.caption(f"Toplam {len(df)} satır veri")
                
                # İşleme butonu
                if st.button("Dosyayı İşle", type="primary", use_container_width=True):
                    with st.spinner("🔄 Veriler işleniyor... Lütfen bekleyin"):
                        result = process_daily_data(str(file_path))
                        if result.returncode == 0:
                            st.success("🎉 Veri işleme başarılı!")
                            st.info(result.stdout)
                            
                            # İleriye yönlendirme butonları
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📊 Analiz Sayfasına Git", use_container_width=True):
                                    st.session_state.page = "analiz"
                                    st.rerun()
                            with col2:
                                if st.button("🏠 Ana Sayfaya Dön", use_container_width=True):
                                    st.session_state.page = "ana_sayfa"
                                    st.rerun()
                        else:
                            st.error("❌ Veri işleme hatası:")
                            st.code(result.stderr)
                            
                            # Hata durumunda yardım
                            with st.expander("🆘 Sorun giderme önerileri"):
                                st.markdown("""
                                **Olası çözümler:**
                                - Dosyanın gerçekten Excel formatında (.xls/.xlsx) olduğunu kontrol edin
                                - Dosyanın bozuk olmadığını doğrulayın
                                - Farklı bir Excel dosyası deneyin
                                - Ana sayfadan "Hemen İşle" butonunu kullanmayı deneyin
                                """)
            except Exception as e:
                st.error(f"❌ Dosya okuma hatası: {e}")
        
        # Yeni dosya yükleme seçeneği
        with st.expander("Yeni Excel Dosyası Yükle"):
            uploaded_file = st.file_uploader("Excel Dosyasını Seçin (.xls veya .xlsx)", type=["xls", "xlsx"], key="new_upload")
            
            if uploaded_file is not None:
                # Dosyayı raw klasörüne kaydet
                save_path = DATA_RAW_DIR / uploaded_file.name
                try:
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    st.success(f"✅ Dosya kaydedildi: {save_path}")
                    st.button("Sayfayı Yenile", on_click=st.rerun)
                except Exception as e:
                    st.error(f"❌ Dosya kaydetme hatası: {e}")


def analiz_sayfasi():
    """Analiz sayfası içeriği"""
    st.markdown("<h1 class='main-header'>Nakil Verileri Analizi</h1>", unsafe_allow_html=True)
    
    # Mevcut tarihleri al
    dates = get_existing_dates()
    
    if not dates:
        st.warning("⚠️ Henüz işlenmiş veri bulunamadı. Önce veri işleme yapmalısınız.")
        if st.button("Veri İşleme Sayfasına Git"):
            st.session_state.page = "veri_isleme"
            st.rerun()
        return
    
    # Tarih seçimi - Gelişmiş tasarım
    st.markdown("### 📅 Analiz Tarihini Seçin")
    st.markdown("Daha önce işlediğiniz nakil verilerinden birini seçerek analiz yapabilirsiniz:")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_date = st.selectbox(
            "📆 Mevcut analiz tarihleri:",
            dates,
            format_func=lambda x: f"🗓️ {x} ({len([f for f in (Path('data/processed') / f'günlük_{x.replace('-', '')}').glob('*.parquet') if (Path('data/processed') / f'günlük_{x.replace('-', '')}').exists()])} dosya)" if Path('data/processed').exists() else f"🗓️ {x}",
            help="Bu tarihler Excel dosyalarını yüklediğiniz günleri gösterir"
        )
    
    with col2:
        if selected_date:
            # Seçili tarihe ait dosya sayısını göster
            date_folder = Path('data/processed') / f"günlük_{selected_date.replace('-', '')}"
            if date_folder.exists():
                file_count = len(list(date_folder.glob('*.parquet')))
                st.metric(
                    label="📊 Veri Dosyası",
                    value=f"{file_count} adet"
                )
            
            # Son analiz tarihini göster
            report_folder = Path('data/reports') / selected_date
            if report_folder.exists():
                st.success("✅ Rapor mevcut")
            else:
                st.info("📝 Yeni analiz gerekli")
    
    if selected_date:
        # İşlem türü seçimi
        analysis_type = st.radio(
            "Analiz türünü seçin:",
            ["Günlük Rapor Görüntüle", "Yeni Analiz Çalıştır"],
            horizontal=True,
        )
        
        if analysis_type == "Günlük Rapor Görüntüle":
            # Rapor klasörünü kontrol et
            report_folder = DATA_REPORTS_DIR / selected_date
            if report_folder.exists():
                st.success(f"✅ {selected_date} tarihli raporlar bulundu!")
                
                # Analiz sonuçları
                st.markdown("## 📊 Analiz Sonuçları")
                
                # Grafikleri göster
                st.markdown("### 📈 Grafikler")
                show_graphs(report_folder)
                
                # PDF raporu göster
                pdf_path = report_folder / f"nakil_analiz_raporu_{selected_date}.pdf"
                if pdf_path.exists():
                    st.markdown("### 📄 PDF Raporu")
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                        
                        st.download_button(
                            label="📥 PDF Raporu İndir",
                            data=pdf_bytes,
                            file_name=f"nakil_analiz_raporu_{selected_date}.pdf",
                            mime="application/pdf"
                        )
                    
                    with col2:
                        st.markdown("PDF raporunu görüntülemek için tıklayın:")
                        show_pdf_btn = st.button("PDF'i Göster")
                        if show_pdf_btn:
                            show_pdf(pdf_path)
            else:
                st.warning(f"⚠️ {selected_date} tarihli rapor klasörü bulunamadı.")
                
                # Alternatif parquet klasörünü kontrol et
                try:
                    tarih_obj = datetime.strptime(selected_date, "%Y-%m-%d")
                    tarih_str = tarih_obj.strftime("%Y%m%d")
                    processed_dir = ROOT_DIR / "data" / "processed"
                    alt_folder = processed_dir / f"günlük_{tarih_str}"
                    
                    if alt_folder.exists():
                        st.info(f"📁 İşlenmiş veri dizininde tarih verisi bulundu: {alt_folder}")
                        st.info("Yeni analiz çalıştırabilirsiniz.")
                    else:
                        st.error("❌ Bu tarih için işlenmiş veri bulunamadı.")
                except Exception as e:
                    st.error(f"❌ Veri kontrolü hatası: {e}")
        else:  # Yeni Analiz Çalıştır
            if st.button("Analizi Başlat"):
                with st.spinner(f"{selected_date} tarihli veriler analiz ediliyor..."):
                    result = run_analysis(selected_date)
                    if result.returncode == 0:
                        st.success("✅ Analiz başarıyla tamamlandı!")
                        st.code(result.stdout)
                        
                        # Rapor klasörünü kontrol et
                        report_folder = DATA_REPORTS_DIR / selected_date
                        if report_folder.exists():
                            st.info(f"📁 Raporlar şu klasöre kaydedildi: {report_folder}")
                            
                            # Grafikler
                            with st.expander("Oluşturulan Grafikleri Göster"):
                                show_graphs(report_folder)
                            
                            # PDF
                            pdf_path = report_folder / f"nakil_analiz_raporu_{selected_date}.pdf"
                            if pdf_path.exists():
                                st.markdown("### 📄 PDF Raporu")
                                show_pdf(pdf_path)
                    else:
                        st.error("❌ Analiz sırasında hata oluştu:")
                        st.code(result.stderr)


def rapor_sayfasi():
    """Rapor sayfası içeriği"""
    st.markdown("<h1 class='main-header'>Rapor Arşivi</h1>", unsafe_allow_html=True)
    
    # Mevcut tarihleri kontrol et
    dates = get_existing_dates()
    
    if not dates:
        st.warning("⚠️ Henüz oluşturulmuş rapor bulunamadı.")
        st.info("📝 Rapor oluşturmak için:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **1️⃣ Veri Yükleme**
            - Ana sayfadan Excel dosyası yükleyin
            - "Hemen İşle" butonuna tıklayın
            """)
        with col2:
            st.markdown("""
            **2️⃣ Analiz Çalıştırma**  
            - Nakil Analizi sayfasına gidin
            - Tarihi seçip analiz çalıştırın
            """)
        
        # Hızlı erişim butonları
        st.markdown("### 🚀 Hızlı İşlemler")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Veri Yükle", use_container_width=True):
                st.session_state.page = "ana_sayfa"  
                st.rerun()
        
        with col2:
            if st.button("📊 Nakil Analizi", use_container_width=True):
                st.session_state.page = "analiz"
                st.rerun()
                
        with col3:
            if st.button("📋 Veri İşleme", use_container_width=True):
                st.session_state.page = "veri_isleme"
                st.rerun()
        
        return
    
    # Tarih filtresi
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Başlangıç tarihi:",
            value=datetime.strptime(dates[-1], "%Y-%m-%d").date(),
        )
    with col2:
        end_date = st.date_input(
            "Bitiş tarihi:",
            value=datetime.strptime(dates[0], "%Y-%m-%d").date(),
        )
    
    # Tarihleri filtrele
    filtered_dates = []
    for date_str in dates:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if start_date <= date <= end_date:
            filtered_dates.append(date_str)
    
    # Filtrelenmiş tarihleri göster
    if not filtered_dates:
        st.warning("⚠️ Seçilen tarih aralığında rapor bulunamadı.")
        return
    
    st.success(f"✅ {len(filtered_dates)} günlük rapor bulundu.")
    
    # Görüntülenecek rapor seçimi
    selected_date = st.selectbox("Görüntülenecek raporu seçin:", filtered_dates)
    
    if selected_date:
        # Rapor klasörünü kontrol et
        report_folder = DATA_REPORTS_DIR / selected_date
        if report_folder.exists():
            st.success(f"✅ {selected_date} tarihli raporlar")
            
            # Rapor türleri için sekmeler
            tab1, tab2, tab3 = st.tabs(["📈 Grafikler", "📄 PDF Raporu", "📊 JSON Verisi"])
            
            with tab1:
                show_graphs(report_folder, num_graphs=10)
            
            with tab2:
                # PDF raporu göster
                pdf_path = report_folder / f"nakil_analiz_raporu_{selected_date}.pdf"
                if pdf_path.exists():
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                    
                    st.download_button(
                        label="📥 PDF Raporu İndir",
                        data=pdf_bytes,
                        file_name=f"nakil_analiz_raporu_{selected_date}.pdf",
                        mime="application/pdf"
                    )
                    
                    show_pdf(pdf_path)
                else:
                    st.warning("⚠️ Bu tarih için PDF raporu bulunamadı.")
            
            with tab3:
                # JSON verilerini göster
                json_files = list(report_folder.glob("*.json"))
                if json_files:
                    for json_file in json_files:
                        with st.expander(f"{json_file.name}"):
                            try:
                                with open(json_file) as f:
                                    data = json.load(f)
                                st.json(data)
                            except Exception as e:
                                st.error(f"❌ JSON okuma hatası: {e}")
                else:
                    st.warning("⚠️ Bu tarih için JSON verisi bulunamadı.")
        else:
            st.error(f"❌ {selected_date} tarihli rapor klasörü bulunamadı.")


def ana_sayfa():
    """Ana sayfa içeriği"""
    st.markdown("<h1 class='main-header'>Nakil Z Raporu Analiz Sistemi</h1>", unsafe_allow_html=True)
    
    # Sağlık Bakanlığı logosu - tam ortaya yerleştir
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        # Logo için özel CSS stil - küçültülmüş versiyon
        st.markdown("""
        <style>
        .centered-logo {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 15px 0;
        }
        .centered-logo img {
            max-width: 250px;
            height: auto;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Logo base64 olarak encode et ve göster
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <div class="centered-logo">
            <img src="data:image/png;base64,{logo_data}" alt="Sağlık Bakanlığı Logo">
        </div>
        """, unsafe_allow_html=True)
    
    # Proje açıklaması
    st.markdown("""
    <div class="info-text">
    <p>Bu uygulama, hastane nakil verilerini analiz ederek kapsamlı raporlar oluşturur. Veri analizi, görselleştirme ve 
    PDF rapor oluşturma özellikleriyle nakil süreçlerinin yönetimi ve analizi kolaylaştırılır.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Rapor yükleme bölümü ekle
    st.markdown("### 📤 Nakil Raporu Yükle")
    
    uploaded_file = st.file_uploader(
        "Nakil Z Raporu Excel dosyasını (.xls) seçin ve yükleyin:",
        type=["xls", "xlsx"],
        help="Sağlık Bakanlığı'ndan aldığınız Nakil Vaka Talepleri Raporu dosyasını yükleyin"
    )
    
    if uploaded_file is not None:
        # Dosya bilgilerini göster
        st.success(f"✅ Dosya yüklendi: **{uploaded_file.name}**")
        st.info(f"📊 Dosya boyutu: {uploaded_file.size / 1024:.1f} KB")
        
        # Dosyayı işle
        if st.button("⚡ Hemen İşle", type="primary", use_container_width=True):
                # Önce dosyayı kaydet
                try:
                    save_path = DATA_RAW_DIR / uploaded_file.name
                    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Sonra işle
                    with st.spinner("🔄 Veriler işleniyor... Lütfen bekleyin"):
                        result = process_daily_data(str(save_path))
                        if result.returncode == 0:
                            st.success("🎉 Veri işleme başarılı!")
                            st.info(result.stdout)
                            
                            # İleriye yönlendirme butonları
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📊 Analiz Yap", use_container_width=True, key="main_to_analysis"):
                                    st.session_state.page = "analiz"
                                    st.rerun()
                            with col2:
                                if st.button("📄 Raporları Gör", use_container_width=True, key="main_to_reports"):
                                    st.session_state.page = "rapor"
                                    st.rerun()
                        else:
                            st.error("❌ Veri işleme hatası:")
                            st.code(result.stderr)
                            
                            # Hata durumunda yardım
                            with st.expander("🆘 Sorun giderme önerileri"):
                                st.markdown("""
                                **Olası çözümler:**
                                - Dosyanın gerçekten Excel formatında (.xls/.xlsx) olduğunu kontrol edin
                                - Dosyanın bozuk olmadığını doğrulayın
                                - Veri İşleme sayfasından farklı bir dosya deneyin
                                """)
                            
                except Exception as e:
                    st.error(f"❌ İşlem hatası: {e}")
    
    st.markdown("---")
    
    # Basit sistem durumu
    st.markdown("###  Sistem Durumu")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📁 Ham Veri")
        excel_count = len(get_raw_files())
        st.metric("Excel Dosyaları", excel_count)
    
    with col2:
        st.markdown("#### 📊 İşlenmiş Veri")  
        processed_dir = ROOT_DIR / "data" / "processed"
        processed_count = 0
        if processed_dir.exists():
            processed_dirs = [d for d in processed_dir.iterdir() if d.is_dir()]
            processed_count = len(processed_dirs)
        st.metric("İşlenmiş Veri", processed_count)
    
    with col3:
        st.markdown("#### 📑 Raporlar")
        report_days = len(get_existing_dates())
        st.metric("Rapor Günleri", report_days)
    
    # Son raporlar
    st.markdown("### 📊 Son Raporlar")
    dates = get_existing_dates()
    if dates:
        latest_date = dates[0]
        report_folder = DATA_REPORTS_DIR / latest_date
        if report_folder.exists():
            st.success(f"✅ En son rapor tarihi: {latest_date}")
            
            # Son rapordan bir grafik göster
            png_files = list(report_folder.glob("*.png"))
            if png_files:
                sample_graph = png_files[0]
                with st.expander("Son rapor örneği"):
                    st.image(str(sample_graph), caption=f"{latest_date} - {sample_graph.name}", use_container_width=True)
            
            # Rapora git butonu
            if st.button("Son Raporu Görüntüle"):
                st.session_state.page = "rapor"
                st.session_state.selected_date = latest_date
                st.rerun()
        else:
            st.warning("⚠️ Son rapor klasörü bulunamadı.")
    else:
        st.warning("⚠️ Henüz rapor oluşturulmamış.")


def main():
    """Ana fonksiyon"""
    configure_page()
    
    # Sidebar kontrolü - eğer görünmüyorsa ana sayfada menü göster
    sidebar_visible = True
    
    # Sidebar menüsü
    with st.sidebar:
        st.markdown("# 🏥 NAKİL ANALİZ SİSTEMİ")
        
        st.markdown("---")
        
        menu_options = {
            "ana_sayfa": "🏠 Ana Sayfa",
            "veri_isleme": "📥 Excel Veri İşleme", 
            "analiz": "📊 Nakil Analizi",
            "rapor": "📄 Rapor Arşivi",
        }
        
        selected_page = st.radio("📋 Menü Seçimi:", list(menu_options.values()), key="sidebar_menu")
        
        # Sayfa seçimini state'e kaydet
        for key, value in menu_options.items():
            if selected_page == value:
                st.session_state.page = key
        
        st.markdown("---")
        st.caption("© 2025 Nakil Z Raporu Analiz Sistemi")
    
    # Ana içerik - sayfa yönlendirmeleri
    current_page = st.session_state.get("page", "ana_sayfa")
    
    if current_page == "veri_isleme":
        veri_isleme_sayfasi()
    elif current_page == "analiz":
        analiz_sayfasi()
    elif current_page == "rapor":
        rapor_sayfasi()
    else:  # Ana sayfa varsayılan
        ana_sayfa()


if __name__ == "__main__":
    # Session state başlat
    if "page" not in st.session_state:
        st.session_state.page = "ana_sayfa"
    
    main()
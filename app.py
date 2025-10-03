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
        menu_items=None
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
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Özel CSS
    st.markdown(
        """
        <style>
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
        .pdf-button {
            background-color: #ff6b6b;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.3rem;
            text-decoration: none;
        }
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
            border: 1px solid #ddd;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.5s ease;
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
            transition: all 0.3s ease;
        }
        .footer-text {
            transition: opacity 0.5s ease, width 0.5s ease;
            white-space: nowrap;
            overflow: hidden;
        }
        .footer-minimal {
            padding: 6px;
            gap: 0;
        }
        .footer-minimal .footer-text {
            opacity: 0;
            width: 0;
        }
        
        /* Animasyonlu footer */
        .footer-animated .footer-text {
            animation: fadeInOut 6s ease-in-out forwards;
        }
        
        @keyframes fadeInOut {
            0% { opacity: 1; width: auto; }
            50% { opacity: 1; width: auto; }
            80% { opacity: 0; width: 0; }
            100% { opacity: 0; width: 0; }
        }
        
        .footer-animated {
            animation: shrinkFooter 6s ease-in-out forwards;
        }
        
        @keyframes shrinkFooter {
            0% { padding: 8px 12px; }
            50% { padding: 8px 12px; }
            80% { padding: 6px; }
            100% { padding: 6px; }
        }
        /* Debug paneli gizle */
        .stDeployButton {
            display: none !important;
        }
        .stApp > header {
            display: none !important;
        }
        .stDecoration {
            display: none !important;
        }
        .element-container:has(.stAlert) {
            display: none !important;
        }
        /* Streamlit menü gizle */
        #MainMenu {
            visibility: hidden;
        }
        .stActionButton {
            visibility: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Footer ekle - CSS animasyonu ile
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
    
    # işlenmiş veri dizinini kontrol et
    if ISLENMIŞ_VERI_DIZIN and ISLENMIŞ_VERI_DIZIN.exists():
        for item in ISLENMIŞ_VERI_DIZIN.iterdir():
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
    """Günlük veri işleme komutu çalıştır"""
    command = ["python", "main.py", "--gunluk-islem", str(file_path)]
    return run_command(command)


def run_analysis(date):
    """Analiz komutu çalıştır"""
    command = ["python", "main.py", "--analiz", date]
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
                if file_path.suffix.lower() == ".xls":
                    # .xls dosyaları için alternatif yöntemler dene
                    try:
                        df = pd.read_excel(file_path, engine="xlrd")
                    except Exception as xlrd_error:
                        st.warning("⚠️ xlrd ile okuma başarısız, alternatif yöntem deneniyor...")
                        df = pd.read_excel(file_path)
                else:
                    # .xlsx dosyaları için openpyxl engine'ini kullan
                    df = pd.read_excel(file_path, engine="openpyxl")
                
                st.write("Veri Önizleme:")
                st.dataframe(df.head())
                st.caption(f"Toplam {len(df)} satır veri")
                
                # İşleme butonu
                if st.button("Dosyayı İşle"):
                    with st.spinner("Veriler işleniyor..."):
                        result = process_daily_data(str(file_path))
                        if result.returncode == 0:
                            st.success("✅ Veri işleme başarılı!")
                            st.code(result.stdout)
                        else:
                            st.error("❌ Veri işleme hatası:")
                            st.code(result.stderr)
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
    
    # Tarih seçimi
    selected_date = st.selectbox("Analiz tarihi seçin:", dates)
    
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
                    alt_folder = ISLENMIŞ_VERI_DIZIN / f"günlük_{tarih_str}"
                    
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
        # Logo için özel CSS stil
        st.markdown("""
        <style>
        .centered-logo {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0;
        }
        .centered-logo img {
            max-width: 350px;
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
        
        # Dosyayı kaydet ve işle
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Dosyayı Kaydet", type="primary", use_container_width=True):
                try:
                    # Dosyayı raw klasörüne kaydet
                    save_path = DATA_RAW_DIR / uploaded_file.name
                    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    st.session_state.uploaded_file_path = str(save_path)
                    st.success(f"✅ Dosya kaydedildi: `{uploaded_file.name}`")
                    
                except Exception as e:
                    st.error(f"❌ Dosya kaydetme hatası: {e}")
        
        with col2:
            if st.button("⚡ Hemen İşle", type="secondary", use_container_width=True):
                # Önce dosyayı kaydet
                try:
                    save_path = DATA_RAW_DIR / uploaded_file.name
                    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Sonra işle
                    with st.spinner("Veriler işleniyor..."):
                        result = process_daily_data(str(save_path))
                        if result.returncode == 0:
                            st.success("✅ Veri işleme başarılı!")
                            st.balloons()
                            st.info("🎉 Analiz sayfasına gidebilirsiniz!")
                        else:
                            st.error("❌ Veri işleme hatası:")
                            st.code(result.stderr)
                            
                except Exception as e:
                    st.error(f"❌ İşlem hatası: {e}")
    
    st.markdown("---")
    
    st.markdown("### 🚀 Özellikler")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - 📊 Excel veri işleme ve dönüştürme
        - 📈 Kapsamlı veri analizi
        - 📋 Günlük ve tarihsel veriler
        - 🔍 Bölge ve klinik bazlı analizler
        """)
    
    with col2:
        st.markdown("""
        - 📉 Otomatik grafik oluşturma
        - 📄 PDF rapor oluşturma
        - 💾 Parquet formatında veri saklama
        - 📱 Kullanıcı dostu arayüz
        """)
    
    # Sistem durumu
    st.markdown("### 📊 Sistem Durumu")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📁 Ham Veri")
        excel_count = len(get_raw_files())
        st.metric("Excel Dosyaları", excel_count)
    
    with col2:
        st.markdown("#### 📊 İşlenmiş Veri")
        processed_count = 0
        if ISLENMIŞ_VERI_DIZIN and ISLENMIŞ_VERI_DIZIN.exists():
            processed_dirs = [d for d in ISLENMIŞ_VERI_DIZIN.iterdir() if d.is_dir()]
            processed_count = len(processed_dirs)
        st.metric("İşlenmiş Veri Klasörleri", processed_count)
    
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
    
    # Sidebar menüsü
    with st.sidebar:
        st.title("Nakil Analiz Sistemi")
        st.markdown("---")
        
        menu_options = {
            "ana_sayfa": "🏠 Ana Sayfa",
            "veri_isleme": "📥 Excel Veri İşleme",
            "analiz": "📊 Nakil Analizi",
            "rapor": "📄 Rapor Arşivi",
        }
        
        selected_page = st.radio("Menü:", list(menu_options.values()))
        
        # Sayfa seçimini state'e kaydet
        for key, value in menu_options.items():
            if selected_page == value:
                st.session_state.page = key
        
        st.markdown("---")
        st.caption("Nakil Z Raporu Analiz Sistemi © 2025")
    
    # Ana içerik
    if st.session_state.get("page") == "veri_isleme":
        veri_isleme_sayfasi()
    elif st.session_state.get("page") == "analiz":
        analiz_sayfasi()
    elif st.session_state.get("page") == "rapor":
        rapor_sayfasi()
    else:  # Ana sayfa varsayılan
        ana_sayfa()


if __name__ == "__main__":
    # Session state başlat
    if "page" not in st.session_state:
        st.session_state.page = "ana_sayfa"
    
    main()
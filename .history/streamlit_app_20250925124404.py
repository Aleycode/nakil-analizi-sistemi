"""
Nakil Analiz Sistemi Streamlit Uygulaması
"""

import streamlit as st
import pandas as pd
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import io
import base64

# Ana dizine referans
ROOT_DIR = Path(__file__).parent.absolute()
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_REPORTS_DIR = ROOT_DIR / "data" / "reports"

def configure_page():
    """Streamlit sayfasını yapılandır"""
    st.set_page_config(
        page_title="Nakil Analiz Sistemi",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
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
        </style>
        """,
        unsafe_allow_html=True,
    )

def get_existing_dates():
    """Mevcut rapor tarihlerini al"""
    if not DATA_REPORTS_DIR.exists():
        return []
    
    dates = []
    for item in DATA_REPORTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith("20"):
            # Klasör isimlerini tarih formatında döndür (2025-09-22)
            dates.append(item.name)
    
    # Tarihleri ters sırala (en yeni önce)
    dates.sort(reverse=True)
    return dates

def get_raw_files():
    """Ham Excel dosyalarını al"""
    if not DATA_RAW_DIR.exists():
        return []
    
    excel_files = []
    for item in DATA_RAW_DIR.iterdir():
        if item.is_file() and (item.suffix == ".xls" or item.suffix == ".xlsx"):
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
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF gösterilirken hata oluştu: {e}")

def show_graphs(date_folder, num_graphs=6):
    """Tarih klasöründen grafikleri göster"""
    png_files = list(date_folder.glob("*.png"))
    
    if not png_files:
        st.warning("Bu tarih için grafik bulunamadı.")
        return
    
    # Grafikler için düzen oluştur
    st.subheader("Analiz Grafikleri")
    
    # Grafikler için 3 kolonlu bir grid oluştur (max 6 grafik)
    cols = st.columns(3)
    
    for i, png_file in enumerate(png_files[:num_graphs]):
        # Görüntülenecek başlık oluştur
        title = png_file.stem.replace("_", " ").replace("-", " ").title()
        
        with cols[i % 3]:
            st.image(str(png_file), caption=title)
            
            # Her sıra sonrası (3 grafik) yeni bir satıra geç
            if (i + 1) % 3 == 0 and i < num_graphs - 1:
                cols = st.columns(3)

def show_statistics(date):
    """İstatistikleri göster"""
    stats_file = DATA_REPORTS_DIR / date / f"nakil_bekleyen_raporu_{date}.txt"
    
    if stats_file.exists():
        with open(stats_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # İstatistikleri güzel göster
        st.subheader("İstatistikler")
        st.text(content)
    else:
        st.warning("Bu tarih için istatistik dosyası bulunamadı.")

def file_uploader_section():
    """Excel dosya yükleme bölümü"""
    
    # Kullanım talimatları
    st.info("""
    **Bu sekmede ne yapabilirsiniz?**
    1. "Dosya Seç" butonuna tıklayarak bilgisayarınızdan Excel dosyasını seçin
    2. Dosya yüklendikten sonra "Günlük Veri İşle" butonuna tıklayın
    3. İşlem tamamlandığında "Analiz" sekmesine geçebilirsiniz
    """)
    
    # Belirgin bir dosya yükleme alanı
    st.markdown("""
    <div style="padding: 20px; border: 2px dashed #2196F3; border-radius: 10px; text-align: center;">
        <h3>Nakil Vaka Excel Dosyası Yükle</h3>
        <p>Excel (.xls veya .xlsx) formatında dosya seçin</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Excel Dosyası Seç", type=["xls", "xlsx"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        # Dosya bilgilerini göster
        file_details = {
            "Dosya Adı": uploaded_file.name,
            "Dosya Boyutu": f"{uploaded_file.size / 1024:.1f} KB" if uploaded_file.size < 1024 * 1024 else f"{uploaded_file.size / (1024*1024):.1f} MB",
            "Dosya Tipi": uploaded_file.type
        }
        
        # Dosya detaylarını tablo olarak göster
        st.markdown("### Yüklenen Dosya Bilgileri")
        for k, v in file_details.items():
            st.write(f"**{k}:** {v}")
        
        # Dosyayı geçici olarak kaydet
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        temp_path = DATA_RAW_DIR / uploaded_file.name
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ Dosya başarıyla yüklendi!")
        
        # Dosya işleme seçenekleri - daha belirgin bir buton
        st.markdown("---")
        st.markdown("### İşlem Seçin")
        
        if st.button("🔄 Günlük Veri İşle", use_container_width=True):
            with st.spinner("Veri işleniyor... Bu işlem birkaç dakika sürebilir."):
                result = process_daily_data(temp_path)
                
                if result.returncode == 0:
                    st.balloons()  # Başarıda balonlar uçur
                    st.success("✅ Veri başarıyla işlendi!")
                    
                    with st.expander("İşlem Detayları", expanded=False):
                        st.text(result.stdout)
                    
                    # Analiz sekmesine geçmek için bilgi
                    st.info("Şimdi 'Analiz' sekmesine geçerek raporunuzu oluşturabilirsiniz.")
                else:
                    st.error("❌ Veri işleme hatası!")
                    with st.expander("Hata Detayları", expanded=True):
                        st.text(result.stderr)
                
                # Sayfayı yenile (yeni işlenen tarihleri göstermek için)
                st.experimental_rerun()

def existing_files_section():
    """Mevcut Excel dosyaları bölümü"""
    
    # Kullanım talimatları
    st.info("""
    **Bu sekmede ne yapabilirsiniz?**
    1. Listeden daha önce yüklenmiş bir Excel dosyasını seçin
    2. "Seçilen Dosyayı İşle" butonuna tıklayarak işlemi başlatın
    3. İşlem tamamlandığında "Analiz" sekmesine geçebilirsiniz
    """)
    
    excel_files = get_raw_files()
    
    if not excel_files:
        st.warning("⚠️ Henüz yüklenmiş Excel dosyası bulunmuyor.")
        st.markdown("""
        <div style="padding: 20px; border: 1px solid #FF9800; border-radius: 10px; text-align: center; background-color: #FFF8E1;">
            <h4>Önce 'Veri Yükleme' sekmesinden bir dosya yükleyin</h4>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Dosya listesini tablo olarak göster
    st.markdown("### Mevcut Excel Dosyaları")
    file_data = []
    
    for file_name in excel_files:
        file_path = DATA_RAW_DIR / file_name
        file_size = file_path.stat().st_size / 1024  # KB
        file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        
        if file_size < 1024:
            size_str = f"{file_size:.1f} KB"
        else:
            size_str = f"{file_size/1024:.1f} MB"
        
        file_data.append({"Dosya Adı": file_name, "Boyut": size_str, "Yükleme Tarihi": file_date})
    
    # Tablo görünümünde dosya listesi
    for i, file in enumerate(file_data):
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.write(f"**{file['Dosya Adı']}**")
        with col2:
            st.write(file['Boyut'])
        with col3:
            st.write(file['Yükleme Tarihi'])
        
        if i < len(file_data) - 1:  # Son satır hariç çizgi ekle
            st.markdown("---")
    
    # Dosya seçimi
    st.markdown("### İşlenecek Dosyayı Seçin")
    selected_file = st.selectbox("Excel dosyası seçin", excel_files)
    
    if selected_file:
        file_path = DATA_RAW_DIR / selected_file
        st.markdown(f"**Seçilen dosya:** {selected_file}")
        
        if st.button("🔄 Seçilen Dosyayı İşle", use_container_width=True):
            with st.spinner("Veri işleniyor... Bu işlem birkaç dakika sürebilir."):
                result = process_daily_data(file_path)
                
                if result.returncode == 0:
                    st.balloons()  # Başarıda balonlar uçur
                    st.success("✅ Veri başarıyla işlendi!")
                    
                    with st.expander("İşlem Detayları", expanded=False):
                        st.text(result.stdout)
                    
                    # Analiz sekmesine geçmek için bilgi
                    st.info("Şimdi 'Analiz' sekmesine geçerek raporunuzu oluşturabilirsiniz.")
                else:
                    st.error("❌ Veri işleme hatası!")
                    with st.expander("Hata Detayları", expanded=True):
                        st.text(result.stderr)

def analysis_section():
    """Analiz bölümü"""
    st.markdown("<h2 class='sub-header'>Nakil Analizi</h2>", unsafe_allow_html=True)
    
    # İşlenmiş tarih listesi
    dates = get_existing_dates()
    
    if not dates:
        st.info("Henüz işlenmiş veri bulunmuyor. Önce bir Excel dosyası yükleyin ve işleyin.")
        return
    
    selected_date = st.selectbox("Analiz Tarihi Seçin", dates)
    
    if st.button("Analiz Yap"):
        with st.spinner(f"{selected_date} tarihi için analiz yapılıyor..."):
            result = run_analysis(selected_date)
            
            if result.returncode == 0:
                st.markdown("<div class='success-box'>Analiz başarıyla tamamlandı!</div>", unsafe_allow_html=True)
                
                # PDF raporu
                pdf_path = DATA_REPORTS_DIR / selected_date / f"nakil_analiz_raporu_{selected_date}.pdf"
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                    
                    st.download_button(
                        label="📄 PDF Raporu İndir",
                        data=pdf_bytes,
                        file_name=f"nakil_analiz_raporu_{selected_date}.pdf",
                        mime="application/pdf"
                    )
                    
                    # PDF önizleme
                    with st.expander("PDF Raporu Önizleme", expanded=False):
                        show_pdf(pdf_path)
                
                # Grafikleri göster
                date_folder = DATA_REPORTS_DIR / selected_date
                show_graphs(date_folder)
                
                # İstatistikleri göster
                show_statistics(selected_date)
                
            else:
                st.error("❌ Analiz hatası!")
                st.text(result.stderr)

def main():
    configure_page()
    
    # Uygulama başlığı
    st.markdown("<h1 class='main-header'>Nakil Analiz Sistemi</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>Bu sistem, nakil vaka talepleri verilerini analiz eder ve otomatik raporlar oluşturur.</p>", unsafe_allow_html=True)
    
    # Sidebar bilgileri
    with st.sidebar:
        st.title("Nakil Analiz")
        st.info(
            """
            Bu uygulamanın kullanımı:
            1. Excel dosyasını yükleyin veya mevcut dosyalardan seçin
            2. 'Günlük Veri İşle' butonuna tıklayın
            3. İşlem tamamlandıktan sonra bir tarih seçin
            4. 'Analiz Yap' butonuna tıklayın
            5. Raporu inceleyin ve PDF olarak indirin
            """
        )
        
        st.markdown("---")
        st.caption("© 2025 Nakil Analiz Sistemi")
    
    # Ana sayfa düzeni
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>Aşağıdan İşlem Seçin</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📤 Veri Yükleme", "📂 Mevcut Dosyalar", "📊 Analiz"])
    
    with tab1:
        st.markdown("<h3 style='color: #1E88E5;'>Excel Dosyası Yükle</h3>", unsafe_allow_html=True)
        file_uploader_section()
    
    with tab2:
        st.markdown("<h3 style='color: #1E88E5;'>Mevcut Excel Dosyaları</h3>", unsafe_allow_html=True)
        existing_files_section()
    
    with tab3:
        st.markdown("<h3 style='color: #1E88E5;'>Nakil Analizi</h3>", unsafe_allow_html=True)
        analysis_section()

if __name__ == "__main__":
    main()
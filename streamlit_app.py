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

# TEK GİRİŞ NOKTASI: app.py'yi doğrudan dosya yolundan yükle (paket adı çakışmalarını önlemek için)
_delegated = False
try:
    import importlib.util
    import pathlib

    app_path = pathlib.Path(__file__).with_name("app.py")
    spec = importlib.util.spec_from_file_location("nakil_app_entry", str(app_path))
    if spec and spec.loader:
        _module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_module)
        if hasattr(_module, "main"):
            _module.main()
            _delegated = True
except Exception:
    # Delegasyon başarısızsa bu dosyanın kendi akışıyla devam edilir
    _delegated = False

if _delegated:
    # İkinci kez render etmeyi engelle
    st.stop()

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
    print(f"Modül import hatası: {e}")
    config_loaded = False

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
        div[data-testid='stCodeBlock'] pre,
        div[data-testid='stCodeBlock'] code,
        pre, code { background-color:#0f172a; color:#e5e7eb; border:1px solid #334155; border-radius:6px; }
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

def get_existing_reports():
    """Mevcut rapor klasörlerini basit şekilde listele"""
    reports = []
    
    if not DATA_REPORTS_DIR.exists():
        return reports
        
    try:
        for item in DATA_REPORTS_DIR.iterdir():
            if not item.is_dir() or not item.name.startswith("20"):
                continue
                
            # PNG dosyalarını kontrol et (grafik var mı?)
            png_files = list(item.glob("*.png"))
            
            # PDF dosyalarını kontrol et
            pdf_files = list(item.glob("*.pdf"))
            
            # JSON dosyalarını kontrol et
            json_files = list(item.glob("*.json"))
            
            # Raporu listeye ekle (en azından bir dosya varsa)
            if png_files or pdf_files or json_files:
                reports.append({
                    "folder_name": item.name,
                    "folder_path": str(item),
                    "png_count": len(png_files),
                    "has_pdf": len(pdf_files) > 0,
                    "has_json": len(json_files) > 0,
                    "display_name": item.name.replace("_", " | "),  # Daha okunabilir format
                    "creation_time": item.stat().st_mtime
                })
        
        # En yeni raporları en başta göster
        reports = sorted(reports, key=lambda x: x["creation_time"], reverse=True)
        
    except Exception as e:
        st.error(f"Rapor listesi alınırken hata: {e}")
        
    return reports

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

def process_daily_data(file_path, unique_id=None):
    """Günlük veri işleme komutu çalıştır"""
    command = ["python", "main.py", "--gunluk-islem", str(file_path)]
    if unique_id:
        command += ["--unique-id", unique_id]
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

def show_graphs(report_folder_path, num_graphs=6):
    """Verilen klasörden grafikleri basit şekilde göster"""
    
    if isinstance(report_folder_path, str):
        report_folder_path = Path(report_folder_path)
    
    # Klasör kontrolü
    if not report_folder_path.exists():
        st.error(f"❌ Rapor klasörü bulunamadı: {report_folder_path}")
        st.info("💡 Lütfen 'Nakil Analizi' sekmesinden yeni bir rapor oluşturun.")
        return
    
    # PNG dosyalarını bul
    png_files = list(report_folder_path.glob("*.png"))

    # Eğer png bulunamazsa, tarih klasöründe ara
    if not png_files:
        # Klasör ismi başındaki tarihi al
        date_part = report_folder_path.name.split('_')[0]
        alt_path = DATA_REPORTS_DIR / date_part
        # Tarih klasöründe png var mı?
        alt_png = list(alt_path.glob("*.png"))
        if alt_png:
            png_files = alt_png
            report_folder_path = alt_path
    
    if not png_files:
        st.warning(f"⚠️ Bu klasörde hiç grafik bulunamadı: {report_folder_path.name}")
        
        # PDF kontrolü
        pdf_files = list(report_folder_path.glob("*.pdf"))
        if pdf_files:
            st.info("📄 PDF raporu mevcut. 'PDF Raporu' sekmesinden görüntüleyebilirsiniz.")
        else:
            st.error("❌ Bu rapor için hiçbir dosya bulunamadı. Rapor oluşturma işleminde sorun yaşanmış olabilir.")
        return
    
    # Grafik sayısı bilgisi
    st.info(f"📊 Toplam {len(png_files)} grafik bulundu.")
    
    # Kategori filtresi (eğer çok grafik varsa)
    display_graphs = png_files
    
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
    
    # İnteraktif grafik görüntüleyici
    tabs = []
    tab_titles = []
    
    # Daha açıklayıcı tab başlıkları oluştur
    for i, png_file in enumerate(display_graphs):
        name = png_file.stem
        # Uzun ismi kısalt
        if len(name) > 25:
            parts = name.split('_')
            if len(parts) > 3:
                short_name = f"{parts[0]}...{parts[-1]}"
            else:
                short_name = name[:25] + "..."
        else:
            short_name = name
            
        tab_titles.append(f"Grafik {i+1}")
    
    # Tab grubu oluştur
    if len(display_graphs) > 1:
        tabs = st.tabs(tab_titles)
    
        # Her tab içinde bir grafik göster
        for i, (tab, png_file) in enumerate(zip(tabs, display_graphs)):
            with tab:
                # Başlık oluştur
                title = png_file.stem.replace("_", " ").replace("-", " ").title()
                st.markdown(f"**{title}**")
                
                # Grafiği göster
                st.image(str(png_file), use_container_width=True)
                
                # Grafik detayları ve indirme butonu
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"Dosya: {png_file.name}")
                with col2:
                    with open(png_file, "rb") as img_file:
                        btn = st.download_button(
                            label="İndir",
                            data=img_file,
                            file_name=png_file.name,
                            mime="image/png",
                            key=f"download_graph_{i}"
                        )
    else:
        # Tek grafik varsa direk göster
        for png_file in display_graphs:
            title = png_file.stem.replace("_", " ").replace("-", " ").title()
            st.markdown(f"**{title}**")
            st.image(str(png_file), use_container_width=True)
            
    # Grid görünüm seçeneği
    if len(display_graphs) > 3 and st.checkbox("Grafikleri grid olarak göster", value=False):
        st.markdown("### Grafik Özeti")
        
        # Grafikler için 3 kolonlu bir grid oluştur
        cols = st.columns(3)
        
        for i, png_file in enumerate(display_graphs):
            # Görüntülenecek başlık oluştur
            title = png_file.stem.replace("_", " ").replace("-", " ").title()
            if len(title) > 40:
                title = title[:40] + "..."
            
            with cols[i % 3]:
                st.image(str(png_file), caption=title, width=250)
                
                # Her sıra sonrası (3 grafik) yeni bir satıra geç
                if (i + 1) % 3 == 0 and i < len(display_graphs) - 1:
                    cols = st.columns(3)

def show_statistics(date):
    """İstatistikleri göster"""
    stats_file = DATA_REPORTS_DIR / date / f"nakil_bekleyen_raporu_{date}.txt"
    
    if stats_file.exists():
        with open(stats_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # İstatistik içeriğini bölümlere ayır
        sections = []
        current_section = []
        current_title = "Genel İstatistikler"
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Yeni bölüm başlığı mı?
            if line.isupper() and len(line) > 10:
                if current_section:  # Önceki bölümü kaydet
                    sections.append({"title": current_title, "content": current_section})
                    current_section = []
                current_title = line
            else:
                current_section.append(line)
                
        # Son bölümü de ekle
        if current_section:
            sections.append({"title": current_title, "content": current_section})
            
        # İstatistikleri güzel bir şekilde göster
        if len(sections) > 1:
            # Sekmeli görünüm oluştur
            tabs = st.tabs([section["title"].title() for section in sections])
            
            for i, (tab, section) in enumerate(zip(tabs, sections)):
                with tab:
                    # Özel formatlanmış içerik
                    st.markdown(f"<h3>{section['title'].title()}</h3>", unsafe_allow_html=True)
                    
                    for line in section["content"]:
                        if line.startswith("•") or line.startswith("-"):
                            st.markdown(f"<div style='margin-left: 20px;'>{line}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div><strong>{line}</strong></div>", unsafe_allow_html=True)
        else:
            # Tek bölüm varsa direkt göster
            st.markdown("<h3>İstatistikler</h3>", unsafe_allow_html=True)
            for line in content.split('\n'):
                if line.strip():
                    st.write(line)
        
        # İstatistik dosyasını indir
        with open(stats_file, "r", encoding="utf-8") as f:
            st.download_button(
                label="📝 İstatistik Dosyasını İndir",
                data=f,
                file_name=f"nakil_istatistik_{date}.txt",
                mime="text/plain"
            )
    else:
        st.warning("⚠️ Bu tarih için istatistik dosyası bulunamadı.")

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
    import hashlib
    
    if uploaded_file is not None:
        # Dosya bilgilerini göster
        file_details = {
            "Dosya Adı": uploaded_file.name,
            "Dosya Boyutu": f"{uploaded_file.size / 1024:.1f} KB" if uploaded_file.size < 1024 * 1024 else f"{uploaded_file.size / (1024*1024):.1f} MB",
            "Dosya Tipi": uploaded_file.type
        }
        st.markdown("### Yüklenen Dosya Bilgileri")
        for k, v in file_details.items():
            st.write(f"**{k}:** {v}")

        # Benzersiz zaman damgası ve dosya hash'i oluştur
        # Önce aynı dosya daha önce kaydedildi mi kontrol et
        file_hash = hashlib.md5(uploaded_file.getbuffer()).hexdigest()[:8]
        
        # Aynı hash'e sahip dosya var mı?
        existing_files = list(DATA_RAW_DIR.glob(f"*_{file_hash}_*"))
        if existing_files:
            # Mevcut dosyanın unique_id'sini kullan
            temp_path = existing_files[0]
            # Dosya adından unique_id'yi parse et: YYYYMMDD_HHMMSS_hash
            parts = temp_path.stem.split("_")
            unique_id = f"{parts[0]}_{parts[1]}_{parts[2]}"  # YYYYMMDD_HHMMSS_hash
            st.info(f"📄 Bu dosya daha önce yüklenmişti, mevcut unique_id kullanılıyor: {unique_id}")
        else:
            # Yeni dosya, yeni unique_id oluştur
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = f"{now_str}_{file_hash}"
            
            # Dosyayı kaydet
            DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
            temp_path = DATA_RAW_DIR / f"{unique_id}_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Dosya başarıyla yüklendi!")
        
        st.info(f"🔑 Unique ID: {unique_id}")

        st.markdown("---")
        st.markdown("### 🚀 Hızlı İşlem")

        if st.button("⚡ Hızlı İşle (Veri İşle + Analiz Yap + PDF Oluştur)", use_container_width=True, type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Adım 1: Veri işleme
            status_text.text("📊 Adım 1/2: Excel verisi işleniyor...")
            progress_bar.progress(25)
            
            # Debug: ortam bilgisi
            with st.expander("🔧 İşlem Detayları (Debug)", expanded=True):
                st.code(f"""
Dosya: {temp_path}
Unique ID: {unique_id}
Çalışma Dizini: {ROOT_DIR}
Python: {sys.executable}
                """)

            result = process_daily_data(temp_path, unique_id=unique_id)
            
            if result.returncode != 0:
                st.error("❌ Veri işleme hatası!")
                with st.expander("Hata Detayları", expanded=True):
                    # Show stderr or stdout if stderr is empty
                    err = result.stderr.strip() or result.stdout.strip() or 'Çıktı yok'
                    st.code(err)
                return
            
            progress_bar.progress(50)
            st.success("✅ Veri başarıyla işlendi!")
            
            # Adım 2: Analiz ve PDF oluşturma
            status_text.text("📈 Adım 2/2: Analiz yapılıyor ve PDF oluşturuluyor...")
            progress_bar.progress(75)
            
            # Tarihi belirle (Excel'den veya bugünden)
            gun_tarihi = datetime.now().strftime("%Y-%m-%d")
            
            # Analiz komutunu çalıştır (unique_id ile)
            # Python yolu olarak sys.executable kullan
            command = [sys.executable, "main.py", "--analiz", gun_tarihi, "--unique-id", unique_id]
            analiz_result = run_command(command)
            
            progress_bar.progress(100)
            
            if analiz_result.returncode != 0:
                st.error("❌ Analiz hatası!")
                with st.expander("Hata Detayları", expanded=True):
                    err = analiz_result.stderr.strip() or analiz_result.stdout.strip() or 'Çıktı yok'
                    st.code(err)
                return
            # Başarılı analiz
            st.balloons()
            st.success("🎉 Rapor başarıyla oluşturuldu!")

            # Son analiz bilgisini sakla ve ön seçim yap
            st.session_state.last_analysis = {"status": "success", "date": gun_tarihi, "unique_id": unique_id}
            st.session_state.preselect_folder = f"{gun_tarihi}_{unique_id}"

            st.info("📂 Raporunuz aşağıda görüntüleniyor...")
            st.rerun()
    else:
        st.warning("⚠️ Henüz yüklenmiş Excel dosyası bulunmuyor.")
        st.markdown("""
        <div style="padding: 20px; border: 1px solid #FF9800; border-radius: 10px; text-align: center; background-color: #FFF8E1;">
            <h4>Önce 'Veri Yükleme' sekmesinden bir dosya yükleyin</h4>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Ham Excel dosyalarını al ve listele
    excel_files = get_raw_files()
    if not excel_files:
        st.info("📂 Henüz işlenmek üzere yüklenmiş Excel dosyası yok.")
        return
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
    """Analiz bölümü - Dosya yükleme ve mevcut raporlar"""
    
    st.markdown("<h1 class='main-header'>Nakil Analizi</h1>", unsafe_allow_html=True)
    
    # === YENİ RAPOR YÜKLEME BÖLÜMÜ ===
    st.markdown("### 📤 Yeni Nakil Raporu Yükle")
    
    uploaded_file = st.file_uploader(
        "Nakil Z Raporu Excel dosyasını (.xls/.xlsx) seçin:",
        type=["xls", "xlsx"],
        help="Sağlık Bakanlığı'ndan aldığınız Nakil Vaka Talepleri Raporu dosyasını yükleyin"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Dosya yüklendi: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
        
        # İki sütunlu düzen: Buton + İpucu
        col1, col2 = st.columns([3, 1])
        with col1:
            start_analysis = st.button(
                "🚀 Nakil Analizi Yap", 
                type="primary", 
                use_container_width=True,
                help="Excel verisini işler, nakil analizini yapar ve PDF raporu oluşturur"
            )
        with col2:
            if st.button("❌ İptal", use_container_width=True):
                st.rerun()
        
        if start_analysis:
            try:
                import hashlib
                
                # Dosya hash'ini hesapla
                file_hash = hashlib.md5(uploaded_file.getbuffer()).hexdigest()[:8]
                
                # Aynı hash'e sahip dosya daha önce kaydedildi mi?
                existing_files = list(DATA_RAW_DIR.glob(f"*_{file_hash}_*"))
                if existing_files:
                    # Mevcut dosyanın unique_id'sini kullan
                    save_path = existing_files[0]
                    parts = save_path.stem.split("_")
                    unique_id = f"{parts[0]}_{parts[1]}_{parts[2]}"
                    st.info(f"📄 Bu dosya daha önce yüklenmişti. Mevcut unique_id kullanılıyor: {unique_id}")
                else:
                    # Yeni dosya - yeni unique_id oluştur
                    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_id = f"{now_str}_{file_hash}"
                    
                    save_path = DATA_RAW_DIR / f"{unique_id}_{uploaded_file.name}"
                    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    st.success(f"✅ Yeni dosya kaydedildi: {unique_id}")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                status_text.text("📊 Adım 1/2: Excel verisi işleniyor...")
                progress_bar.progress(25)
                
                # Debug: Komut bilgisi
                with st.expander("🔧 İşlem Detayları (Debug)", expanded=True):
                    st.code(f"""
Dosya: {save_path}
Unique ID: {unique_id}
Çalışma Dizini: {ROOT_DIR}
Python: {sys.executable}
                    """)

                result = process_daily_data(save_path, unique_id=unique_id)
                
                if result.returncode != 0:
                    st.error("❌ Veri işleme hatası!")
                    with st.expander("Hata Detayları", expanded=True):
                        err = result.stderr.strip() or result.stdout.strip() or 'Çıktı yok'
                        st.code(err)
                else:
                    progress_bar.progress(50)
                    st.success("✅ Veri başarıyla işlendi!")
                    
                    status_text.text("📈 Adım 2/2: Analiz yapılıyor ve PDF oluşturuluyor...")
                    progress_bar.progress(75)
                    
                    # Tarihi belirle (Excel'den veya bugünden)
                    gun_tarihi = datetime.now().strftime("%Y-%m-%d")
                    
                    # Analiz komutunu çalıştır (unique_id ile)
                    command = [sys.executable, "main.py", "--analiz", gun_tarihi, "--unique-id", unique_id]
                    analiz_result = run_command(command)
                    
                    progress_bar.progress(100)
                    status_text.text("")
                    
                    if analiz_result.returncode == 0:
                        st.balloons()
                        st.success("🎉 Tüm işlemler tamamlandı! PDF raporunuz hazır.")
                        
                        # Başarı durumunu session_state'e kaydet
                        st.session_state.last_analysis = {
                            "status": "success",
                            "date": gun_tarihi,
                            "unique_id": unique_id,
                        }
                        st.session_state.preselect_folder = f"{gun_tarihi}_{unique_id}"
                        
                        st.info("📂 Rapor Arşivi sayfasına yönlendiriliyorsunuz...")
                        
                        # Rapor arşivi sayfasına yönlendirme
                        st.session_state.page = "rapor"
                        st.rerun()
                    else:
                        st.error("❌ Analiz hatası!")
                        with st.expander("Hata Detayları", expanded=True):
                            err = analiz_result.stderr.strip() or analiz_result.stdout.strip() or 'Çıktı yok'
                            st.code(err)
                
            except Exception as e:
                st.error(f"❌ İşlem hatası: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # === MEVCUT RAPORLAR BÖLÜMÜ ===
    st.markdown("---")
    st.markdown("### 📋 Son Oluşturulan Raporlar")
    
    # Mevcut raporları listele
    reports = get_existing_reports()
    if not reports:
        st.info("📝 Henüz rapor oluşturulmamış. Yukarıdan bir Excel dosyası yükleyip analiz yapabilirsiniz.")
    else:
        # İlk 3 raporu göster
        st.markdown(f"**Toplam {len(reports)} rapor bulundu.** İlk 3 rapor gösteriliyor:")
        
        for i, report in enumerate(reports[:3]):
            with st.expander(f"📊 {report['display_name']} ({report['png_count']} grafik)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("� Grafik", report['png_count'])
                with col2:
                    st.metric("📄 PDF", "✅" if report['has_pdf'] else "❌")
                with col3:
                    st.metric("📊 JSON", "✅" if report['has_json'] else "❌")
                
                # PDF indirme butonu
                report_path = Path(report['folder_path'])
                pdf_files = list(report_path.glob("*.pdf"))
                if pdf_files:
                    with open(pdf_files[0], "rb") as f:
                        st.download_button(
                            "� PDF İndir",
                            data=f.read(),
                            file_name=pdf_files[0].name,
                            mime="application/pdf",
                            key=f"pdf_download_{i}"
                        )
        
        st.info("💡 Tüm raporları görüntülemek için **Rapor Arşivi** sekmesine gidin.")

def main():
    configure_page()
    
    # Sidebar menüsü
    with st.sidebar:
        st.markdown("# 🏥 NAKİL ANALİZ SİSTEMİ")
        
        st.markdown("---")
        
        menu_options = {
            "ana_sayfa": "🏠 Ana Sayfa",
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
    
    if current_page == "analiz":
        analysis_section()
    elif current_page == "rapor":
        # Rapor Arşivi Sayfası
        st.markdown("<h1 class='main-header'>Rapor Arşivi</h1>", unsafe_allow_html=True)
        
        # === YENİ RAPOR OLUŞTURMA BÖLÜMÜ ===
        st.markdown("### 📤 Yeni Rapor Oluştur")
        
        uploaded_file = st.file_uploader(
            "Nakil Z Raporu Excel dosyasını (.xls/.xlsx) seçin:",
            type=["xls", "xlsx"],
            help="Sağlık Bakanlığı'ndan aldığınız Nakil Vaka Talepleri Raporu dosyasını yükleyin",
            key="rapor_arsivi_uploader"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ Dosya yüklendi: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            
            # İki sütunlu düzen: Buton + İpucu
            col1, col2 = st.columns([3, 1])
            with col1:
                start_analysis = st.button(
                    "🚀 Rapor Oluştur", 
                    type="primary", 
                    use_container_width=True,
                    help="Excel verisini işler, nakil analizini yapar ve PDF raporu oluşturur",
                    key="rapor_olustur_btn"
                )
            with col2:
                if st.button("❌ İptal", use_container_width=True, key="rapor_iptal_btn"):
                    st.rerun()
            
            if start_analysis:
                try:
                    import hashlib
                    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_hash = hashlib.md5(uploaded_file.getbuffer()).hexdigest()[:8]
                    unique_id = f"{now_str}_{file_hash}"
                    
                    save_path = DATA_RAW_DIR / f"{unique_id}_{uploaded_file.name}"
                    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("📊 Adım 1/2: Excel verisi işleniyor...")
                    progress_bar.progress(25)
                    
                    # Debug: Komut bilgisi
                    with st.expander("🔧 İşlem Detayları (Debug)", expanded=True):
                        st.code(f"""
Dosya: {save_path}
Unique ID: {unique_id}
Çalışma Dizini: {ROOT_DIR}
Python: {sys.executable}
                        """)

                    result = process_daily_data(save_path, unique_id=unique_id)
                    
                    if result.returncode != 0:
                        st.error("❌ Veri işleme hatası!")
                        with st.expander("Hata Detayları", expanded=True):
                            err = result.stderr.strip() or result.stdout.strip() or 'Çıktı yok'
                            st.code(err)
                        return
                    
                    progress_bar.progress(50)
                    st.success("✅ Veri başarıyla işlendi!")
                    
                    status_text.text("📈 Adım 2/2: Analiz yapılıyor ve PDF oluşturuluyor...")
                    progress_bar.progress(75)
                    
                    # Tarihi belirle (Excel'den veya bugünden)
                    gun_tarihi = datetime.now().strftime("%Y-%m-%d")
                    
                    # Analiz komutunu çalıştır (unique_id ile)
                    command = [sys.executable, "main.py", "--analiz", gun_tarihi, "--unique-id", unique_id]
                    analiz_result = run_command(command)
                    
                    progress_bar.progress(100)
                    status_text.text("")
                    
                    if analiz_result.returncode == 0:
                        st.balloons()
                        st.success("🎉 Rapor başarıyla oluşturuldu!")
                        
                        # Başarı durumunu session_state'e kaydet
                        st.session_state.last_analysis = {
                            "status": "success",
                            "date": gun_tarihi,
                            "unique_id": unique_id,
                        }
                        st.session_state.preselect_folder = f"{gun_tarihi}_{unique_id}"
                        
                        st.info("📂 Raporunuz aşağıda görüntüleniyor...")
                        st.rerun()
                    else:
                        st.error("❌ Analiz hatası!")
                        with st.expander("Hata Detayları", expanded=True):
                            err = analiz_result.stderr.strip() or analiz_result.stdout.strip() or 'Çıktı yok'
                            st.code(err)
                
                except Exception as e:
                    st.error(f"❌ İşlem hatası: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        st.markdown("---")
        
        # === MEVCUT RAPORLAR BÖLÜMÜ ===
        st.markdown("### 📋 Mevcut Raporlar")
        
        # Son işlem durum kutucuğu
        last = st.session_state.get("last_analysis")
        if last:
            if last.get("status") == "success":
                st.success("✅ Son işlem: Nakil analizi başarıyla tamamlandı.")
            else:
                with st.expander("❌ Son işlem hata detayı", expanded=True):
                    st.markdown("Analiz sırasında hata oluştu.")
        
        # Mevcut raporları listele
        reports = get_existing_reports()
        if not reports:
            st.warning("⚠️ Henüz oluşturulmuş rapor bulunamadı.")
            st.info("📝 Yukarıdan bir Excel dosyası yükleyip rapor oluşturabilirsiniz.")
        else:
            st.markdown(f"### 📋 Mevcut Raporlar ({len(reports)} adet)")
            
            # Rapor seçimi - basit format
            selected_idx = st.selectbox(
                "Görüntülenecek raporu seçin:",
                range(len(reports)),
                format_func=lambda x: reports[x]['display_name'],
                index=0
            )
            
            # Seçilen raporu al
            selected = reports[selected_idx]
            
            st.success(f"✅ Seçilen rapor: {selected['display_name']}")
            
            # Rapor bilgileri
            report_path = Path(selected['folder_path'])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📈 Grafik Sayısı", selected['png_count'])
            with col2:
                st.metric("📄 PDF Raporu", "✅ Var" if selected['has_pdf'] else "❌ Yok")
            with col3:
                st.metric("📊 JSON Verisi", "✅ Var" if selected['has_json'] else "❌ Yok")
            
            # Tab'lar ile içerik gösterimi
            tab1, tab2, tab3 = st.tabs(["📈 Grafikler", "📄 PDF Raporu", "📊 JSON Verisi"])
            
            with tab1:
                show_graphs(report_path, num_graphs=10)
            
            with tab2:
                pdf_files = list(report_path.glob("*.pdf"))
                if pdf_files:
                    pdf_file = pdf_files[0]  # İlk PDF'i al
                    with open(pdf_file, "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.download_button(
                        label="📥 PDF Raporu İndir",
                        data=pdf_bytes,
                        file_name=pdf_file.name,
                        mime="application/pdf"
                    )
                    
                    # PDF önizlemesi
                    try:
                        show_pdf(str(pdf_file))
                    except Exception as e:
                        st.error(f"PDF önizleme hatası: {e}")
                else:
                    st.warning("⚠️ Bu rapor için PDF dosyası bulunamadı.")
            
            with tab3:
                json_files = list(report_path.glob("*.json"))
                if json_files:
                    json_file = json_files[0]  # İlk JSON'ı al
                    with st.expander(f"JSON Verisi: {json_file.name}"):
                        try:
                            with open(json_file, encoding="utf-8") as f:
                                data = json.load(f)
                            st.json(data)
                        except Exception as e:
                            st.error(f"❌ JSON okuma hatası: {e}")
                else:
                    st.warning("⚠️ JSON verisi bulunamadı.")
    else:  # Ana sayfa varsayılan
        # Ana sayfa içeriği
        st.markdown("<h1 class='main-header'>Nakil Z Raporu Analiz Sistemi</h1>", unsafe_allow_html=True)
        st.markdown("<p class='info-text'>Bu sistem, nakil vaka talepleri verilerini analiz eder ve otomatik raporlar oluşturur.</p>", unsafe_allow_html=True)
        
        # Excel yükleme bölümü
        st.markdown("### 📤 Nakil Raporu Yükle")
        file_uploader_section()

if __name__ == "__main__":
    # Session state başlat
    if "page" not in st.session_state:
        st.session_state.page = "ana_sayfa"
    
    main()
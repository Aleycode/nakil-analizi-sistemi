"""
Basit Streamlit Test Uygulaması
"""

import streamlit as st
import base64
from pathlib import Path

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Nakil Analiz Test",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Nakil Analiz Sistemi")
st.markdown("## Test Uygulaması")

# Sistem durumu
col1, col2 = st.columns(2)
with col1:
    st.success("✅ Sistem başarıyla çalışıyor!")
with col2:
    st.info("📂 PDF dosyaları kontrol ediliyor...")

# PDF dosyalarını bul
data_dir = Path(__file__).parent / "data" / "reports"
pdf_files = list(data_dir.glob("**/*.pdf"))

if pdf_files:
    st.success(f"✅ {len(pdf_files)} PDF dosyası bulundu!")
    
    # PDF seçimi
    pdf_names = [f.name for f in pdf_files]
    selected_pdf = st.selectbox("Görüntülenecek PDF'i seçin:", pdf_names)
    
    if selected_pdf:
        # Seçilen PDF'in tam yolunu bul
        selected_pdf_path = next(f for f in pdf_files if f.name == selected_pdf)
        
        st.write(f"📄 **Seçilen PDF:** {selected_pdf_path}")
        
        # İndirme butonu
        with open(selected_pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.download_button(
                label="📥 PDF İndir",
                data=pdf_bytes,
                file_name=selected_pdf,
                mime="application/pdf",
                width="stretch"
            )
        
        with col2:
            if st.button("📖 PDF Göster", width="stretch"):
                st.session_state.show_pdf = True
        
        # PDF görüntüle
        if st.session_state.get("show_pdf", False):
            st.markdown("### PDF İçeriği")
            try:
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                pdf_display = f'''
                <iframe 
                    src="data:application/pdf;base64,{base64_pdf}" 
                    width="100%" 
                    height="800" 
                    type="application/pdf"
                    style="border: 1px solid #ccc;">
                </iframe>
                '''
                st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ PDF gösterilirken hata oluştu: {e}")
    
    # Dosya detayları
    with st.expander("📋 PDF Dosya Detayları"):
        for pdf_file in pdf_files:
            file_size = pdf_file.stat().st_size / 1024  # KB
            st.write(f"• **{pdf_file.name}** - {file_size:.1f} KB - {pdf_file.parent.name}")
else:
    st.error("❌ PDF dosyası bulunamadı.")
    st.info("💡 Ana uygulama çalıştırılarak PDF raporları oluşturulabilir.")

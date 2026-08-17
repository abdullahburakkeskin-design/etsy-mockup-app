import streamlit as st
from PIL import Image
import io
import os
import replicate

st.set_page_config(
    page_title="AI Art Studio: Mockup & 8K Upscaler",
    page_icon="🎨",
    layout="wide"
)

st.title("🎨 AI Art Studio: Gerçekçi Mockup & 8K Upscaler")
st.write("Tablonuzu yükleyin; yapay zeka ile **gerçekçi oda mockup'ları** oluşturun ve **8K / 300 DPI kalitesine yükseltin**.")

# Streamlit Secrets Üzerinden Token Kontrolü
try:
    REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
except Exception:
    st.error("⚠️ API Şifresi (Token) Bulunamadı! Lütfen Streamlit Settings > Secrets alanına REPLICATE_API_TOKEN değerinizi ekleyin.")
    st.stop()

# Sekme Yapısı
tab1, tab2 = st.tabs(["🖼️ Yapay Zeka Oda Mockup'ı", "🔍 4K / 8K Görsel Netleştirme (Upscaler)"])

uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file)
    
    # ---------------------------------------------------------
    # TAB 1: AI MOCKUP GENERATOR
    # ---------------------------------------------------------
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(raw_img, caption="Orijinal Tablonuz", use_container_width=True)
            
        with col2:
            st.markdown("### ⚙️ Mockup Seçenekleri")
            style_option = st.selectbox(
                "İç Mekan Konsepti",
                [
                    "Modern Minimalist Salon (Gün Işığı)",
                    "İskandinav Çalışma Odası (Ahşap & Bitkiler)",
                    "Lüks Sanat Galerisi (Spot Işıklar)",
                    "Boho-Chic Yatak Odası (Toprak Tonları)"
                ]
            )
            frame_style = st.selectbox(
                "Çerçeve Stili", 
                ["Siyah Ahşap Çerçeve", "Doğal Meşe Çerçeve", "Beyaz Çerçeve", "Çerçevesiz İnce Kanvas"]
            )
            
            run_mockup = st.button("✨ Yapay Zeka İle Odada Oluştur", type="primary", use_container_width=True)

        if run_mockup:
            st.markdown("---")
            st.info("⏳ Yapay Zeka tablonuzun dokusunu koruyarak odayı tasarlıyor...")
            
            img_bytes = io.BytesIO()
            raw_img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            prompts = {
                "Modern Minimalist Salon (Gün Işığı)": "A high-end modern minimalist living room wall, soft natural sunlight, luxury interior design, stylish furniture, realistic photo",
                "İskandinav Çalışma Odası (Ahşap & Bitkiler)": "A cozy Scandinavian style room wall with wooden desk, indoor plant, warm aesthetic ambient lighting, realistic photo",
                "Lüks Sanat Galerisi (Spot Işıklar)": "A modern art gallery interior corridor wall, spotlighting, sleek hardwood floors, premium atmosphere, realistic photo",
                "Boho-Chic Yatak Odası (Toprak Tonları)": "A stylish Boho-chic bedroom interior, textured beige wall, pampas grass decor, warm natural shadows, realistic photo"
            }
            
            full_prompt = (
                f"A wall artwork framed with {frame_style} seamlessly hanging on the wall in this room: {prompts[style_option]}. "
                f"Keep the original artwork untouched and identical inside the frame, 8k resolution, professional interior photography."
            )
            
            try:
                output = replicate.run(
                    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    input={
                        "image": img_bytes,
                        "prompt": full_prompt,
                        "prompt_strength": 0.8,
                        "num_outputs": 1
                    }
                )
                if output and len(output) > 0:
                    st.success("✅ Mockup Başarıyla Üretildi!")
                    st.image(output[0], caption="Yapay Zeka Mockup Çıktısı", use_container_width=True)
            except Exception as e:
                st.error(f"Mockup oluşturulurken bir hata meydana geldi: {str(e)}")

    # ---------------------------------------------------------
    # TAB 2: 4K / 8K RESOLUTION UPSCALER (300 DPI)
    # ---------------------------------------------------------
    with tab2:
        st.markdown("### 🔍 Görsel Çözünürlüğünü Yükseltme (Super Resolution)")
        st.write("Görselinizin piksellerini yapay zeka ile doldurarak netleştirin ve baskıya hazır (300 DPI) hale getirin.")
        
        scale_factor = st.radio("Hedef Çözünürlük Büyüklüğü", ["2x (Full HD / 2K)", "4x (4K Ultra HD)", "8x (8K Baskı Kalitesi - 300 DPI)"])
        scale_map = {"2x (Full HD / 2K)": 2, "4x (4K Ultra HD)": 4, "8x (8K Baskı Kalitesi - 300 DPI)": 8}
        
        run_upscale = st.button("🚀 Görseli Netleştir ve Büyüt", type="primary")
        
        if run_upscale:
            st.info("⏳ Yapay Zeka pikselleri yeniden işliyor ve netleştiriyor...")
            
            img_bytes = io.BytesIO()
            raw_img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            try:
                output_url = replicate.run(
                    "nightmareai/real-esrgan:42203314ed1d2ee0b5511116347e4122cd0ed303e6de732238d6732a603b857f",
                    input={
                        "image": img_bytes,
                        "scale": scale_map[scale_factor],
                        "face_enhance": False
                    }
                )
                
                if output_url:
                    st.success(f"✅ Görsel Başarıyla {scale_factor} Seviyesine Yükseltildi!")
                    st.image(output_url, caption="Yüksek Çözünürlüklü Çıktı", use_container_width=True)
            except Exception as e:
                st.error(f"Upscale işlemi sırasında hata oluştu: {str(e)}")

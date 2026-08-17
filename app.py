import streamlit as st
from PIL import Image
import io
import zipfile
import replicate
import os

st.set_page_config(
    page_title="AI Mockup Generator - Etsy Studio",
    page_icon="🖼️",
    layout="wide"
)

# Başlık ve Açıklama
st.title("🖼️ Yapay Zeka Destekli Gerçekçi Mockup Üretici")
st.write("""
Tablonuzun **orijinal renklerini, detaylarını ve boyut oranını %100 koruyarak** 
yapay zeka yardımıyla modern iç mekan görselleri ve çerçeve mockup'ları oluşturun.
""")

# Sol Menü - API Key Yapılandırması
st.sidebar.header("🔑 Yapay Zeka Bağlantısı")
api_key = st.sidebar.text_input(
    "Replicate API Key", 
    type="password", 
    help="replicate.com adresinden alacağınız API anahtarı."
)

if not api_key:
    st.info("💡 Başlamak için lütfen sol menüden Replicate API anahtarınızı girin.")
    st.stop()

os.environ["REPLICATE_API_TOKEN"] = api_key

# Yapay Zeka İç Mekan Konseptleri (Prompts)
PROMPTS = {
    "1. Modern Minimalist Salon": "A high-end modern minimalist living room wall, soft natural sunlight, luxury interior design, stylish furniture around, realistic photo",
    "2. İskandinav Tarzı Çalışma Alanı": "A cozy Scandinavian style room wall with wooden desk, indoor plant, warm aesthetic ambient lighting, realistic photo",
    "3. Boho Style Yatak Odası": "A stylish Boho-chic bedroom interior, textured beige wall, pampas grass decor, warm natural shadows, realistic photo",
    "4. Galeri Duvarı / Şık Koridor": "A modern art gallery interior corridor wall, spotlighting, sleek hardwood floors, premium atmosphere, realistic photo"
}

# Görsel Yükleme Alanı
uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file)
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.image(raw_img, caption="Orijinal Tablo Görseli", use_container_width=True)
    
    with col_right:
        st.markdown("### ⚙️ Mockup Seçenekleri")
        frame_color = st.selectbox(
            "Çerçeve Seçeneği", 
            ["Siyah Ahşap Çerçeve", "Doğal Ahşap Çerçeve", "Beyaz Çerçeve", "Çerçevesiz Kanvas (Canvas)"]
        )
        
        generate_btn = st.button("✨ 4 Yapay Zeka Mockup'ını Üret", type="primary", use_container_width=True)

    if generate_btn:
        st.markdown("---")
        st.markdown("### ⏳ Yapay Zeka Odaları Çiziyor...")
        progress_bar = st.progress(0)
        
        generated_images = {}
        
        # Orijinal Görseli Byte Formatına Dönüştür
        img_bytes = io.BytesIO()
        raw_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # 4 Farklı Varyasyon İçin AI Çağrısı
        for idx, (style_name, prompt_text) in enumerate(PROMPTS.items()):
            full_prompt = (
                f"A framed wall art artwork in a frame ({frame_color}). "
                f"Placed on the wall in {prompt_text}. "
                f"Keeping the exact original artwork untouched inside the frame, 8k resolution, interior design photography."
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
                generated_images[style_name] = output[0]
            except Exception as e:
                st.error(f"{style_name} üretilirken bir hata oluştu: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(PROMPTS))

        st.success("✅ Tüm Yapay Zeka Mockup'ları Başarıyla Üretildi!")
        
        # Sonuçları Sekmelerde Göster
        tabs = st.tabs(list(generated_images.keys()))
        for tab, (style_name, img_url) in zip(tabs, generated_images.items()):
            with tab:
                st.image(img_url, caption=style_name, use_container_width=True)

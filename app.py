import streamlit as st
from PIL import Image
import io
import os
import replicate

st.set_page_config(
    page_title="AI Mockup Studio",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ Otomatik AI Mockup Üretici")
st.write("Tablonuzun **renklerini ve detaylarını bozmadan** yapay zeka ile modern oda mockup'ları oluşturun.")

# ---------------------------------------------------------
# API ANAHTARI KONTROLÜ (Streamlit Secrets)
# ---------------------------------------------------------
try:
    REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
except Exception:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Cloud 'Secrets' alanına REPLICATE_API_TOKEN ekleyin.")
    st.stop()

# 4 Farklı İç Mekan Konsepti
PROMPTS = {
    "1. Modern Minimalist Salon": "A high quality photo of a luxury modern minimalist living room wall, soft natural sunlight, elegant interior design, realistic photo",
    "2. İskandinav Çalışma Alanı": "A high quality photo of a cozy Scandinavian study room wall, wooden desk, indoor plants, realistic photo",
    "3. Boho Style Yatak Odası": "A high quality photo of a boho-chic bedroom interior wall, warm textures, pampas grass, realistic photo",
    "4. Sanat Galerisi Koridoru": "A high quality photo of a modern art gallery corridor wall, gallery spotlights, realistic photo"
}

uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file)
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.image(raw_img, caption="Orijinal Tablonuz", use_container_width=True)
    
    with col_right:
        st.markdown("### ⚙️ Mockup Seçenekleri")
        frame_style = st.selectbox(
            "Çerçeve Stili", 
            ["Black Wooden Frame", "Natural Oak Frame", "White Frame", "Thin Canvas"]
        )
        
        generate_btn = st.button("✨ 4 Mockup'ı Otomatik Üret", type="primary", use_container_width=True)

    if generate_btn:
        st.markdown("---")
        st.markdown("### ⏳ Yapay Zeka Görselleri Oluşturuyor...")
        progress_bar = st.progress(0)
        
        # Görseli byte formatına dönüştür
        img_bytes = io.BytesIO()
        raw_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        generated_images = {}
        
        for idx, (style_name, room_prompt) in enumerate(PROMPTS.items()):
            full_prompt = (
                f"A framed wall artwork inside a {frame_style} seamlessly hanging on the wall in this interior: {room_prompt}. "
                f"Keep the exact inner artwork untouched, 8k resolution, professional interior design photography."
            )
            
            try:
                # Replicate SDXL / ControlNet Görsel Üretimi
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
                    generated_images[style_name] = output[0]

            except Exception as e:
                st.error(f"{style_name} üretilirken bir hata oluştu: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(PROMPTS))

        if generated_images:
            st.success("✅ Tüm Mockup'lar Başarıyla Üretildi!")
            tabs = st.tabs(list(generated_images.keys()))
            for tab, (style_name, img_url) in zip(tabs, generated_images.items()):
                with tab:
                    st.image(img_url, caption=style_name, use_container_width=True)

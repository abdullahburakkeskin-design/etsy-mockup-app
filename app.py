import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import io
import requests

st.set_page_config(
    page_title="AI Art Studio - Yapay Zeka Mockup",
    page_icon="🖼️",
    layout="wide"
)

# ---------------------------------------------------------
# HUGGING FACE INFERENCE API (GÜVENLİ SECRETS BAĞLANTISI)
# ---------------------------------------------------------
# Token koda yazılmaz, Streamlit Secrets alanından çekilir
HF_TOKEN = st.secrets.get("HF_TOKEN", "")

def generate_ai_room_hf(prompt):
    """
    Hugging Face API üzerinden FLUX modelini kullanarak fotogerçekçi oda çizer.
    """
    if not HF_TOKEN:
        st.error("🔑 Hugging Face Token bulunamadı. Lütfen Streamlit ayarlarındaki Secrets alanına HF_TOKEN değişkenini tanımlayın.")
        return None

    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {"width": 1024, "height": 768}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
        elif response.status_code == 503:
            st.info("ℹ️ Yapay zeka modeli başlatılıyor, lütfen 5 saniye sonra tekrar deneyin.")
            return None
        else:
            st.error(f"API Hatası (Kod: {response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Bağlantı Hatası: {str(e)}")
        return None

# ---------------------------------------------------------
# ÇERÇEVE VE DERİNLİK GÖLGESİ
# ---------------------------------------------------------
def prepare_framed_artwork(art_img, frame_type, frame_thickness_ratio=0.03):
    w, h = art_img.size
    border_px = int(max(w, h) * frame_thickness_ratio)
    
    frame_colors = {
        "Siyah Ahşap": (22, 22, 22),
        "Doğal Meşe Ahşap": (165, 113, 78),
        "Beyaz Minimal": (245, 245, 245),
        "Koyu Ceviz": (65, 38, 25)
    }
    
    bg_color = frame_colors.get(frame_type, (22, 22, 22))
    
    passepartout_size = int(border_px * 0.8)
    art_with_pass = ImageOps.expand(art_img, border=passepartout_size, fill=(250, 250, 248))
    framed = ImageOps.expand(art_with_pass, border=border_px, fill=bg_color)
    
    shadow_pad = int(max(framed.size) * 0.08)
    canvas_w = framed.width + shadow_pad * 2
    canvas_h = framed.height + shadow_pad * 2
    
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", framed.size, (0, 0, 0, 110))
    shadow_blur = ImageFilter.GaussianBlur(radius=int(shadow_pad * 0.45))
    
    canvas.paste(shadow, (shadow_pad + int(shadow_pad*0.2), shadow_pad + int(shadow_pad*0.3)))
    canvas = canvas.filter(shadow_blur)
    canvas.paste(framed, (shadow_pad, shadow_pad))
    
    return canvas

# ---------------------------------------------------------
# ARAYÜZ
# ---------------------------------------------------------
st.title("🖼️ AI Art Studio: Yapay Zeka Tabanlı Fotogerçekçi Mockup")
st.write("FLUX.1 Yapay zeka modelini kullanarak tablonuzu fotogerçekçi iç mekan ve galeri tasarımlarına dönüştürün.")

uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.image(raw_img, caption="Orijinal Tablonuz", use_container_width=True)
        
    with col_r:
        st.markdown("### 🎨 Yapay Zeka İç Mekan Tasarımı")
        
        style_preset = st.selectbox(
            "Yapay Zeka Oda Konsepti",
            [
                "Modern İskandinav Salonu (Aydınlık, Ahşap Mobilyalar, Bitkiler)",
                "Lüks Minimalist Galeri Duvarı (Stüdyo Işıklandırması)",
                "Boho Chic Yatak Odası (Sıcak Tonlar, Doğal Gün Işığı)",
                "Endüstriyel Loft Daire (Tuğla / Beton Duvar, Deri Koltuk)"
            ]
        )
        
        frame_choice = st.selectbox(
            "Çerçeve Stili", 
            ["Siyah Ahşap", "Doğal Meşe Ahşap", "Beyaz Minimal", "Koyu Ceviz"]
        )
        
        generate_btn = st.button("🚀 Yapay Zeka ile Mockup Oluştur", type="primary", use_container_width=True)

    if generate_btn:
        with st.spinner("🤖 FLUX Yapay zeka modeli mekanı çiziyor... (Yaklaşık 5-8 sn)"):
            prompts_map = {
                "Modern İskandinav Salonu (Aydınlık, Ahşap Mobilyalar, Bitkiler)": "A bright modern Scandinavian living room interior, neutral wall, oak wood furniture, green plants, natural sunlight, architectural digest photo, photorealistic 8k",
                "Lüks Minimalist Galeri Duvarı (Stüdyo Işıklandırması)": "A minimalist art gallery room, museum spotlighting, clean beige wall, soft shadows, 8k professional interior photography",
                "Boho Chic Yatak Odası (Sıcak Tonlar, Doğal Gün Işığı)": "A cozy boho chic bedroom interior, warm cream wall, rattan decorative items, warm morning sun, photorealistic 8k",
                "Endüstriyel Loft Daire (Tuğla / Beton Duvar, Deri Koltuk)": "An industrial loft living room with concrete wall, leather sofa, soft ambient lighting, modern architecture, 8k photo"
            }
            
            selected_prompt = prompts_map.get(style_preset)
            
            ai_room_bg = generate_ai_room_hf(selected_prompt)
            
            if ai_room_bg is not None:
                framed_canvas = prepare_framed_artwork(raw_img, frame_choice)
                
                wall_w, wall_h = ai_room_bg.size
                target_h = int(wall_h * 0.45)
                aspect = framed_canvas.width / framed_canvas.height
                target_w = int(target_h * aspect)
                
                scaled_artwork = framed_canvas.resize((target_w, target_h), Image.Resampling.LANCZOS)
                
                pos_x = (wall_w - target_w) // 2
                pos_y = (wall_h - target_h) // 2 - int(wall_h * 0.05)
                
                ai_room_bg.paste(scaled_artwork, (pos_x, pos_y), scaled_artwork)
                final_result = ai_room_bg.convert("RGB")
                
                st.success("✅ FLUX Yapay Zeka Mockup'ınız Başarıyla Hazırlandı!")
                st.image(final_result, caption=f"AI Üretimi: {style_preset}", use_container_width=True)
                
                buf = io.BytesIO()
                final_result.save(buf, format="JPEG", quality=95)
                st.download_button(
                    label="📥 Yüksek Çözünürlüklü Mockup'ı İndir",
                    data=buf.getvalue(),
                    file_name="ai_mockup_result.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )

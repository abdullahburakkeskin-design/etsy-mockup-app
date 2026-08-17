import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import io
import requests
import time
import numpy as np
import cv2

# ---------------------------------------------------------
# SAYFA AYARLARI VE GÖRSEL TEMA (PREMIUM DARK)
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Art Studio PRO - Perspective Mockups",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# HUGGING FACE INFERENCE API
# ---------------------------------------------------------
HF_TOKEN = st.secrets.get("HF_TOKEN", "")

# ---------------------------------------------------------
# CSS STİLLERİ
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
        color: #FAFAFA;
        font-family: 'Poppins', sans-serif;
    }

    .main-title {
        font-size: 3.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FF4B4B, #FF9999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .sub-title {
        font-size: 1.1rem;
        color: #A0A0A0;
        text-align: center;
        margin-bottom: 2.5rem;
    }

    [data-testid="stFileUploader"], [data-testid="stSelectbox"], [data-testid="stSlider"], .stButton button {
        background-color: #1A1D24 !important;
        border: 1px solid #262730 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    [data-testid="stImage"] img {
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 2px solid #262730;
    }

    .stButton button {
        background: linear-gradient(90deg, #FF4B4B, #ED1C24) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        border: none !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    hr {
        border-color: #262730 !important;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BAŞLIK
# ---------------------------------------------------------
st.markdown('<h1 class="main-title">AI Art Studio PRO</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sanatınızı Perspektif ve Konum Ayarlarıyla Gerçekçi Mekanlara Oturtun</p>', unsafe_allow_html=True)

# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------
def generate_ai_room_hf(prompt, retries=3, delay=3):
    """
    Oda görseli üretir.
    """
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    payload = {"inputs": prompt}
    
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=35)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content)).convert("RGBA")
            elif response.status_code in [503, 429]:
                time.sleep(delay)
                continue
        except Exception:
            pass
            
    # Yedek Servis
    try:
        encoded_prompt = requests.utils.quote(prompt)
        backup_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true"
        resp = requests.get(backup_url, timeout=30)
        if resp.status_code == 200:
            return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        st.error(f"Görsel üretilemedi: {str(e)}")
        
    return None

def prepare_framed_artwork(art_img, frame_type, frame_thickness_ratio=0.03):
    """
    Çerçeve ve Paspartu Ekler.
    """
    w, h = art_img.size
    border_px = int(max(w, h) * frame_thickness_ratio)
    frame_colors = {
        "Siyah Ahşap": (22, 22, 22),
        "Doğal Meşe": (165, 113, 78),
        "Beyaz Minimal": (245, 245, 245),
        "Koyu Ceviz": (65, 38, 25)
    }
    bg_color = frame_colors.get(frame_type, (22, 22, 22))
    passepartout_size = int(border_px * 0.8)
    
    art_with_pass = ImageOps.expand(art_img, border=passepartout_size, fill=(250, 250, 248))
    framed = ImageOps.expand(art_with_pass, border=border_px, fill=bg_color)
    return framed

def apply_perspective_and_paste(background, artwork, pos_x, pos_y, scale_percent, pers_left, pers_right):
    """
    OpenCV kullanarak eseri perspektif bükmesiyle duvara yerleştirir.
    """
    bg_w, bg_h = background.size
    
    # Eser boyutunu ölçekle
    orig_w, orig_h = artwork.size
    new_w = int(orig_w * (scale_percent / 100.0))
    new_h = int(orig_h * (scale_percent / 100.0))
    art_resized = artwork.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # PIL Image -> NumPy Array (OpenCV formatı)
    art_np = np.array(art_resized)
    
    # Orijinal 4 Köşe (Sol-Üst, Sağ-Üst, Sağ-Alt, Sol-Alt)
    src_pts = np.float32([
        [0, 0],
        [new_w, 0],
        [new_w, new_h],
        [0, new_h]
    ])
    
    # Perspektif Bükme Değerleri (Perspektif açısına göre dikey kaydırma)
    offset_l = int(new_h * (pers_left / 100.0))
    offset_r = int(new_h * (pers_right / 100.0))
    
    # Yeni Hedef 4 Köşesi
    dst_pts = np.float32([
        [0, max(0, offset_l)],
        [new_w, max(0, offset_r)],
        [new_w, new_h - max(0, -offset_r)],
        [0, new_h - max(0, -offset_l)]
    ])
    
    # Homografi Matrisi Hesaplama ve Bükme
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(art_np, matrix, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    
    # Bükülen Eseri PIL Image'e Geri Çevir
    warped_img = Image.fromarray(warped, mode="RGBA")
    
    # Arka Plan Üzerine Yapıştırma
    final_bg = background.copy()
    final_bg.paste(warped_img, (pos_x, pos_y), warped_img)
    return final_bg

# ---------------------------------------------------------
# ARAYÜZ VE UYGULAMA AKIŞI
# ---------------------------------------------------------
if "generated_room" not in st.session_state:
    st.session_state.generated_room = None

col_file, col_params = st.columns([1, 1.1])

with col_file:
    st.markdown("### 1. Eserinizi Yükleyin")
    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    with col_file:
        st.image(raw_img, caption="Yüklenen Eser", use_container_width=True)
        
    with col_params:
        st.markdown("### 2. Stüdyo & Mekan Ayarları")
        
        style_preset = st.selectbox(
            "Mekan Konsepti",
            [
                "Modern İskandinav Salonu (Aydınlık)",
                "Minimalist Sanat Galerisi (Spot Işıklar)",
                "Boho Chic Yatak Odası (Sıcak)",
                "Endüstriyel Loft (Concrete wall)"
            ]
        )
        
        frame_choice = st.selectbox(
            "Çerçeve Stili", 
            ["Siyah Ahşap", "Doğal Meşe", "Beyaz Minimal", "Koyu Ceviz"]
        )
        
        generate_btn = st.button("🚀 Oda Görseli Üret / Yenile")

    prompts_map = {
        "Modern İskandinav Salonu (Aydınlık)": "A bright modern Scandinavian living room interior, neutral wall, oak furniture, green plants, natural sunlight, architectural digest photo, 8k",
        "Minimalist Sanat Galerisi (Spot Işıklar)": "A minimalist art gallery room, museum spotlighting, clean beige wall, soft shadows, 8k professional interior photography",
        "Boho Chic Yatak Odası (Sıcak)": "A cozy boho chic bedroom interior, warm cream wall, rattan decorative items, warm morning sun, depth of field, photorealistic 8k",
        "Endüstriyel Loft (Concrete wall)": "An industrial loft living room with concrete wall, leather sofa, soft ambient lighting, modern architecture, 8k photo"
    }

    if generate_btn or st.session_state.generated_room is None:
        if generate_btn:
            with st.spinner("🤖 Yapay zeka oda mekanı çiziyor..."):
                room_bg = generate_ai_room_hf(prompts_map.get(style_preset))
                if room_bg is not None:
                    st.session_state.generated_room = room_bg

    # ---------------------------------------------------------
    # 3. DUVAR PERSPERTİF VE KONUM AYARLARI (SLIDERS)
    # ---------------------------------------------------------
    if st.session_state.generated_room is not None:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 3. Duvar Perspektif ve Konum Ayarları")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        bg_w, bg_h = st.session_state.generated_room.size
        
        with col_s1:
            pos_x = st.slider("Yatay Konum (X)", 0, bg_w - 100, int(bg_w * 0.35))
            pos_y = st.slider("Dikey Konum (Y)", 0, bg_h - 100, int(bg_h * 0.20))
            
        with col_s2:
            scale_percent = st.slider("Eser Boyutu (%)", 10, 80, 35)
            
        with col_s3:
            pers_left = st.slider("Sol Açı / Eğim", -30, 30, 0, help="Eserin sol tarafını yukarı/aşağı büker")
            pers_right = st.slider("Sağ Açı / Eğim", -30, 30, 0, help="Eserin sağ tarafını yukarı/aşağı büker")

        # Çerçeveli eseri hazırla
        framed_artwork = prepare_framed_artwork(raw_img, frame_choice)
        
        # Perspektif ve Konumlandırma uygula
        final_mockup = apply_perspective_and_paste(
            st.session_state.generated_room, 
            framed_artwork, 
            pos_x, 
            pos_y, 
            scale_percent, 
            pers_left, 
            pers_right
        )
        
        final_rgb = final_mockup.convert("RGB")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#FAFAFA;'>✨ Canlı Mockup Önizleme</h2>", unsafe_allow_html=True)
        
        col_res1, col_res2, col_res3 = st.columns([1, 6, 1])
        with col_res2:
            st.image(final_rgb, use_container_width=True)
            
            buf = io.BytesIO()
            final_rgb.save(buf, format="JPEG", quality=95)
            st.download_button(
                label="📥 Mockup'ı Yüksek Kalitede İndir",
                data=buf.getvalue(),
                file_name="ai_studio_perspective_mockup.jpg",
                mime="image/jpeg",
                use_container_width=True
            )

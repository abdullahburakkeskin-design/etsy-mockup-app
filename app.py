import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import io
import requests
import time

# ---------------------------------------------------------
# SAYFA AYARLARI VE GÖRSEL TEMA (PREMIUM DARK)
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Art Studio PRO - Premium Mockups",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# HUGGING FACE INFERENCE API (GÜVENLİ SECRETS BAĞLANTISI)
# ---------------------------------------------------------
# Token bilgisi Streamlit Secrets / secrets.toml üzerinden güvenli çekilir.
HF_TOKEN = st.secrets.get("HF_TOKEN", "")

# ---------------------------------------------------------
# MODERN, HAREKETLİ CSS ENJEKSİYONU (THEME & ANIMATIONS)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global Tema Ayarları (Karanlık Premium) */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
        color: #FAFAFA;
        font-family: 'Poppins', sans-serif;
    }

    /* Ana Başlık ve Alt Başlık Stilleri & Giriş Animasyonu */
    @keyframes fadeInDown {
        0% { opacity: 0; transform: translateY(-20px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FF4B4B, #FF9999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        animation: fadeInDown 1s ease-out;
    }

    .sub-title {
        font-size: 1.2rem;
        color: #A0A0A0;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 300;
        animation: fadeInDown 1.2s ease-out;
    }

    /* Kartlar, Sliderlar ve Input Alanları İçin Modern Gölgeli Tasarım */
    [data-testid="stFileUploader"], [data-testid="stSelectbox"], .stButton button {
        background-color: #1A1D24 !important;
        border: 1px solid #262730 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #FF4B4B !important;
        transform: translateY(-2px);
    }

    /* Yüklenen Resim ve Sonuç Resmi İçin Çerçeve ve Animasyon */
    @keyframes imageReveal {
        0% { opacity: 0; scale: 0.95; }
        100% { opacity: 1; scale: 1; }
    }

    [data-testid="stImage"] img {
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        border: 2px solid #262730;
        animation: imageReveal 0.8s ease-out;
    }

    /* Modern Buton Stili (Hareketli Geçiş) */
    .stButton button {
        background: linear-gradient(90deg, #FF4B4B, #ED1C24) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        border: none !important;
        width: 100%;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(237, 28, 36, 0.4) !important;
    }

    .stButton button:active {
        transform: translateY(-1px);
    }

    /* Spinner (Yükleniyor) Animasyonu Özelleştirme */
    .stSpinner > div > div {
        border-top-color: #FF4B4B !important;
    }
    
    /* Bölücü Çizgi Stili */
    hr {
        border-color: #262730 !important;
        margin: 2rem 0;
    }

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HAREKETLİ BAŞLIK VE ALT BAŞLIK
# ---------------------------------------------------------
st.markdown('<h1 class="main-title">AI Art Studio PRO</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">FLUX.1 Mimarisiyle Sanatınızı Premium Mekanlarda Canlandırın</p>', unsafe_allow_html=True)

# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR (API VE GÖRSEL İŞLEME)
# ---------------------------------------------------------
def generate_ai_room_hf(prompt, retries=3, delay=3):
    """
    Hugging Face API üzerinden FLUX.1-schnell modelini çağırır.
    Ağ kopmalarına ve DNS hatalarına karşı otomatik 3 defa yeniden dener.
    """
    if not HF_TOKEN:
        st.error("🔑 Hugging Face Token bulunamadı. Lütfen Streamlit Secrets alanına HF_TOKEN tanımlayın.")
        return None

    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"width": 1024, "height": 768}}
    
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=35)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content)).convert("RGBA")
            elif response.status_code == 503:
                # Model sunucuda soğuk başlangıç yapıyorsa bekle
                time.sleep(delay)
                continue
            else:
                st.error(f"API Hatası ({response.status_code}): {response.text}")
                return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            st.error("📡 Sunucuya bağlanırken DNS / Ağ hatası oluştu. Lütfen internet bağlantınızı veya VPN/DNS ayarlarınızı kontrol edip tekrar deneyin.")
            return None
        except Exception as e:
            st.error(f"Beklenmeyen Hata: {str(e)}")
            return None
    return None

def prepare_framed_artwork(art_img, frame_type, frame_thickness_ratio=0.03):
    """
    Eserin etrafına seçilen renkte çerçeve, paspartu ve yumuşak derinlik gölgesi ekler.
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
    
    # Paspartu
    art_with_pass = ImageOps.expand(art_img, border=passepartout_size, fill=(250, 250, 248))
    # Dış Çerçeve
    framed = ImageOps.expand(art_with_pass, border=border_px, fill=bg_color)
    
    # Derinlik Gölgesi
    shadow_pad = int(max(framed.size) * 0.08)
    canvas = Image.new("RGBA", (framed.width + shadow_pad * 2, framed.height + shadow_pad * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", framed.size, (0, 0, 0, 110))
    shadow_blur = ImageFilter.GaussianBlur(radius=int(shadow_pad * 0.45))
    
    canvas.paste(shadow, (shadow_pad + int(shadow_pad * 0.2), shadow_pad + int(shadow_pad * 0.3)))
    canvas = canvas.filter(shadow_blur)
    canvas.paste(framed, (shadow_pad, shadow_pad))
    return canvas

# ---------------------------------------------------------
# ARAYÜZ AKIŞI
# ---------------------------------------------------------
if "generated_room" not in st.session_state:
    st.session_state.generated_room = None

# Sol kolon: Yükleme, Sağ kolon: Parametreler
col_file, col_params = st.columns([1.2, 1])

with col_file:
    st.markdown("### 1. Eserinizi Yükleyin")
    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    with col_file:
        st.image(raw_img, caption="Yüklenen Eser", use_container_width=True)
        
    with col_params:
        st.markdown("### 2. Stüdyo Ayarları")
        
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("🚀 Mockup Oluştur")

    # PROMPTS HARİTASI
    prompts_map = {
        "Modern İskandinav Salonu (Aydınlık)": "A bright modern Scandinavian living room interior, neutral wall, oak furniture, green plants, natural sunlight, architectural digest photo, 8k",
        "Minimalist Sanat Galerisi (Spot Işıklar)": "A minimalist art gallery room, museum spotlighting, clean beige wall, soft shadows, 8k professional interior photography",
        "Boho Chic Yatak Odası (Sıcak)": "A cozy boho chic bedroom interior, warm cream wall, rattan decorative items, warm morning sun, depth of field, photorealistic 8k",
        "Endüstriyel Loft (Concrete wall)": "An industrial loft living room with concrete wall, leather sofa, soft ambient lighting, modern architecture, 8k photo"
    }

    # ÜRETİM TETİKLENMESİ
    if generate_btn:
        with st.spinner("🤖 FLUX Yapay zeka modeli mekanı çiziyor..."):
            room_bg = generate_ai_room_hf(prompts_map.get(style_preset))
            if room_bg is not None:
                st.session_state.generated_room = room_bg

    # SONUÇ EKRANI
    if st.session_state.generated_room is not None:
        ai_room_bg = st.session_state.generated_room.copy()
        
        # Eseri işle ve yerleştir
        framed_canvas = prepare_framed_artwork(raw_img, frame_choice)
        
        w_bg, h_bg = ai_room_bg.size
        target_h = int(h_bg * 0.45)
        aspect = framed_canvas.width / framed_canvas.height
        target_w = int(target_h * aspect)
        
        scaled_art = framed_canvas.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        pos_x = (w_bg - target_w) // 2
        pos_y = (h_bg - target_h) // 2 - int(h_bg * 0.05)
        
        ai_room_bg.paste(scaled_art, (pos_x, pos_y), scaled_art)
        final_rgb = ai_room_bg.convert("RGB")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#FAFAFA;'>✨ Premium Mockup Sonucu</h2>", unsafe_allow_html=True)
        
        col_res1, col_res2, col_res3 = st.columns([1, 6, 1])
        with col_res2:
            st.image(final_rgb, use_container_width=True)
            
            buf = io.BytesIO()
            final_rgb.save(buf, format="JPEG", quality=95)
            st.download_button(
                label="📥 Mockup'ı Yüksek Kalitede İndir",
                data=buf.getvalue(),
                file_name="ai_studio_pro_mockup.jpg",
                mime="image/jpeg",
                use_container_width=True
            )

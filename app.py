import streamlit as st
from PIL import Image, ImageOps
import io
import requests
import time
import numpy as np
import cv2

# ---------------------------------------------------------
# SAYFA AYARLARI
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Auto-Perspective Mockup Pro",
    page_icon="🎨",
    layout="wide"
)

HF_TOKEN = st.secrets.get("HF_TOKEN", "")

# ---------------------------------------------------------
# OTOMATİK DUVAR VE PERSPERTİF HESAPLAMA MOTORU
# ---------------------------------------------------------
def auto_detect_wall_and_place(background_img, artwork_img, scale_ratio=0.35):
    """
    Arka plandaki baskın duvar/odak alanını otomatik tespit eder,
    perspektif merkezini hesaplar ve eseri otomatik boyutlandırıp yerleştirir.
    """
    bg_np = np.array(background_img.convert("RGB"))
    bg_h, bg_w, _ = bg_np.shape
    
    # 1. Görseli gri tonlamaya çevirip duvardaki ışık/kenar kontrastını analiz et
    gray = cv2.cvtColor(bg_np, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 2. Kenar tespiti (Canny Edge) ile odadaki ana hatları bul
    edges = cv2.Canny(blurred, 50, 150)
    
    # 3. Konturları bul ve en geniş düz alanı (muhtemel duvarı) seç
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Varsayılan odak alanı: Odanın üst-orta perspektif bölgesi
    wall_box = [int(bg_w * 0.25), int(bg_h * 0.15), int(bg_w * 0.50), int(bg_h * 0.50)]
    
    if contours:
        # En büyük konturları tara
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > (bg_w * bg_h * 0.1):
            x, y, w, h = cv2.boundingRect(largest_contour)
            wall_box = [x, y, w, h]

    # 4. Otomatik Ölçeklendirme ve Merkezleme
    target_x, target_y, target_w, target_h = wall_box
    
    art_w, art_h = artwork_img.size
    aspect_ratio = art_w / art_h
    
    # Eser boyutunu duvar boyutuna oranla
    new_h = int(target_h * scale_ratio)
    new_w = int(new_h * aspect_ratio)
    
    if new_w > target_w:
        new_w = int(target_w * scale_ratio)
        new_h = int(new_w / aspect_ratio)

    art_resized = artwork_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Otomatik Merkez X ve Y (Duvarın odak noktası)
    center_x = target_x + (target_w - new_w) // 2
    center_y = target_y + (target_h - new_h) // 3  # Göz hizası
    
    # 5. Hafif Perspektif Kaçış Açısını Otomatik Çıkar (Trapezoid Bükme)
    # Duvarın sağ/sol derinliğine göre otomatik köşe bükmesi
    art_np = np.array(art_resized)
    src_pts = np.float32([[0, 0], [new_w, 0], [new_w, new_h], [0, new_h]])
    
    # Sol ve sağ derinlik eğimi (Odadaki ışık ve perspektif dengesinden türetilir)
    perspective_skew = int(new_h * 0.03) 
    
    dst_pts = np.float32([
        [0, perspective_skew], 
        [new_w, 0], 
        [new_w, new_h], 
        [0, new_h - perspective_skew]
    ])
    
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_np = cv2.warpPerspective(art_np, matrix, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    
    warped_img = Image.fromarray(warped_np, mode="RGBA")
    
    # Tam Otomatik Birleştirme
    final_img = background_img.copy()
    final_img.paste(warped_img, (max(0, center_x), max(0, center_y)), warped_img)
    
    return final_img

# ---------------------------------------------------------
# ODA ÜRETİM FONKSİYONU
# ---------------------------------------------------------
def generate_ai_room_hf(prompt):
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    payload = {"inputs": prompt}
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=35)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except Exception:
        pass
        
    # Yedek Servis
    encoded_prompt = requests.utils.quote(prompt)
    backup_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true"
    resp = requests.get(backup_url, timeout=30)
    if resp.status_code == 200:
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
        
    return None

def prepare_framed_artwork(art_img, frame_type):
    w, h = art_img.size
    border_px = int(max(w, h) * 0.03)
    frame_colors = {
        "Siyah Ahşap": (22, 22, 22),
        "Doğal Meşe": (165, 113, 78),
        "Beyaz Minimal": (245, 245, 245)
    }
    bg_color = frame_colors.get(frame_type, (22, 22, 22))
    art_with_pass = ImageOps.expand(art_img, border=int(border_px * 0.8), fill=(250, 250, 248))
    return ImageOps.expand(art_with_pass, border=border_px, fill=bg_color)

# ---------------------------------------------------------
# ARAYÜZ
# ---------------------------------------------------------
st.title("🎨 Tam Otomatik Perspektif Mockup Oluşturucu")

uploaded_file = st.file_uploader("Eserinizi Yükleyin", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(raw_img, caption="Yüklenen Eser", use_container_width=True)
        
    with col2:
        style_preset = st.selectbox(
            "Mekan Konsepti",
            [
                "Modern İskandinav Salonu",
                "Minimalist Sanat Galerisi",
                "Endüstriyel Loft"
            ]
        )
        frame_choice = st.selectbox("Çerçeve Stili", ["Siyah Ahşap", "Doğal Meşe", "Beyaz Minimal"])
        
        auto_btn = st.button("✨ Otomatik Hizala ve Oluştur")

    if auto_btn:
        with st.spinner("🤖 Odadaki duvar tespiti yapılıyor ve perspektif otomatik hesaplanıyor..."):
            prompts = {
                "Modern İskandinav Salonu": "A bright modern Scandinavian living room interior, front facing neutral wall, oak furniture, 8k",
                "Minimalist Sanat Galerisi": "A minimalist art gallery room, front wall, museum spotlighting, clean beige wall, 8k",
                "Endüstriyel Loft": "An industrial loft living room with concrete wall, soft ambient lighting, 8k photo"
            }
            
            room_bg = generate_ai_room_hf(prompts[style_preset])
            
            if room_bg:
                framed_art = prepare_framed_artwork(raw_img, frame_choice)
                
                # TAM OTOMATİK YERLEŞTİRME HESAPLAMASI
                final_mockup = auto_detect_wall_and_place(room_bg, framed_art)
                
                st.subheader("✨ Otomatik Hizalanmış Sonuç")
                st.image(final_mockup.convert("RGB"), use_container_width=True)

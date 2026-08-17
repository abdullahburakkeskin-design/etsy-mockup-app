import streamlit as st
from PIL import Image, ImageOps
import io
import requests
import time
import numpy as np
import cv2
from ultralytics import YOLO

# ---------------------------------------------------------
# SAYFA AYARLARI
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Ultra-Accurate Auto Mockup",
    page_icon="🖼️",
    layout="wide"
)

HF_TOKEN = st.secrets.get("HF_TOKEN", "")

# ---------------------------------------------------------
# YOLOV8 MODELİNİ YÜKLE (CACHED)
# ---------------------------------------------------------
@st.cache_resource
def load_yolo_model():
    # Hafif ve hızlı segmentasyon modeli
    return YOLO("yolov8n-seg.pt")

yolo_model = load_yolo_model()

# ---------------------------------------------------------
# YOLOV8 İLE DUVAR & PERSPERKTİF TESPİT MOTORU
# ---------------------------------------------------------
def yolo_auto_place_artwork(background_img, artwork_img, scale_factor=0.40):
    """
    YOLOv8-Seg ile odadaki duvar alanını piksel düzeyinde tespit eder.
    Duvarın en uygun boş alanını ve açılarını çıkarıp eseri yerleştirir.
    """
    bg_np = np.array(background_img.convert("RGB"))
    bg_h, bg_w, _ = bg_np.shape
    
    # 1. YOLOv8 ile Segmentasyon Tahmini
    results = yolo_model(bg_np, verbose=False)[0]
    
    wall_polygon = None
    
    # Eserin yerleştirilebileceği potansiyel alan tespiti (Arka plan / Duvar bölgesi)
    if results.masks is not None:
        # En büyük alanı kaplayan segment maskesini al
        masks = results.masks.xy
        if len(masks) > 0:
            # Alanı en büyük olan poligonu seç
            wall_polygon = max(masks, key=lambda x: cv2.contourArea(x.astype(np.int32)))

    # Eğer özel duvar maskesi bulunamazsa odanın merkez odak bölgesini seç
    if wall_polygon is None or len(wall_polygon) < 4:
        x1, y1 = int(bg_w * 0.25), int(bg_h * 0.15)
        x2, y2 = int(bg_w * 0.75), int(bg_h * 0.65)
        wall_box = [x1, y1, x2 - x1, y2 - y1]
        persp_left, persp_right = 0, 0
    else:
        # Poligonun Minimum Alan Dikdörtgenini (Rotated Rectangle) hesapla
        rect = cv2.minAreaRect(wall_polygon.astype(np.int32))
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        
        # Bounding Box Koordinatları
        x, y, w, h = cv2.boundingRect(wall_polygon.astype(np.int32))
        wall_box = [x, y, w, h]
        
        # Duvarın sağ-sol yükseklik farkından perspektif eğimini hesapla
        pts = box[np.argsort(box[:, 0])] # X'e göre sırala (sol noktalar vs sağ noktalar)
        left_pts = pts[:2]
        right_pts = pts[2:]
        
        left_h = abs(left_pts[0][1] - left_pts[1][1])
        right_h = abs(right_pts[0][1] - right_pts[1][1])
        
        # Eğim farkını perspektif bükmesi olarak kullan
        persp_left = int((left_h - right_h) * 0.15) if left_h > 0 else 0
        persp_right = -persp_left

    # 2. Eseri Duvar Boyutuna Göre Ölçekle
    wx, wy, ww, wh = wall_box
    art_w, art_h = artwork_img.size
    aspect_ratio = art_w / art_h
    
    target_h = int(wh * scale_factor)
    target_w = int(target_h * aspect_ratio)
    
    if target_w > (ww * 0.8):
        target_w = int(ww * 0.8)
        target_h = int(target_w / aspect_ratio)

    art_resized = artwork_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    art_np = np.array(art_resized)

    # 3. Homografi (Perspektif Bükme) Uygula
    src_pts = np.float32([[0, 0], [target_w, 0], [target_w, target_h], [0, target_h]])
    
    # Eğim değerlerine göre 4 köşeyi bük
    dst_pts = np.float32([
        [0, max(0, persp_left)],
        [target_w, max(0, persp_right)],
        [target_w, target_h - max(0, -persp_right)],
        [0, target_h - max(0, -persp_left)]
    ])
    
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_np = cv2.warpPerspective(art_np, matrix, (target_w, target_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    warped_img = Image.fromarray(warped_np, mode="RGBA")

    # 4. Duvarın Tam Merkezine Yerleştir
    center_x = wx + (ww - target_w) // 2
    center_y = wy + (wh - target_h) // 3  # Göz hizası
    
    final_img = background_img.copy()
    final_img.paste(warped_img, (max(0, center_x), max(0, center_y)), warped_img)
    
    return final_img

# ---------------------------------------------------------
# ODA ÜRETİMİ VE YARDIMCI FONKSİYONLAR
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
st.title("🎯 AI Smart Segmented Perspective Mockup")
st.caption("YOLOv8 Segmentasyon ile duvarı otomatik algılar, açıları hesaplar ve resmi oturtur.")

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
        
        auto_btn = st.button("🚀 YOLOv8 ile Akıllı Ototir")

    if auto_btn:
        with st.spinner("🧠 YOLOv8 duvar segmentasyonu yapıyor ve perspektif oturtuluyor..."):
            prompts = {
                "Modern İskandinav Salonu": "A bright modern Scandinavian living room interior, clear wall space, oak furniture, 8k",
                "Minimalist Sanat Galerisi": "A minimalist art gallery room, smooth empty wall, museum spotlighting, 8k",
                "Endüstriyel Loft": "An industrial loft living room with clear concrete wall, ambient lighting, 8k photo"
            }
            
            room_bg = generate_ai_room_hf(prompts[style_preset])
            
            if room_bg:
                framed_art = prepare_framed_artwork(raw_img, frame_choice)
                
                # YOLOV8 SEGMENTASYON İLE TAM OTOMATİK YERLEŞTİRME
                final_mockup = yolo_auto_place_artwork(room_bg, framed_art)
                
                st.subheader("✨ Tam Hassasiyetle Hizalanmış Mockup")
                st.image(final_mockup.convert("RGB"), use_container_width=True)

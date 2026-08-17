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
    page_title="AI Smart Multi-Frame Mockup Pro",
    page_icon="🖼️",
    layout="wide"
)

HF_TOKEN = st.secrets.get("HF_TOKEN", "")

# ---------------------------------------------------------
# YOLOV8 MODELİNİ YÜKLE
# ---------------------------------------------------------
@st.cache_resource
def load_yolo_model():
    return YOLO("yolov8n-seg.pt")

yolo_model = load_yolo_model()

# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR: PARÇALAMA VE ÇERÇEVELEME
# ---------------------------------------------------------
def prepare_framed_artwork(art_img, frame_type):
    """Tek bir görsele çerçeve ve paspartu ekler."""
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

def split_and_frame_artwork(art_img, set_type, frame_type, gap_ratio=0.08):
    """
    Eseri seçilen set tipine göre (1, 2 veya 3 parça) böler,
    her parçayı çerçeveler ve aralarında boşluk olan TEK BİR SET görseli birleştirir.
    """
    w, h = art_img.size
    pieces = []
    
    num_splits = 1
    if set_type == "2'li Set (Diptik)":
        num_splits = 2
    elif set_type == "3'lü Set (Triptik)":
        num_splits = 3
        
    piece_w = w // num_splits
    
    # 1. Görseli dikey parçalara böl ve çerçevele
    for i in range(num_splits):
        crop_box = (i * piece_w, 0, (i + 1) * piece_w, h)
        cropped_piece = art_img.crop(crop_box)
        framed_piece = prepare_framed_artwork(cropped_piece, frame_type)
        pieces.append(framed_piece)
        
    if num_splits == 1:
        return pieces[0]
        
    # 2. Çerçeveli parçaları yan yana boşluk bırakarak birleştir
    single_fw, single_fh = pieces[0].size
    gap_px = int(single_fw * gap_ratio)
    
    total_set_w = (single_fw * num_splits) + (gap_px * (num_splits - 1))
    total_set_h = single_fh
    
    # Saydam tuval oluştur
    set_canvas = Image.new("RGBA", (total_set_w, total_set_h), (0, 0, 0, 0))
    
    current_x = 0
    for p in pieces:
        set_canvas.paste(p, (current_x, 0), p)
        current_x += single_fw + gap_px
        
    return set_canvas

# ---------------------------------------------------------
# DUVAR TESPİT VE SET YERLEŞTİRME MOTORU
# ---------------------------------------------------------
def yolo_auto_place_set(background_img, artwork_set_img, scale_factor=0.50):
    """
    Oluşturulan tablo setini (1'li, 2'li veya 3'lü) duvarın ortasına yerleştirir.
    """
    bg_np = np.array(background_img.convert("RGB"))
    bg_h, bg_w, _ = bg_np.shape
    
    results = yolo_model(bg_np, verbose=False)[0]
    wall_polygon = None
    
    if results.masks is not None and len(results.masks.xy) > 0:
        wall_polygon = max(results.masks.xy, key=lambda x: cv2.contourArea(x.astype(np.int32)))

    if wall_polygon is None or len(wall_polygon) < 4:
        x1, y1 = int(bg_w * 0.20), int(bg_h * 0.15)
        x2, y2 = int(bg_w * 0.80), int(bg_h * 0.65)
        wall_box = [x1, y1, x2 - x1, y2 - y1]
        persp_left, persp_right = 0, 0
    else:
        rect = cv2.minAreaRect(wall_polygon.astype(np.int32))
        box = np.int32(cv2.boxPoints(rect))
        x, y, w, h = cv2.boundingRect(wall_polygon.astype(np.int32))
        wall_box = [x, y, w, h]
        
        pts = box[np.argsort(box[:, 0])]
        left_h = abs(pts[0][1] - pts[1][1])
        right_h = abs(pts[2][1] - pts[3][1])
        persp_left = int((left_h - right_h) * 0.12) if left_h > 0 else 0
        persp_right = -persp_left

    wx, wy, ww, wh = wall_box
    set_w, set_h = artwork_set_img.size
    aspect_ratio = set_w / set_h
    
    # Çoklu setlerde duvar kaplama oranını ayarla
    target_w = int(ww * scale_factor)
    target_h = int(target_w / aspect_ratio)
    
    if target_h > (wh * 0.65):
        target_h = int(wh * 0.65)
        target_w = int(target_h * aspect_ratio)

    set_resized = artwork_set_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    set_np = np.array(set_resized)

    # Perspektif Bükmesi
    src_pts = np.float32([[0, 0], [target_w, 0], [target_w, target_h], [0, target_h]])
    dst_pts = np.float32([
        [0, max(0, persp_left)],
        [target_w, max(0, persp_right)],
        [target_w, target_h - max(0, -persp_right)],
        [0, target_h - max(0, -persp_left)]
    ])
    
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_np = cv2.warpPerspective(set_np, matrix, (target_w, target_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    warped_img = Image.fromarray(warped_np, mode="RGBA")

    # Duvarın Merkez Hizasına Yerleştirme
    center_x = wx + (ww - target_w) // 2
    center_y = wy + (wh - target_h) // 3
    
    final_img = background_img.copy()
    final_img.paste(warped_img, (max(0, center_x), max(0, center_y)), warped_img)
    
    return final_img

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

# ---------------------------------------------------------
# ARAYÜZ AKIŞI
# ---------------------------------------------------------
st.title("🖼️ Galeri Duvarı & Çoklu Tablo Seti Mockup Pro")

uploaded_file = st.file_uploader("Eserinizi Yükleyin", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(raw_img, caption="Orijinal Yüklenen Eser", use_container_width=True)
        
    with col2:
        set_choice = st.radio(
            "Tablo Yerleşim Düzeni",
            ["Tek Parça", "2'li Set (Diptik)", "3'lü Set (Triptik)"],
            horizontal=True
        )
        
        style_preset = st.selectbox(
            "Mekan Konsepti",
            [
                "Modern İskandinav Salonu",
                "Minimalist Sanat Galerisi",
                "Endüstriyel Loft"
            ]
        )
        frame_choice = st.selectbox("Çerçeve Stili", ["Siyah Ahşap", "Doğal Meşe", "Beyaz Minimal"])
        
        auto_btn = st.button("🚀 Tablo Setini Oluştur ve Hizala")

    if auto_btn:
        with st.spinner("🤖 Eser parçalanıyor, çerçeveleniyor ve galeri duvarına diziliyor..."):
            prompts = {
                "Modern İskandinav Salonu": "A bright modern Scandinavian living room interior, wide empty wall space, oak furniture, 8k",
                "Minimalist Sanat Galerisi": "A minimalist art gallery room, wide clean beige wall, museum spotlighting, 8k",
                "Endüstriyel Loft": "An industrial loft living room with wide concrete wall, ambient lighting, 8k photo"
            }
            
            room_bg = generate_ai_room_hf(prompts[style_preset])
            
            if room_bg:
                # 1. Eseri parçala ve set haline getir
                artwork_set = split_and_frame_artwork(raw_img, set_choice, frame_choice)
                
                # 2. Seti duvara akıllı olarak yerleştir
                final_mockup = yolo_auto_place_set(room_bg, artwork_set)
                
                st.subheader(f"✨ Galeri Duvarı Sonucu ({set_choice})")
                st.image(final_mockup.convert("RGB"), use_container_width=True)

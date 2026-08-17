import streamlit as st
import os
import io
import requests
import numpy as np
import cv2
from PIL import Image, ImageOps
from ultralytics import YOLO

# ---------------------------------------------------------
# 1. AYARLAR & MODEL YÜKLEME (HATA KONTROLLÜ)
# ---------------------------------------------------------
st.set_page_config(page_title="Gallery Mockup", layout="wide")

@st.cache_resource
def get_model():
    # Modelin yerel dizinde olup olmadığını kontrol et
    model_path = "yolov8n-seg.pt"
    if not os.path.exists(model_path):
        # Eğer yoksa ultralytics otomatik indirir, yine de uyarı ver
        st.sidebar.warning("Model dosyası indiriliyor, lütfen bekleyin...")
    return YOLO("yolov8n-seg.pt")

try:
    yolo_model = get_model()
except Exception as e:
    st.error(f"YOLO Modeli yüklenirken hata oluştu: {e}")
    st.stop()

# ---------------------------------------------------------
# 2. GÖRSEL İŞLEME FONKSİYONLARI
# ---------------------------------------------------------
def prepare_framed_artwork(art_img, frame_type):
    border_px = int(max(art_img.size) * 0.03)
    frame_colors = {"Siyah Ahşap": (22, 22, 22), "Doğal Meşe": (165, 113, 78), "Beyaz Minimal": (245, 245, 245)}
    bg_color = frame_colors.get(frame_type, (22, 22, 22))
    img = ImageOps.expand(art_img, border=int(border_px * 0.8), fill=(250, 250, 248))
    return ImageOps.expand(img, border=border_px, fill=bg_color)

def combine_custom_artworks(image_list, frame_type):
    framed = [prepare_framed_artwork(i, frame_type) for i in image_list]
    min_h = min([p.height for p in framed])
    resized = []
    for p in framed:
        aspect = p.width / p.height
        resized.append(p.resize((int(min_h * aspect), min_h), Image.Resampling.LANCZOS))
    
    total_w = sum([p.width for p in resized]) + (len(resized) - 1) * int(min_h * 0.08)
    canvas = Image.new("RGBA", (total_w, min_h), (0, 0, 0, 0))
    curr_x = 0
    for p in resized:
        canvas.paste(p, (curr_x, 0), p)
        curr_x += p.width + int(min_h * 0.08)
    return canvas

# ---------------------------------------------------------
# 3. YERLEŞTİRME VE AI ODA ÜRETİMİ
# ---------------------------------------------------------
def yolo_auto_place_set(background_img, artwork_set_img):
    bg_np = np.array(background_img.convert("RGB"))
    results = yolo_model(bg_np, verbose=False)[0]
    
    # Duvar maskesi bul (Basitleştirilmiş)
    if results.masks is not None and len(results.masks.xy) > 0:
        mask = max(results.masks.xy, key=lambda x: cv2.contourArea(x.astype(np.int32)))
        x, y, w, h = cv2.boundingRect(mask.astype(np.int32))
    else:
        h, w = bg_np.shape[:2]
        x, y, w, h = int(w*0.2), int(h*0.2), int(w*0.6), int(h*0.5)

    # Ölçekleme
    target_w = int(w * 0.4)
    ratio = artwork_set_img.height / artwork_set_img.width
    target_h = int(target_w * ratio)
    
    art_resized = artwork_set_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Yerleştirme
    final_img = background_img.copy()
    paste_x = x + (w - target_w) // 2
    paste_y = y + (h - target_h) // 2
    final_img.paste(art_resized, (paste_x, paste_y), art_resized)
    return final_img

# ---------------------------------------------------------
# 4. ARAYÜZ
# ---------------------------------------------------------
st.title("🖼️ AI Galeri Duvarı")
layout = st.radio("Düzen", ["Tek Eser", "2'li Set", "3'lü Set"], horizontal=True)

images = []
cols = st.columns(3 if "3'lü" in layout else (2 if "2'li" in layout else 1))

for i, col in enumerate(cols):
    f = col.file_uploader(f"Eser {i+1}", type=["jpg", "png"], key=f"f{i}")
    if f: images.append(Image.open(f).convert("RGBA"))

if len(images) > 0 and st.button("🚀 Oluştur"):
    with st.spinner("AI oda oluşturuluyor..."):
        # AI Oda Üretimi (Pollinations daha hızlıdır)
        prompt = "Modern minimalist living room with empty wall"
        resp = requests.get(f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=768&nologo=true")
        room_bg = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        
        # İşleme
        combined = combine_custom_artworks(images, "Siyah Ahşap")
        final = yolo_auto_place_set(room_bg, combined)
        
        st.image(final.convert("RGB"), use_container_width=True)

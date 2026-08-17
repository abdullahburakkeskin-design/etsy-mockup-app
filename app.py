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
    page_title="AI Custom Gallery Wall Mockup",
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
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------
def prepare_framed_artwork(art_img, frame_type):
    """Tek bir görsele çerçeve ve paspartu ekler."""
    w, h = art_img.size
    border_px = int(max(w, h) * 0.03)
    frame_colors = {
        "Siyah Ahşap": (22, 22, 22),
        "Doğal Meşe": (165, 113, 78),
        "Beyaz Minimal": (245, 245, 245),
        "Koyu Ceviz": (65, 38, 25)
    }
    bg_color = frame_colors.get(frame_type, (22, 22, 22))
    art_with_pass = ImageOps.expand(art_img, border=int(border_px * 0.8), fill=(250, 250, 248))
    return ImageOps.expand(art_with_pass, border=border_px, fill=bg_color)

def combine_custom_artworks(image_list, frame_type, gap_ratio=0.08):
    """
    Yüklenen farklı eserleri çerçeveler ve yüksekliklerini eşitleyerek
    yan yana boşluklu bir galeri seti (triptik/diptik) oluşturur.
    """
    if not image_list:
        return None
        
    framed_pieces = [prepare_framed_artwork(img, frame_type) for img in image_list]
    
    # Tüm parçaların yüksekliklerini en küçük boyuta göre eşitle (orantılı)
    target_h = min([p.height for p in framed_pieces])
    resized_pieces = []
    
    for p in framed_pieces:
        aspect = p.width / p.height
        new_w = int(target_h * aspect)
        resized_pieces.append(p.resize((new_w, target_h), Image.Resampling.LANCZOS))
        
    # Toplam genişlik ve boşluk hesaplama
    total_w = sum([p.width for p in resized_pieces])
    gap_px = int(target_h * gap_ratio)
    total_gap_w = gap_px * (len(resized_pieces) - 1)
    
    canvas_w = total_w + total_gap_w
    canvas_h = target_h
    
    set_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    current_x = 0
    for p in resized_pieces:
        set_canvas.paste(p, (current_x, 0), p)
        current_x += p.width + gap_px
        
    return set_canvas

# ---------------------------------------------------------
# DUVAR TESPİT VE YERLEŞTİRME MOTORU
# ---------------------------------------------------------
def yolo_auto_place_set(background_img, artwork_set_img, scale_factor=0.50):
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
    
    target_w = int(ww * scale_factor)
    target_h = int(target_w / aspect_ratio)
    
    if target_h > (wh * 0.65):
        target_h = int(wh * 0.65)
        target_w = int(target_h * aspect_ratio)

    set_resized = artwork_set_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    set_np = np.array(set_resized)

    # Perspektif Bükme
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
st.title("🖼️ Çoklu Eser Kombinasyon Mockup Pro")
st.markdown("Seçtiğiniz düzene göre farklı eserleri ayrı ayrı yükleyin, sistem bunları galeri duvarında birleştirsin.")

# Düzen Seçimi
layout_choice = st.radio(
    "Galeri Düzeni",
    ["Tek Eser", "2'li Kombinasyon (Diptik)", "3'lü Kombinasyon (Triptik)"],
    horizontal=True
)

st.markdown("---")

uploaded_images = []

if layout_choice == "Tek Eser":
    f = st.file_uploader("Eseri Yükleyin", type=["png", "jpg", "jpeg"], key="art1")
    if f: uploaded_images.append(Image.open(f).convert("RGBA"))

elif layout_choice == "2'li Kombinasyon (Diptik)":
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        f1 = st.file_uploader("1. Eser (Sol)", type=["png", "jpg", "jpeg"], key="art1")
        if f1: uploaded_images.append(Image.open(f1).convert("RGBA"))
    with col_u2:
        f2 = st.file_uploader("2. Eser (Sağ)", type=["png", "jpg", "jpeg"], key="art2")
        if f2: uploaded_images.append(Image.open(f2).convert("RGBA"))

elif layout_choice == "3'lü Kombinasyon (Triptik)":
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        f1 = st.file_uploader("1. Eser (Sol)", type=["png", "jpg", "jpeg"], key="art1")
        if f1: uploaded_images.append(Image.open(f1).convert("RGBA"))
    with col_u2:
        f2 = st.file_uploader("2. Eser (Orta)", type=["png", "jpg", "jpeg"], key="art2")
        if f2: uploaded_images.append(Image.open(f2).convert("RGBA"))
    with col_u3:
        f3 = st.file_uploader("3. Eser (Sağ)", type=["png", "jpg", "jpeg"], key="art3")
        if f3: uploaded_images.append(Image.open(f3).convert("RGBA"))

# Gerekli sayıda eser yüklendiyse stüdyo ayarlarını aç
expected_count = 1 if layout_choice == "Tek Eser" else (2 if "2'li" in layout_choice else 3)

if len(uploaded_images) == expected_count:
    st.markdown("---")
    col_opt1, col_opt2 = st.columns(2)
    
    with col_opt1:
        style_preset = st.selectbox(
            "Mekan Konsepti",
            [
                "Modern İskandinav Salonu",
                "Minimalist Sanat Galerisi",
                "Endüstriyel Loft"
            ]
        )
    with col_opt2:
        frame_choice = st.selectbox("Çerçeve Stili", ["Siyah Ahşap", "Doğal Meşe", "Beyaz Minimal", "Koyu Ceviz"])
        
    generate_btn = st.button("🚀 Kombinasyonu Duvara Yerleştir")

    if generate_btn:
        with st.spinner("🤖 Eserler hizalanıyor, çerçeveleniyor ve akıllı duvar mekanına yerleştiriliyor..."):
            prompts = {
                "Modern İskandinav Salonu": "A bright modern Scandinavian living room interior, wide empty wall space, oak furniture, 8k",
                "Minimalist Sanat Galerisi": "A minimalist art gallery room, wide clean beige wall, museum spotlighting, 8k",
                "Endüstriyel Loft": "An industrial loft living room with wide concrete wall, ambient lighting, 8k photo"
            }
            
            room_bg = generate_ai_room_hf(prompts[style_preset])
            
            if room_bg:
                # Eserleri kombinle
                combined_set = combine_custom_artworks(uploaded_images, frame_choice)
                
                # Duvara yerleştir
                final_mockup = yolo_auto_place_set(room_bg, combined_set)
                
                st.subheader("✨ Galeri Duvarı Kombinasyon Sonucu")
                st.image(final_mockup.convert("RGB"), use_container_width=True)
                
                buf = io.BytesIO()
                final_mockup.convert("RGB").save(buf, format="JPEG", quality=95)
                st.download_button(
                    label="📥 Kombinasyon Mockup'ı İndir",
                    data=buf.getvalue(),
                    file_name="gallery_wall_mockup.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )

import streamlit as st
import io
import zipfile
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw
import os

st.set_page_config(
    page_title="Etsy Art Studio - 300 DPI 4K & Realist Mockups",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Modern CSS Styling (Keep from previous)
st.markdown("""
<style>
    /* Main Background and Fonts */
    .main {
        background-color: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom Header Banner */
    .header-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
    }
    .header-box h1 {
        color: #F8FAFC;
        font-weight: 700;
        font-size: 2.4rem;
        margin-bottom: 0.5rem;
    }
    .header-box p {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-bottom: 0;
    }

    /* Cards and Containers */
    .stCard {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 1.5rem;
    }

    /* Download Button Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Define pre-configured room backgrounds with coordinates and aspect ratio hints
ROOM_DATABASE = {
    "Luxury Bosphorus Living (Angled)": {
        "file": "luxury_bosphorus_angled.jpg",
        "coords": (1238, 280, 1960, 1160),  # Top-left and bottom-right
        "ar_hint": 0.65,  # Tall dikey
        "mat_default": 0,
    },
    "Scandinavian Living (Straight)": {
        "file": "scandi_living_straight.jpg",
        "coords": (180, 240, 1220, 1150),
        "ar_hint": 0.85, # Less dikey
        "mat_default": 35,
    },
    "Boho Desk (Close-up, Angled)": {
        "file": "boho_desk_angled.jpg",
        "coords": (210, 170, 715, 875),
        "ar_hint": 0.7,
        "mat_default": 40,
    },
    "Modern Minimal Bedroom (Perspective)": {
        "file": "minimal_bedroom_persp.jpg",
        "coords": (510, 110, 1080, 930), # Perspective warp needed
        "ar_hint": 0.6, # Very tall
        "mat_default": 0,
        "perspective": True
    },
    # Gallery Wall option for user to customize
    "Customizable Gallery Wall (Straight)": {
        "file": "custom_gallery_wall.jpg",
        "coords": (500, 200, 1500, 1000),  # Main central spot
        "ar_hint": 1.0,  # Square-ish
        "mat_default": 40,
    }
}

# Add a warning that background files are needed for real operation
st.sidebar.warning("Note: This app is a structure. In a real deployment, you would need to add high-resolution background files to a 'backgrounds' folder and configure ROOM_DATABASE.")

def load_artwork(uploaded_file):
    return Image.open(uploaded_file)

def process_image_300dpi_4k(img: Image.Image, target_long_edge=3840):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    w, h = img.size
    if max(w, h) < target_long_edge:
        if w >= h:
            new_w = target_long_edge
            new_h = int(h * (target_long_edge / w))
        else:
            new_h = target_long_edge
            new_w = int(w * (target_long_edge / h))
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        img_resized = img.copy()
        
    return img_resized

def apply_to_realist_room(artwork: Image.Image, room_config, mat_width=None, frame_width=25, frame_color=(20, 20, 20)):
    # Simulate loading a background from a folder.
    # In a real app, you would have files like 'backgrounds/luxury_bosphorus_angled.jpg'
    room_w, room_h = 2400, 1800 # High res base
    
    # In this demo, we *simulate* a background for the chosen theme.
    # In a real app, use: background = Image.open(f"backgrounds/{room_config['file']}")
    background = Image.new('RGB', (room_w, room_h), (240, 240, 240))
    draw = ImageDraw.Draw(background)
    draw.rectangle([0, 0, room_w, room_h], fill='#EFECE6') # Base wall simulation
    
    # Simulate room elements for depth (e.g., a simple sofa)
    if "Sofa" in room_config['file']:
        draw.rectangle([0, room_h-300, room_w, room_h], fill='#1E293B')
    
    # Artwork placement logic
    target_box = room_config['coords']
    target_w = target_box[2] - target_box[0]
    target_h = target_box[3] - target_box[1]
    
    # Scale artwork to fit the target box area while preserving aspect ratio
    art_w, art_h = artwork.size
    art_aspect = art_w / art_h
    
    # Determine maximum dimension
    max_dim = int(target_h)
    new_h = max_dim
    new_w = int(new_h * art_aspect)
    
    # Handle square cases better
    if target_w < new_w:
        new_w = int(target_w)
        new_h = int(new_w / art_aspect)

    art_fitted = artwork.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Mat (White Border)
    if mat_width is None:
        mat_width = room_config.get('mat_default', 35)
    
    if mat_width > 0:
        art_fitted = ImageOps.expand(art_fitted, border=mat_width, fill='#F9F9F6')
    
    # Frame
    framed_art = ImageOps.expand(art_fitted, border=frame_width, fill=frame_color)
    
    fw, fh = framed_art.size
    
    # Create realistic shadow with perspective-matched drop
    shadow_opacity = 0.4
    shadow_blur = 30
    
    shadow = Image.new('RGBA', (fw + shadow_blur*2, fh + shadow_blur*2), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle([shadow_blur, shadow_blur, fw + shadow_blur, fh + shadow_blur], fill=(0, 0, 0, int(255 * shadow_opacity)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
    
    # Position final framed art and shadow.
    # Center framed art in the target box
    pos_x = target_box[0] + (target_w - fw) // 2
    pos_y = target_box[1] + (target_h - fh) // 2
    
    # Add shadow offset (depth)
    shadow_off_x = 10
    shadow_off_y = 15
    
    # Perspective warping would happen *here* if needed, applying to both artwork and shadow.
    # We will simulate straight-on placement in this code structure.
    # Example for perspective:
    # if room_config.get('perspective'):
    #     # Define perspective coordinates
    #     persp_w, persp_h = fw * 1.05, fh * 0.95
    #     framed_art = framed_art.resize((persp_w, persp_h)) # Simple scaling for perspective simulation
    
    background.convert('RGBA')
    background.paste(shadow, (pos_x - shadow_blur + shadow_off_x, pos_y - shadow_blur + shadow_off_y), shadow)
    background.paste(framed_art, (pos_x, pos_y), framed_art.convert('RGBA'))
    
    return background.convert('RGB')

def generate_listing_set(art_img: Image.Image, mat_width):
    mockups = {}
    
    # Selection of 4 distinct and realistic mockups
    # These coordinates and setups are designed to match user request.
    
    # 1. Luxury Bosphorus (Angled, Black Frame, No Mat)
    mockups["1_Luxury_Bosphorus_Angled.jpg"] = apply_to_realist_room(
        art_img, ROOM_DATABASE["Luxury Bosphorus Living (Angled)"], mat_width=0, frame_width=15
    )
    
    # 2. Scandinavian Living (Straight, Wood Frame, Mat)
    mockups["2_Scandi_Living_Straight.jpg"] = apply_to_realist_room(
        art_img, ROOM_DATABASE["Scandinavian Living (Straight)"], mat_width=mat_width, frame_color=(195, 155, 115)
    )
    
    # 3. Boho Desk Corner (Close-up, Black Frame, Mat)
    mockups["3_Boho_Corner_Close.jpg"] = apply_to_realist_room(
        art_img, ROOM_DATABASE["Boho Desk (Close-up, Angled)"], mat_width=mat_width, frame_width=20
    )
    
    # 4. Modern Minimal Bedroom (Perspective, White Frame, No Mat)
    mockups["4_Minimal_Bedroom_Persp.jpg"] = apply_to_realist_room(
        art_img, ROOM_DATABASE["Modern Minimal Bedroom (Perspective)"], mat_width=0, frame_color=(245, 245, 242)
    )
    
    return mockups

# ----------------- STREAMLIT MODERN UI -----------------

# Header Section
st.markdown("""
<div class="header-box">
    <h1>🎨 Etsy Art Studio Pro</h1>
    <p>300 DPI 4K Master Dosya & Mobilyalı Gerçekçi Oda Mockup Hazırlayıcı (Realist Veritabanı)</p>
</div>
""", unsafe_allow_html=True)

# Main Grid Layout
col_upload, col_preview = st.columns([1, 1], gap="large")

with col_upload:
    st.markdown("### 📤 1. Tablo Görselinizi Yükleyin")
    uploaded_file = st.file_uploader(
        "PNG, JPEG veya WEBP formatında dijital sanat çalışmanızı seçin", 
        type=["jpg", "jpeg", "png", "webp"],
        help="Görseliniz otomatik olarak 300 DPI 4K çözünürlüğe yükseltilecektir."
    )
    
    if uploaded_file is not None:
        raw_img = Image.open(uploaded_file)
        st.markdown(f"""
        <div style="background-color:#F1F5F9; padding:12px 18px; border-radius:8px; border-left:4px solid #3B82F6; margin-top:10px;">
            <b>Mevcut Boyut:</b> {raw_img.size[0]} x {raw_img.size[1]} px <br>
            <b>Hedef Boyut:</b> 3840 px (4K Ultra HD @ 300 DPI)
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### ⚙️ 2. Görüntüleme Ayarları")
        
        # User Input for matting width across all generated mockups
        user_mat_w = st.number_input("Tüm Mockup'lar İçin Paspartu Genişliği (px)", min_value=0, max_value=100, value=35, help="Bazı odalar varsayılanı kullanır, ancak bu değer diğerlerini güncelleyecektir.")

        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("⚡ Tüm Listing Setini Üret (1 Master + 4 Mockup)", type="primary", use_container_width=True)

with col_preview:
    st.markdown("### 🖼️ Görsel Önizlemesi")
    if uploaded_file is not None:
        st.image(raw_img, caption="Yüklenen Orijinal Çalışma", use_container_width=True)
    else:
        st.info("Lütfen sol taraftan bir tablo görseli yükleyin.")

# İşlem Aşaması
if uploaded_file is not None and 'generate_btn' in locals() and generate_btn:
    st.markdown("---")
    with st.spinner("⏳ Görseliniz 4K 300 DPI çözünürlüğe dönüştürülüyor ve mobilyalı *gerçekçi* oda duvarlarına yerleştiriliyor..."):
        # 1. 300 DPI 4K Master Dosya
        high_res_master = process_image_300dpi_4k(raw_img, target_long_edge=3840)
        
        # 2.Listing Setini Üret
        mockup_dict = generate_listing_set(high_res_master, user_mat_w)
        
        # 3. ZIP Paketleme
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Orijinal 300 DPI JPEG
            img_byte_arr = io.BytesIO()
            high_res_master.save(img_byte_arr, format='JPEG', quality=98, dpi=(300, 300))
            zip_file.writestr("0_MASTER_ORJINAL_300DPI_4K.jpg", img_byte_arr.getvalue())
            
            # Mockup JPEG'leri
            for filename, mockup_img in mockup_dict.items():
                m_byte_arr = io.BytesIO()
                mockup_img.save(m_byte_arr, format='JPEG', quality=95, dpi=(300, 300))
                zip_file.writestr(filename, m_byte_arr.getvalue())
        
        zip_buffer.seek(0)
        
        st.markdown("### ✨ Sonuçlar Hazır!")
        
        # Download Box
        col_dl1, col_dl2 = st.columns([2, 1])
        with col_dl1:
            st.download_button(
                label="📦 1 Orjinal 300DPI JPEG + 4 Realist Mobilyalı Mockup'ı İndir (ZIP)",
                data=zip_buffer,
                file_name="Etsy_Listing_Pack_Realist.zip",
                mime="application/zip",
                use_container_width=True
            )
        with col_dl2:
            st.success("✅ 5 Görsel Hazır!")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabs Gallery
        st.markdown("### 🏛️ Listing Seti Galerisi")
        tabs = st.tabs([
            "0. 300 DPI 4K Master", 
            "1. Luxury Bosphorus", 
            "2. Scandi Living", 
            "3. Boho Corner", 
            "4. Minimal Bedroom"
        ])
        
        with tabs[0]:
            st.image(high_res_master, caption=f"300 DPI 4K JPEG Master Dosya ({high_res_master.size[0]}x{high_res_master.size[1]} px)", use_container_width=True)
        with tabs[1]:
            st.image(mockup_dict["1_Luxury_Bosphorus_Angled.jpg"], caption="Luxury Bosphorus Living Corner", use_container_width=True)
        with tabs[2]:
            st.image(mockup_dict["2_Scandi_Living_Straight.jpg"], caption="Scandinavian Living Room", use_container_width=True)
        with tabs[3]:
            st.image(mockup_dict["3_Boho_Corner_Close.jpg"], caption="Boho Corner Close-up Desk", use_container_width=True)
        with tabs[4]:
            st.image(mockup_dict["4_Minimal_Bedroom_Persp.jpg"], caption="Modern Minimal Bedroom (Angled View)", use_container_width=True)

import streamlit as st
import io
import zipfile
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw

st.set_page_config(
    page_title="Etsy Art Studio - 300 DPI 4K & Furniture Mockups",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Modern CSS Styling
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

    /* Custom Badges */
    .badge {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

def process_image_300dpi_4k(img: Image.Image, target_long_edge=3840):
    """Görseli 300 DPI ve 4K piksel boyutuna getirir."""
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

def draw_sofa(draw, width, height, sofa_color='#334155', cushion_color='#475569'):
    """Detaylı modern kanepe ve minder çizimi"""
    sofa_y = int(height * 0.62)
    sofa_w = int(width * 0.65)
    sofa_left = (width - sofa_w) // 2
    sofa_right = sofa_left + sofa_w
    sofa_h = int(height * 0.28)
    
    # Kanepe Gölgesi
    draw.ellipse([sofa_left - 30, sofa_y + sofa_h - 10, sofa_right + 30, sofa_y + sofa_h + 30], fill='#00000033')
    
    # Ahşap Ayaklar
    leg_w = 18
    for leg_x in [sofa_left + 40, sofa_left + 160, sofa_right - 160, sofa_right - 40]:
        draw.polygon([(leg_x, sofa_y + sofa_h - 20), (leg_x + leg_w, sofa_y + sofa_h - 20), 
                      (leg_x + leg_w + 10, sofa_y + sofa_h + 30), (leg_x - 5, sofa_y + sofa_h + 30)], fill='#5C4033')
    
    # Kanepe Sırtlığı (Backrest)
    draw.rounded_rectangle([sofa_left, sofa_y, sofa_right, sofa_y + sofa_h - 40], radius=25, fill=sofa_color)
    
    # Oturma Minderleri (Seat Cushions - 3 Bölme)
    seat_y = sofa_y + int(sofa_h * 0.45)
    seat_h = int(sofa_h * 0.45)
    cushion_w = (sofa_w - 60) // 3
    for i in range(3):
        cx = sofa_left + 30 + i * (cushion_w + 5)
        draw.rounded_rectangle([cx, seat_y, cx + cushion_w, seat_y + seat_h], radius=15, fill=cushion_color, outline='#1E293B', width=2)
    
    # Kolçaklar (Armrests)
    draw.rounded_rectangle([sofa_left - 20, sofa_y + 30, sofa_left + 45, sofa_y + sofa_h], radius=18, fill=sofa_color, outline='#1E293B', width=2)
    draw.rounded_rectangle([sofa_right - 45, sofa_y + 30, sofa_right + 20, sofa_y + sofa_h], radius=18, fill=sofa_color, outline='#1E293B', width=2)
    
    # Kırlentler (Accent Pillows)
    draw.rounded_rectangle([sofa_left + 50, seat_y - 45, sofa_left + 140, seat_y + 30], radius=10, fill='#EAB308')  # Hardal Sarısı Kırlent
    draw.rounded_rectangle([sofa_right - 140, seat_y - 45, sofa_right - 50, seat_y + 30], radius=10, fill='#94A3B8')  # Gri Kırlent

def draw_armchair(draw, width, height):
    """Tekli berjer/sandalye detayları çizimi"""
    chair_x = int(width * 0.30)
    chair_y = int(height * 0.60)
    chair_w = int(width * 0.40)
    chair_h = int(height * 0.32)
    
    # Gölge
    draw.ellipse([chair_x - 20, chair_y + chair_h - 10, chair_x + chair_w + 20, chair_y + chair_h + 25], fill='#00000022')
    
    # Ayaklar
    for leg_x in [chair_x + 30, chair_x + chair_w - 40]:
        draw.polygon([(leg_x, chair_y + chair_h - 20), (leg_x + 12, chair_y + chair_h - 20), 
                      (leg_x + 20, chair_y + chair_h + 35), (leg_x - 8, chair_y + chair_h + 35)], fill='#3D2314')
        
    # Gövde
    draw.rounded_rectangle([chair_x, chair_y, chair_x + chair_w, chair_y + chair_h - 20], radius=30, fill='#D97706')  # Taba Rengi Deri
    draw.rounded_rectangle([chair_x + 35, chair_y + 25, chair_x + chair_w - 35, chair_y + chair_h - 30], radius=15, fill='#B45309')

def draw_plant_and_lamp(draw, width, height):
    """Yan sehpa, saksı bitkisi ve lambader detayları"""
    # Sol Taraf: Lambader
    lamp_x = int(width * 0.12)
    draw.line([(lamp_x, height * 0.35), (lamp_x, height * 0.85)], fill='#1E293B', width=6)  # Gövde
    draw.polygon([(lamp_x - 40, height * 0.85), (lamp_x + 40, height * 0.85), (lamp_x, height * 0.83)], fill='#1E293B')  # Taban
    draw.polygon([(lamp_x - 50, height * 0.45), (lamp_x + 50, height * 0.45), (lamp_x - 35, height * 0.32), (lamp_x + 35, height * 0.32)], fill='#F8FAFC')  # Başlık
    
    # Sağ Taraf: Saksı Bitkisi (Monstera / Deve Tabanı)
    plant_x = int(width * 0.86)
    plant_y = int(height * 0.68)
    draw.rounded_rectangle([plant_x - 35, plant_y, plant_x + 35, plant_y + 80], radius=10, fill='#E2E8F0')  # Beyaz Seramik Saksı
    
    # Yapraklar
    leaves = [
        (plant_x, plant_y - 30, 45), (plant_x - 30, plant_y - 60, 50),
        (plant_x + 35, plant_y - 50, 40), (plant_x - 15, plant_y - 90, 55),
        (plant_x + 20, plant_y - 80, 48)
    ]
    for lx, ly, r in leaves:
        draw.ellipse([lx - r, ly - r//2, lx + r, ly + r//2], fill='#15803D')

def create_modern_interior(theme_name, width=2400, height=1800):
    """ Kanepe, sandalye ve sehpa detaylarıyla zenginleştirilmiş modern oda iç mekanı """
    bg = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(bg)
    
    if theme_name == "Modern Velvet Lounge":
        # Sıcak Bej Duvar & Lamine Ahşap Parke
        draw.rectangle([0, 0, width, height * 0.73], fill='#EFECE6')  # Bej Duvar
        draw.rectangle([0, height * 0.73, width, height], fill='#A38260')  # Ahşap Zemin
        # Süpürgelik
        draw.rectangle([0, height * 0.72, width, height * 0.73], fill='#FFFFFF')
        # Parke derz çizgileri
        for y in range(int(height * 0.73), height, 50):
            draw.line([(0, y), (width, y)], fill='#8C6D4C', width=2)
        
        # Mobilyalar
        draw_sofa(draw, width, height, sofa_color='#1E293B', cushion_color='#334155')  # Lacivert Modern Kanepe
        draw_plant_and_lamp(draw, width, height)

    elif theme_name == "Scandi Oak Living Room":
        # Açık Gri Duvar & Açık Meşe Parke
        draw.rectangle([0, 0, width, height * 0.72], fill='#E2E8F0')  # Açık Gri Duvar
        draw.rectangle([0, height * 0.72, width, height], fill='#C8B49C')  # Meşe Parke
        draw.rectangle([0, height * 0.71, width, height * 0.72], fill='#F1F5F9')
        
        # Zümrüt Yeşili Kanepe
        draw_sofa(draw, width, height, sofa_color='#065F46', cushion_color='#047857')
        draw_plant_and_lamp(draw, width, height)

    elif theme_name == "Warm Boho Reading Corner":
        # Terrakotta / Adaçayı Sıcak Duvar & Ahşap Zemin
        draw.rectangle([0, 0, width, height * 0.75], fill='#D6CEC5')  # Sıcak Vizon Duvar
        draw.rectangle([0, height * 0.75, width, height], fill='#8C6B50')  # Zemin
        draw.rectangle([0, height * 0.74, width, height * 0.75], fill='#E2D9CF')
        
        # Berjer Sandalye & Yan Sehpa Detayı
        draw_armchair(draw, width, height)
        draw_plant_and_lamp(draw, width, height)

    else:  # Minimalist Executive Suite
        # Koyu Antrasit Duvar & Parlak Zemin
        draw.rectangle([0, 0, width, height * 0.70], fill='#334155')  # Slate Antrasit Duvar
        draw.rectangle([0, height * 0.70, width, height], fill='#1E293B')  # Koyu Zemin
        draw.rectangle([0, height * 0.69, width, height * 0.70], fill='#475569')
        
        # Taba Deri Kanepe
        draw_sofa(draw, width, height, sofa_color='#7C2D12', cushion_color='#9A3412')
        draw_plant_and_lamp(draw, width, height)

    return bg

def apply_frame_and_shadow(room_bg: Image.Image, artwork: Image.Image, box_coords, frame_color=(20, 20, 20), frame_width=28, mat_width=40):
    """Görseli duvarda tam kanepe/sandalye üzerine hizalar, gölge ve çerçeve giydirir."""
    target_w = box_coords[2] - box_coords[0]
    target_h = box_coords[3] - box_coords[1]
    
    # Görseli çerçeveye uyarla
    art_fitted = ImageOps.fit(artwork, (target_w, target_h), Image.Resampling.LANCZOS)
    
    # Paspartu (İç Beyaz Karton)
    if mat_width > 0:
        art_fitted = ImageOps.expand(art_fitted, border=mat_width, fill='#FAF9F6')
    
    # Dış Çerçeve
    framed_art = ImageOps.expand(art_fitted, border=frame_width, fill=frame_color)
    
    fw, fh = framed_art.size
    
    # Gerçekçi Derin Tablo Gölgesi
    shadow = Image.new('RGBA', (fw + 80, fh + 80), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle([40, 40, fw + 40, fh + 40], fill=(0, 0, 0, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    
    # Konumlandırma
    pos_x = box_coords[0] - (fw - target_w) // 2
    pos_y = box_coords[1] - (fh - target_h) // 2
    
    # Odaya Birlikte Yerleştirme
    room_rgba = room_bg.convert('RGBA')
    room_rgba.paste(shadow, (pos_x - 20, pos_y + 20), shadow)
    room_rgba.paste(framed_art, (pos_x, pos_y))
    
    return room_rgba.convert('RGB')

def generate_all_mockups(art_img: Image.Image):
    """4 Farklı Mobilyalı Oda Konseptinde Mockup Üretir."""
    mockups = {}
    
    # 1. Modern Lacivert Kanepe Üzeri (Siyah Çerçeve)
    bg1 = create_modern_interior("Modern Velvet Lounge")
    m1 = apply_frame_and_shadow(bg1, art_img, (850, 260, 1550, 1020), frame_color=(25, 25, 25), frame_width=26, mat_width=35)
    mockups["1_Modern_Kanepe_Salon_Mockup.jpg"] = m1
    
    # 2. İskandinav Yeşil Kanepe Üzeri (Açık Ahşap Çerçeve)
    bg2 = create_modern_interior("Scandi Oak Living Room")
    m2 = apply_frame_and_shadow(bg2, art_img, (870, 240, 1530, 1000), frame_color=(195, 155, 115), frame_width=28, mat_width=30)
    mockups["2_Iskandinav_Salon_Mockup.jpg"] = m2
    
    # 3. Sıcak Berjer Sandalye Okuma Köşesi (Beyaz Çerçeve)
    bg3 = create_modern_interior("Warm Boho Reading Corner")
    m3 = apply_frame_and_shadow(bg3, art_img, (880, 220, 1520, 980), frame_color=(245, 245, 242), frame_width=30, mat_width=40)
    mockups["3_Sicak_Berjer_Kosesi_Mockup.jpg"] = m3
    
    # 4. Koyu Antrasit Taba Deri Kanepe Üzeri (İnce Siyah Çerçeve)
    bg4 = create_modern_interior("Minimalist Executive Suite")
    m4 = apply_frame_and_shadow(bg4, art_img, (840, 230, 1560, 1010), frame_color=(15, 15, 15), frame_width=20, mat_width=0)
    mockups["4_Koyu_Executive_Salon_Mockup.jpg"] = m4
    
    return mockups

# ----------------- STREAMLIT MODERN UI -----------------

# Header Section
st.markdown("""
<div class="header-box">
    <h1>🎨 Etsy Digital Art Studio</h1>
    <p>300 DPI 4K Dönüştürücü & Mobilyalı Gerçekçi Oda Mockup Hazırlayıcı</p>
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("🚀 Görselleri & Mockup'ları Üret", type="primary", use_container_width=True)

with col_preview:
    st.markdown("### 🖼️ Görsel Önizlemesi")
    if uploaded_file is not None:
        st.image(raw_img, caption="Yüklenen Orijinal Çalışma", use_container_width=True)
    else:
        st.info("Lütfen sol taraftan bir tablo görseli yükleyin.")

# İşlem Aşaması
if uploaded_file is not None and 'generate_btn' in locals() and generate_btn:
    st.markdown("---")
    with st.spinner("⏳ Görseliniz 4K 300 DPI çözünürlüğe dönüştürülüyor ve mobilyalı oda duvarlarına yerleştiriliyor..."):
        # 1. 300 DPI 4K Dönüştürme
        high_res_img = process_image_300dpi_4k(raw_img, target_long_edge=3840)
        
        # 2. Mobilyalı Mockup Üretimi
        mockup_dict = generate_all_mockups(high_res_img)
        
        # 3. ZIP Paketleme
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Orijinal 300 DPI JPEG
            img_byte_arr = io.BytesIO()
            high_res_img.save(img_byte_arr, format='JPEG', quality=98, dpi=(300, 300))
            zip_file.writestr("0_ORJINAL_300DPI_4K.jpg", img_byte_arr.getvalue())
            
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
                label="📦 1 Orjinal 300DPI JPEG + 4 Mobilyalı Mockup'ı İndir (ZIP)",
                data=zip_buffer,
                file_name="Etsy_Art_300DPI_Mockups.zip",
                mime="application/zip",
                use_container_width=True
            )
        with col_dl2:
            st.success("✅ 5 Görsel Hazır!")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabs Gallery
        st.markdown("### 🏛️ Mockup Galerisi")
        tabs = st.tabs([
            "0. 300 DPI 4K Orjinal", 
            "1. Modern Lacivert Kanepe", 
            "2. İskandinav Yeşil Kanepe", 
            "3. Berjer Sandalye Köşesi", 
            "4. Executive Koyu Salon"
        ])
        
        with tabs[0]:
            st.image(high_res_img, caption=f"300 DPI 4K JPEG Master Dosya ({high_res_img.size[0]}x{high_res_img.size[1]} px)", use_container_width=True)
        with tabs[1]:
            st.image(mockup_dict["1_Modern_Kanepe_Salon_Mockup.jpg"], caption="Modern Lacivert Kanepe Üzeri Tablo Konumu", use_container_width=True)
        with tabs[2]:
            st.image(mockup_dict["2_Iskandinav_Salon_Mockup.jpg"], caption="İskandinav Yeşil Kanepe Üzeri Tablo Konumu", use_container_width=True)
        with tabs[3]:
            st.image(mockup_dict["3_Sicak_Berjer_Kosesi_Mockup.jpg"], caption="Sıcak Berjer Sandalye & Okuma Köşesi Tablo Konumu", use_container_width=True)
        with tabs[4]:
            st.image(mockup_dict["4_Koyu_Executive_Salon_Mockup.jpg"], caption="Executive Koyu Antrasit Salon Tablo Konumu", use_container_width=True)

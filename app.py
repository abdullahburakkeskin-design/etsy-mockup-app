import streamlit as st
import io
import zipfile
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw

st.set_page_config(
    page_title="Etsy 4K 300DPI & Mockup Generator",
    page_icon="🖼️",
    layout="wide"
)

def process_image_300dpi_4k(img: Image.Image, target_long_edge=3840):
    """Görseli 300 DPI ve 4K piksel boyutuna getirip RGB JPEG uyumlu hale getirir."""
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

def create_room_background(theme_name, width=2000, height=1500):
    """Estetik ve gerçekçi 4 farklı oda iç mekanı oluşturur."""
    bg = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(bg)
    
    if theme_name == "Modern Salon":
        # Duvar ve zemin
        draw.rectangle([0, 0, width, height * 0.72], fill='#EAE7E1')  # Sıcak krem/gri duvar
        draw.rectangle([0, height * 0.72, width, height], fill='#A3886A')  # Ahşap parke zemin
        # Parke çizgileri
        for y in range(int(height * 0.72), height, 40):
            draw.line([(0, y), (width, y)], fill='#8C7355', width=2)
        # Süpürgelik
        draw.rectangle([0, height * 0.71, width, height * 0.72], fill='#FFFFFF')
        
    elif theme_name == "İskandinav Çalışma Odası":
        # Minimalist beyaz/gri tonlar
        draw.rectangle([0, 0, width, height * 0.70], fill='#F2F4F5')
        draw.rectangle([0, height * 0.70, width, height], fill='#D3C5B4')  # Açık meşe zemin
        # Süpürgelik
        draw.rectangle([0, height * 0.69, width, height * 0.70], fill='#E0E0E0')
        # Masa üstü detay (alt kısımda ahşap dokunuş)
        draw.rectangle([200, height * 0.85, width - 200, height], fill='#B89B7A')

    elif theme_name == "Boho Yatak Odası":
        # Adaçayı yeşili / Sıcak Terracotta tonları
        draw.rectangle([0, 0, width, height * 0.75], fill='#D8E2DC')  # Yumuşak Yeşillik
        draw.rectangle([0, height * 0.75, width, height], fill='#CBBAA6')  # Bej Zemin
        # Ahşap panel altlık
        draw.rectangle([0, height * 0.60, width, height * 0.75], fill='#8C6D58')
        for x in range(0, width, 50):
            draw.line([(x, height * 0.60), (x, height * 0.75)], fill='#6E5341', width=3)

    else:  # Galeri Sergi Duvarı
        # Minimalist Galeri - Beton/Antrasit
        draw.rectangle([0, 0, width, height * 0.80], fill='#3A3D40')  # Koyu Gri
        draw.rectangle([0, height * 0.80, width, height], fill='#222426')  # Koyu Zemin
        # Spot Işığı efekti
        spot = Image.new('L', (width, height), 0)
        spot_draw = ImageDraw.Draw(spot)
        spot_draw.ellipse([width//2 - 600, -100, width//2 + 600, height * 0.85], fill=120)
        spot = spot.filter(ImageFilter.GaussianBlur(150))
        
        bg_np = np.array(bg, dtype=np.float32)
        spot_np = np.array(spot, dtype=np.float32) / 255.0
        for i in range(3):
            bg_np[:, :, i] = np.clip(bg_np[:, :, i] + spot_np * 60, 0, 255)
        bg = Image.fromarray(bg_np.astype(np.uint8))

    return bg

def apply_frame_and_shadow(room_bg: Image.Image, artwork: Image.Image, box_coords, frame_color=(20, 20, 20), frame_width=25, mat_width=35):
    """Tasarımı paspartu, çerçeve ve yumuşak gölge efektiyle odaya yerleştirir."""
    target_w = box_coords[2] - box_coords[0]
    target_h = box_coords[3] - box_coords[1]
    
    # Görseli çerçeve oranına sığdır/kırp
    art_fitted = ImageOps.fit(artwork, (target_w, target_h), Image.Resampling.LANCZOS)
    
    # Paspartu (İç beyaz kenarlık) ekleme
    if mat_width > 0:
        art_fitted = ImageOps.expand(art_fitted, border=mat_width, fill='#F9F9F6')
    
    # Ahşap/Siyah/Beyaz Çerçeve ekleme
    framed_art = ImageOps.expand(art_fitted, border=frame_width, fill=frame_color)
    
    fw, fh = framed_art.size
    
    # Gerçekçi Gölge Katmanı Oluşturma
    shadow = Image.new('RGBA', (fw + 60, fh + 60), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rectangle([30, 30, fw + 30, fh + 30], fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(25))
    
    # Yerleştirme
    pos_x = box_coords[0] - (fw - target_w) // 2
    pos_y = box_coords[1] - (fh - target_h) // 2
    
    # Gölgeyi ve Çerçeveyi Birlikte Odaya Yapıştır
    room_rgba = room_bg.convert('RGBA')
    room_rgba.paste(shadow, (pos_x - 15, pos_y + 15), shadow)
    room_rgba.paste(framed_art, (pos_x, pos_y))
    
    return room_rgba.convert('RGB')

def generate_all_mockups(art_img: Image.Image):
    """4 farklı konseptte duvar mockup'ı oluşturur."""
    mockups = {}
    
    # 1. Modern Salon (Siyah Çerçeve)
    bg1 = create_room_background("Modern Salon")
    m1 = apply_frame_and_shadow(bg1, art_img, (700, 300, 1300, 1000), frame_color=(25, 25, 25), frame_width=20, mat_width=30)
    mockups["Mockup_1_Modern_Salon.jpg"] = m1
    
    # 2. İskandinav Çalışma Odası (Açık Ahşap Çerçeve)
    bg2 = create_room_background("İskandinav Çalışma Odası")
    m2 = apply_frame_and_shadow(bg2, art_img, (750, 250, 1250, 950), frame_color=(190, 150, 110), frame_width=22, mat_width=25)
    mockups["Mockup_2_Iskandinav_Oda.jpg"] = m2
    
    # 3. Boho Yatak Odası (Beyaz Çerçeve)
    bg3 = create_room_background("Boho Yatak Odası")
    m3 = apply_frame_and_shadow(bg3, art_img, (720, 220, 1280, 920), frame_color=(245, 245, 240), frame_width=25, mat_width=40)
    mockups["Mockup_3_Boho_Stil.jpg"] = m3
    
    # 4. Galeri Sergi Duvarı (Minimal İnce Siyah Çerçeve)
    bg4 = create_room_background("Galeri Sergi Duvarı")
    m4 = apply_frame_and_shadow(bg4, art_img, (680, 280, 1320, 1020), frame_color=(15, 15, 15), frame_width=15, mat_width=0)
    mockups["Mockup_4_Galeri_Duvarı.jpg"] = m4
    
    return mockups

# ----------------- STREAMLIT ARAYÜZÜ -----------------
st.title("🎨 Etsy Tablo Otomasyonu: 300 DPI 4K & Toplu Mockup")
st.write("Herhangi bir tablo/sanat görselinizi yükleyin. Sistem otomatik olarak **4K 300 DPI Orjinal JPEG** dosyanızı ve **4 farklı odada mockup** görsellerini üretsin.")

uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG veya JPEG)", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    raw_img = Image.open(uploaded_file)
    
    st.subheader("📷 Yüklenen Görsel Önizleme")
    col_orig, col_info = st.columns([1, 2])
    with col_orig:
        st.image(raw_img, use_container_width=True)
    with col_info:
        st.info(f"**Orijinal Boyut:** {raw_img.size[0]} x {raw_img.size[1]} px")
        st.success("✅ Dönüştürmeye hazır! İşlemi başlatmak için aşağıdaki butona tıklayın.")

    if st.button("⚡ 300 DPI 4K Yap ve Mockup'ları Üret", type="primary"):
        with st.spinner("Görsel 4K & 300 DPI seviyesine yükseltiliyor ve oda mockup'ları hazırlanıyor..."):
            # 1. Orjinal Görseli 4K ve 300 DPI Yap
            high_res_img = process_image_300dpi_4k(raw_img, target_long_edge=3840)
            
            # 2. Mockup'ları Oluştur
            mockup_dict = generate_all_mockups(high_res_img)
            
            # 3. Görselleri Hazırla (Ekranda Gösterim ve ZIP içi)
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Orijinal 300DPI 4K Görseli Ekle
                img_byte_arr = io.BytesIO()
                high_res_img.save(img_byte_arr, format='JPEG', quality=98, dpi=(300, 300))
                zip_file.writestr("0_ORJINAL_300DPI_4K.jpg", img_byte_arr.getvalue())
                
                # Mockup'ları Ekle
                for filename, mockup_img in mockup_dict.items():
                    m_byte_arr = io.BytesIO()
                    mockup_img.save(m_byte_arr, format='JPEG', quality=95, dpi=(300, 300))
                    zip_file.writestr(filename, m_byte_arr.getvalue())
            
            zip_buffer.seek(0)
            
            st.divider()
            st.success("🎉 Tüm görseller başarıyla hazırlandı!")
            
            # ZIP İndirme Butonu
            st.download_button(
                label="📦 1 Orjinal + 4 Mockup Görselini İndir (ZIP / JPEG)",
                data=zip_buffer,
                file_name="Etsy_Listing_Pack_300DPI.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            # Hazırlanan Görsellerin Galeri Gösterimi
            st.subheader("🖼️ Hazırlanan Görseller ve Mockup Önizlemeleri")
            
            tabs = st.tabs(["0. Orjinal (300 DPI 4K)", "1. Modern Salon", "2. İskandinav Oda", "3. Boho Stil", "4. Galeri Duvarı"])
            
            with tabs[0]:
                st.image(high_res_img, caption=f"300 DPI 4K JPEG ({high_res_img.size[0]}x{high_res_img.size[1]} px)", use_container_width=True)
            with tabs[1]:
                st.image(mockup_dict["Mockup_1_Modern_Salon.jpg"], caption="Modern Salon Mockup (JPEG)", use_container_width=True)
            with tabs[2]:
                st.image(mockup_dict["Mockup_2_Iskandinav_Oda.jpg"], caption="İskandinav Çalışma Odası Mockup (JPEG)", use_container_width=True)
            with tabs[3]:
                st.image(mockup_dict["Mockup_3_Boho_Stil.jpg"], caption="Boho Yatak Odası Mockup (JPEG)", use_container_width=True)
            with tabs[4]:
                st.image(mockup_dict["Mockup_4_Galeri_Duvarı.jpg"], caption="Galeri Sergi Duvarı Mockup (JPEG)", use_container_width=True)

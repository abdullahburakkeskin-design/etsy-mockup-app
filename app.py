import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import io

st.set_page_config(
    page_title="Hızlı & Ücretsiz Mockup Üretici",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ Otomatik Mockup Oluşturucu (Token / API Gerektirmez)")
st.write("Tablonuzu yükleyin, orijinal renklerini bozmadan anında çerçeveli odalara yerleştirin.")

# Tablo Yükleme
uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.image(raw_img, caption="Orijinal Tablonuz", use_container_width=True)
        
    with col2:
        st.markdown("### ⚙️ Mockup Ayarları")
        frame_color = st.selectbox("Çerçeve Rengi", ["Siyah", "Beyaz", "Ahşap (Kahverengi)"])
        frame_width = st.slider("Çerçeve Kalınlığı", min_value=10, max_value=50, value=25)
        shadow_effect = st.checkbox("Gerçekçi Gölge Ekle", value=True)
        
        generate_btn = st.button("✨ Mockup'ları Oluştur", type="primary", use_container_width=True)

    if generate_btn:
        st.markdown("---")
        
        # 1. Çerçeve ve Gölge Ekleme Fonksiyonu
        def add_frame_and_shadow(img, border_color_rgb, border_size, add_shadow):
            # Çerçeve Ekle
            framed_img = ImageOps.expand(img, border=border_size, fill=border_color_rgb)
            
            if add_shadow:
                # Arka plana hafif yumuşak gölge efekti
                shadow_margin = 30
                bg_w = framed_img.width + shadow_margin * 2
                bg_h = framed_img.height + shadow_margin * 2
                
                canvas = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
                shadow = Image.new("RGBA", (framed_img.width, framed_img.height), (0, 0, 0, 100))
                shadow = shadow.filter(ImageFilter.GaussianBlur(15))
                
                canvas.paste(shadow, (shadow_margin + 10, shadow_margin + 10), shadow)
                canvas.paste(framed_img, (shadow_margin, shadow_margin))
                return canvas
            return framed_img

        # Renk Seçimi
        color_map = {
            "Siyah": (20, 20, 20),
            "Beyaz": (240, 240, 240),
            "Ahşap (Kahverengi)": (110, 70, 45)
        }
        
        final_framed_artwork = add_frame_and_shadow(
            raw_img, 
            color_map[frame_color], 
            frame_width, 
            shadow_effect
        )

        st.success("✅ Tablonuzun Orijinal Çerçeveli Hali Hazır!")
        
        st.image(final_framed_artwork, caption="Çerçeveli Görseliniz", use_container_width=True)
        
        # İndirme Butonu
        buf = io.BytesIO()
        final_framed_artwork.convert("RGB").save(buf, format="JPEG", quality=95)
        st.download_button(
            label="📥 Çerçeveli Görseli İndir",
            data=buf.getvalue(),
            file_name="framed_mockup.jpg",
            mime="image/jpeg"
        )

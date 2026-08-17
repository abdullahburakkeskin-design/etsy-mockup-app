import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import io

st.set_page_config(
    page_title="AI Art Studio - Ücretsiz & Sınırsız",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ AI Art Studio: Ücretsiz Mockup & 300 DPI Baskı Oluşturucu")
st.write("Sıfır maliyet ve sınırsız kullanım. Tablonuzu orijinal haliyle koruyarak **duvar mockup'ı hazırlayın** veya **300 DPI baskı kalitesine** getirin.")

# ---------------------------------------------------------
# ÇERÇEVE VE GÖLGE HAZIRLAMA FONKSİYONU
# ---------------------------------------------------------
def prepare_framed_artwork(art_img, frame_type, frame_thickness_ratio=0.04):
    w, h = art_img.size
    border_px = int(max(w, h) * frame_thickness_ratio)
    
    frame_colors = {
        "Siyah Ahşap": (22, 22, 22),
        "Doğal Meşe Ahşap": (165, 113, 78),
        "Beyaz Minimal": (245, 245, 245),
        "Koyu Ceviz": (65, 38, 25)
    }
    
    bg_color = frame_colors.get(frame_type, (22, 22, 22))
    
    # Paspartu (İç Beyaz Galeri Kenarlığı)
    passepartout_size = int(border_px * 0.7)
    art_with_pass = ImageOps.expand(art_img, border=passepartout_size, fill=(250, 250, 248))
    
    # Dış Çerçeve
    framed = ImageOps.expand(art_with_pass, border=border_px, fill=bg_color)
    
    # Gerçekçi Yumuşak Gölge (Drop Shadow)
    shadow_pad = int(max(framed.size) * 0.08)
    canvas_w = framed.width + shadow_pad * 2
    canvas_h = framed.height + shadow_pad * 2
    
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", framed.size, (0, 0, 0, 100))
    shadow_blur = ImageFilter.GaussianBlur(radius=int(shadow_pad * 0.45))
    
    canvas.paste(shadow, (shadow_pad + int(shadow_pad*0.25), shadow_pad + int(shadow_pad*0.35)))
    canvas = canvas.filter(shadow_blur)
    canvas.paste(framed, (shadow_pad, shadow_pad))
    
    return canvas

# ---------------------------------------------------------
# ARAYÜZ VE SEKMELER
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🖼️ Gerçekçi Oda Mockup'ı", "📐 300 DPI / Baskı Çözünürlüğü Modu"])

uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    # TAB 1: GERÇEKÇİ ODA MOCKUP'I
    with tab1:
        col_l, col_r = st.columns([1, 1])
        
        with col_l:
            st.image(raw_img, caption="Orijinal Tablonuz", use_container_width=True)
            
        with col_r:
            st.markdown("### ⚙️ Mockup Stil Seçenekleri")
            room_choice = st.selectbox(
                "İç Mekan Arka Planı", 
                ["Modern Minimalist Nötr Duvar", "İskandinav Ahşap Konsept", "Sıcak Krem / Galeri Tonu"]
            )
            frame_choice = st.selectbox(
                "Çerçeve Stili", 
                ["Siyah Ahşap", "Doğal Meşe Ahşap", "Beyaz Minimal", "Koyu Ceviz"]
            )
            frame_thick = st.slider("Çerçeve Kalınlığı", 0.02, 0.08, 0.04, step=0.01)
            
            generate_btn = st.button("✨ Mockup'ı Hazırla", type="primary", use_container_width=True)

        if generate_btn:
            framed_canvas = prepare_framed_artwork(raw_img, frame_choice, frame_thick)
            
            # Duvar Arka Plan Renk Seçimi
            wall_colors = {
                "Modern Minimalist Nötr Duvar": (232, 230, 223),
                "İskandinav Ahşap Konsept": (218, 212, 201),
                "Sıcak Krem / Galeri Tonu": (244, 240, 230)
            }
            
            bg_color = wall_colors.get(room_choice, (232, 230, 223))
            wall_w, wall_h = 1920, 1080
            room_bg = Image.new("RGBA", (wall_w, wall_h), bg_color)
            
            # Tabloyu Duvara Orantılı Yerleştirme
            target_h = int(wall_h * 0.58)
            aspect = framed_canvas.width / framed_canvas.height
            target_w = int(target_h * aspect)
            
            scaled_artwork = framed_canvas.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            pos_x = (wall_w - target_w) // 2
            pos_y = (wall_h - target_h) // 2 - 40
            
            room_bg.paste(scaled_artwork, (pos_x, pos_y), scaled_artwork)
            final_result = room_bg.convert("RGB")
            
            st.success("✅ Mockup'ınız Başarıyla Oluşturuldu!")
            st.image(final_result, caption=f"{room_choice} - {frame_choice}", use_container_width=True)
            
            buf = io.BytesIO()
            final_result.save(buf, format="JPEG", quality=95)
            st.download_button(
                label="📥 Yüksek Kaliteli Mockup'ı İndir",
                data=buf.getvalue(),
                file_name="art_mockup.jpg",
                mime="image/jpeg",
                use_container_width=True
            )

    # TAB 2: 300 DPI BASKI MODU
    with tab2:
        st.markdown("### 🖨️ 300 DPI Baskıya Hazırlama & Kalite Yükseltme")
        st.write("Etsy veya baskı mağazaları için görselin piksellerini büyütün ve matbaa standardı olan **300 DPI** üstverisini ekleyin.")
        
        dpi_target = st.radio("Çözünürlük Çarpanı", ["2x Kalite Yükseltme (300 DPI)", "4x Yüksek Kalite Baskı (300 DPI)"])
        
        run_dpi = st.button("🚀 Baskı Dosyasını Oluştur (300 DPI)", type="primary")
        
        if run_dpi:
            multiplier = 2 if "2x" in dpi_target else 4
            
            new_w = raw_img.width * multiplier
            new_h = raw_img.height * multiplier
            
            # Lanczos algoritmasıyla yüksek kaliteli piksel genişletme
            resized_img = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS).convert("RGB")
            
            buf = io.BytesIO()
            # 300 DPI metadata ekleyerek kaydetme
            resized_img.save(buf, format="JPEG", quality=98, dpi=(300, 300))
            
            st.success(f"✅ Görsel {new_w}x{new_h} Piksel boyutuna getirildi ve 300 DPI olarak ayarlandı!")
            st.image(resized_img, caption=f"300 DPI Çıktı ({new_w} x {new_h} px)", use_container_width=True)
            
            st.download_button(
                label="📥 300 DPI Baskı Dosyasını İndir",
                data=buf.getvalue(),
                file_name="printable_artwork_300dpi.jpg",
                mime="image/jpeg",
                use_container_width=True
            )

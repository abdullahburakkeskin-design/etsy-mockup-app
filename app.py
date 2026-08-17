import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import io
import requests
import urllib.parse
import time

st.set_page_config(
    page_title="AI Art Studio - Yapay Zeka Mockup",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ AI Art Studio: Yapay Zeka Tabanlı Fotogerçekçi Mockup")
st.write("Yapay zeka modellerini kullanarak tablonuzu fotogerçekçi iç mekan ve galeri tasarımlarına dönüştürün.")

# ---------------------------------------------------------
# POLINATIONS AI / FLUX - YAPAY ZEKA GÖRSEL ÜRETİMİ (ÜCRETSİZ)
# ---------------------------------------------------------
def generate_ai_room_background(prompt, width=1280, height=854):
    """
    Ücretsiz ve sınırsız Yapay Zeka görsel üretim servisi (FLUX Model altyapısı)
    """
    encoded_prompt = urllib.parse.quote(prompt)
    seed = int(time.time()) % 100000
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux&nologo=true"
    
    response = requests.get(image_url, timeout=30)
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content)).convert("RGBA")
    else:
        raise Exception("AI Görsel servisine erişilemedi.")

# ---------------------------------------------------------
# ÇERÇEVE VE GÖLGE HAZIRLAMA FONKSİYONU
# ---------------------------------------------------------
def prepare_framed_artwork(art_img, frame_type, frame_thickness_ratio=0.03):
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
    passepartout_size = int(border_px * 0.8)
    art_with_pass = ImageOps.expand(art_img, border=passepartout_size, fill=(250, 250, 248))
    
    # Dış Çerçeve
    framed = ImageOps.expand(art_with_pass, border=border_px, fill=bg_color)
    
    # Yumuşak Derinlik Gölgesi (Drop Shadow)
    shadow_pad = int(max(framed.size) * 0.08)
    canvas_w = framed.width + shadow_pad * 2
    canvas_h = framed.height + shadow_pad * 2
    
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", framed.size, (0, 0, 0, 110))
    shadow_blur = ImageFilter.GaussianBlur(radius=int(shadow_pad * 0.45))
    
    canvas.paste(shadow, (shadow_pad + int(shadow_pad*0.2), shadow_pad + int(shadow_pad*0.3)))
    canvas = canvas.filter(shadow_blur)
    canvas.paste(framed, (shadow_pad, shadow_pad))
    
    return canvas

# ---------------------------------------------------------
# ARAYÜZ
# ---------------------------------------------------------
uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file).convert("RGBA")
    
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.image(raw_img, caption="Orijinal Tablonuz", use_container_width=True)
        
    with col_r:
        st.markdown("### 🎨 Yapay Zeka İç Mekan Tasarımı")
        
        style_preset = st.selectbox(
            "Yapay Zeka Oda Konsepti",
            [
                "Modern İskandinav Salonu (Aydınlık, Ahşap Mobilyalar, Bitkiler)",
                "Lüks Minimalist Galeri Duvarı (Stüdyo Işıklandırması)",
                "Boho Chic Yatak Odası (Sıcak Tonlar, Doğal Gün Işığı)",
                "Endüstriyel Loft Daire (Tuğla / Beton Duvar, Deri Koltuk)",
                "Özel Prompt (Kendi İç Mekanınızı Yazın)"
            ]
        )
        
        custom_prompt = ""
        if style_preset == "Özel Prompt (Kendi İç Mekanınızı Yazın)":
            custom_prompt = st.text_input("İngilizce prompt girin:", "A modern luxury living room with beige wall, realistic sunlight, 8k professional photography")
            
        frame_choice = st.selectbox(
            "Çerçeve Stili", 
            ["Siyah Ahşap", "Doğal Meşe Ahşap", "Beyaz Minimal", "Koyu Ceviz"]
        )
        
        generate_btn = st.button("🚀 Yapay Zeka ile Mockup Oluştur", type="primary", use_container_width=True)

    if generate_btn:
        with st.spinner("🤖 Yapay zeka fotogerçekçi iç mekanı çiziyor ve tablonuzu yerleştiriyor... (Yaklaşık 10 sn)"):
            try:
                # Prompt Seçimi
                prompts_map = {
                    "Modern İskandinav Salonu (Aydınlık, Ahşap Mobilyalar, Bitkiler)": "A bright modern Scandinavian living room interior, neutral soft wall, oak wood furniture, indoor green plants, natural sunlight through window, architectural digest photograph, 8k resolution, photorealistic",
                    "Lüks Minimalist Galeri Duvarı (Stüdyo Işıklandırması)": "A minimalist art gallery room, museum spotlighting, clean beige plaster wall, elegant interior design, soft shadows, 8k professional interior photography",
                    "Boho Chic Yatak Odası (Sıcak Tonlar, Doğal Gün Işığı)": "A cozy boho chic bedroom interior, warm cream wall, rattan decorative items, warm morning sun, depth of field, photorealistic 8k",
                    "Endüstriyel Loft Daire (Tuğla / Beton Duvar, Deri Koltuk)": "An industrial loft living room with concrete microcement wall, leather sofa, soft ambient lighting, modern architecture, 8k interior design"
                }
                
                selected_prompt = custom_prompt if style_preset == "Özel Prompt (Kendi İç Mekanınızı Yazın)" else prompts_map.get(style_preset)
                
                # 1. Yapay Zeka ile fotogerçekçi oda arka planını çiz
                ai_room_bg = generate_ai_room_background(selected_prompt)
                
                # 2. Tabloyu çerçevele ve gölgelendir
                framed_canvas = prepare_framed_artwork(raw_img, frame_choice)
                
                # 3. Tabloyu yapay zeka odasının boyutuna uygun ölçekle
                wall_w, wall_h = ai_room_bg.size
                target_h = int(wall_h * 0.45)
                aspect = framed_canvas.width / framed_canvas.height
                target_w = int(target_h * aspect)
                
                scaled_artwork = framed_canvas.resize((target_w, target_h), Image.Resampling.LANCZOS)
                
                # 4. Tabloyu duvara (merkeze hafif yukarı) monte et
                pos_x = (wall_w - target_w) // 2
                pos_y = (wall_h - target_h) // 2 - int(wall_h * 0.05)
                
                ai_room_bg.paste(scaled_artwork, (pos_x, pos_y), scaled_artwork)
                final_result = ai_room_bg.convert("RGB")
                
                st.success("✅ Yapay Zeka Mockup'ınız Başarıyla Hazırlandı!")
                st.image(final_result, caption=f"AI Üretimi: {style_preset}", use_container_width=True)
                
                buf = io.BytesIO()
                final_result.save(buf, format="JPEG", quality=95)
                st.download_button(
                    label="📥 Yüksek Çözünürlüklü Yapay Zeka Mockup'ını İndir",
                    data=buf.getvalue(),
                    file_name="ai_mockup_result.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Görsel oluşturulurken bir hata oluştu: {str(e)}")

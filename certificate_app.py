# certificate_app.py
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd, io, zipfile

st.set_page_config(page_title="Certificate Generator - CloudX", layout="wide")
st.title("Certificate Generator - CloudX")

# ---------------- File Inputs ----------------
template_file = st.file_uploader("Upload Certificate Template (PNG)", type=["png"])
csv_file = st.file_uploader("Upload CSV (must have 'Name' and 'RegNo' columns)", type=["csv"])
font_file = st.file_uploader("Upload a .ttf Font File", type=["ttf"])

# ---------------- Helper ----------------
def load_font(uploaded_font, size):
    if uploaded_font is not None:
        # Reset pointer every time we use the uploaded file
        uploaded_font.seek(0)
        font_bytes = uploaded_font.read()
        return ImageFont.truetype(io.BytesIO(font_bytes), size)
    else:
        return ImageFont.load_default()

# ---------------- Main Logic ----------------
if template_file and csv_file:
    df = pd.read_csv(csv_file)
    template = Image.open(template_file).convert("RGB")
    W, H = template.size

    # Sidebar controls
    st.sidebar.header("⚙️ Adjust Settings")
    name_x = st.sidebar.slider("Name X Position", 0, W, W // 2)
    name_y = st.sidebar.slider("Name Y Position", 0, H, H // 2)
    reg_x = st.sidebar.slider("RegNo X Position (center ref)", 0, W, W // 2)
    reg_y = st.sidebar.slider("RegNo Y Position (0 = auto below name)", 0, H, 0)

    name_font_size = st.sidebar.slider("Name Font Size", 20, 400, 200)
    reg_font_size = st.sidebar.slider("RegNo Font Size", 10, 200, 64)
    reg_spacing = st.sidebar.slider("Spacing below Name (if auto)", 0, 200, 50)

    text_color = st.sidebar.color_picker("Text Color", "#000000")
    preview_index = st.sidebar.number_input("Preview Row Index", 0, len(df) - 1, 0)

    # Certificates
    output_images = []
    for _, row in df.iterrows():
        name = str(row["Name"]).strip()
        regno = str(row["RegNo"]).strip()

        cert = template.copy()
        draw = ImageDraw.Draw(cert)

        font_name = load_font(font_file, name_font_size)
        font_reg = load_font(font_file, reg_font_size)

        # ---- Draw Name ----
        bbox = draw.textbbox((0, 0), name, font=font_name)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw_x = name_x - text_w // 2 - bbox[0]
        draw_y = name_y - text_h // 2 - bbox[1]
        draw.text((draw_x, draw_y), name, font=font_name, fill=text_color)

        # ---- Draw RegNo ----
        if reg_y == 0:  # auto below name
            reg_draw_y = draw_y + text_h + reg_spacing
        else:
            reg_draw_y = reg_y

        bbox_r = draw.textbbox((0, 0), regno, font=font_reg)
        reg_w = bbox_r[2] - bbox_r[0]
        reg_draw_x = reg_x - reg_w // 2 - bbox_r[0]
        draw.text((reg_draw_x, reg_draw_y), regno, font=font_reg, fill=text_color)

        # Save to memory
        safe = "".join(c for c in name if c.isalnum() or c in (" ", "_")).rstrip()
        out_name = f"{safe}_{regno}.png"
        img_bytes = io.BytesIO()
        cert.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        output_images.append((out_name, img_bytes))

    # ZIP Download
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for fname, img_bytes in output_images:
            zf.writestr(fname, img_bytes.read())
    zip_buffer.seek(0)

    st.success(f"Generated {len(output_images)} certificates.")
    st.download_button(
        "⬇️ Download All Certificates (ZIP)",
        data=zip_buffer,
        file_name="certificates.zip",
        mime="application/zip"
    )

    # Preview
    preview_name, preview_img = output_images[preview_index]
    st.subheader(f"🔍 Preview: {preview_name}")
    st.image(preview_img, use_container_width=True)
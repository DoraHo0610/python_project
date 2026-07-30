import base64
import getpass
import os
import random
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="選擇障礙小幫手 - 王品小幫手", page_icon="🎲", layout="wide"
)

# 頁頭與回首頁按鈕
col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("🎲 5. 選擇障礙小幫手 - 今天吃哪家？")
with col_home:
    if st.button("🏠 回首頁", key="top_home_5"):
        st.switch_page("app.py")

st.markdown("---")

load_dotenv("./.env", override=True)


@st.cache_data
def load_data():
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "wowprime")

    engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(engine_url)

    query = "SELECT s.*, b.brand_name FROM stores s LEFT JOIN brands b ON s.brand_id = b.brand_id WHERE s.status = '營業中';"
    df = pd.read_sql(query, engine)
    df = df.dropna(subset=["google_rating", "google_review_count"])
    df["brand_name"] = df["brand_name"].fillna("未知品牌")
    return df


try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ 資料載入失敗: {e}")
    st.stop()

# ----------------------------------------------------
# 主要畫面中間：篩選下拉選單 (放置於標題下方)
# ----------------------------------------------------
filter_col1, filter_col2 = st.columns(2)

brand_list = ["全部品牌"] + sorted(df_raw["brand_name"].unique().tolist())
city_list = ["全部縣市"] + sorted(df_raw["city"].unique().tolist())

with filter_col1:
    selected_brand = st.selectbox("🎯 偏好品牌", brand_list)

with filter_col2:
    selected_city = st.selectbox("📍 用餐縣市", city_list)

df_filtered = df_raw.copy()
if selected_brand != "全部品牌":
    df_filtered = df_filtered[df_filtered["brand_name"] == selected_brand]
if selected_city != "全部縣市":
    df_filtered = df_filtered[df_filtered["city"] == selected_city]


# 讀取本地圖片並轉換為 Base64 供前端 HTML 直接讀取的輔助函式 (避免瀏覽器跨域阻擋)
def get_image_base64(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return ""


# 整理品牌圖片 Mapping (以品牌名稱對應 Base64 圖片)
picture_dir = "picture"
brand_images_base64 = {}
if os.path.exists(picture_dir):
    for brand in df_raw["brand_name"].unique():
        # 尋找 picture 資料夾下對應品牌的 png 圖片 (例如 picture/王品.png)
        img_path = os.path.join(picture_dir, f"{brand}.png")
        brand_images_base64[brand] = get_image_base64(img_path)

# 將選出的門市資料轉換
filtered_stores = df_filtered[["full_name", "brand_name"]].to_dict("records")

if len(filtered_stores) == 0:
    st.warning("⚠️ 查無符合條件的門市，請調整上方偏好條件！")
else:
    display_stores = filtered_stores[:12]
    if len(filtered_stores) > 12:
        st.info(
            f"💡 目前符合條件的門市共 {len(filtered_stores)} 家，已為您隨機抽選 12 家代表進入轉盤參賽！"
        )
        display_stores = random.sample(filtered_stores, 12)

    # 包含店名與品牌名稱的 JSON 資料
    stores_json = str(display_stores)
    img_map_json = str(brand_images_base64)

    # 動態產生更大尺寸 (600px x 600px) 的轉盤 HTML/JS
    wheel_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .wheel-container {{ text-align: center; font-family: sans-serif; }}
            #canvas {{ border: 5px solid #333; border-radius: 50%; margin-top: 10px; box-shadow: 0px 6px 12px rgba(0,0,0,0.15); }}
            #spin-btn {{ 
                background-color: #ff4b4b; color: white; border: none; 
                padding: 14px 40px; font-size: 22px; font-weight: bold; 
                border-radius: 30px; cursor: pointer; margin-top: 25px;
                box-shadow: 0px 4px 10px rgba(255, 75, 75, 0.4);
                transition: transform 0.1s ease, background-color 0.2s;
            }}
            #spin-btn:hover {{ background-color: #e03b3b; transform: scale(1.05); }}
            #winner-display {{ font-size: 28px; font-weight: bold; color: #ff4b4b; margin-top: 20px; height: 50px; }}
        </style>
    </head>
    <body>
        <div class="wheel-container">
            <!-- 放大 Canvas 至 600px -->
            <canvas id="canvas" width="600" height="600"></canvas><br>
            <button id="spin-btn" onclick="spin()">🎰 開始抽籤！</button>
            <div id="winner-display"></div>
        </div>

        <script>
            const stores = {stores_json};
            const brandImgMap = {img_map_json};
            const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#88D49E', '#E8A87C', '#C38D9E', '#41B3A3', '#E27D60', '#85DCBA'];
            
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const cx = canvas.width / 2; // 300
            const cy = canvas.height / 2; // 300
            const radius = cx - 20; // 半徑 280
            
            let startAngle = 0;
            const arc = Math.PI / (stores.length / 2);
            let spinTimeout = null;
            let spinAngleStart = 10;
            let spinTime = 0;
            let spinTimeTotal = 0;

            // 預載入圖片
            const loadedImages = {{}};
            let loadedCount = 0;
            const totalBrands = Object.keys(brandImgMap).length;

            for (let brand in brandImgMap) {{
                if (brandImgMap[brand]) {{
                    const img = new Image();
                    img.src = brandImgMap[brand];
                    img.onload = function() {{
                        loadedImages[brand] = img;
                        drawWheel();
                    }};
                }}
            }}

            function drawWheel() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                for(let i = 0; i < stores.length; i++) {{
                    const angle = startAngle + i * arc;
                    ctx.fillStyle = colors[i % colors.length];
                    
                    // 繪製扇形區域
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, angle, angle + arc, false);
                    ctx.arc(cx, cy, 0, angle + arc, angle, true);
                    ctx.fill();

                    // 保存畫布狀態並準備繪製內容
                    ctx.save();
                    ctx.translate(cx + Math.cos(angle + arc / 2) * (radius - 80), 
                                  cy + Math.sin(angle + arc / 2) * (radius - 80));
                    ctx.rotate(angle + arc / 2 + Math.PI / 2);

                    const brandName = stores[i].brand_name;
                    const img = loadedImages[brandName];

                    if (img) {{
                        // 如果有對應的品牌圖片，渲染圖片 (設定圖片寬高為 50x50px)
                        const imgSize = 50;
                        ctx.drawImage(img, -imgSize / 2, -imgSize / 2, imgSize, imgSize);
                    }} else {{
                        // 如果沒有圖片，回退使用文字顯示
                        ctx.fillStyle = "white";
                        ctx.font = "bold 16px sans-serif";
                        const text = stores[i].full_name.length > 8 ? stores[i].full_name.substring(0,8) + '..' : stores[i].full_name;
                        ctx.fillText(text, -ctx.measureText(text).width / 2, 0);
                    }}
                    
                    ctx.restore();
                }}

                // 繪製頂部箭頭 (Pointer)
                ctx.fillStyle = "#333";
                ctx.beginPath();
                ctx.moveTo(cx - 16, cy - radius - 8);
                ctx.lineTo(cx + 16, cy - radius - 8);
                ctx.lineTo(cx, cy - radius + 22);
                ctx.fill();
            }}

            function rotateWheel() {{
                spinTime += 30;
                if(spinTime >= spinTimeTotal) {{
                    stopRotateWheel();
                    return;
                }}
                const spinAngle = spinAngleStart - easeOut(spinTime, 0, spinAngleStart, spinTimeTotal);
                startAngle += (spinAngle * Math.PI / 180);
                drawWheel();
                spinTimeout = setTimeout(rotateWheel, 30);
            }}

            function stopRotateWheel() {{
                clearTimeout(spinTimeout);
                const degrees = startAngle * 180 / Math.PI + 90;
                const arcd = arc * 180 / Math.PI;
                const index = Math.floor((360 - degrees % 360) / arcd) % stores.length;
                document.getElementById('winner-display').innerHTML = "🎉 今天就吃： " + stores[index].full_name + "！";
            }}

            function easeOut(t, b, c, d) {{
                const ts = (t/=d)*t;
                const tc = ts*t;
                return b+c*(tc + -3*ts + 3*t);
            }}

            function spin() {{
                document.getElementById('winner-display').innerHTML = "🎲 抽籤中...";
                spinAngleStart = Math.random() * 10 + 10;
                spinTime = 0;
                spinTimeTotal = Math.random() * 3000 + 4000;
                rotateWheel();
            }}

            drawWheel();
        </script>
    </body>
    </html>
    """

    # 將嵌入元件高度放大至 800px 以完整容納 600px 的轉盤
    components.html(wheel_html, height=800)

st.markdown("---")
if st.button("🏠 回到首頁", key="bottom_home_5"):
    st.switch_page("app.py")
import base64
import json
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="美食隨機轉盤 - 王品集團", page_icon="🎲", layout="wide"
)

# 頁頭與回首頁按鈕
col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("🎲 4. 選擇障礙嗎? 我是你的小幫手 ~ 一起決定今天吃哪家！")
with col_home:
    if st.button("🏠 回首頁", key="top_home_5"):
        st.switch_page("wowprime.py")

st.markdown("---")

load_dotenv("./.env", override=True)


@st.cache_data
def load_data():
    # DB_HOST = os.environ.get("DB_HOST", "localhost")
    # DB_PORT = int(os.environ.get("DB_PORT", 3306))
    # DB_USER = os.environ.get("DB_USER", "root")
    # DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    # DB_NAME = os.environ.get("DB_NAME", "wowprime")

    # engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    # engine = create_engine(engine_url)

    # query = "SELECT s.*, b.brand_name FROM stores s LEFT JOIN brands b ON s.brand_id = b.brand_id WHERE s.status = '營業中';"
    # df = pd.read_sql(query, engine)
    # df = df.dropna(subset=["google_rating", "google_review_count"])
    # df["brand_name"] = df["brand_name"].fillna("未知品牌")
    # return df

    # 優先讀取 Streamlit Secrets，若無則降級讀取 os.environ
    DB_HOST = st.secrets.get("DB_HOST", os.environ.get("DB_HOST", "localhost"))
    DB_PORT = int(st.secrets.get("DB_PORT", os.environ.get("DB_PORT", 6543)))
    DB_USER = st.secrets.get("DB_USER", os.environ.get("DB_USER", "postgres"))
    DB_PASSWORD = st.secrets.get("DB_PASSWORD", os.environ.get("DB_PASSWORD", ""))
    DB_NAME = st.secrets.get("DB_NAME", os.environ.get("DB_NAME", "postgres"))

    # 連線至 Supabase PostgreSQL
    engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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


# 讀取本地圖片並轉 Base64文字直接嵌入 HTML(不轉Base64HTML會出現跨域問題，導致圖片無法顯示)
# 轉盤是用前端 HTML5 Canvas 渲染的。前端瀏覽器是在使用者的電腦運作，無法讀取你伺服器硬碟裡的路徑，瀏覽器就找不圖片。
def get_image_base64(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return ""


picture_dir = "picture"
brand_images_base64 = {}
if os.path.exists(picture_dir):
    for brand in df_raw["brand_name"].unique():
        img_path = os.path.join(picture_dir, f"{brand}.png")
        brand_images_base64[brand] = get_image_base64(img_path)



# ----------------------------------------------------
# 步驟 1：請使用者選擇縣市 (放大標題文字)
# ----------------------------------------------------
city_list = ["請選擇縣市..."] + sorted(df_raw["city"].unique().tolist())

# 1. 自訂放大的下拉選單標題 (字體 20px、加粗)
st.markdown(
    "<p style='font-size: 22px; font-weight: bold; margin-bottom: 8px;'>📍 請選擇你現在位於的縣市：</p>",
    unsafe_allow_html=True,
)

# 2. 隱藏 selectbox 的原生小標題，避免重複顯示
selected_city = st.selectbox(
    "📍 請選擇你現在位於的縣市：",
    city_list,
    index=0,
    label_visibility="collapsed",
)


# ----------------------------------------------------
# 步驟 2 & 3：轉盤與結果呈現邏輯
# ----------------------------------------------------
if selected_city == "請選擇縣市...":
    # 🌟 修改點：自訂放大的藍色提示框 (字體 20px)
    st.markdown(
        """
        <div style="
            font-size: 18px; 
            margin-bottom: 20px;">
            👆 請先在上方下拉選單選擇您目前的縣市，小幫手將為您準備專屬轉盤喔！
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    df_city_stores = df_raw[df_raw["city"] == selected_city]
    available_brands = sorted(df_city_stores["brand_name"].unique().tolist())

    if len(available_brands) == 0:
        st.warning(f"⚠️ **{selected_city}** 目前沒有營業中的王品集團門市喔！")

    elif len(available_brands) == 1:
        # 單一品牌直接列出所有門市
        only_brand = available_brands[0]
        st.info(
            f"💡 在 **{selected_city}** 目前只有 **1 個** 王品集團品牌，別無選擇啦！"
        )


        img_path = os.path.join(picture_dir, f"{only_brand}.png")
        if os.path.exists(img_path):
            st.image(img_path, width=200)
        else:
            st.markdown(f"### 🍽️ {only_brand}")

        st.subheader(f"🎉 今天就決定吃：【{only_brand}】！")
        st.write(
            f"下方為 **{selected_city}** 的 {only_brand} 門市資訊 ~~ 提供你快速訂位唷！"
        )


        st.markdown("---")

        st.markdown("#### 📍 門市據點與訂位連結：")
        target_stores = df_city_stores[
            df_city_stores["brand_name"] == only_brand
        ]
        for _, row in target_stores.iterrows():
            with st.container():
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**🏠 {row['full_name']}**")
                    st.caption(f"📍 地址：{row['address']}")
                with c2:
                    booking_url = row.get("booking_url", "")
                    if (
                        pd.notnull(booking_url)
                        and str(booking_url).startswith("http")
                    ):
                        st.link_button("👉 立即線上訂位", booking_url)
                    else:
                        st.caption("無線上訂位")
                st.divider()

    else:
        # 多品牌轉盤
        st.write(
            f"目前 **{selected_city}** 共有 **{len(available_brands)}** 個王品集團品牌，點擊下方開始轉盤抽籤！"
        )

        stores_by_brand = {}
        for brand in available_brands:
            b_stores = df_city_stores[df_city_stores["brand_name"] == brand]
            stores_by_brand[brand] = []
            for _, r in b_stores.iterrows():
                stores_by_brand[brand].append({
                    "full_name": r["full_name"],
                    "address": r["address"],
                    "booking_url": (
                        r["booking_url"]
                        if pd.notnull(r["booking_url"])
                        and str(r["booking_url"]).startswith("http")
                        else ""
                    ),
                })

        brands_json = json.dumps(available_brands, ensure_ascii=False)
        img_map_json = json.dumps(brand_images_base64, ensure_ascii=False)
        stores_data_json = json.dumps(stores_by_brand, ensure_ascii=False)

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
                    border-radius: 30px; cursor: pointer; margin-top: 20px;
                    box-shadow: 0px 4px 10px rgba(255, 75, 75, 0.4);
                    transition: transform 0.1s ease, background-color 0.2s;
                }}
                #spin-btn:hover {{ background-color: #e03b3b; transform: scale(1.05); }}
                #winner-display {{ 
                    font-size: 28px; font-weight: bold; color: #ff4b4b; 
                    margin-top: 20px; height: 60px;
                    background-color: #fff5f5; border-radius: 12px;
                    display: flex; align-items: center; justify-content: center;
                    border: 2px dashed #ff4b4b; padding: 10px;
                }}
                #store-list-container {{
                    margin-top: 30px; text-align: left; background: #ffffff;
                    padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                }}
                .store-item {{
                    display: flex; justify-content: space-between; align-items: center;
                    padding: 12px 0; border-bottom: 1px solid #eee;
                }}
                .store-item:last-child {{ border-bottom: none; }}
                .store-name {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 4px; }}
                .store-address {{ font-size: 14px; color: #666; }}
                .booking-btn {{
                    background-color: #ff4b4b; color: white !important;
                    padding: 8px 16px; text-decoration: none; border-radius: 6px;
                    font-weight: bold; font-size: 14px; display: inline-block;
                }}
                .no-booking {{ color: #999; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="wheel-container">
                <canvas id="canvas" width="600" height="600"></canvas><br>
                <button id="spin-btn" onclick="spin()">🎰 開始抽籤！</button>
                <div id="winner-display">🎲 準備好了嗎？點擊按鈕讓命運決定！</div>
                <div id="store-list-container" style="display: none;"></div>
            </div>

            <script>
                const brands = {brands_json};
                const brandImgMap = {img_map_json};
                const storesData = {stores_data_json};
                const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#88D49E', '#E8A87C', '#C38D9E', '#41B3A3', '#E27D60', '#85DCBA'];
                
                const canvas = document.getElementById('canvas');
                const ctx = canvas.getContext('2d');
                const cx = canvas.width / 2;
                const cy = canvas.height / 2;
                const radius = cx - 20;
                
                let startAngle = 0;
                const arc = Math.PI / (brands.length / 2);
                let spinTimeout = null;
                let spinAngleStart = 10;
                let spinTime = 0;
                let spinTimeTotal = 0;

                const loadedImages = {{}};

                // 1. 繪製轉盤核心函式
                function drawWheel() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    for(let i = 0; i < brands.length; i++) {{
                        const angle = startAngle + i * arc;
                        ctx.fillStyle = colors[i % colors.length];
                        
                        // 畫彩虹扇形
                        ctx.beginPath();
                        ctx.arc(cx, cy, radius, angle, angle + arc, false);
                        ctx.arc(cx, cy, 0, angle + arc, angle, true);
                        ctx.fill();

                        ctx.save();
                        ctx.translate(cx + Math.cos(angle + arc / 2) * (radius - 90), 
                                      cy + Math.sin(angle + arc / 2) * (radius - 90));
                        ctx.rotate(angle + arc / 2 + Math.PI / 2);

                        const brandName = brands[i];
                        const img = loadedImages[brandName];

                        // 如果圖片載入完成就顯示圖片，否則顯示品牌文字
                        if (img && img.complete && img.naturalWidth !== 0) {{
                            const imgSize = 55;
                            ctx.drawImage(img, -imgSize / 2, -imgSize / 2, imgSize, imgSize);
                        }} else {{
                            ctx.fillStyle = "white";
                            ctx.font = "bold 16px sans-serif";
                            ctx.fillText(brandName, -ctx.measureText(brandName).width / 2, 0);
                        }}
                        
                        ctx.restore();
                    }}

                    // 指針
                    ctx.fillStyle = "#333";
                    ctx.beginPath();
                    ctx.moveTo(cx - 16, cy - radius - 8);
                    ctx.lineTo(cx + 16, cy - radius - 8);
                    ctx.lineTo(cx, cy - radius + 22);
                    ctx.fill();
                }}

                // 2. 先立即強制渲染一次轉盤（確保畫布絕對不空白）
                drawWheel();

                // 3. 預載入圖片，載入完成後補刷圖片
                for (let b of brands) {{
                    if (brandImgMap[b]) {{
                        const img = new Image();
                        img.src = brandImgMap[b];
                        img.onload = function() {{
                            loadedImages[b] = img;
                            drawWheel(); // 圖片載入完成，補刷
                        }};
                    }}
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
                    const index = Math.floor((360 - degrees % 360) / arcd) % brands.length;
                    const winnerBrand = brands[index];

                    document.getElementById('winner-display').innerHTML = "🎉 今天就吃：【" + winnerBrand + "】！";

                    const storeContainer = document.getElementById('store-list-container');
                    const stores = storesData[winnerBrand] || [];

                    let htmlContent = '<h3 style="margin-top:0; color:#333;">📍 【' + winnerBrand + '】門市據點與訂位連結：</h3>';
                    
                    stores.forEach(s => {{
                        const bookingHtml = s.booking_url 
                            ? '<a href="' + s.booking_url + '" target="_blank" class="booking-btn">👉 立即線上訂位</a>'
                            : '<span class="no-booking">無線上訂位</span>';

                        htmlContent += '<div class="store-item">' +
                            '<div>' +
                                '<div class="store-name">🏠 ' + s.full_name + '</div>' +
                                '<div class="store-address">📍 地址：' + s.address + '</div>' +
                            '</div>' +
                            '<div>' + bookingHtml + '</div>' +
                        '</div>';
                    }});

                    storeContainer.innerHTML = htmlContent;
                    storeContainer.style.display = 'block';
                }}

                function easeOut(t, b, c, d) {{
                    const ts = (t/=d)*t;
                    const tc = ts*t;
                    return b+c*(tc + -3*ts + 3*t);
                }}

                function spin() {{
                    document.getElementById('winner-display').innerHTML = "🎲 轉盤轉動中... 猜猜看會抽中哪一家...";
                    document.getElementById('store-list-container').style.display = 'none';
                    spinAngleStart = Math.random() * 10 + 10;
                    spinTime = 0;
                    spinTimeTotal = Math.random() * 3000 + 4000;
                    rotateWheel();
                }}
            </script>
        </body>
        </html>
        """

        components.html(wheel_html, height=1300)

st.markdown("---")
if st.button("🏠 回到首頁", key="bottom_home_5"):
    st.switch_page("wowprime.py")





# ---------------------------------------------------------
# 頁尾：技術標籤、開發者權益與免責聲明
# ---------------------------------------------------------
st.markdown("---")

# 1. 技術框架與數據源標示
st.caption(
    "Powered by Streamlit | 數據來源：王品集團官網 & Google Maps 公開數據"
)

# 2. 開發者資訊與原創保護聲明
st.caption(
    "**專案開發者：何莉維 | 開發時間：2026年8月 **"
    "**聲明 (Disclaimer & Copyright)**：\n"
    "1. 原創聲明與著作權保護：本專案程式碼、UI 佈局與數據分析架構由開發者獨立完成，僅作為個人作品集展示（Academic"
    " Portfolio）。未經原作者授權，禁止擅自複製、抄襲重製或作為他人課程作業/報告提交。\n"
    "2. 數據與商標權屬：本專案無任何商業營利用途。專案中引用之品牌名稱、LOGO 商標與門市公開數據，其智慧財產權分別歸王品集團與"
    " Google 所有。"
)

import time
import folium
from geopy.geocoders import Nominatim

place = "台北市中正區羅斯福路二段9號"

# 🎯 關鍵修復：必須給予一個自訂且獨特的 user_agent，避免被 OSM 判定為惡意爬蟲發送 403 拒絕
geolocator = Nominatim(user_agent="my_wowprime_project_v1")

try:
    # 發送轉換請求
    location = geolocator.geocode(place, timeout=10)

    if location:
        print(f"✅ 成功轉換地址：{place}")
        print(f"📍 緯度 (Lat): {location.latitude}")
        print(f"📍 經度 (Lng): {location.longitude}")
        print(f"📍 完整地名: {location.address}")

        # 建立 Folium 地圖
        m = folium.Map(location=[location.latitude, location.longitude], zoom_start=16)
        folium.Marker([location.latitude, location.longitude], popup=place).add_to(m)
        m.save("map.html")
        print("🗺️ 地圖已順利儲存為 map.html")

    else:
        print(f"❌ OSM 資料庫中找不到地址：{place}")

except Exception as e:
    print(f"❌ 發生錯誤: {e}")
  
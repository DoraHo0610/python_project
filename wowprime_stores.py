import getpass
import os
import re
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 載入 .env 設定
load_dotenv("./.env", override=True)


# ==========================================
# 0. 共用工具函式 (地址拆解)
# ==========================================
def parse_address_info(address: str):
    if not address:
        return None, None
    match = re.match(r"^(.{2}[縣市])(.{1,4}[鄉鎮市區])", address.strip())
    if match:
        return match.group(1), match.group(2)
    elif len(address) >= 3:
        return address[:3], None
    return None, None


# ==========================================
# 1. 各品牌專屬爬蟲函式區 (依序擴充)
# ==========================================


# --- [品牌 1] 王品牛排 ---
def scrape_wangsteak(brand_id: int):
    brand_name = "王品牛排"
    url = "https://www.wangsteak.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        card_contents = soup.select("div.card-content")
        for card in card_contents:
            title_el = card.select_one("div.title")
            store_name = title_el.text.strip() if title_el else ""

            phone_el = card.select_one("a.phone")
            phone = phone_el.text.strip() if phone_el else ""

            addr_el = card.select_one("a.address")
            address = addr_el.text.strip() if addr_el else ""

            booking_el = card.select_one("a.normal-btn.a")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )
        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")
    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 2] 西堤牛排 ---
def scrape_tasty(brand_id: int):
    brand_name = "西堤牛排"
    url = "https://www.tasty.com.tw/shop/list.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        shop_cards = soup.select("div.ShopList__shopInner")
        for card in shop_cards:
            name_el = card.select_one("div.ShopList__shopName a")
            store_name = name_el.text.strip() if name_el else ""

            phone_el = card.select_one("div.ShopList__shopPhone a")
            phone = phone_el.text.strip() if phone_el else ""

            addr_el = card.select_one("div.ShopList__shopAdd a")
            address = addr_el.text.strip() if addr_el else ""

            booking_el = card.select_one(
                "div.ShopList__shopBtns a[href*='inline'],"
                " div.ShopList__shopBtns a"
            )
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )
        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")
    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 3] 原燒 日式燒肉 ---
def scrape_yakiyan(brand_id: int):
    brand_name = "原燒"
    url = "https://www.yakiyan.com/store-list.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片區塊
        store_rows = soup.select("div.store-row")

        for row in store_rows:
            # 2. 抓取門市名稱 (div.store-name > a)
            name_el = row.select_one("div.store-name a")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 抓取地址 (div.address > a)
            addr_el = row.select_one("div.address a")
            address = addr_el.text.strip() if addr_el else ""

            # 4. 抓取電話 (div.phone > a)
            phone_el = row.select_one("div.phone a")
            phone = phone_el.text.strip() if phone_el else ""

            # 5. 抓取線上訂位連結 (div.btn-online-booking > a)
            booking_el = row.select_one("div.btn-online-booking a")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 6. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 4] 聚 日式鍋物 ---
def scrape_giguo(brand_id: int):
    brand_name = "聚 日式鍋物"
    url = "https://www.giguo.com.tw/store-list.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市區塊 <div class="bottom-box">
        boxes = soup.select("div.bottom-box")

        for box in boxes:
            # 2. 分店名稱 (<div class="title"> > a)
            name_el = box.select_one("div.title a")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 地址 (<div class="address"> > span > a 或 div.address a)
            addr_el = box.select_one("div.address a")
            address = addr_el.text.strip() if addr_el else ""

            # 4. 電話 (<div class="phone"> > a)
            phone_el = box.select_one("div.phone a")
            phone = phone_el.text.strip() if phone_el else ""

            # 5. 線上訂位連結 (<div class="btn btn-online-booking"> > a)
            booking_el = box.select_one("div.btn.btn-online-booking a")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 6. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"聚 {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 5] 藝奇 和牛岩板燒日本料理 ---
def scrape_ikki(brand_id: int):
    brand_name = "藝奇"
    url = "https://www.ikki.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 <div class="row no-gutters store-list-item">
        items = soup.select("div.store-list-item")

        for item in items:
            # 2. 分店名稱 (div.store-list-name > a)
            name_el = item.select_one("div.store-list-name a")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 地址 (div.store-list-add > p)
            # p 標籤裡面包含地址與「查看地圖」連結，先移除 a 標籤再取純文字
            add_div = item.select_one("div.store-list-add")
            address = ""
            if add_div:
                p_tag = add_div.select_one("p")
                if p_tag:
                    # 複製一個副本處理，避免影響原 DOM
                    p_clone = BeautifulSoup(str(p_tag), "html.parser")
                    for a_map in p_clone.find_all("a"):
                        a_map.decompose()  # 移除地圖連結文字
                    address = p_clone.text.strip()

            # 4. 電話 (div.store-list-tel > a)
            phone_el = item.select_one("div.store-list-tel a")
            phone = phone_el.text.strip() if phone_el else ""

            # 5. 線上訂位連結 (div.store-list-online > a)
            booking_el = item.select_one("div.store-list-online a")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 6. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"藝奇 {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 6] 夏慕尼 新香榭鐵板燒 ---
def scrape_chamonix(brand_id: int):
    brand_name = "夏慕尼"
    # 🎯 直接請求夏慕尼門市資料的後端 API（或將網址改為 AJAX 接口）
    # 如果官方有 Ajax 介面，通常是 POST 或 GET 帶參數，以下為直接抓取全門市 JSON 的標準寫法
    url = "https://www.chamonix.com.tw/store.php"
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest"  # 偽裝成 AJAX 請求
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        
        # 嘗試解析 HTML 裡面的 JavaScript 變數（許多王品系列網站會把 storeData 直接寫在 <script> 裡）
        script_match = re.search(r"var\s+stores\s*=\s*(\[.*?\]);", res.text, re.DOTALL)
        
        if script_match:
            # 情況 A：門市資料以 JSON 陣列藏在 <script> 標籤內
            import json
            raw_json = script_match.group(1)
            store_data_list = json.loads(raw_json)
            
            for item in store_data_list:
                store_name = item.get("name", "").replace("夏慕尼", "").strip()
                address = item.get("address", "").strip()
                phone = item.get("phone", "").strip()
                booking_url = item.get("booking_url") or item.get("inline_url") or item.get("link")
                
                city, district = parse_address_info(address)
                
                stores.append({
                    "brand_id": brand_id,
                    "store_name": store_name,
                    "full_name": f"夏慕尼 {store_name}",
                    "address": address,
                    "city": city,
                    "district": district,
                    "phone": phone,
                    "booking_url": booking_url,
                    "business_hours": "詳見官網",
                    "status": "營業中",
                })
        else:
            # 情況 B：若無法直接抓 JSON，改用 BeautifulSoup 解析完整包含 JS 區塊的 HTML
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select("div.p-2")

            for card in cards:
                name_el = card.select_one("div.text-break")
                store_name = name_el.text.strip() if name_el else ""

                address = ""
                phone = ""
                tr_elements = card.select("table tr")

                for tr in tr_elements:
                    tr_text = tr.text
                    if "地址" in tr_text:
                        addr_td = tr.select_one("td")
                        if addr_td:
                            address = addr_td.text.strip()
                    elif "電話" in tr_text:
                        phone_td = tr.select_one("td")
                        if phone_td:
                            phone = phone_td.text.strip()

                # 🎯 全網頁搜尋：直接在整個網頁原始碼 (res.text) 搜尋該店名對應的 inline 網址
                booking_url = None
                if store_name:
                    # 在整份網頁文字中搜尋包含該門市名稱與 inline.app 的區塊
                    pattern = rf"{store_name}.*?(https://inline\.app/booking/[^\s'\"]+)"
                    match = re.search(pattern, res.text, re.DOTALL)
                    if match:
                        booking_url = match.group(1)
                    else:
                        # 備用：直接搜尋整份網頁裡出現的所有 inline 網址
                        all_inlines = re.findall(r"https://inline\.app/booking/[^\s'\"]+", res.text)
                        # 如果有找到且數目對得上，依序比對
                        if all_inlines:
                            # 嘗試從 card 的周邊 HTML 撈取
                            parent_html = str(card.parent)
                            p_match = re.search(r"https://inline\.app/booking/[^\s'\"]+", parent_html)
                            if p_match:
                                booking_url = p_match.group(0)

                city, district = parse_address_info(address)

                if store_name:
                    stores.append({
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"夏慕尼 {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    })

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 7] 陶板屋 和風創意料理 ---
def scrape_tokiya(brand_id: int):
    brand_name = "陶板屋"
    url = "https://www.tokiya.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 section.item
        items = soup.select("section.item")

        for item in items:
            # 2. 分店名稱 (div.name)
            name_el = item.select_one("div.name")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 電話 (li.phone a)
            phone_el = item.select_one("li.phone a")
            phone = phone_el.text.strip() if phone_el else ""

            # 4. 地址 (抓第一個非 phone / time 區塊的 cms-txt，或特定 li 裡面的 cms-txt)
            address = ""
            addr_li = item.select_one("ul.data-list > li:not(.phone):not(.time) div.cms-txt")
            if addr_li:
                address = addr_li.text.strip()
            else:
                # 備用方案：尋找沒有 class 的 li 下的 cms-txt
                all_cms = item.select("ul.data-list div.cms-txt")
                if all_cms:
                    address = all_cms[0].text.strip()

            # 5. 營業時間 (li.time div.cms-txt)
            time_el = item.select_one("li.time div.cms-txt")
            business_hours = time_el.text.strip() if time_el else "詳見官網"

            # 6. 線上訂位連結 (div.other-btn 裡找線上訂位的 a 標籤)
            booking_el = item.select_one("div.other-btn a[title*='訂位'], div.other-btn a[href*='inline']")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 7. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 8] 品田牧場 日式豬排定食 ---
def scrape_pinnada(brand_id: int):
    brand_name = "品田牧場"
    url = "https://www.pinnada.com.tw/branch.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.store-detail
        details = soup.select("div.store-detail")

        for detail in details:
            # 2. 分店名稱 (div.store-name > a)
            name_el = detail.select_one("div.store-name a")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 地址 (div.address > a)
            addr_el = detail.select_one("div.address a")
            address = addr_el.text.strip() if addr_el else ""

            # 4. 電話 (div.tel > a)
            phone_el = detail.select_one("div.tel a")
            phone = phone_el.text.strip() if phone_el else ""

            # 5. 線上訂位連結 (div.links 裡的第一個 a 標籤或包含 reserve_web/inline 的連結)
            booking_el = detail.select_one("div.links a")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 6. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 9] 石二鍋 ---
def scrape_12hotpot(brand_id: int):
    brand_name = "石二鍋"
    url = "https://www.12hotpot.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.store-item
        items = soup.select("div.store-item")

        for item in items:
            # 2. 分店名稱 (h4.fz-C > strong)
            name_el = item.select_one("h4.fz-C strong")
            if not name_el:
                name_el = item.select_one("h4.fz-C")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 電話 (a[href*='tel:'])
            phone_el = item.select_one("a[href^='tel:']")
            phone = phone_el.text.strip() if phone_el else ""

            # 4. 地址 (a[href*='google.com/maps'])
            addr_el = item.select_one("a[href*='google.com/maps']")
            address = addr_el.text.strip() if addr_el else ""

            # 5. 營業時間 (抓取 ewa-rteLine 的文字組合)
            time_lines = item.select("div.ewa-rteLine")
            if time_lines:
                business_hours = " ".join([line.text.strip() for line in time_lines if line.text.strip()])
            else:
                business_hours = "詳見官網"

            # 6. 線上訂位連結 (尋找 inline 或 reserve 相關連結，若無則為 None)
            booking_el = item.select_one("a[href*='inline'], a[href*='reserve']")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else 'https://page.line.me/118pulop'
            )

            # 7. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 10] 青花驕 麻辣鍋 ---
def scrape_chinhuajiao(brand_id: int):
    brand_name = "青花驕"
    url = "https://www.chinhuajiao.com/stores.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # 預設的線上訂位連結
    default_booking_url = (
        "https://inline.app/booking/-MaXEQcbiWaRjXyLytUu:inline-live-2?language=zh-tw"
    )

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.store-detail 或 div.detail
        details = soup.select("div.detail")

        for detail in details:
            # 2. 分店名稱 (div.name)
            name_el = detail.select_one("div.name")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 解析地址與電話 (div.detail_add > p)
            address = ""
            phone = ""
            p_tags = detail.select("div.detail_add p")

            if len(p_tags) >= 1:
                address = p_tags[0].text.strip()
            if len(p_tags) >= 2:
                phone = p_tags[1].text.strip()

            # 4. 線上訂位連結 (若找不到則帶入預設 inline 連結)
            booking_el = detail.select_one("a[href*='inline'], a[href*='reserve']")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else default_booking_url
            )

            # 5. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 11] 享鴨 烤鴨與中華料理 ---
def scrape_xiangduck(brand_id: int):
    brand_name = "享鴨"
    url = "https://www.xiangduck.com.tw/shops.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.shops_sec
        shops = soup.select("div.shops_sec")

        for shop in shops:
            # 2. 分店名稱 (div.shops_sec_title > h1)
            name_el = shop.select_one("div.shops_sec_title h1")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 線上訂位連結 (div.shops_sec_map > a)
            booking_el = shop.select_one("div.shops_sec_map a[href*='reserve'], div.shops_sec_map a[href*='inline'], div.shops_sec_map a")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 4. 解析地址、電話與營業時間 (遍歷 div.shops_sec_text)
            address = ""
            phone = ""
            business_hours = "詳見官網"

            text_boxes = shop.select("div.shops_sec_text")
            for box in text_boxes:
                h1_text = box.select_one("h1").text if box.select_one("h1") else ""
                
                if "地" in h1_text and "址" in h1_text:
                    h2_el = box.select_one("h2")
                    if h2_el:
                        address = h2_el.text.strip()
                elif "話" in h1_text:
                    h2_el = box.select_one("h2")
                    if h2_el:
                        phone = h2_el.text.strip()
                elif "營業時間" in h1_text:
                    time_el = box.select_one("div.editor-container") or box.select_one("div.ql-snow")
                    if time_el:
                        business_hours = " ".join(time_el.stripped_strings)

            # 5. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 12] 丰禾 台味風格料理 ---
def scrape_veggtable(brand_id: int):
    brand_name = "丰禾"
    url = "https://www.veggtable.com/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # 預設線上訂位連結
    default_booking_url = (
        "https://inline.app/booking/-MaXEa1W0wx-8phbX8w-:inline-live-2?language=zh-tw?utm_source=web"
    )

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.storeItem
        items = soup.select("div.storeItem")

        for item in items:
            # 2. 分店名稱 (h4.title)
            name_el = item.select_one("h4.title")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 電話 (a[href^='tel:'])
            phone_el = item.select_one("a[href^='tel:']")
            phone = phone_el.text.strip() if phone_el else ""

            # 4. 地址 (a[href*='google.com/maps'])
            addr_el = item.select_one("a[href*='google.com/maps']")
            address = addr_el.text.strip() if addr_el else ""

            # 5. 營業時間 (抓取 storeIntro 裡面的 editor-container 純文字)
            business_hours = "詳見官網"
            time_container = item.select_one("div.storeIntro div.editor-container")
            if time_container:
                business_hours = " ".join(time_container.stripped_strings)

            # 6. 線上訂位連結 (若找不到則帶入預設 inline 連結)
            booking_el = item.select_one("a[href*='inline'], a[href*='reserve']")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else default_booking_url
            )

            # 7. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 13] 12MINI 快煮小火鍋 ---
def scrape_12mini(brand_id: int):
    brand_name = "12MINI"
    url = "https://www.12mini.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.card--store
        cards = soup.select("div.card--store")

        for card in cards:
            # 2. 分店名稱 (div.caption__title)
            name_el = card.select_one("div.caption__title")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 電話 (a.contect__phone 或 a[href^='tel:'])
            phone_el = card.select_one("a.contect__phone, a[href^='tel:']")
            phone = phone_el.text.strip() if phone_el else ""

            # 4. 地址與營業時間 (解析各 content__desc 區塊)
            address = ""
            business_hours = "詳見官網"

            desc_list = card.select("div.content__desc")
            for desc in desc_list:
                # 若包含 editor-container，代表是營業時間區塊
                editor = desc.select_one("div.editor-container")
                if editor:
                    business_hours = " ".join(editor.stripped_strings)
                # 若沒有 editor 且不包含 tel: 連結，則為地址區塊
                elif not desc.select_one("a[href^='tel:']"):
                    txt = desc.text.strip()
                    if txt:
                        address = txt

            # 5. 外帶點餐連結 (替代 booking_url)
            # 優先搜尋 ga-label="外帶點餐" 的 a 標籤或包含 order/wowprime 的外帶連結
            takeout_el = card.select_one("a[ga-label='外帶點餐'], a[href*='aio2.wowprime.com'], a[href*='order']")
            booking_url = (
                takeout_el["href"]
                if takeout_el and takeout_el.has_attr("href")
                else None
            )

            # 6. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,  # 存放外帶點餐連結
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 14] 和牛涮 日式鍋物放題 ---
def scrape_wagyushabu(brand_id: int):
    brand_name = "和牛涮"
    base_url = "https://www.wagyushabu.com.tw/"
    start_url = "https://www.wagyushabu.com.tw/store_detail.php?store=10"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        # 步驟 1：先請求進入第一個分店頁面
        res = requests.get(start_url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        store_urls = set()
        store_urls.add(start_url)

        # 步驟 2：從 <input onclick="..."> 中用正則表達式提取所有分店連結
        input_buttons = soup.select("input[onclick*='store_detail.php']")
        for btn in input_buttons:
            onclick_text = btn.get("onclick", "")
            # 正則表達式抓取 store_detail.php?store=數字
            match = re.search(r"store_detail\.php\?store=\d+", onclick_text)
            if match:
                full_url = base_url + match.group(0)
                store_urls.add(full_url)

        print(f"🔍 【{brand_name}】共成功解析出 {len(store_urls)} 個分店連結，開始逐一採集...")

        # 步驟 3：迴圈進入各分店頁面爬取詳細資料
        for detail_url in store_urls:
            try:
                sub_res = requests.get(detail_url, headers=headers, timeout=10)
                sub_res.encoding = "utf-8"
                sub_soup = BeautifulSoup(sub_res.text, "html.parser")

                # (1) 分店名稱 (h3 標籤)
                name_el = sub_soup.select_one("h3")
                store_name = name_el.text.strip() if name_el else ""

                if not store_name:
                    continue

                # (2) 線上訂位連結 (a.cow_button 或包含 inline 的 a 標籤)
                booking_el = sub_soup.select_one("a.cow_button, a[href*='inline']")
                booking_url = (
                    booking_el["href"]
                    if booking_el and booking_el.has_attr("href")
                    else None
                )

                # (3) 解析 table 裡面的 電話、地址、營業時間
                phone = ""
                address = ""
                business_hours = "詳見官網"

                tr_elements = sub_soup.select("table tr")
                for tr in tr_elements:
                    tr_text = tr.text
                    if "電話" in tr_text:
                        tel_a = tr.select_one("a[href^='tel:']")
                        if tel_a:
                            phone = tel_a.text.strip()
                    elif "地址" in tr_text:
                        addr_div = tr.select_one("div.text-break") or tr.select_one("td")
                        if addr_div:
                            address = addr_div.text.strip()
                    elif "店舖介紹" in tr_text:
                        intro_div = tr.select_one("div.editor-container") or tr.select_one("td")
                        if intro_div:
                            business_hours = " ".join(intro_div.stripped_strings)

                # (4) 解析縣市與鄉鎮區
                city, district = parse_address_info(address)

                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

            except Exception as sub_e:
                print(f"⚠️ 抓取分店頁面失敗 [{detail_url}]: {sub_e}")

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 15] 尬鍋 台式潮鍋 ---
def scrape_godguo(brand_id: int):
    brand_name = "尬鍋"
    url = "https://www.godguo.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # 指定的線上訂位連結
    default_booking_url = "https://inline.app/booking/-MMxL4IS9O7Uv0VE6H5f:inline-live-2?language=zh-tw"

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 section.shops_section
        sections = soup.select("section.shops_section")

        for section in sections:
            # 2. 分店名稱 (h1 標籤)
            name_el = section.select_one("h1")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 電話 (a[href^='tel:'] 或包含號碼的 h2)
            phone = ""
            phone_el = section.select_one("a[href^='tel:']")
            if phone_el:
                phone = phone_el.text.strip()

            # 4. 地址 (a[href*='google.com/maps'] 或後續 h2)
            address = ""
            map_a = section.select_one("a[href*='google.com/maps']")
            if map_a:
                # 嘗試從地圖連結的文字提取（若包含地址）
                map_text = map_a.text.strip()
                if "MAP" not in map_text and len(map_text) > 5:
                    address = map_text

            # 如果地圖連結只是按鈕，從所有 h2 標籤中比對電話與地址
            h2_tags = [h2.text.strip() for h2 in section.select("h2") if h2.text.strip()]
            for txt in h2_tags:
                if not phone and re.search(r"\d{2,4}-?\d{6,8}", txt):
                    phone = txt
                elif not address and ("市" in txt or "縣" in txt) and ("區" in txt or "鄉" in txt or "鎮" in txt or "路" in txt or "街" in txt):
                    address = txt

            # 5. 營業時間 (尋找 <h3>營業時間</h3> 後方的 <h2> 或內容)
            business_hours = "詳見官網"
            h3_tags = section.select("h3")
            for h3 in h3_tags:
                if "營業時間" in h3.text:
                    next_h2 = h3.find_next_sibling("h2")
                    if next_h2:
                        business_hours = next_h2.text.strip()
                    break

            # 6. 線上訂位連結 (依需求固定帶入指定的 inline 連結)
            booking_url = default_booking_url

            # 7. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 16] 肉次方 燒肉放題 ---
def scrape_powerofmeat(brand_id: int):
    brand_name = "肉次方"
    url = "https://www.powerofmeat.com.tw/shop-location"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.location-card
        cards = soup.select("div.location-card")

        for card in cards:
            # 2. 分店名稱 (h4.card-title)
            name_el = card.select_one("h4.card-title")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 電話 (a[href^='tel:'])
            phone_el = card.select_one("a[href^='tel:']")
            phone = phone_el.text.strip() if phone_el else ""

            # 4. 地址 (a[href*='google.com/maps'])
            addr_el = card.select_one("a[href*='google.com/maps']")
            address = addr_el.text.strip() if addr_el else ""

            # 5. 營業時間 (div.ql-editor 裡的純文字)
            time_el = card.select_one("div.ql-editor")
            business_hours = (
                " ".join(time_el.stripped_strings) if time_el else "詳見官網"
            )

            # 6. 線上訂位連結 (a.order-btn 或包含 reserve/inline 的連結)
            booking_el = card.select_one(
                "a.order-btn, a[href*='reserve'], a[href*='inline']"
            )
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 7. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores




# --- [品牌 17] 金咕 韓式原塊烤肉 ---
def scrape_chingubbq(brand_id: int):
    brand_name = "金咕"
    url = "https://www.chingubbq.com.tw/branch.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.card--branch
        cards = soup.select("div.card--branch")

        for card in cards:
            # 2. 分店名稱 (h2)
            name_el = card.select_one("h2")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 地址 (caption__content is-address -> 雙底線)
            address = ""
            addr_div = card.select_one("div.caption__content.is-address span")
            if addr_div:
                # 複製一份節點處理，避免分解影響原 DOM
                addr_clone = BeautifulSoup(str(addr_div), "html.parser")
                for a_map in addr_clone.find_all("a"):
                    a_map.decompose()  # 移除 GoogleMap 連結文字
                address = (
                    addr_clone.text.replace("(", "")
                    .replace(")", "")
                    .strip()
                )

            # 4. 電話 (caption__content is-phone -> 雙底線)
            phone_el = card.select_one("div.caption__content.is-phone span")
            phone = phone_el.text.strip() if phone_el else ""

            # 5. 營業時間 (caption__content is-time -> 雙底線)
            time_el = card.select_one("div.caption__content.is-time span")
            business_hours = (
                " ".join(time_el.stripped_strings) if time_el else "詳見官網"
            )

            # 6. 線上訂位連結 (div.card--button 裡的第一個 a 標籤或包含 inline 的連結)
            booking_el = card.select_one(
                "div.card--button a.button--primary, a[href*='inline']"
            )
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 7. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores



# --- [品牌 18] 就饗鐵板燒 ---
# --- Inline.app 訂位系統 ---
def scrape_joxiang(brand_id: int):
    brand_name = "就饗鐵板燒"

    # 由於 Inline 設有防爬蟲驗證阻擋 requests，直接定義 5 家門市完整資料檔
    joxiang_raw_data = [
        {
            "store_name": "台北忠孝東店",
            "address": "台北市大安區忠孝東路四段49巷4弄10號",
            "phone": "02-2731-6008",
            "booking_url": "https://inline.app/booking/-NNAYIs0cQ18gM5Ixkfg:inline-live-3/-NNAYJ26fCjNgGOSff_h",
        },
        {
            "store_name": "台北長安東店",
            "address": "台北市中山區長安東路二段78-2號1樓",
            "phone": "02-2508-2252",
            "booking_url": "https://inline.app/booking/-NNAYIs0cQ18gM5Ixkfg:inline-live-3/-NdotMJWMYFGe_hfXbtK",
        },
        {
            "store_name": "蘆洲萬家福店",
            "address": "新北市蘆洲區五華街282號4樓",
            "phone": "02-2857-2252",
            "booking_url": "https://inline.app/booking/-NNAYIs0cQ18gM5Ixkfg:inline-live-3/-OCrbXjdvt7_oiRk5gfo",
        },
        {
            "store_name": "高雄富民店",
            "address": "高雄市左營區富民路353號",
            "phone": "07-558-0198",
            "booking_url": "https://inline.app/booking/-NNAYIs0cQ18gM5Ixkfg:inline-live-3/-O-B-ncwUqfqXCLMaVoy",
        },
        {
            "store_name": "高雄夢時代店",
            "address": "高雄市前鎮區中華五路789號1樓",
            "phone": "07-823-2252",
            "booking_url": "https://inline.app/booking/-NNAYIs0cQ18gM5Ixkfg:inline-live-3/-O-BP_9JD7tV4kPaLDop",
        },
    ]

    stores = []
    try:
        for item in joxiang_raw_data:
            store_name = item["store_name"]
            address = item["address"]
            phone = item["phone"]
            booking_url = item["booking_url"]

            # 自動解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            stores.append(
                {
                    "brand_id": brand_id,
                    "store_name": store_name,
                    "full_name": f"{brand_name} {store_name}",
                    "address": address,
                    "city": city,
                    "district": district,
                    "phone": phone,
                    "booking_url": booking_url,
                    "business_hours": "詳見訂位頁面",
                    "status": "營業中",
                }
            )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores




# --- [品牌 19] 莆田 PUTIEN ---
def scrape_putien(brand_id: int):
    brand_name = "莆田"
    url = "https://www.putien.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市文字卡片區塊 div.text-control
        cards = soup.select("div.text-control")

        for card in cards:
            # 2. 分店名稱 (div.text-title)
            name_el = card.select_one("div.text-title")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 地址 (div.adr 下方的 a 標籤)
            addr_el = card.select_one("div.adr a")
            address = addr_el.text.strip() if addr_el else ""

            # 4. 電話 (div.phone 下方的 a 標籤)
            phone_el = card.select_one("div.phone a")
            phone = phone_el.text.strip() if phone_el else ""

            # 5. 線上訂位連結 (div.simple-button-box 下方包含 inline 的 a 標籤)
            booking_el = card.select_one("div.simple-button-box a[href*='inline']")
            booking_url = (
                booking_el["href"]
                if booking_el and booking_el.has_attr("href")
                else None
            )

            # 6. 解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": "詳見官網",
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# --- [品牌 20] 阪前和牛鐵板燒 ---
# --- Inline.app 訂位系統 ---
def scrape_itamae(brand_id: int):
    brand_name = "阪前和牛鐵板燒"

    # 由於 Inline 設有防爬蟲驗證阻擋 requests，直接定義門市資料清單
    itamae_raw_data = [
        {
            "store_name": "台北中山北店",
            "address": "台北市中山區中山北路二段52號",
            "phone": "0225221399",
            "booking_url": (
                "https://inline.app/booking/-NEd6gWFYYn694vcUeG2:inline-live-1/-NEd6gjTQN396tI1yHYd"
            ),
        },
        {
            "store_name": "台中文心五權西店",
            "address": "台中市南屯區五權西路二段273號",
            "phone": "0424721799",
            "booking_url": (
                "https://inline.app/booking/-NEd6gWFYYn694vcUeG2:inline-live-1/-NdnwYI2CIHJodVa3Pi0"
            ),
        },
        {
            "store_name": "台北安和店",
            "address": "台北市大安區安和路一段116號",
            "phone": "0227840068",
            "booking_url": (
                "https://inline.app/booking/-NEd6gWFYYn694vcUeG2:inline-live-1/-O5Deb568CnBfTTVTesb"
            ),
        },
        {
            "store_name": "桃園台茂店",
            "address": "桃園市蘆竹區南崁路一段112號B2",
            "phone": "033120350",
            "booking_url": (
                "https://inline.app/booking/-NEd6gWFYYn694vcUeG2:inline-live-1/-O5Dec9Zp3yD7RNWqKnq"
            ),
        },
        {
            "store_name": "板橋民生店",
            "address": "新北市板橋區民生路二段251號2樓",
            "phone": "02-82581801",
            "booking_url": (
                "https://inline.app/booking/-NEd6gWFYYn694vcUeG2:inline-live-1/-OQ2NU4kc_NPTA1sPbgZ"
            ),
        },
        {
            "store_name": "台北SOGO忠孝店",
            "address": "台北市大安區忠孝東路四段45號11樓",
            "phone": "0227789155",
            "booking_url": (
                "https://inline.app/booking/-NEd6gWFYYn694vcUeG2:inline-live-1/-Of1n4RH9GPdMbjMeIq9"
            ),
        },
    ]

    stores = []
    try:
        for item in itamae_raw_data:
            store_name = item["store_name"]
            address = item["address"]
            phone = item["phone"]
            booking_url = item["booking_url"]

            # 自動解析縣市與鄉鎮區
            city, district = parse_address_info(address)

            stores.append(
                {
                    "brand_id": brand_id,
                    "store_name": store_name,
                    "full_name": f"{brand_name} {store_name}",
                    "address": address,
                    "city": city,
                    "district": district,
                    "phone": phone,
                    "booking_url": booking_url,
                    "business_hours": "詳見訂位頁面",
                    "status": "營業中",
                }
            )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores




# ==========================================
# 2. 主執行流程 (Main Pipeline)
# ==========================================
def main():
    # 1. MySQL 資料庫連線
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER") or input("DB user: ")
    DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass(
        "DB password: "
    )
    DB_NAME = os.environ.get("DB_NAME", "wowprime")

    engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(engine_url)

    # 2. 撈取 brands 資料表中的品牌名單對照表
    print("🔍 正在獲取資料庫中的品牌對照資料...")
    brands_df = pd.read_sql(
        "SELECT brand_id, brand_name FROM brands;", con=engine
    )

    # 建立輔助函式：用品牌關鍵字尋找 brand_id
    def get_brand_id(keyword):
        matched = brands_df[
            brands_df["brand_name"].str.contains(keyword, na=False)
        ]
        if not matched.empty:
            return int(matched.iloc[0]["brand_id"])
        return None

    all_stores = []

    #3. 依序執行各品牌門市採集
    # (1) 抓取王品牛排
    wang_id = get_brand_id("王品")
    wang_stores = scrape_wangsteak(brand_id=wang_id)
    all_stores.extend(wang_stores)

    # (2) 抓取西堤牛排
    tasty_id = get_brand_id("西堤") or get_brand_id("TASTy")
    tasty_stores = scrape_tasty(brand_id=tasty_id)
    all_stores.extend(tasty_stores)

    # (3) 抓取原燒
    yakiyan_id = get_brand_id("原燒")
    yakiyan_stores = scrape_yakiyan(brand_id=yakiyan_id)
    all_stores.extend(yakiyan_stores)

    # (4) 抓取 聚 日式鍋物
    giguo_id = get_brand_id("聚")
    giguo_stores = scrape_giguo(brand_id=giguo_id)
    all_stores.extend(giguo_stores)


    # (5) 抓取 藝奇
    ikki_id = get_brand_id("藝奇")
    ikki_stores = scrape_ikki(brand_id=ikki_id)
    all_stores.extend(ikki_stores)

    # (6) 抓取 夏慕尼
    chamonix_id = get_brand_id("夏慕尼")
    chamonix_stores = scrape_chamonix(brand_id=chamonix_id)
    all_stores.extend(chamonix_stores)


    # (7) 抓取 陶板屋
    tokiya_id = get_brand_id("陶板屋")
    tokiya_stores = scrape_tokiya(brand_id=tokiya_id)
    all_stores.extend(tokiya_stores)


    # (8) 抓取 品田牧場
    pinnada_id = get_brand_id("品田")
    pinnada_stores = scrape_pinnada(brand_id=pinnada_id)
    all_stores.extend(pinnada_stores)


    # (9) 抓取 石二鍋
    hotpot_id = get_brand_id("石二鍋")
    hotpot_stores = scrape_12hotpot(brand_id=hotpot_id)
    all_stores.extend(hotpot_stores)


    # (10) 抓取 青花驕
    chinhuajiao_id = get_brand_id("青花驕")
    chinhuajiao_stores = scrape_chinhuajiao(brand_id=chinhuajiao_id)
    all_stores.extend(chinhuajiao_stores)


    # (11) 抓取 享鴨
    xiangduck_id = get_brand_id("享鴨")
    xiangduck_stores = scrape_xiangduck(brand_id=xiangduck_id)
    all_stores.extend(xiangduck_stores)


    # (12) 抓取 丰禾
    veggtable_id = get_brand_id("丰禾")
    veggtable_stores = scrape_veggtable(brand_id=veggtable_id)
    all_stores.extend(veggtable_stores)


    # (13) 抓取 12MINI
    mini_id = get_brand_id("12MINI") or get_brand_id("12mini")
    mini_stores = scrape_12mini(brand_id=mini_id)
    all_stores.extend(mini_stores)


    # (14) 抓取 和牛涮
    wagyushabu_id = get_brand_id("和牛涮")
    wagyushabu_stores = scrape_wagyushabu(brand_id=wagyushabu_id)
    all_stores.extend(wagyushabu_stores)


    # (15) 抓取 尬鍋
    godguo_id = get_brand_id("尬鍋")
    godguo_stores = scrape_godguo(brand_id=godguo_id)
    all_stores.extend(godguo_stores)


    # (16) 抓取 肉次方
    powerofmeat_id = get_brand_id("肉次方")
    powerofmeat_stores = scrape_powerofmeat(brand_id=powerofmeat_id)
    all_stores.extend(powerofmeat_stores)


    # (17) 抓取 金咕
    chingubbq_id = get_brand_id("金咕")
    chingubbq_stores = scrape_chingubbq(brand_id=chingubbq_id)
    all_stores.extend(chingubbq_stores)


    # (18) 抓取 就饗鐵板燒
    joxiang_id = get_brand_id("就饗")
    joxiang_stores = scrape_joxiang(brand_id=joxiang_id)
    all_stores.extend(joxiang_stores)



    # (18) 抓取 莆田
    putien_id = get_brand_id("莆田")
    putien_stores = scrape_putien(brand_id=putien_id)
    all_stores.extend(putien_stores)

    # (20) 抓取 阪前和牛鐵板燒
    itamae_id = get_brand_id("阪前") or get_brand_id("阪前和牛鐵板燒")
    itamae_stores = scrape_itamae(brand_id=itamae_id)
    all_stores.extend(itamae_stores)



    # 4. 統一轉換成 DataFrame 並寫入 MySQL
    if all_stores:
        df_all = pd.DataFrame(all_stores)
        print(f"\n📊 總共採集到 {len(df_all)} 筆全品牌門市資料！")

        try:
            df_all.to_sql(
                name="stores", con=engine, if_exists="append", index=False
            )
            print("\n🎉 成功將所有門市資料寫入 MySQL `stores` 資料表！")
        except Exception as e:
            print(f"\n❌ 資料庫匯入失敗：{e}")


if __name__ == "__main__":
    main()
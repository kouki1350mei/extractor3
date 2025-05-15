import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import requests
from PIL import Image
from io import BytesIO

# Firebase接続
if not firebase_admin._apps:
    firebase_secret = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(firebase_secret)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://product-categorizer-bb01c-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

# データ取得
ref = db.reference('/products')
raw_data = ref.get()
if raw_data is None:
    st.error("商品データが見つかりません。")
    st.stop()

# UI設定
st.title("🧮 商品検索 - extractor")

# 検索条件
keyword = st.text_input("🔎 商品名（部分一致）")
name_option = st.selectbox("✒️ 名入れ対応", ["すべて", "可", "不可"])
price_min = st.number_input("💴 最小費用", value=0)
price_max = st.number_input("💴 最大費用", value=10000)
category_filter = st.text_input("🏷️ カテゴリ名（完全一致）").strip()

# フィルタ処理
results = []
for uuid, product in raw_data.items():
    name = product.get("商品名", "")
    price_str = product.get("費用", "")
    printable = product.get("名入れ可否", "")
    cat_attr = product.get("カテゴリ属性")

    # 商品名
    if keyword and keyword not in name:
        continue

    # 名入れ
    if name_option == "可" and printable != "可":
        continue
    if name_option == "不可" and printable != "不可":
        continue

    # 費用
    try:
        price = int(price_str.replace(",", ""))
        if price < price_min or price > price_max:
            continue
    except:
        continue  # 費用が数値でないものは除外

    # カテゴリ属性
    if not cat_attr:
        continue
    if category_filter and category_filter not in cat_attr:
        continue

    results.append(product)

# 結果表示
st.markdown(f"### 検索結果：{len(results)} 件")

for product in results:
    st.subheader(product.get("商品名", "名称不明"))
    st.write(f"名入れ可否: {product.get('名入れ可否', '不明')}")
    st.write(f"費用: {product.get('費用', '不明')}")
    st.write(f"カテゴリ属性: {product.get('カテゴリ属性', {})}")
    if product.get("画像リンク"):
        try:
            st.image(product["画像リンク"][0], width=150)
        except:
            st.write("画像表示に失敗しました")
    st.markdown(f"[🌐 商品ページへ]({product.get('URL')})", unsafe_allow_html=True)
    st.markdown("---")

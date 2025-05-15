import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import requests
from PIL import Image
from io import BytesIO

# Firebase接続（secretsの内容確認用デバッグ付き）
if not firebase_admin._apps:
    firebase_secret = st.secrets["FIREBASE_CREDENTIALS"]

    # ✅ デバッグ用：型と中身を表示（Streamlit上に出る）
    st.write("firebase_secret の型:", type(firebase_secret))
    st.write("firebase_secret の中身:", firebase_secret)

    cred = credentials.Certificate(firebase_secret)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://product-categorizer-bb01c-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

# データ取得
ref = db.reference('/products')
raw_data = ref.get()
if raw_data is None:
    st.error("Firebaseに商品データが存在しません。")
    st.stop()

# タイトル
st.title("🧮 商品検索 - extractor")

# --- 検索条件入力 ---
keyword = st.text_input("🔎 商品名（部分一致）")
name_option = st.selectbox("✒️ 名入れ対応", ["すべて", "可", "不可"])
price_min = st.number_input("💴 最小費用", value=0)
price_max = st.number_input("💴 最大費用", value=10000)
category_filter = st.text_input("🏷️ カテゴリ名（完全一致）").strip()

# --- 検索ロジック ---
results = []
for uuid, product in raw_data.items():
    name = product.get("商品名", "")
    price_str = product.get("費用", "")
    printable = product.get("名入れ可否", "")
    cat_attr = product.get("カテゴリ属性")

    # 商品名検索
    if keyword and keyword not in name:
        continue

    # 名入れ可否フィルター
    if name_option == "可" and printable != "可":
        continue
    if name_option == "不可" and printable != "不可":
        continue

    # 費用フィルター
    try:
        price = int(price_str.replace(",", ""))
        if price < price_min or price > price_max:
            continue
    except:
        continue  # 費用が数値でなければ除外

    # カテゴリ属性フィルター
    if not cat_attr:
        continue
    if category_filter and category_filter not in cat_attr:
        continue

    results.append(product)

# --- 結果表示 ---
st.markdown(f"### 🎯 検索結果：{len(results)} 件")

for product in results:
    st.subheader(product.get("商品名", "名称不明"))
    st.write(f"名入れ可否: {product.get('名入れ可否', '不明')}")
    st.write(f"費用: {product.get('費用', '不明')}")
    st.write(f"カテゴリ属性: {product.get('カテゴリ属性', {})}")
    
    # 画像の表示（1枚目のみ）
    if product.get("画像リンク"):
        try:
            response = requests.get(product["画像リンク"][0])
            img = Image.open(BytesIO(response.content))
            st.image(img, width=150)
        except:
            st.write("画像の取得に失敗しました")

    # 商品ページリンク（あれば）
    if product.get("URL"):
        st.markdown(f"[🌐 商品ページを開く]({product['URL']})", unsafe_allow_html=True)

    st.markdown("---")

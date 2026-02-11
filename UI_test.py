import streamlit as st
import pandas as pd
import numpy as np
import time

# 1. Cấu hình trang (Layout Wide, Tiêu đề kĩ thuật)
st.set_page_config(
    page_title="Real Estate Data Intelligence System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS để giao diện trông "phẳng" và chuyên nghiệp (Enterprise Look)
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    h1 {font-size: 22px; border-bottom: 1px solid #ccc; padding-bottom: 5px; text-transform: uppercase;}
    h3 {font-size: 14px; font-weight: bold; text-transform: uppercase; color: #555; margin-top: 20px;}
    .stDataFrame {border: 1px solid #e0e0e0;}
    div[data-testid="stMetricValue"] {font-size: 18px; font-family: 'Courier New', monospace;}
    div[data-testid="stMetricLabel"] {font-size: 12px; color: #666;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: ETL CONFIGURATION ---
with st.sidebar:
    st.subheader("PIPELINE CONFIGURATION")

    st.text("Target Sources")
    st.multiselect("Active Scrapers", ["Source_A (Batdongsan)", "Source_B (Chotot)", "Source_C (AloNhadat)"],
                   default=["Source_A (Batdongsan)", "Source_B (Chotot)"])

    st.divider()

    st.text("Extraction Logic (BS4/Selenium)")
    st.slider("Request Delay (ms)", 100, 5000, 800)
    st.checkbox("Headless Browser", value=True)
    st.checkbox("Rotate User-Agents", value=True)

    st.divider()

    st.text("Validation Rules")
    min_price = st.number_input("Min Price Filter (Billion VND)", value=1.5)
    max_price = st.number_input("Max Price Filter (Billion VND)", value=50.0)
    st.toggle("Remove Duplicates (Fuzzy Logic)", value=True)

    st.markdown("---")
    st.caption("System Status: OPERATIONAL")
    st.caption("Engine: Python 3.9 / Selenium 4.1")

# --- HEADER: SYSTEM METRICS ---
st.title("REAL ESTATE DATA INGESTION & ANALYTICS CONSOLE")

# Tạo 5 cột metrics hiển thị sức khỏe dữ liệu
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("TOTAL RECORDS SCANNED", "2,450,112", "+15.2k")
with m2:
    st.metric("VALIDATED RECORDS", "2,105,400", "85.9%")
with m3:
    st.metric("DATA INTEGRITY SCORE", "98.2%", "+0.4%")
with m4:
    st.metric("AVG PARSE TIME", "0.45s", "-0.02s")
with m5:
    st.metric("DB STORAGE SIZE", "4.2 GB", "+120MB")

st.divider()

# --- MAIN SECTION: SPLIT VIEW ---
# Chia màn hình: Bên trái là Logs chạy (Scraping), Bên phải là Dữ liệu (Intelligence)
col_left, col_right = st.columns([1, 2])

# --- LEFT COLUMN: LIVE PIPELINE LOGS ---
with col_left:
    st.subheader("LIVE EXTRACTION LOGS (TAIL -F)")

    # Giả lập log chạy của tool scraping
    log_content = """[14:20:01] [INFO] [Scraper-01] Navigating to page 142...
[14:20:02] [INFO] [Parser] Extracted 24 items from DOM.
[14:20:02] [INFO] [Normalizer] Standardizing currency format: '5 tỷ 2' -> 5.2e9
[14:20:03] [WARN] [Validator] Record ID #9921: Price outlier detected (1200 tỷ). Flagged for review.
[14:20:03] [INFO] [DB_Load] Batch insert 20 records into table `properties_raw`.
[14:20:04] [INFO] [Scraper-02] Rotating proxy 192.168.x.x -> Success.
[14:20:05] [INFO] [Dedupe] Duplicate found (Simhashing score 0.95). Merging records.
[14:20:06] [INFO] [Pipeline] Cycle completed. Sleeping 2s."""

    st.code(log_content, language="bash")

    st.subheader("DATA VALIDATION STATS")
    # Biểu đồ nhỏ hiển thị lý do data bị loại bỏ
    validation_data = pd.DataFrame({
        'Reason': ['Duplicate', 'Missing Price', 'Invalid Area', 'Outlier Price', 'Old Date'],
        'Count': [1400, 500, 300, 120, 800]
    })
    st.dataframe(validation_data, hide_index=True, use_container_width=True)

# --- RIGHT COLUMN: INTELLIGENCE & ANALYTICS ---
with col_right:
    st.subheader("MARKET INTELLIGENCE (STANDARDIZED DATA)")

    # 1. Bảng dữ liệu đã làm sạch (Clean Data)
    # Tạo data giả thực tế
    data = []
    districts = ["District 1", "District 3", "Cau Giay", "Binh Thanh", "District 7"]
    types = ["Apartment", "House", "Villa", "Commercial"]

    for i in range(10):
        dist = np.random.choice(districts)
        area = np.random.randint(45, 150)
        price = np.round(area * np.random.uniform(0.05, 0.2), 2)  # Giá tỉ lệ theo diện tích

        data.append({
            "Property_UUID": f"PROP-{np.random.randint(100000, 999999)}",
            "District": dist,
            "Type": np.random.choice(types),
            "Area (m2)": area,
            "Price (Bil VND)": price,
            "Price/m2 (Mil VND)": int((price * 1000) / area),
            "Last_Updated": "2024-02-06"
        })

    df_prop = pd.DataFrame(data)

    st.dataframe(
        df_prop,
        column_config={
            "Price (Bil VND)": st.column_config.NumberColumn(format="%.2f ₫"),
            "Area (m2)": st.column_config.NumberColumn(format="%d m²"),
        },
        use_container_width=True,
        hide_index=True
    )

    # 2. Biểu đồ phân tích (Market Analysis)
    st.subheader("MARKET TREND ANALYSIS")

    tab1, tab2 = st.tabs(["Price Distribution", "Avg Price by District"])

    with tab1:
        # Biểu đồ Line chart giả lập biến động giá
        chart_data = pd.DataFrame(
            np.random.randn(20, 3) + [100, 120, 90],
            columns=['District 1', 'District 7', 'Binh Thanh']
        )
        st.line_chart(chart_data)
        st.caption("Figure 1: Price Fluctuation Index (Last 30 Days)")

    with tab2:
        # Biểu đồ Bar chart giá trung bình
        avg_data = pd.DataFrame({
            "District": districts,
            "Avg Price/m2 (Mil VND)": [180, 150, 110, 95, 125]
        }).set_index("District")
        st.bar_chart(avg_data)

# Footer
st.markdown("---")
st.text("Output generated by Analytics Engine v2.0 | Connected to PostgreSQL Warehouse")
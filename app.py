import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# Cấu hình trang
st.set_page_config(
    page_title="Kết quả Giao dịch Chứng khoán", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# File dữ liệu (bạn tự cập nhật file này hàng ngày)
DATA_FILE = "trading_results.csv"

# Hướng dẫn tạo file CSV mẫu nếu chưa có
if not os.path.exists(DATA_FILE):
    st.error(f"""
    ⚠️ **Chưa tìm thấy file dữ liệu!**
    
    Vui lòng tạo file `{DATA_FILE}` với cấu trúc sau:
    
    ```
    Ngày,Lãi/Lỗ,Ghi chú
    2024-01-01,500000,Mua VNM
    2024-01-02,-200000,Cắt lỗ HPG
    2024-01-03,1500000,Bán VIC
    ```
    
    - **Ngày**: Định dạng YYYY-MM-DD
    - **Lãi/Lỗ**: Số tiền lãi (dương) hoặc lỗ (âm)
    - **Ghi chú**: Mô tả ngắn gọn (có thể để trống)
    """)
    st.stop()

# Cấu hình (có thể đặt vào file config riêng)
VON_BAN_DAU = 100000000  # 100 triệu - thay đổi con số này theo vốn thực tế

# Đọc dữ liệu
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
        df['Ngày'] = pd.to_datetime(df['Ngày'])
        df = df.sort_values('Ngày').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return pd.DataFrame()

# CSS tùy chỉnh
st.markdown("""
<style>
    .big-metric {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .profit {
        color: #28a745;
    }
    .loss {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📈 Kết quả Giao dịch Chứng khoán")
st.markdown("---")

# Load dữ liệu
df = load_data()

if df.empty:
    st.warning("Chưa có dữ liệu giao dịch để hiển thị.")
    st.stop()

# Tính toán các chỉ số
df['Vốn tích lũy'] = VON_BAN_DAU + df['Lãi/Lỗ'].cumsum()
df['% Tăng trưởng ngày'] = (df['Lãi/Lỗ'] / df['Vốn tích lũy'].shift(1).fillna(VON_BAN_DAU)) * 100
df['% ROI tổng'] = ((df['Vốn tích lũy'] - VON_BAN_DAU) / VON_BAN_DAU) * 100

# Bộ lọc ngày
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    start_date = st.date_input(
        "📅 Từ ngày", 
        value=df['Ngày'].min().date(),
        max_value=df['Ngày'].max().date()
    )
with col2:
    end_date = st.date_input(
        "📅 Đến ngày", 
        value=df['Ngày'].max().date(),
        min_value=df['Ngày'].min().date()
    )
with col3:
    st.write("")
    st.write("")
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Lọc dữ liệu
df_filtered = df[(df['Ngày'].dt.date >= start_date) & (df['Ngày'].dt.date <= end_date)].copy()

if df_filtered.empty:
    st.warning("Không có dữ liệu trong khoảng thời gian này!")
    st.stop()

# Tính toán thống kê
von_hien_tai = df_filtered.iloc[-1]['Vốn tích lũy']
roi_hien_tai = df_filtered.iloc[-1]['% ROI tổng']
tong_lai_lo = df_filtered['Lãi/Lỗ'].sum()
ngay_lai = (df_filtered['Lãi/Lỗ'] > 0).sum()
ngay_lo = (df_filtered['Lãi/Lỗ'] < 0).sum()
ti_le_thang = (ngay_lai / len(df_filtered) * 100) if len(df_filtered) > 0 else 0

# Hiển thị các chỉ số chính
st.subheader("📊 Tổng quan Hiệu suất")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "💰 Vốn hiện tại", 
        f"{von_hien_tai:,.0f} đ",
        delta=f"{roi_hien_tai:+.2f}%"
    )

with col2:
    delta_color = "normal" if tong_lai_lo >= 0 else "inverse"
    st.metric(
        "📈 Tổng Lãi/Lỗ", 
        f"{tong_lai_lo:+,.0f} đ",
        delta=f"{(tong_lai_lo/VON_BAN_DAU*100):+.2f}%"
    )

with col3:
    st.metric(
        "🎯 Tỷ lệ thắng", 
        f"{ti_le_thang:.1f}%",
        delta=f"{ngay_lai}/{len(df_filtered)} ngày",
        delta_color="off"
    )

with col4:
    ngay_gd = len(df_filtered)
    st.metric(
        "📅 Số ngày GD", 
        f"{ngay_gd}",
        delta=f"Lãi: {ngay_lai} | Lỗ: {ngay_lo}",
        delta_color="off"
    )

with col5:
    lai_tb = df_filtered[df_filtered['Lãi/Lỗ'] > 0]['Lãi/Lỗ'].mean() if ngay_lai > 0 else 0
    lo_tb = abs(df_filtered[df_filtered['Lãi/Lỗ'] < 0]['Lãi/Lỗ'].mean()) if ngay_lo > 0 else 0
    rr_ratio = lai_tb / lo_tb if lo_tb > 0 else 0
    st.metric(
        "⚖️ R:R Ratio", 
        f"{rr_ratio:.2f}",
        delta=f"Lãi TB: {lai_tb:,.0f}đ",
        delta_color="off"
    )

st.markdown("---")

# Biểu đồ tăng trưởng vốn
st.subheader("📈 Biểu đồ Tăng trưởng Vốn")

fig = go.Figure()

# Màu sắc cho đường biểu đồ
line_color = '#28a745' if von_hien_tai >= VON_BAN_DAU else '#dc3545'

fig.add_trace(go.Scatter(
    x=df_filtered['Ngày'],
    y=df_filtered['Vốn tích lũy'],
    mode='lines+markers',
    name='Vốn tích lũy',
    line=dict(color=line_color, width=3),
    marker=dict(size=8, line=dict(width=2, color='white')),
    fill='tonexty',
    fillcolor=f'rgba({"40, 167, 69" if von_hien_tai >= VON_BAN_DAU else "220, 53, 69"}, 0.1)',
    hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                  'Vốn: <b>%{y:,.0f} đ</b><br>' +
                  '<extra></extra>'
))

# Đường vốn ban đầu
fig.add_hline(
    y=VON_BAN_DAU, 
    line_dash="dash", 
    line_color="#6c757d",
    line_width=2,
    annotation_text=f"Vốn ban đầu: {VON_BAN_DAU:,.0f} đ",
    annotation_position="right"
)

fig.update_layout(
    xaxis_title="Thời gian",
    yaxis_title="Giá trị tài khoản (VNĐ)",
    hovermode='x unified',
    height=500,
    showlegend=False,
    yaxis=dict(tickformat=','),
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
)

st.plotly_chart(fig, use_container_width=True)

# Biểu đồ % tăng trưởng hàng ngày
st.subheader("📊 % Tăng trưởng Hàng ngày")

fig2 = go.Figure()

colors = ['#28a745' if x > 0 else '#dc3545' for x in df_filtered['% Tăng trưởng ngày']]

fig2.add_trace(go.Bar(
    x=df_filtered['Ngày'],
    y=df_filtered['% Tăng trưởng ngày'],
    marker_color=colors,
    hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                  'Tăng trưởng: <b>%{y:.2f}%</b><br>' +
                  '<extra></extra>'
))

fig2.add_hline(y=0, line_color='gray', line_width=1)

fig2.update_layout(
    xaxis_title="Thời gian",
    yaxis_title="% Tăng trưởng",
    hovermode='x unified',
    height=400,
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', ticksuffix='%')
)

st.plotly_chart(fig2, use_container_width=True)

# Bảng chi tiết giao dịch
st.subheader("📋 Lịch sử Giao dịch Chi tiết")

# Chuẩn bị dữ liệu hiển thị
df_display = df_filtered[['Ngày', 'Lãi/Lỗ', '% Tăng trưởng ngày', 'Vốn tích lũy', 'Ghi chú']].copy()
df_display['Ngày'] = df_display['Ngày'].dt.strftime('%d/%m/%Y')
df_display = df_display.sort_values('Ngày', ascending=False).reset_index(drop=True)

# Định dạng hiển thị
df_display['Lãi/Lỗ'] = df_display['Lãi/Lỗ'].apply(lambda x: f"{x:+,.0f} đ")
df_display['% Tăng trưởng ngày'] = df_display['% Tăng trưởng ngày'].apply(lambda x: f"{x:+.2f}%")
df_display['Vốn tích lũy'] = df_display['Vốn tích lũy'].apply(lambda x: f"{x:,.0f} đ")

st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    height=400
)

# Footer
st.markdown("---")
st.caption(f"📅 Cập nhật lần cuối: {df['Ngày'].max().strftime('%d/%m/%Y')} | 💼 Vốn ban đầu: {VON_BAN_DAU:,.0f} đ")
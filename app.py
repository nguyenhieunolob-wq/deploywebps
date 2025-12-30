import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Cấu hình trang
st.set_page_config(
    page_title="Em Hiếu Trading", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== CẤU HÌNH - THAY ĐỔI Ở ĐÂY ==========
VON_BAN_DAU = 70000000  # Vốn ban đầu thực tế của bạn (VNĐ) - để tính %
SHEET_ID = "1ZQuZwswfnXJzEgxalV3B3VFXq9AiE-rS0jBa_1B-TPk"
SHEET_NAME = "Gain"
# ===============================================

# URL để đọc Google Sheets dưới dạng CSV
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# CSS tùy chỉnh
st.markdown("""
<style>
    .logo-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        margin: 20px 0 40px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .investor-input {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Đọc dữ liệu từ Google Sheets
@st.cache_data(ttl=60)  # Cache 60 giây
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        
        # Kiểm tra cột bắt buộc
        if 'Date' not in df.columns or 'Gain' not in df.columns:
            st.error("⚠️ Google Sheet phải có ít nhất 2 cột: **Date** và **Gain**")
            return pd.DataFrame()
        
        # Chuyển đổi Date
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        
        # Xử lý cột Gain: loại bỏ dấu phẩy phân cách hàng nghìn
        df['Gain'] = df['Gain'].astype(str).str.replace(',', '').str.replace('.', '')
        df['Gain'] = pd.to_numeric(df['Gain'], errors='coerce')
        
        # Xử lý cột Deposit (nếu có)
        if 'Deposit' in df.columns:
            df['Deposit'] = df['Deposit'].astype(str).str.replace(',', '').str.replace('.', '')
            df['Deposit'] = pd.to_numeric(df['Deposit'], errors='coerce').fillna(0)
        else:
            df['Deposit'] = 0  # Nếu không có cột Deposit, mặc định = 0
        
        # Loại bỏ dòng trống
        df = df.dropna(subset=['Date', 'Gain'])
        df = df.sort_values('Date').reset_index(drop=True)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Không thể đọc Google Sheet! Lỗi: {e}")
        return pd.DataFrame()

# Logo/Header
st.markdown('<h1 class="logo-title">📈 Em Hiếu Trading</h1>', unsafe_allow_html=True)

# Load dữ liệu
df = load_data()

if df.empty:
    st.warning("📋 Chưa có dữ liệu giao dịch hoặc Google Sheet chưa được cấu hình đúng.")
    st.stop()

# Tính toán % ROI dựa trên vốn thực tế (luôn bắt đầu từ 100%)
df['% Portfolio'] = 100 + ((df['Gain'].cumsum()) / VON_BAN_DAU) * 100
df['% ROI tổng'] = ((df['Gain'].cumsum()) / VON_BAN_DAU) * 100
df['% Tăng trưởng ngày'] = (df['Gain'] / (VON_BAN_DAU + df['Gain'].cumsum().shift(1).fillna(0))) * 100

# ========== BIỂU ĐỒ PNL (TOÀN BỘ LỊCH SỬ) ==========
st.subheader("📊 Biểu đồ PNL - Toàn bộ lịch sử")

fig_pnl = go.Figure()

# Màu sắc dựa trên hiệu suất cuối cùng
portfolio_final = df.iloc[-1]['% Portfolio']
line_color = '#28a745' if portfolio_final >= 100 else '#dc3545'

fig_pnl.add_trace(go.Scatter(
    x=df['Date'],
    y=df['% Portfolio'],
    mode='lines+markers',
    name='Portfolio Value',
    line=dict(color=line_color, width=3),
    marker=dict(size=8, line=dict(width=2, color='white')),
    fill='tonexty',
    fillcolor=f'rgba({"40, 167, 69" if portfolio_final >= 100 else "220, 53, 69"}, 0.1)',
    hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                  'Portfolio: <b>%{y:.2f}%</b><br>' +
                  '<extra></extra>'
))

# Đường 100% (vốn gốc)
fig_pnl.add_hline(
    y=100, 
    line_dash="dash", 
    line_color="#6c757d",
    line_width=2,
    annotation_text="100% (Vốn gốc)",
    annotation_position="right"
)

fig_pnl.update_layout(
    xaxis_title="Thời gian",
    yaxis_title="Giá trị Portfolio (%)",
    hovermode='x unified',
    height=500,
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
    yaxis=dict(ticksuffix='%', showgrid=True, gridcolor='rgba(128,128,128,0.2)')
)

st.plotly_chart(fig_pnl, use_container_width=True)

st.markdown("---")

# ========== BỘ LỌC NGÀY CHO PHẦN HIỆU SUẤT ==========
st.subheader("📅 Chọn khoảng thời gian để xem hiệu suất")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    start_date = st.date_input(
        "Từ ngày", 
        value=df['Date'].min().date(),
        max_value=df['Date'].max().date()
    )
with col2:
    end_date = st.date_input(
        "Đến ngày", 
        value=df['Date'].max().date(),
        min_value=df['Date'].min().date()
    )
with col3:
    st.write("")
    st.write("")
    if st.button("🔄 Làm mới", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Lọc dữ liệu theo khoảng thời gian
df_filtered = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)].copy()

if df_filtered.empty:
    st.warning("Không có dữ liệu trong khoảng thời gian này!")
    st.stop()

# Tính toán thống kê cho khoảng thời gian đã chọn
roi_filtered = (df_filtered['Gain'].sum() / VON_BAN_DAU) * 100
ngay_lai = (df_filtered['Gain'] > 0).sum()
ngay_lo = (df_filtered['Gain'] < 0).sum()
ngay_hoa = (df_filtered['Gain'] == 0).sum()
ti_le_thang = (ngay_lai / len(df_filtered) * 100) if len(df_filtered) > 0 else 0

st.markdown("---")

# ========== HIỆU SUẤT ==========
st.subheader("📊 Hiệu suất (Khoảng thời gian đã chọn)")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "📈 ROI", 
        f"{roi_filtered:+.2f}%",
        delta=f"{df_filtered['Gain'].sum():+,.0f} đ (nếu vốn 100tr)",
        delta_color="off"
    )

with col2:
    st.metric(
        "🎯 Tỷ lệ thắng", 
        f"{ti_le_thang:.1f}%",
        delta=f"{ngay_lai} thắng / {ngay_lo} thua",
        delta_color="off"
    )

with col3:
    st.metric(
        "📅 Số ngày GD", 
        f"{len(df_filtered)}",
        delta=f"Lãi: {ngay_lai} | Lỗ: {ngay_lo}",
        delta_color="off"
    )

st.markdown("---")

# ========== TÍNH TOÁN CHO NHÀ ĐẦU TƯ ==========
st.markdown('<div class="investor-input">', unsafe_allow_html=True)
st.subheader("💼 Tính toán cho khoản đầu tư của bạn")

col_input1, col_input2, col_input3 = st.columns([2, 2, 2])

with col_input1:
    so_tien_dau_tu = st.number_input(
        "Nhập số tiền bạn đầu tư (VNĐ):",
        min_value=0,
        value=50000000,
        step=1000000,
        format="%d"
    )

with col_input2:
    if so_tien_dau_tu > 0:
        # Tính theo toàn bộ lịch sử
        roi_toan_bo = df.iloc[-1]['% ROI tổng']
        gia_tri_hien_tai = so_tien_dau_tu * (1 + roi_toan_bo / 100)
        loi_nhuan = gia_tri_hien_tai - so_tien_dau_tu
        
        st.metric(
            "💰 Giá trị hiện tại",
            f"{gia_tri_hien_tai:,.0f} đ",
            delta=f"{loi_nhuan:+,.0f} đ"
        )

with col_input3:
    if so_tien_dau_tu > 0:
        st.metric(
            "📈 ROI của bạn",
            f"{roi_toan_bo:+.2f}%",
            delta=f"Portfolio: {(100 + roi_toan_bo):.2f}%",
            delta_color="off"
        )

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ========== CÁC BIỂU ĐỒ PHỤ ==========
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 % Tăng trưởng Hàng ngày")
    
    fig2 = go.Figure()
    
    colors = ['#28a745' if x > 0 else '#dc3545' if x < 0 else '#ffc107' 
              for x in df_filtered['% Tăng trưởng ngày']]
    
    fig2.add_trace(go.Bar(
        x=df_filtered['Date'],
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
        height=350,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', ticksuffix='%')
    )
    
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.subheader("🎯 Phân bố Kết quả")
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Ngày Lãi', 'Ngày Lỗ', 'Hòa vốn'],
        values=[ngay_lai, ngay_lo, ngay_hoa],
        marker=dict(colors=['#28a745', '#dc3545', '#ffc107']),
        hole=0.4,
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Số ngày: %{value}<br>Tỷ lệ: %{percent}<extra></extra>'
    )])
    
    fig_pie.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

# Phân tích % Lãi/Lỗ
st.subheader("📊 Phân tích Chi tiết")
col_a, col_b, col_c, col_d = st.columns(4)

max_gain_pct = df_filtered['% Tăng trưởng ngày'].max()
max_loss_pct = df_filtered['% Tăng trưởng ngày'].min()
avg_gain_pct = df_filtered[df_filtered['% Tăng trưởng ngày'] > 0]['% Tăng trưởng ngày'].mean() if ngay_lai > 0 else 0
avg_loss_pct = df_filtered[df_filtered['% Tăng trưởng ngày'] < 0]['% Tăng trưởng ngày'].mean() if ngay_lo > 0 else 0

with col_a:
    st.metric("📈 Lãi lớn nhất", f"{max_gain_pct:+.2f}%")
with col_b:
    st.metric("📉 Lỗ lớn nhất", f"{max_loss_pct:+.2f}%")
with col_c:
    st.metric("📊 Lãi trung bình", f"{avg_gain_pct:+.2f}%")
with col_d:
    st.metric("📊 Lỗ trung bình", f"{avg_loss_pct:+.2f}%")

# Footer
st.markdown("---")
st.caption(f"📅 Cập nhật: {df['Date'].max().strftime('%d/%m/%Y')} | 🔄 Dữ liệu tự động làm mới mỗi 60 giây")

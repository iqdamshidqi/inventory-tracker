
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Supermarket Sales Monitoring",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────
#  THEME
# ─────────────────────────────────────────────────────────
PALETTE    = ["#38BDF8","#818CF8","#34D399","#FB923C","#F472B6","#FACC15","#A78BFA"]
BG         = "#0F172A"
CARD_BG    = "#1E293B"
GRID_COLOR = "#334155"
TEXT_COLOR = "#F1F5F9"
ACCENT     = "#38BDF8"
POS        = "#34D399"
WARN       = "#FACC15"

PLOTLY_LAYOUT = dict(
    paper_bgcolor = BG,
    plot_bgcolor  = CARD_BG,
    font          = dict(color=TEXT_COLOR, family="sans-serif", size=12),
    xaxis         = dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, showgrid=True),
    yaxis         = dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, showgrid=True),
    margin        = dict(l=10, r=10, t=50, b=10),
    legend        = dict(bgcolor=CARD_BG, bordercolor=GRID_COLOR, borderwidth=1),
    hoverlabel    = dict(bgcolor=CARD_BG, font_color=TEXT_COLOR, bordercolor=ACCENT),
)

def apply_theme(fig, height=380):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig

MONTHS_ORDER = ["2019-01", "2019-02", "2019-03"]
DAYS_ORDER   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# ─────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────
st.title("🛒 Supermarket Sales Dashboard")
st.caption("Workshop Data Analitik | Live Performance Monitor")
st.divider()

# ─────────────────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────────────────
URL_SHEET = (
    "https://docs.google.com/spreadsheets/d/"
    "16kweJYYuHeHgxxMfclM6iVSonWg5EIZ3W5ExrggmUIY/export?format=csv"
)

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.replace("\ufeff", "", regex=False).str.strip().str.replace(r"\s+", " ", regex=True)
    col_map = {c.lower(): c for c in df.columns}
    rename  = {}
    for target in ["Date","Time","Branch","City","Customer type","Gender",
                   "Product line","Unit price","Quantity","Tax 5%","Total",
                   "Payment","cogs","gross income","Rating","Invoice ID"]:
        if target not in df.columns and target.lower() in col_map:
            rename[col_map[target.lower()]] = target
    if rename:
        df = df.rename(columns=rename)

    df["Date"]     = pd.to_datetime(df["Date"], errors="coerce")
    df["Month"]    = df["Date"].dt.to_period("M").astype(str)
    df["MonthNum"] = df["Date"].dt.month
    df["DOW"]      = df["Date"].dt.day_name()
    df["Hour"]     = pd.to_datetime(df["Time"], format="%H:%M", errors="coerce").dt.hour
    df["Week"]     = df["Date"].dt.isocalendar().week.astype(int)
    return df

try:
    df_raw = load_data(URL_SHEET)

    # ─────────────────────────────────────────────────────
    #  SIDEBAR FILTERS
    # ─────────────────────────────────────────────────────
    st.sidebar.header("⚙️ Filter Data")

    cabang = st.sidebar.multiselect("Cabang (Branch)", options=sorted(df_raw["Branch"].unique()), default=sorted(df_raw["Branch"].unique()))
    tipe = st.sidebar.multiselect("Tipe Pelanggan", options=list(df_raw["Customer type"].unique()), default=list(df_raw["Customer type"].unique()))
    produk = st.sidebar.multiselect("Lini Produk", options=sorted(df_raw["Product line"].unique()), default=sorted(df_raw["Product line"].unique()))

    if st.sidebar.button("🔄 Sinkronisasi Data Terbaru"):
        st.cache_data.clear()
        st.rerun()

    # Apply filters
    df = df_raw[
        df_raw["Branch"].isin(cabang) &
        df_raw["Customer type"].isin(tipe) &
        df_raw["Product line"].isin(produk)
    ].copy()

    if df.empty:
        st.warning("Tidak ada data yang sesuai dengan filter.")
        st.stop()

    # ─────────────────────────────────────────────────────
    #  KPI METRICS
    # ─────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("💰 Total Revenue",   f"${df['Total'].sum():,.0f}")
    k2.metric("💵 Gross Income",    f"${df['gross income'].sum():,.0f}")
    k3.metric("🧾 Transaksi",       f"{len(df):,}")
    k4.metric("🛒 Avg Basket Size", f"${df['Total'].mean():,.2f}")
    k5.metric("⭐ Avg Rating",      f"{df['Rating'].mean():.2f} / 10")

    st.divider()

    # ─────────────────────────────────────────────────────
    #  TABS
    # ─────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Performa Bisnis",
        "⏰ Pemantauan Operasional",
        "🎯 Strategi & Pelanggan",
        "📋 Data Center",
    ])

    # ====================================================
    #  TAB 1 — PERFORMA BISNIS
    # ====================================================
    with tab1:
        # Dual-axis monthly trend
        monthly = df.groupby("Month").agg(Revenue=("Total","sum"), Transactions=("Invoice ID","count")).reset_index()
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=monthly["Month"], y=monthly["Revenue"], name="Revenue ($)", marker_color=ACCENT), secondary_y=False)
        fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Transactions"], name="Transaksi", mode="lines+markers", line=dict(color=WARN, width=3), marker=dict(size=9, color=WARN)), secondary_y=True)
        fig.update_layout(title="Tren Pendapatan & Volume Transaksi Bulanan", **PLOTLY_LAYOUT, height=350)
        st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            br = df.groupby("Branch")["Total"].sum().reset_index()
            fig = px.bar(br, x="Branch", y="Total", color="Branch", color_discrete_sequence=PALETTE, text=br["Total"].apply(lambda v: f"${v:,.0f}"), title="Pendapatan per Cabang")
            fig.update_traces(textposition="outside")
            st.plotly_chart(apply_theme(fig), use_container_width=True)

        with c2:
            pl = df.groupby("Product line")["Total"].sum().sort_values().reset_index()
            fig = px.bar(pl, y="Product line", x="Total", orientation="h", color="Total", color_continuous_scale=["#1E293B","#38BDF8"], text=pl["Total"].apply(lambda v: f"${v:,.0f}"), title="Pendapatan per Lini Produk")
            fig.update_traces(textposition="outside")
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    # ====================================================
    #  TAB 2 — PEMANTAUAN OPERASIONAL
    # ====================================================
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            hourly = df.groupby("Hour").agg(Transactions=("Invoice ID","count")).reset_index()
            fig = px.line(hourly, x="Hour", y="Transactions", markers=True, title="Arus Transaksi per Jam (Traffic Pantau)")
            fig.update_traces(line_color=ACCENT, line_width=3, marker=dict(size=8, color=WARN))
            if not hourly.empty:
                peak = int(hourly.loc[hourly["Transactions"].idxmax(), "Hour"])
                fig.add_vline(x=peak, line_dash="dash", line_color=WARN, annotation_text=f" Peak Hour: {peak}:00", annotation_font_color=WARN)
            st.plotly_chart(apply_theme(fig), use_container_width=True)

        with c2:
            dow = df.groupby("DOW")["Total"].sum().reindex([d for d in DAYS_ORDER if d in df["DOW"].unique()]).reset_index()
            fig = px.bar(dow, x="DOW", y="Total", color="Total", color_continuous_scale=["#1E293B","#818CF8"], text=dow["Total"].apply(lambda v: f"${v:,.0f}"), title="Pendapatan per Hari")
            fig.update_traces(textposition="outside")
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(apply_theme(fig), use_container_width=True)

        # Heatmap Ops
        heat = df.pivot_table(index="Product line", columns="Branch", values="Total", aggfunc="sum").fillna(0)
        fig = go.Figure(go.Heatmap(z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(), colorscale="Blues", text=heat.values.astype(int), texttemplate="$%{text:,}"))
        fig.update_layout(title="Distribusi Beban Penjualan: Produk x Cabang", **PLOTLY_LAYOUT, height=350)
        st.plotly_chart(fig, use_container_width=True)

    # ====================================================
    #  TAB 3 — STRATEGI & PELANGGAN
    # ====================================================
    with tab3:
        c1, c2, c3 = st.columns(3)
        with c1:
            fig = px.pie(df, names="Customer type", color="Customer type", color_discrete_map={"Member":"#818CF8","Normal":"#34D399"}, hole=0.5, title="Komposisi Pelanggan")
            st.plotly_chart(apply_theme(fig, height=350), use_container_width=True)
        with c2:
            fig = px.pie(df, names="Payment", color_discrete_sequence=PALETTE, hole=0.5, title="Metode Pembayaran")
            st.plotly_chart(apply_theme(fig, height=350), use_container_width=True)
        with c3:
            mem = df.groupby(["Branch","Customer type"]).size().reset_index(name="Count")
            fig = px.bar(mem, x="Branch", y="Count", color="Customer type", barmode="group", color_discrete_map={"Member":"#818CF8","Normal":"#34D399"}, title="Member vs Normal per Cabang")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(apply_theme(fig, height=350), use_container_width=True)

        rfm = df.groupby("Product line").agg(Transactions=("Invoice ID","count"), AvgBasket=("Total","mean"), TotalRevenue=("Total","sum")).reset_index()
        fig = px.scatter(rfm, x="Transactions", y="AvgBasket", size="TotalRevenue", color="Product line", color_discrete_sequence=PALETTE, text="Product line", size_max=60, title="Matriks Performa Produk (Volume vs Avg Basket)")
        fig.update_traces(textposition="top center")
        st.plotly_chart(apply_theme(fig, height=400), use_container_width=True)

    # ====================================================
    #  TAB 4 — DATA CENTER
    # ====================================================
    with tab4:
        with st.expander("🔀 Custom Pivot Table (Untuk Eksplorasi Cepat)", expanded=True):
            pv1, pv2, pv3, pv4 = st.columns(4)
            pv_row = pv1.selectbox("Baris:", ["Branch","City","Product line","Customer type","Payment"])
            pv_col = pv2.selectbox("Kolom:", ["Month","DOW","Customer type","Gender"])
            pv_val = pv3.selectbox("Nilai:", ["Total","gross income","Quantity","Rating"])
            pv_agg = pv4.selectbox("Agregasi:", ["sum","mean","count"])

            pivot = df.pivot_table(index=pv_row, columns=pv_col, values=pv_val, aggfunc=pv_agg).round(2)
            st.dataframe(pivot, use_container_width=True)

        st.subheader("Log Transaksi")
        st.dataframe(df[["Invoice ID","Date","Time","Branch","Customer type","Product line","Unit price","Quantity","Total","Payment"]].reset_index(drop=True), use_container_width=True, height=400)

except Exception as e:
    st.error("Gagal memuat data. Pastikan link Google Sheets sudah disetel Publik.")
    st.exception(e)
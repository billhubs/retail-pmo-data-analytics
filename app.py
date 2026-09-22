import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# 1. Page Configuration & Professional Dark Aesthetics
# ---------------------------------------------------------
st.set_page_config(
    page_title="Retail Catalog & Inventory Control Tower",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    div[data-testid="stMetric"] {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
    }
    .story-card {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 20px;
    }
    .story-card h4 { margin: 0 0 6px 0; color: #818cf8; font-size: 1.05rem; }
    .story-card p { margin: 0; color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; }
    
    .chart-context {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 0.82rem;
        color: #94a3b8;
        margin-top: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 2. Optimized Chart Styling & Layout Utility
# ---------------------------------------------------------
def apply_fast_style(fig, height=360, show_legend=True):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=11),
        margin=dict(l=20, r=20, t=45, b=25),
        height=height,
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="right",
            x=1,
            font=dict(size=10, color="#cbd5e1"),
        ),
    )
    return fig


# ---------------------------------------------------------
# 3. High-Performance Data Processing (Medallion Pipeline)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_medallion_pipeline():
    # 1. BRONZE LAYER
    bronze_path = "data/raw/shein_products_raw.csv"
    if not os.path.exists(bronze_path):
        bronze_path = "data/processed/shein_clustered_features.csv"

    df_bronze = (
        pd.read_csv(bronze_path) if os.path.exists(bronze_path) else pd.DataFrame()
    )

    # 2. SILVER LAYER
    silver_path = "data/processed/shein_clustered_features.csv"
    df_silver = (
        pd.read_csv(silver_path) if os.path.exists(silver_path) else pd.DataFrame()
    )

    # 3. GOLD LAYER & VENDORS
    gold_path = "data/processed/shein_gold_master.csv"
    df_gold = (
        pd.read_csv(gold_path) if os.path.exists(gold_path) else pd.DataFrame()
    )

    vendors_path = "data/processed/vendors_master.csv"
    df_vendors = (
        pd.read_csv(vendors_path)
        if os.path.exists(vendors_path)
        else pd.DataFrame()
    )

    # Feature Engineering & Multi-Supply Chain Dynamics Simulation
    if not df_silver.empty:
        np.random.seed(42)

        # Fallback for missing SKU IDs
        if "sku_id" not in df_silver.columns:
            df_silver["sku_id"] = [
                f"SKU-{10000 + i}" for i in range(len(df_silver))
            ]

        if "category" in df_silver.columns:
            df_silver["main_category"] = "Apparel & Retail"
            df_silver["sub_category"] = df_silver["category"].fillna(
                "Unassigned"
            )
            df_silver["product_type"] = (
                df_silver["product_name"]
                .astype(str)
                .str.split()
                .str[0]
            )

        df_silver["normalized_title"] = (
            df_silver["product_name"].astype(str).str.title().str.strip()
        )
        df_silver["is_missing_metadata"] = (
            df_silver[["price", "category"]].isnull().any(axis=1)
        )
        df_silver["price"] = (
            pd.to_numeric(df_silver["price"], errors="coerce").fillna(25.0)
        )

        # Multi-Level Stock Pipeline Simulation
        df_silver["store_stock"] = np.random.randint(5, 300, size=len(df_silver))
        df_silver["warehouse_stock"] = np.random.randint(
            20, 800, size=len(df_silver)
        )
        df_silver["sales_30d"] = np.random.randint(10, 450, size=len(df_silver))

        df_silver["daily_sales"] = (df_silver["sales_30d"] / 30).replace(0, 0.1)
        df_silver["days_of_supply"] = (
            df_silver["store_stock"] + df_silver["warehouse_stock"]
        ) / df_silver["daily_sales"]

        def assign_po_status(row):
            if row["days_of_supply"] < 15:
                return (
                    "PO Issued & In-Transit"
                    if np.random.rand() > 0.4
                    else "UNRAISED PO (Risk)"
                )
            return "Stock Healthy (No PO)"

        df_silver["po_status"] = df_silver.apply(assign_po_status, axis=1)

        df_silver["po_quantity"] = np.where(
            df_silver["po_status"] == "PO Issued & In-Transit",
            np.random.randint(100, 500, size=len(df_silver)),
            0,
        )

        po_reasons = [
            "Awaiting Vendor MOQ (Minimum Order)",
            "Working Capital / Budget Hold",
            "Lead Time Negotiation in Progress",
            "Supplier Capacity Limit Reached",
        ]
        df_silver["unraised_po_reason"] = np.where(
            df_silver["po_status"] == "UNRAISED PO (Risk)",
            np.random.choice(po_reasons, size=len(df_silver)),
            "N/A - Normal",
        )

        conditions = [
            (df_silver["sales_30d"] > 250),
            (df_silver["sales_30d"].between(100, 250)),
            (df_silver["sales_30d"] < 100),
        ]
        choices = ["Fast Moving", "Slow Moving", "Dead Stock"]
        df_silver["stock_velocity"] = pd.Categorical(
            pd.Series(np.select(conditions, choices, default="Slow Moving")),
            categories=["Fast Moving", "Slow Moving", "Dead Stock"],
        )

        df_silver["price_tier"] = pd.qcut(
            df_silver["price"].rank(method="first"),
            q=3,
            labels=["Budget", "Mid-Tier", "Premium"],
        )

        df_silver["total_inventory_value"] = (
            df_silver["store_stock"] + df_silver["warehouse_stock"]
        ) * df_silver["price"]
        df_silver["estimated_cogs"] = df_silver["total_inventory_value"] * 0.60
        df_silver["gross_profit"] = (
            df_silver["total_inventory_value"] - df_silver["estimated_cogs"]
        )

    return df_bronze, df_silver, df_gold, df_vendors


# ---------------------------------------------------------
# 4. Main Application Execution
# ---------------------------------------------------------
try:
    df_bronze, df_silver, df_gold, df_vendors = load_medallion_pipeline()

    # HEADER BRANDING
    st.title("🛍️ Retail Catalog & Store Inventory Control Tower")
    st.caption(
        "Executive Dashboard: Cleaned Multi-Level Stock Reconciliation, Financial KPIs & Medallion Pipeline"
    )
    st.markdown("---")

    # SIDEBAR CONTROLS
    st.sidebar.header("🎛️ Operations Filter Panel")
    categories = (
        ["All Categories"]
        + sorted(df_silver["sub_category"].dropna().unique().tolist())
        if "sub_category" in df_silver.columns
        else ["All Categories"]
    )

    selected_cat = st.sidebar.selectbox("Filter Category", categories)
    audit_only = st.sidebar.checkbox(
        "Show Incomplete Metadata Only", value=False
    )

    # Filter Logic
    filtered_df = df_silver.copy()
    if selected_cat != "All Categories":
        filtered_df = filtered_df[filtered_df["sub_category"] == selected_cat]
    if audit_only:
        filtered_df = filtered_df[filtered_df["is_missing_metadata"] == True]

    # BRIEFING NARRATIVE CARD
    st.markdown(
        """
        <div class="story-card">
            <h4>💡 Executive Briefing & Operational Alignment</h4>
            <p>Dashboard ini menyelaraskan <b>Katalog Produk</b> dengan <b>Operasional Supply Chain Toko & Gudang</b>. Gunakan tab navigasi di bawah untuk meninjau proyeksi finansial, rekonsiliasi PO, inspeksi Medallion Data Pipeline, dan arsitektur basis data.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # TABS NAVIGATION
    tab_overview, tab_reconcile, tab_medallion, tab_catalog, tab_schema = (
        st.tabs(
            [
                "📊 Executive Overview",
                "📦 Multi-Stock & PO Reconciliation",
                "🥉🥈 Medallion Layers (Raw & Silver)",
                "🏷️ Catalog Taxonomy & Audit",
                "🗄️ Structured Dataset Schemas",
            ]
        )
    )

    # ==========================================
    # TAB 1: EXECUTIVE & FINANCIAL OVERVIEW
    # ==========================================
    with tab_overview:
        st.subheader("💰 Business Financial KPIs")

        total_revenue = filtered_df["total_inventory_value"].sum()
        total_profit = filtered_df["gross_profit"].sum()
        margin_pct = (
            (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        )
        flexible_cash = total_profit * 0.35

        dead_stock_value = filtered_df[
            filtered_df["stock_velocity"] == "Dead Stock"
        ]["total_inventory_value"].sum()
        unraised_risk_value = (
            filtered_df[filtered_df["po_status"] == "UNRAISED PO (Risk)"][
                "total_inventory_value"
            ].sum()
            * 0.20
        )
        potential_loss = dead_stock_value + unraised_risk_value

        # ROW 1: FINANCIAL METRICS CARDS
        f1, f2, f3, f4, f5 = st.columns(5)
        f1.metric("Est. Gross Revenue", f"${total_revenue:,.0f}")
        f2.metric("Gross Profit", f"${total_profit:,.0f}")
        f3.metric("Profit Margin (%)", f"{margin_pct:.1f}%")
        f4.metric(
            "💵 Flexible Cash",
            f"${flexible_cash:,.0f}",
            help="Dana bebas aman untuk ekspansi/budget baru",
        )
        f5.metric(
            "⚠️ Potential Loss",
            f"${potential_loss:,.0f}",
            delta="Risk Capital",
            delta_color="inverse",
        )

        st.markdown("---")

        # ROW 2: CATALOG & INVENTORY METRICS
        st.subheader("📦 Inventory & Catalog Metrics")
        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Total Catalog SKUs", f"{len(filtered_df):,}")

        health_score = (
            (
                (len(filtered_df) - filtered_df["is_missing_metadata"].sum())
                / len(filtered_df)
                * 100
            )
            if len(filtered_df) > 0
            else 100
        )
        o2.metric("Catalog Health Score", f"{health_score:.1f}%")

        unraised_count = len(
            filtered_df[filtered_df["po_status"] == "UNRAISED PO (Risk)"]
        )
        o3.metric(
            "Unraised Critical POs",
            f"{unraised_count:,}",
            delta="Bottleneck Risk",
            delta_color="inverse",
        )

        in_transit_count = len(
            filtered_df[filtered_df["po_status"] == "PO Issued & In-Transit"]
        )
        o4.metric("Active POs In-Transit", f"{in_transit_count:,}", delta="On Order")

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            if "price_tier" in filtered_df.columns:
                tier_summary = (
                    filtered_df.groupby("price_tier", observed=False)[
                        "total_inventory_value"
                    ]
                    .sum()
                    .reset_index()
                )
                fig_pie = px.pie(
                    tier_summary,
                    names="price_tier",
                    values="total_inventory_value",
                    title="<b>Kontribusi Nilai Inventory per Price Tier ($)</b>",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_pie.update_traces(textinfo="percent+label")
                st.plotly_chart(
                    apply_fast_style(fig_pie), use_container_width=True
                )
                st.markdown(
                    """
                    <div class="chart-context">
                        <b>📖 Story Context:</b> Menampilkan distribusi kapitalisasi modal berdasarkan tingkatan harga produk.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_g2:
            if "po_status" in filtered_df.columns:
                po_summary = (
                    filtered_df["po_status"].value_counts().reset_index()
                )
                po_summary.columns = ["po_status", "count"]
                fig_po_pie = px.bar(
                    po_summary,
                    x="po_status",
                    y="count",
                    title="<b>Status Requisisi Order (PO Breakdown)</b>",
                    color="po_status",
                    color_discrete_map={
                        "Stock Healthy (No PO)": "#10b981",
                        "PO Issued & In-Transit": "#3b82f6",
                        "UNRAISED PO (Risk)": "#ef4444",
                    },
                )
                fig_po_pie.update_layout(
                    xaxis_title="Status PO", yaxis_title="Jumlah SKU"
                )
                st.plotly_chart(
                    apply_fast_style(fig_po_pie), use_container_width=True
                )
                st.markdown(
                    """
                    <div class="chart-context">
                        <b>📖 Story Context:</b> Memantau rasio stok sehat vs stok yang sedang dipesan (In-Transit) vs stok kritis yang belum di-PO.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ==========================================
    # TAB 2: MULTI-STOCK & PO RECONCILIATION
    # ==========================================
    with tab_reconcile:
        st.subheader("📊 Multi-Echelon Stock vs. PO Reconciliation Analytics")
        st.caption(
            "Perbandingan terpadu antara Stok Toko, Stok Gudang Pusat, Penjualan 30-Hari, dan Kuantitas Order PO."
        )

        # CLEAN GROUPED BAR CHART WITH TRUNCATED TITLES
        sample_skus = (
            filtered_df.sort_values(by="sales_30d", ascending=False)
            .head(10)
            .copy()
        )
        sample_skus["clean_title"] = sample_skus["normalized_title"].apply(
            lambda x: x[:18] + "..." if len(str(x)) > 18 else str(x)
        )

        fig_reconcile = go.Figure()
        fig_reconcile.add_trace(
            go.Bar(
                x=sample_skus["clean_title"],
                y=sample_skus["store_stock"],
                name="Store Stock",
                marker_color="#818cf8",
            )
        )
        fig_reconcile.add_trace(
            go.Bar(
                x=sample_skus["clean_title"],
                y=sample_skus["warehouse_stock"],
                name="Warehouse Reserve",
                marker_color="#38bdf8",
            )
        )
        fig_reconcile.add_trace(
            go.Bar(
                x=sample_skus["clean_title"],
                y=sample_skus["sales_30d"],
                name="30-Day Sales",
                marker_color="#f59e0b",
            )
        )
        fig_reconcile.add_trace(
            go.Bar(
                x=sample_skus["clean_title"],
                y=sample_skus["po_quantity"],
                name="On-Order PO Qty",
                marker_color="#10b981",
            )
        )

        fig_reconcile.update_layout(
            title="<b>Komparasi Stok vs Penjualan vs PO (Top 10 Active SKUs)</b>",
            barmode="group",
            xaxis_title="Top Selling SKUs",
            yaxis_title="Volume Unit",
        )
        st.plotly_chart(
            apply_fast_style(fig_reconcile, height=400),
            use_container_width=True,
        )
        st.markdown(
            """
            <div class="chart-context">
                <b>📖 Story Context:</b> Komparasi visual untuk mendeteksi kesenjangan stok (*stock gap*). Jika laju Penjualan tinggi melebihi Stok Toko & Gudang, pastikan status baris hijau (On-Order PO Qty) memadai.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        col_r1, col_r2 = st.columns([1, 2])

        with col_r1:
            st.markdown("### ⚠️ Bottleneck PO Belum Diterbitkan")
            st.caption(
                "Kendala operasional pada SKU bernilai *Days of Supply* < 15 hari."
            )
            unraised_df = filtered_df[
                filtered_df["po_status"] == "UNRAISED PO (Risk)"
            ]
            if not unraised_df.empty:
                reason_counts = (
                    unraised_df["unraised_po_reason"]
                    .value_counts()
                    .reset_index()
                )
                reason_counts.columns = ["Kendala / Alasan", "Jumlah SKU"]
                st.dataframe(
                    reason_counts, use_container_width=True, hide_index=True
                )

        with col_r2:
            if not unraised_df.empty:
                fig_reason = px.pie(
                    reason_counts,
                    names="Kendala / Alasan",
                    values="Jumlah SKU",
                    title="<b>Proporsi Kendala Requisisi PO</b>",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig_reason.update_traces(textinfo="percent+label")
                st.plotly_chart(
                    apply_fast_style(fig_reason, height=300),
                    use_container_width=True,
                )

        st.markdown("### 📄 Audit Log Rekonsiliasi Stok & Requisisi Order")
        cols_reconcile_table = [
            c
            for c in [
                "sku_id",
                "normalized_title",
                "sub_category",
                "store_stock",
                "warehouse_stock",
                "sales_30d",
                "days_of_supply",
                "po_status",
                "po_quantity",
                "unraised_po_reason",
            ]
            if c in filtered_df.columns
        ]
        st.dataframe(
            filtered_df[cols_reconcile_table]
            .sort_values(by="days_of_supply", ascending=True)
            .head(150),
            column_config={
                "sku_id": "SKU ID",
                "normalized_title": "Nama Produk",
                "sub_category": "Kategori",
                "store_stock": st.column_config.NumberColumn(
                    "Stok Toko", format="%d"
                ),
                "warehouse_stock": st.column_config.NumberColumn(
                    "Stok Gudang", format="%d"
                ),
                "sales_30d": st.column_config.NumberColumn(
                    "Sales (30 Hari)", format="%d"
                ),
                "days_of_supply": st.column_config.NumberColumn(
                    "Ketahanan (Hari)", format="%.1f Hari"
                ),
                "po_status": "Status PO",
                "po_quantity": st.column_config.NumberColumn(
                    "Qty Order PO", format="%d"
                ),
                "unraised_po_reason": "Kendala PO",
            },
            use_container_width=True,
            hide_index=True,
        )

    # ==========================================
    # TAB 3: MEDALLION LAYERS (BRONZE & SILVER)
    # ==========================================
    with tab_medallion:
        st.subheader("🧱 Data Pipeline: Inspection Layer")
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown("### 🥉 Bronze Layer (Raw Ingestion)")
            st.caption(
                "Data mentah dari feed ingestion POS/Catalog tanpa pembersihan."
            )
            if not df_bronze.empty:
                st.metric("Total Rows Ingested", f"{len(df_bronze):,}")
                st.dataframe(df_bronze.head(100), use_container_width=True)

        with col_m2:
            st.markdown("### 🥈 Silver Layer (Cleaned & Enriched)")
            st.caption(
                "Data terstruktur hasil transformasi, normalisasi, dan klasifikasi."
            )
            if not df_silver.empty:
                st.metric("Total Cleaned SKUs", f"{len(df_silver):,}")
                cols_silver_preview = [
                    c
                    for c in [
                        "sku_id",
                        "normalized_title",
                        "store_stock",
                        "warehouse_stock",
                        "sales_30d",
                        "po_status",
                    ]
                    if c in df_silver.columns
                ]
                st.dataframe(
                    df_silver[cols_silver_preview].head(100),
                    use_container_width=True,
                )

    # ==========================================
    # TAB 4: CATALOG TAXONOMY & AUDIT
    # ==========================================
    with tab_catalog:
        st.subheader("🌳 Product Taxonomy & Data Quality Audit")

        col_cat1, col_cat2 = st.columns([1, 2])
        with col_cat1:
            st.markdown(
                """
                **📌 Aturan Standar Data Katalog:**
                * **Hirarki Taxonomy:** Main Category → Sub-Category → Product Type.
                * **Normalisasi Teks:** Penyesuaian ke *Title Case*, hapus spasi berlebih.
                * **Kelengkapan Attribute:** Menjamin tidak ada data kosong (`Null`) pada kolom *price* dan *category*.
                """
            )
            if "sub_category" in filtered_df.columns:
                top_cats = (
                    filtered_df["sub_category"]
                    .value_counts()
                    .head(5)
                    .reset_index()
                )
                top_cats.columns = ["Sub-Kategori", "Jumlah SKU"]
                st.write("**Top 5 Kategori Dominan:**")
                st.dataframe(
                    top_cats, use_container_width=True, hide_index=True
                )

        with col_cat2:
            if "sub_category" in filtered_df.columns:
                fig_cat_bar = px.bar(
                    filtered_df["sub_category"]
                    .value_counts()
                    .reset_index()
                    .head(8),
                    x="count",
                    y="sub_category",
                    orientation="h",
                    title="<b>Volume SKU per Sub-Kategori Utama</b>",
                    color_discrete_sequence=["#818cf8"],
                    labels={
                        "count": "Total SKU",
                        "sub_category": "Sub Kategori",
                    },
                )
                fig_cat_bar.update_layout(
                    yaxis=dict(autorange="reversed")
                )
                st.plotly_chart(
                    apply_fast_style(fig_cat_bar), use_container_width=True
                )

        st.markdown("### 📄 Audit Log Normalisasi Katalog (Silver Data)")
        show_cols = [
            c
            for c in [
                "sku_id",
                "product_name",
                "normalized_title",
                "sub_category",
                "price",
                "is_missing_metadata",
            ]
            if c in filtered_df.columns
        ]
        st.dataframe(
            filtered_df[show_cols].head(300),
            column_config={
                "sku_id": "SKU ID",
                "product_name": "Nama Asli (Raw)",
                "normalized_title": "Nama Ter-Normalisasi",
                "sub_category": "Kategori",
                "price": st.column_config.NumberColumn(
                    "Harga ($)", format="$%.2f"
                ),
                "is_missing_metadata": "Missing Attribute?",
            },
            use_container_width=True,
            hide_index=True,
        )

    # ==========================================
    # TAB 5: STRUCTURED DATASET SCHEMAS
    # ==========================================
    with tab_schema:
        st.subheader("🗄️ Relational & Document Schema Architecture")
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            st.markdown(
                "**🐬 SQL Relational Schema (Multi-Echelon Inventory 3NF)**"
            )
            st.code(
                """
CREATE TABLE inventory_reconciliation (
    sku_id VARCHAR(50) PRIMARY KEY,
    store_stock INT NOT NULL DEFAULT 0,
    warehouse_stock INT NOT NULL DEFAULT 0,
    sales_30d INT NOT NULL DEFAULT 0,
    days_of_supply DECIMAL(5,2),
    po_status VARCHAR(50),
    po_quantity INT DEFAULT 0,
    unraised_po_reason VARCHAR(255)
);
                """,
                language="sql",
            )

        with col_s2:
            st.markdown(
                "**🍃 NoSQL BSON / JSON Schema (Supply Chain Tracking)**"
            )
            st.json(
                {
                    "sku_id": "SKU-99218",
                    "inventory_breakdown": {
                        "store_stock": 12,
                        "warehouse_stock": 40,
                        "sales_30d": 180,
                        "days_of_supply": 8.6,
                    },
                    "po_pipeline": {
                        "status": "UNRAISED PO (Risk)",
                        "reason": "Awaiting Vendor MOQ (Minimum Order)",
                        "po_quantity": 0,
                    },
                }
            )

except Exception as e:
    st.error(f"Execution Error: {e}")

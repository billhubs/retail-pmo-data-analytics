# 🛍️ Retail Catalog & Store Inventory Control Tower

## 📌 Executive Summary

The **Retail Catalog & Store Inventory Control Tower** is an integrated analytics and data engineering platform built using Streamlit. It bridges e-commerce catalog management (*Product Taxonomy & Data Normalization*) with multi-echelon retail supply chain visibility (*Store Stock*, *Warehouse Reserve*, *30-Day Sales Velocity*, and *Purchase Order Reconciliation*).

By leveraging a **Medallion Architecture (Bronze $\rightarrow$ Silver $\rightarrow$ Gold)**, the system ensures raw ingestion feeds from POS/ERP systems are transformed into actionable business insights for C-Suite executives, Merchandising, Sourcing, and Store Operations teams.

---

## 🏗️ Technical & Data Architecture

### 1. Medallion Pipeline Architecture

* **🥉 Bronze Layer (Raw Ingestion):** Stores raw, unrefined data feeds directly collected from web scrapers or POS system logs without modification.
* **🥈 Silver Layer (Cleansed & Enriched):** Performs string normalization (*title-casing*), metadata audit checks, stock velocity classification (*Fast/Slow/Dead Stock*), and price tier mapping.
* **🥇 Gold Layer (Business Aggregation):** Computes executive KPIs, revenue projections, gross profit margins, and potential risk capital metrics.

### 2. Multi-Echelon Supply Chain Logic

$$\text{Days of Supply} = \frac{\text{Store Stock} + \text{Warehouse Stock}}{\text{Daily Sales Rate}}$$

* **Fast Moving:** High sales velocity SKUs facing inventory exhaustion risks ($\text{Days of Supply} < 15\text{ days}$).
* **Slow Moving:** SKUs with steady, balanced turnover rates ($15 \le \text{Days of Supply} \le 60\text{ days}$).
* **Dead Stock:** SKUs with excessive stock accumulation ($\text{Days of Supply} > 60\text{ days}$), representing tied-up working capital.

---

## 🎯 Key Dashboard Modules (`app.py`)

### 1. 📊 Executive & Financial Overview

* **Business Financial KPIs:** Tracks *Est. Gross Revenue*, *Gross Profit*, *Profit Margin (%)*, *Flexible Cash* (35% allocated from gross profit for store expansion/marketing), and *Potential Loss* (risk capital tied up in dead stock + potential stockout lost sales).
* **Inventory Capitalization:** Visualizes capital allocation across price tiers and inventory movement classifications.

### 2. 📦 Multi-Stock & PO Reconciliation

* **Visual Reconciliation:** Side-by-side grouped bar chart comparing **Store Stock**, **Warehouse Stock**, **30-Day Sales Velocity**, and **On-Order PO Quantities**.
* **Bottleneck Analysis:** Identifies operational root causes for unraised critical POs (e.g., *Vendor MOQ thresholds*, *Working Capital Holds*, *Lead Time Negotiations*, or *Supplier Capacity Limits*).
* **Interactive Table Audit:** Detailed inventory coverage audit log formatted with clean numeric configurations.

### 3. 🥉🥈 Medallion Data Inspection

* Side-by-side transparency inspection tab to compare raw ingestion data (*Bronze*) against cleansed and transformed feature sets (*Silver*).

### 4. 🏷️ Catalog Taxonomy & Data Audit

* **Taxonomy Framework:** Hierarchical product categorization mapping (*Main Category $\rightarrow$ Sub-Category $\rightarrow$ Product Type*).
* **Data Quality Score:** Measures catalog health percentage based on completeness of core attributes (Price, Category, SKU IDs).

### 5. 🗄️ Structured Dataset Schemas

* **SQL Relational Schema (3NF):** DDL scripts designed for retail OLTP operational databases.
* **NoSQL JSON Schema:** Annotated document structures ready for Feature Stores or AI/ML model training initiatives.

---

## 💻 Tech Stack & Dependencies

* **Language:** Python 3.10+
* **Dashboard Framework:** Streamlit
* **Data Engine:** Pandas, NumPy
* **Visualization:** Plotly Express, Plotly Graph Objects
* **Performance Optimization:** `@st.cache_data` (In-Memory Data Caching & Vectorized Computation)

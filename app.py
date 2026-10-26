import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Kamus SKU SYB", page_icon="📦", layout="centered")

SUPABASE_URL = "https://cswevaxdtjnkakppsowx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNzd2V2YXhkdGpua2FrcHBzb3d4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI5NjM2NjQsImV4cCI6MjEwODUzOTY2NH0.iuAcjRRuF20fOhA7X2Z9QPEiEm9I2z4Typb6yLs9Zss"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("📦 Kamus & Management SKU")

# Buat Tab Menu: Pencarian & Input Baru
tab1, tab2 = st.tabs(["🔍 Cari SKU", "➕ Tambah SKU Baru"])

# --- TAB 1: PENCARIAN SKU ---
with tab1:
    st.write("Cari detail komposisi produk satuan maupun bundling.")
    query_sku = st.text_input("Masukkan Kode SKU:", "").strip().upper()

    if query_sku:
        sku_master = supabase.table("skus").select("*").eq("sku_code", query_sku).execute()
        
        if sku_master.data:
            data_master = sku_master.data[0]
            st.success(f"**SKU Ditemukan:** {data_master['sku_code']}")
            st.write(f"**Nama Etalase:** {data_master['display_name']}")
            if data_master.get('shopee_id'):
                st.write(f"**Kode Shopee:** {data_master['shopee_id']}")
                
            st.markdown("---")
            st.subheader("📋 Rincian / Komposisi Produk:")
            components = supabase.table("sku_components").select("qty, product_name, child_sku").eq("parent_sku", query_sku).execute()
            
            if components.data:
                st.table(components.data)
            else:
                st.info("SKU ini tidak memiliki rincian komponen bundling tambahan.")
        else:
            st.error(f"SKU '{query_sku}' tidak ditemukan di database.")

# --- TAB 2: INPUT DATA BARU ---
with tab2:
    st.subheader("Input SKU Master / Bundling Baru")
    
    with st.form("form_tambah_sku", clear_on_submit=True):
        new_sku = st.text_input("Kode SKU Utama (misal: BSYB999 / SYB999)*").strip().upper()
        new_shopee_id = st.text_input("Kode Shopee (opsional)").strip()
        new_display_name = st.text_input("Nama Etalase / Produk*").strip()
        
        st.markdown("---")
        st.write("**Isi Komposisi Produk Pertama (Wajib):**")
        comp1_qty = st.number_input("QTY Item 1", min_value=1, value=1)
        comp1_name = st.text_input("Nama Produk Satuan 1*").strip()
        comp1_sku = st.text_input("SKU Satuan 1 (misal: SYB104)*").strip().upper()
        
        submitted = st.form_submit_button("Simpan SKU Baru")
        
        if submitted:
            if not new_sku or not new_display_name or not comp1_name or not comp1_sku:
                st.error("Semua kolom bertanda * wajib diisi!")
            else:
                try:
                    # 1. Simpan ke master skus
                    supabase.table("skus").upsert({
                        "sku_code": new_sku,
                        "shopee_id": new_shopee_id if new_shopee_id else None,
                        "display_name": new_display_name
                    }).execute()
                    
                    # 2. Simpan komponen 1
                    supabase.table("sku_components").insert({
                        "parent_sku": new_sku,
                        "qty": comp1_qty,
                        "product_name": comp1_name,
                        "child_sku": comp1_sku
                    }).execute()
                    
                    st.success(f"Berhasil menambahkan SKU '{new_sku}' ke database!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data: {e}")

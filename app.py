import streamlit as st
from supabase import create_client, Client

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Kamus SKU SYB",
    page_icon="📦",
    layout="centered"
)

# Inisialisasi Supabase Client
SUPABASE_URL = "https://cswevaxdtjnkakppsowx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNzd2V2YXhkdGpua2FrcHBzb3d4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI5NjM2NjQsImV4cCI6MjEwODUzOTY2NH0.iuAcjRRuF20fOhA7X2Z9QPEiEm9I2z4Typb6yLs9Zss"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Tampilan Header Web
st.title("📦 Kamus & Lookup SKU")
st.write("Cari detail komposisi produk satuan maupun bundling dengan cepat.")

# Input Pencarian SKU
query_sku = st.text_input("Masukkan Kode SKU (contoh: BSYB012 atau SYB104):", "").strip().upper()

if query_sku:
    # 1. Query ke Tabel Utama (skus)
    sku_master = supabase.table("skus").select("*").eq("sku_code", query_sku).execute()
    
    if sku_master.data:
        data_master = sku_master.data[0]
        st.success(f"**SKU Ditemukan:** {data_master['sku_code']}")
        st.write(f"**Nama Etalase:** {data_master['display_name']}")
        if data_master.get('shopee_id'):
            st.write(f"**Kode Shopee:** {data_master['shopee_id']}")
            
        st.markdown("---")
        st.subheader("📋 Rincian / Komposisi Produk:")
        
        # 2. Query ke Tabel Komposisi (sku_components)
        components = supabase.table("sku_components").select("qty, product_name, child_sku").eq("parent_sku", query_sku).execute()
        
        if components.data:
            # Tampilkan dalam bentuk tabel rapi
            st.table(components.data)
        else:
            st.info("SKU ini tidak memiliki rincian komponen bundling tambahan.")
    else:
        st.error(f"SKU '{query_sku}' tidak ditemukan di database.")
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

# --- TAB 2: INPUT DATA BARU (DILENGKAPI HINGGA 7 PRODUK) ---
with tab2:
    st.subheader("Input SKU Master / Bundling Baru")
    
    with st.form("form_tambah_sku", clear_on_submit=True):
        new_sku = st.text_input("Kode SKU Utama (misal: BSYB999 / SYB999)*").strip().upper()
        new_shopee_id = st.text_input("Kode Shopee (opsional)").strip()
        new_display_name = st.text_input("Nama Etalase / Produk*").strip()
        
        st.markdown("---")
        st.subheader("📦 Komposisi Produk Bundling (Max 7 Item)")
        
        # Loop untuk membuat form 7 Produk (Produk 1 Wajib, 2-7 Opsional)
        items_input = []
        for i in range(1, 8):
            is_required = "(Wajib)" if i == 1 else "(Opsional)"
            st.write(f"**Produk {i} {is_required}:**")
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                p_qty = st.number_input(f"QTY {i}", min_value=1, value=1, key=f"qty_{i}")
            with col2:
                p_sku = st.text_input(f"SKU Satuan {i}", key=f"sku_{i}").strip().upper()
            with col3:
                p_name = st.text_input(f"Nama Produk Satuan {i}", key=f"name_{i}").strip()
                
            items_input.append({
                'index': i,
                'qty': p_qty,
                'sku': p_sku,
                'name': p_name
            })
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Simpan SKU & Seluruh Komposisi")
        
        if submitted:
            # Validasi input utama & produk 1
            if not new_sku or not new_display_name or not items_input[0]['sku'] or not items_input[0]['name']:
                st.error("Kode SKU Utama, Nama Etalase, serta SKU & Nama Produk 1 WAJIB diisi!")
            else:
                try:
                    # 1. Simpan ke master skus
                    supabase.table("skus").upsert({
                        "sku_code": new_sku,
                        "shopee_id": new_shopee_id if new_shopee_id else None,
                        "display_name": new_display_name
                    }).execute()
                    
                    # 2. Filter & kumpulkan komponen yang diisi saja
                    components_to_insert = []
                    for item in items_input:
                        if item['sku'] or item['name']:  # Jika SKU atau Nama diisi
                            components_to_insert.append({
                                "parent_sku": new_sku,
                                "qty": item['qty'],
                                "product_name": item['name'] if item['name'] else item['sku'],
                                "child_sku": item['sku'] if item['sku'] else None
                            })
                    
                    # 3. Simpan ke sku_components
                    if components_to_insert:
                        supabase.table("sku_components").insert(components_to_insert).execute()
                    
                    st.success(f"Berhasil menyimpan SKU '{new_sku}' beserta {len(components_to_insert)} rincian produk!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data: {e}")

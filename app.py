import streamlit as st
import pandas as pd
import re
from supabase import create_client, Client

st.set_page_config(page_title="Kamus SKU SYB", page_icon="📦", layout="centered")

SUPABASE_URL = "https://cswevaxdtjnkakppsowx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNzd2V2YXhkdGpua2FrcHBzb3d4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI5NjM2NjQsImV4cCI6MjEwODUzOTY2NH0.iuAcjRRuF20fOhA7X2Z9QPEiEm9I2z4Typb6yLs9Zss"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("📦 Kamus & Management SKU")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Cari SKU", "➕ Tambah SKU Baru", "📖 Daftar Semua SKU", "✏️ Edit SKU"])

# --- FUNGSI AUTO GENERATE SKU ---
def generate_next_sku(prefix):
    res = supabase.table("skus").select("sku_code").like("sku_code", f"{prefix}%").execute()
    max_num = 0
    if res.data:
        for item in res.data:
            code = item['sku_code']
            digits = re.findall(r'\d+', code)
            if digits:
                num = int(digits[-1])
                if num > max_num:
                    max_num = num
    next_num = max_num + 1
    return f"{prefix}{next_num:03d}"

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

# --- TAB 2: INPUT DATA BARU (DENGAN AUTO-GENERATE) ---
with tab2:
    st.subheader("Input SKU Master / Bundling Baru")
    
    sku_type = st.radio("Pilih Tipe SKU:", ["Bundling (BSYB)", "Satuan (SYB)"], horizontal=True)
    prefix = "BSYB" if "Bundling" in sku_type else "SYB"
    
    suggested_sku = generate_next_sku(prefix)
    
    with st.form("form_tambah_sku", clear_on_submit=True):
        st.info(f"Saran Kode SKU Otomatis Selanjutnya: **{suggested_sku}**")
        new_sku = st.text_input("Kode SKU Utama*", value=suggested_sku).strip().upper()
        new_shopee_id = st.text_input("Kode Shopee (opsional)").strip()
        new_display_name = st.text_input("Nama Etalase / Produk*").strip()
        
        st.markdown("---")
        st.subheader("📦 Komposisi Produk Bundling (Max 7 Item)")
        
        items_input = []
        for i in range(1, 8):
            is_req = "(Wajib)" if i == 1 else "(Opsional)"
            st.write(f"**Produk {i} {is_req}:**")
            c1, c2, c3 = st.columns([1, 2, 2])
            with c1:
                p_qty = st.number_input(f"QTY {i}", min_value=1, value=1, key=f"add_qty_{i}")
            with c2:
                p_sku = st.text_input(f"SKU Satuan {i}", key=f"add_sku_{i}").strip().upper()
            with c3:
                p_name = st.text_input(f"Nama Produk Satuan {i}", key=f"add_name_{i}").strip()
                
            items_input.append({'qty': p_qty, 'sku': p_sku, 'name': p_name})
            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Simpan SKU Baru")
        
        if submitted:
            if not new_sku or not new_display_name or not items_input[0]['sku'] or not items_input[0]['name']:
                st.error("Kode SKU Utama, Nama Etalase, serta SKU & Nama Produk 1 WAJIB diisi!")
            else:
                try:
                    supabase.table("skus").upsert({
                        "sku_code": new_sku,
                        "shopee_id": new_shopee_id if new_shopee_id else None,
                        "display_name": new_display_name
                    }).execute()
                    
                    comps = []
                    for item in items_input:
                        if item['sku'] or item['name']:
                            comps.append({
                                "parent_sku": new_sku,
                                "qty": item['qty'],
                                "product_name": item['name'] if item['name'] else item['sku'],
                                "child_sku": item['sku'] if item['sku'] else None
                            })
                    
                    if comps:
                        supabase.table("sku_components").insert(comps).execute()
                    
                    st.success(f"Berhasil menyimpan SKU '{new_sku}'!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan data: {e}")

# --- TAB 3: DAFTAR SEMUA SKU ---
with tab3:
    st.subheader("📖 Dictionary Semua SKU")
    all_skus = supabase.table("skus").select("sku_code, display_name, shopee_id").order("sku_code").execute()

    if all_skus.data:
        df_skus = pd.DataFrame(all_skus.data)
        df_skus.rename(columns={'sku_code': 'Kode SKU', 'display_name': 'Nama Etalase', 'shopee_id': 'Kode Shopee'}, inplace=True)
        
        filter_text = st.text_input("🔎 Filter daftar (cari kode / etalase):", "").strip()
        if filter_text:
            df_filt = df_skus[
                df_skus['Kode SKU'].str.contains(filter_text, case=False, na=False) |
                df_skus['Nama Etalase'].str.contains(filter_text, case=False, na=False)
            ]
            st.dataframe(df_filt, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_skus, use_container_width=True, hide_index=True)

# --- TAB 4: EDIT SKU ---
with tab4:
    st.subheader("✏️ Edit Data SKU / Etalase")
    
    all_skus_list = supabase.table("skus").select("sku_code, display_name").order("sku_code").execute()
    
    if all_skus_list.data:
        sku_options = [f"{item['sku_code']} - {item['display_name']}" for item in all_skus_list.data]
        selected_option = st.selectbox("Pilih SKU yang ingin diedit:", sku_options)
        
        target_sku_code = selected_option.split(" - ")[0]
        
        # Load Data Eksisting
        sku_info = supabase.table("skus").select("*").eq("sku_code", target_sku_code).execute().data[0]
        comps_info = supabase.table("sku_components").select("*").eq("parent_sku", target_sku_code).execute().data
        
        with st.form("form_edit_sku"):
            st.write(f"Editing Kode SKU: **{target_sku_code}**")
            edit_shopee_id = st.text_input("Kode Shopee", value=sku_info.get('shopee_id') or "")
            edit_display_name = st.text_input("Nama Etalase / Produk", value=sku_info.get('display_name') or "")
            
            st.markdown("---")
            st.subheader("Komposisi Produk Bundling")
            
            edit_items = []
            for i in range(1, 8):
                existing_comp = comps_info[i-1] if i <= len(comps_info) else {}
                
                st.write(f"**Produk {i}:**")
                c1, c2, c3 = st.columns([1, 2, 2])
                with c1:
                    e_qty = st.number_input(f"QTY {i}", min_value=1, value=int(existing_comp.get('qty', 1)), key=f"edit_qty_{i}")
                with c2:
                    e_sku = st.text_input(f"SKU Satuan {i}", value=existing_comp.get('child_sku') or "", key=f"edit_sku_{i}").strip().upper()
                with c3:
                    e_name = st.text_input(f"Nama Produk {i}", value=existing_comp.get('product_name') or "", key=f"edit_name_{i}").strip()
                
                edit_items.append({'qty': e_qty, 'sku': e_sku, 'name': e_name})
                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
                
            edit_submitted = st.form_submit_button("Simpan Perubahan Edit")
            
            if edit_submitted:
                if not edit_display_name:
                    st.error("Nama Etalase tidak boleh kosong!")
                else:
                    try:
                        # 1. Update data master
                        supabase.table("skus").update({
                            "shopee_id": edit_shopee_id if edit_shopee_id else None,
                            "display_name": edit_display_name
                        }).eq("sku_code", target_sku_code).execute()
                        
                        # 2. Hapus komponen lama & masukkan komponen baru
                        supabase.table("sku_components").delete().eq("parent_sku", target_sku_code).execute()
                        
                        new_comps = []
                        for item in edit_items:
                            if item['sku'] or item['name']:
                                new_comps.append({
                                    "parent_sku": target_sku_code,
                                    "qty": item['qty'],
                                    "product_name": item['name'] if item['name'] else item['sku'],
                                    "child_sku": item['sku'] if item['sku'] else None
                                })
                        
                        if new_comps:
                            supabase.table("sku_components").insert(new_comps).execute()
                            
                        st.success(f"Berhasil memperbarui data SKU '{target_sku_code}'!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal memperbarui data: {e}")

# 1. Install library yang dibutuhkan di Google Colab
!pip install supabase openpyxl pandas

import pandas as pd
from supabase import create_client
from google.colab import files

# 2. Upload file Excel revisi langsung dari komputer
print("Silakan pilih dan upload file 'NEEE SKU REVISI.xlsx' kamu:")
uploaded = files.upload()

file_path = list(uploaded.keys())[0]

# 3. Konfigurasi Kredensial Supabase
SUPABASE_URL = "https://cswevaxdtjnkakppsowx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNzd2V2YXhkdGpua2FrcHBzb3d4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI5NjM2NjQsImV4cCI6MjEwODUzOTY2NH0.iuAcjRRuF20fOhA7X2Z9QPEiEm9I2z4Typb6yLs9Zss"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------------------------
# OLAH DATA SHEET "satuan" & "bundling"
# -------------------------------------------------------------
skus_master = []
components_data = []

# Sheet Satuan
print("\nMengolah Sheet 'satuan'...")
df_satuan = pd.read_excel(file_path, sheet_name='satuan')
for _, row in df_satuan.iterrows():
    sku_code = str(row['SKU']).strip() if pd.notna(row['SKU']) else None
    barcode = str(row['Barcode']).strip() if pd.notna(row['Barcode']) else ""
    product_name = str(row['Produk']).strip() if pd.notna(row['Produk']) else ""
    
    if sku_code and sku_code.lower() != 'nan':
        skus_master.append({
            "sku_code": sku_code,
            "display_name": product_name,
            "barcode": barcode
        })
        components_data.append({
            "parent_sku": sku_code,
            "qty": 1,
            "product_name": product_name,
            "child_sku": sku_code,
            "barcode": barcode
        })

# Sheet Bundling
print("Mengolah Sheet 'bundling'...")
df_bundling = pd.read_excel(file_path, sheet_name='bundling')
for _, row in df_bundling.iterrows():
    parent_sku = str(row['SKU']).strip() if pd.notna(row['SKU']) else None
    display_name = str(row['NAMA ETALASE/VARIASI']).strip() if pd.notna(row['NAMA ETALASE/VARIASI']) else ""
    variasi = str(row['variasi']).strip() if pd.notna(row['variasi']) else ""
    
    if variasi and variasi.lower() != 'nan':
        display_name = f"{display_name} - {variasi}"
        
    if parent_sku and parent_sku.lower() != 'nan':
        skus_master.append({
            "sku_code": parent_sku,
            "display_name": display_name,
            "barcode": ""
        })
        
        # Komponen 1
        qty1 = row['QTY'] if pd.notna(row['QTY']) else 1
        pname1 = str(row['NAMA PRODUK 1']).strip() if pd.notna(row['NAMA PRODUK 1']) else ""
        csku1 = str(row['SKU.1']).strip() if pd.notna(row['SKU.1']) else ""
        bc1 = str(row['barcode']).strip() if pd.notna(row['barcode']) else ""
        
        if pname1 or csku1:
            components_data.append({
                "parent_sku": parent_sku,
                "qty": int(qty1) if str(qty1).replace('.','').isdigit() else 1,
                "product_name": pname1 if pname1 else csku1,
                "child_sku": csku1 if (csku1 and csku1.lower() != 'nan') else None,
                "barcode": bc1 if (bc1 and bc1.lower() != 'nan') else ""
            })
            
        # Komponen 2 s/d 7
        comp_specs = [
            ('QTY.1', 'NAMA PRODUK 2', 'SKU.2', 'barcode.1'),
            ('QTY.2', 'NAMA PRODUK 3', 'SKU.3', 'barcode.2'),
            ('QTY.3', 'NAMA PRODUK 4', 'SKU.4', 'barcode.3'),
            ('QTY.4', 'NAMA PRODUK 5', 'SKU.5', None),
            ('QTY.5', 'NAMA PRODUK 6', 'SKU.6', None),
            ('QTY.6', 'NAMA PRODUK 7', 'SKU.7', None),
        ]
        
        for q_col, p_col, s_col, b_col in comp_specs:
            pname = str(row[p_col]).strip() if pd.notna(row[p_col]) else ""
            csku = str(row[s_col]).strip() if pd.notna(row[s_col]) else ""
            qval = row[q_col] if pd.notna(row[q_col]) else 1
            bc = str(row[b_col]).strip() if (b_col and pd.notna(row[b_col])) else ""
            
            if pname or csku:
                components_data.append({
                    "parent_sku": parent_sku,
                    "qty": int(qval) if str(qval).replace('.','').isdigit() else 1,
                    "product_name": pname if pname else csku,
                    "child_sku": csku if (csku and csku.lower() != 'nan') else None,
                    "barcode": bc if (bc and bc.lower() != 'nan') else ""
                })

# -------------------------------------------------------------
# KOSONGKAN DATABASE LAMA & UPLOAD DATA REVISI
# -------------------------------------------------------------
print("\n1. Mengosongkan seluruh database Supabase lama...")
while True:
    res_skus = supabase.table("skus").select("sku_code").limit(1000).execute()
    if not res_skus.data:
        break
    all_codes = [item['sku_code'] for item in res_skus.data]
    for i in range(0, len(all_codes), 100):
        batch = all_codes[i:i + 100]
        supabase.table("sku_components").delete().in_("parent_sku", batch).execute()
        supabase.table("skus").delete().in_("sku_code", batch).execute()

print("   -> Supabase berhasil dikosongkan total!")

# Deduplikasi ketat
df_master_unique = pd.DataFrame(skus_master).drop_duplicates(subset=['sku_code']).to_dict('records')
df_comp = pd.DataFrame(components_data)
df_comp_clean = df_comp.drop_duplicates(subset=['parent_sku', 'product_name']).to_dict('records')

print(f"\n2. Mengunggah {len(df_master_unique)} Master SKU ke tabel 'skus'...")
batch_size = 500
for i in range(0, len(df_master_unique), batch_size):
    batch = df_master_unique[i:i + batch_size]
    supabase.table("skus").upsert(batch).execute()

print(f"3. Mengunggah {len(df_comp_clean)} Komposisi Produk ke tabel 'sku_components'...")
for i in range(0, len(df_comp_clean), batch_size):
    batch = df_comp_clean[i:i + batch_size]
    supabase.table("sku_components").insert(batch).execute()

print("\n✅ SELESAI! Database Supabase berhasil di-reset & di-update ke versi revisi terbaru.")

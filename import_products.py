import pandas as pd
import json
import re
import os
import urllib.request
import ssl
from urllib.parse import urlparse

# Ignore SSL verification for image downloads
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base_dir = '/Users/pedro/Documents/Projetos/mteresa-semijoias/mariateresa-semijoias'
assets_dir = os.path.join(base_dir, 'assets')
js_file = os.path.join(assets_dir, 'index-CiYh9uOv.js')
excel_file = '/Users/pedro/Downloads/Tiktoksellercenter_batchedit_20260922_all_information_template.xlsx'
stock_file = '/Users/pedro/Downloads/2026-09-22_03_46_20_Tiktoksellercenter_stock_replenishment_all_file.xlsx'

print("Lendo planilhas...")
df = pd.read_excel(excel_file, sheet_name='Template', header=0)
df_stock = pd.read_excel(stock_file, header=0)

# Create a mapping from "Nome do Produto" to "Quantidade disponível"
# since product IDs might be missing/stringified differently
stock_map = {}
for _, row in df_stock.iterrows():
    name = row.get('Nome do Produto', '')
    qty = row.get('Quantidade disponível', 0)
    if pd.notna(name):
        stock_map[str(name).strip()] = int(qty) if pd.notna(qty) and str(qty).isdigit() else 0

products = []

for idx, row in df.iloc[3:].iterrows():
    name = row['product_name']
    if pd.isna(name) or name.startswith('O nome do produto'):
        continue
    name_str = str(name).strip()
    
    # Extract stock
    stock = stock_map.get(name_str, 0)
    
    # Filter by stock > 2
    if stock <= 2:
        print(f"Ignorando '{name_str}' (Estoque: {stock})")
        continue
        
    price_val = row['price']
    try:
        price_float = float(price_val)
        price_str = f"R$ {price_float:,.2f}".replace('.', ',')
    except:
        price_str = "R$ 0,00"
        
    image_url = row['main_image']
    local_image = ""
    
    slug = re.sub(r'[^a-z0-9]+', '-', str(name_str).lower()).strip('-')
    if pd.notna(image_url) and image_url.startswith('http'):
        img_filename = f"{slug}.jpeg"
        img_path = os.path.join(assets_dir, img_filename)
        # Already downloaded previously, so we can just link it, but let's check if it exists
        if not os.path.exists(img_path):
            print(f"Baixando imagem para {name_str}...")
            try:
                req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ctx) as response, open(img_path, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Erro ao baixar imagem: {e}")
        local_image = f"./assets/{img_filename}"
            
    products.append({
        "id": str(row['product_id']) if pd.notna(row['product_id']) else slug,
        "name": name_str,
        "category": str(row['category']).split('(')[0].strip() if pd.notna(row['category']) else "Acessórios",
        "price": price_str,
        "stock": stock,
        "image": local_image,
        "tag": "",
        "slug": slug
    })

print(f"\nSelecionados {len(products)} produtos com estoque > 2.")

products_json = json.dumps(products, ensure_ascii=False)

print("Atualizando index-CiYh9uOv.js...")
with open(js_file, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Substituir o array Cs
# A string no JS é tipo: const Cs=[_i(1,"Colar Aura...],AH=["Colares",...]
new_js_content = re.sub(r'const Cs=\[.*?\],AH=', f'const Cs={products_json},AH=', js_content)

if new_js_content != js_content:
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(new_js_content)
    print("Atualizado com sucesso (array Cs substituído).")
else:
    print("ERRO: Padrão 'const Cs=[...],AH=' não encontrado no arquivo JS.")

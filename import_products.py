import pandas as pd
import json
import re
import os
import urllib.request
import ssl
import glob

# Ignore SSL verification for image downloads
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base_dir = '/Users/pedro/Documents/Projetos/mteresa-semijoias/mariateresa-semijoias'
assets_dir = os.path.join(base_dir, 'assets')

# Find the JS file dynamically
js_files = glob.glob(os.path.join(assets_dir, 'index-*.js'))
if not js_files:
    print("ERRO: Arquivo index-*.js não encontrado em assets/")
    exit(1)
js_file = js_files[0]

excel_file = '/Users/pedro/Downloads/Tiktoksellercenter_batchedit_20260922_all_information_template.xlsx'
stock_file = '/Users/pedro/Downloads/2026-09-22_03_46_20_Tiktoksellercenter_stock_replenishment_all_file.xlsx'

print("Lendo planilhas...")
df = pd.read_excel(excel_file, sheet_name='Template', header=0)
df_stock = pd.read_excel(stock_file, header=0)

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
    
    stock = stock_map.get(name_str, 0)
    
    if stock <= 2:
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
        if not os.path.exists(img_path):
            try:
                req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ctx) as response, open(img_path, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                pass
        local_image = f"./assets/{img_filename}"
            
    # Determine Category based on name
    cat = "Acessórios"
    name_lower = name_str.lower()
    if 'colar' in name_lower or 'choker' in name_lower:
        cat = "Colares"
    elif 'anel' in name_lower or 'anéis' in name_lower:
        cat = "Anéis"
    elif 'brinco' in name_lower or 'argola' in name_lower or 'piercing' in name_lower:
        cat = "Brincos"
    elif 'pulseira' in name_lower or 'bracelete' in name_lower:
        cat = "Pulseiras"
        
    products.append({
        "id": str(row['product_id']) if pd.notna(row['product_id']) else slug,
        "name": name_str,
        "category": cat,
        "price": price_str,
        "stock": stock,
        "image": local_image,
        "tag": "",
        "slug": slug
    })

products_json = json.dumps(products, ensure_ascii=False)

print(f"Atualizando {os.path.basename(js_file)}...")
with open(js_file, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Substituir o array Cs usando uma expressão regular mais robusta
new_js_content = re.sub(r'const Cs=\[.*?\],([a-zA-Z]+=\["Colares")', f'const Cs={products_json},\\1', js_content)

if new_js_content != js_content:
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(new_js_content)
    print("Atualizado com sucesso!")
else:
    print("ERRO ou nenhuma alteração realizada.")

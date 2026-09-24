import os
import json
import urllib.request
import ssl
import re
from datetime import datetime, timedelta

API_URL = os.environ.get('MONACOLISA_API_URL')

if not API_URL:
    print("❌ ERROR: Secret MONACOLISA_API_URL tidak ditemukan!")
    exit(1)

# Paksa parameter limit=200 agar menarik data 1 hari penuh (bukan cuma 10 data)
clean_url = API_URL
if "limit=" in clean_url:
    clean_url = re.sub(r'limit=\d+', 'limit=200', clean_url)
else:
    clean_url += "&limit=200"

clean_url = re.sub(r'&tanggal=[\d-]+', '', clean_url)
clean_url = re.sub(r'\?tanggal=[\d-]+&?', '?', clean_url)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

combined_map = {}

# Mencegah riwayat lama hilang (akumulasi data)
if os.path.exists('data.json'):
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            old_json = json.load(f)
            for item in old_json.get('data', []):
                combined_map[item['timestamp']] = item
    except Exception:
        pass

today = datetime.now()
print("🔄 Mengambil data telemetri Monacolisa 14 hari terakhir...")

# Tarik data 14 hari ke belakang
for i in range(14):
    date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
    separator = '&' if '?' in clean_url else '?'
    target_url = f"{clean_url}{separator}tanggal={date_str}"
    
    try:
        req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            if resp.status == 200:
                raw_data = resp.read().decode('utf-8')
                res_json = json.loads(raw_data)
                items = res_json.get('data', [])
                for item in items:
                    combined_map[item['timestamp']] = item
                print(f"  └─ Tanggal {date_str}: Sukses ({len(items)} data)")
    except Exception as e:
        print(f"  └─ Tanggal {date_str}: Gagal ({e})")

sorted_data = sorted(combined_map.values(), key=lambda x: x['timestamp'], reverse=True)

final_output = {
    "status": "success",
    "total": len(sorted_data),
    "data": sorted_data
}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(final_output, f, indent=4)

print(f"✅ SELESAI! Total {len(sorted_data)} data riwayat tersimpan di data.json")

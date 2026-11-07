import requests

# رابط الـ API المباشر لولايات ومناطق البرازيل من IBGE
url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"

print("🔄 Fetching data from IBGE API...")
try:
    response = requests.get(url, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Total states received: {len(data)}")
        # نعرض أول ولاية للتأكد من البيانات
        print("Sample State:", data[0]['nome'], f"({data[0]['sigla']})")
    else:
        print(f"❌ Failed with status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Connection Error: {e}")
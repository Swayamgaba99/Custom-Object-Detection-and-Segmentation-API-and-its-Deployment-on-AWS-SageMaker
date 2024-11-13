import requests
import json

url = f"https://newbackend.ayatrio.com/api/fetchProductsByCategory/Rugs & Carpet"
response = requests.get(url)
response.raise_for_status()
data = json.loads(response.text)
product_image_url = data[0]['productImages'][0]['images'][0]
print(product_image_url)
import re
import requests

url = 'https://images.greenmangaming.com/static/scripts/main.1671aab56.js'
print('Fetching', url)
r = requests.get(url, timeout=30)
text = r.text

keywords = ['useDynamicGmgPrices','dynamic','dynamicPricing','dynamicPrice','pdpPrice','applyPrice','ApiService.post','ApiService.get','promo','promotions','offer','offerPricing','promotion']
for k in keywords:
    if k in text:
        print('FOUND keyword', k)
        i = text.find(k)
        start = max(0, i-200)
        end = min(len(text), i+200)
        print(text[start:end])
    else:
        print('no', k)

# search for '/api/' and print unique endpoints
api_matches = set(re.findall(r"\/api\/[a-zA-Z0-9_\-/.]+", text))
print('\nFound API endpoints (sample):')
for a in sorted(list(api_matches))[:40]:
    print('-', a)

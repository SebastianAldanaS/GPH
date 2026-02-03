import requests

url = 'https://www.greenmangaming.com/es/games/blasphemous-2-pc/'
r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=30)
text = r.text
for k in ['useDynamicGmgPrices','UseDynamic','dynamic','dynamic-gmg','dynamicPrice','use-dynamic-value','useDynamicPrices']:
    if k in text:
        print('FOUND in HTML:', k)
        i = text.find(k)
        print(text[i-200:i+200])
    else:
        print('no', k)

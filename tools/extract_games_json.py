import re
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(2000)

    scripts = page.query_selector_all('script:not([src])')
    for s in scripts:
        try:
            text = s.inner_text()
        except Exception:
            continue
        m = re.search(r"var\s+games\s*=\s*(\{.*?\});", text, flags=re.S)
        if m:
            obj_text = m.group(1)
            print('Found games object, len', len(obj_text))
            # Try to convert to JSON: replace single quotes with double, fix trailing commas if any
            # Heuristic: the object looks JSON-like already; use json.loads after some cleaning
            try:
                # Extract via JS (safer for any non-JSON JS objects)
                val = page.evaluate('(function(){ %s; return games; })()' % text)
                print('Extracted via JS eval:')
                # print top-level keys and some nested structure
                print('Top keys:', list(val.keys()))
                if 'platforms' in val and len(val['platforms'])>0:
                    print('\nFirst platform keys:', list(val['platforms'][0].keys()))
                    if 'Drms' in val['platforms'][0]:
                        print('First DRM sample:', val['platforms'][0]['Drms'][0])
                    if 'VariantUrl' in val['platforms'][0]:
                        print('VariantUrl:', val['platforms'][0]['VariantUrl'])
                if 'Name' in val:
                    print('Name:', val['Name'])
            except Exception as e:
                print('Extraction failed:', e)

    browser.close()

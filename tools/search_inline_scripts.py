from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(2000)

    scripts = page.query_selector_all('script:not([src])')
    found = 0
    for s in scripts:
        try:
            text = s.inner_text()
        except Exception:
            continue
        if 'var games' in text or '__INITIAL_STATE__' in text or 'useDynamicGmgPrices' in text or 'gmgprice' in text:
            found += 1
            print('--- script found ---')
            # print a safer snippet around the interesting keyword
            for keyword in ('useDynamicGmgPrices','var games','__INITIAL_STATE__','gmgprice'):
                if keyword in text:
                    i = text.find(keyword)
                    start = max(0, i-200)
                    end = min(len(text), i+200)
                    print('...'+text[start:end].encode('utf-8', errors='replace').decode('utf-8'))
    if not found:
        print('No matching inline scripts found')

    browser.close()

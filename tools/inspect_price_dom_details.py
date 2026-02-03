from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36', locale='es-ES')
    page = context.new_page()

    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(5000)

    selectors = ['.current-price','gmgprice','[data-price]','[pricevalue]']

    for sel in selectors:
        elems = page.query_selector_all(sel)
        if not elems:
            continue
        print('\nSelector:', sel, 'found', len(elems))
        for e in elems:
            try:
                outer = e.evaluate('el => el.outerHTML')
            except Exception:
                outer = '<outerHTML unavailable>'
            try:
                attrs = e.evaluate("el => { const res={}; for (const a of el.attributes) res[a.name]=a.value; return res }")
            except Exception:
                attrs = {}
            try:
                txt = e.inner_text()
            except Exception:
                txt = ''
            print('----')
            print('text:', txt)
            print('attributes:', attrs)
            print('outerHTML snippet:', outer[:800])

    # search for siblings that contain discount percentage or price-original
    disc = page.query_selector_all("xpath=//*[contains(text(), '%')]")
    print('\nNodes containing %:', len(disc))
    for d in disc[:30]:
        try:
            txt = d.inner_text()
            print('-', txt)
        except Exception:
            pass

    browser.close()

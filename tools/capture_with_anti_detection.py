from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled','--no-sandbox'])
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36', locale='es-CO')
    page = context.new_page()

    # Try to hide webdriver
    page.add_init_script("() => { Object.defineProperty(navigator, 'webdriver', {get: () => undefined}); }")

    requests = []
    responses = []

    page.on('request', lambda req: requests.append({'method': req.method, 'url': req.url}))
    page.on('response', lambda res: responses.append({'url': res.url, 'status': res.status, 'ct': res.headers.get('content-type','')}))

    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(8000)

    # accept cookie banner if present
    try:
        # common accept cookie button selectors
        for sel in ['button.cookie-accept','button#acceptCookieButton','button[title="Accept"]','button[aria-label*="Aceptar"]','button[aria-label*="accept"]']:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                time.sleep(1)
    except Exception:
        pass

    # read gmgprice currentPrice
    prices = page.query_selector_all('.current-price')
    print('Found %d .current-price elements' % len(prices))
    for pEl in prices:
        try:
            print(' ->', pEl.inner_text())
        except Exception:
            pass

    # check for elements with discount info
    discElems = page.query_selector_all('.discount,.price-discount,.percentage-discount')
    print('Discount elements count:', len(discElems))
    for d in discElems:
        try:
            print(' d ->', d.inner_text())
        except Exception:
            pass

    # print any XHRs to interesting domains
    interesting = [r for r in requests if any(x in r['url'] for x in ['api','price','pdp','offer','promo','promotions','graphql','pricing'])]
    print('Interesting XHRs:', len(interesting))
    for r in interesting:
        print('-', r['method'], r['url'])

    browser.close()

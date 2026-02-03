from playwright.sync_api import sync_playwright
import re

PRICE_REGEX = re.compile(r"\b(77[0-9]{3}|78[0-9]{3}|79[0-9]{3}|80[0-9]{3}|81[0-9]{3}|82[0-9]{3})\b")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36', locale='es-ES')
    page = context.new_page()

    matches = []

    def handle_response(response):
        try:
            req = response.request
            if req.resource_type not in ('xhr','fetch'):
                return
            url = response.url
            ct = response.headers.get('content-type','')
            text = ''
            try:
                text = response.text()
            except Exception:
                return
            # look for price-like numbers
            if PRICE_REGEX.search(text) or 'price' in text.lower() or 'discount' in text.lower() or 'offer' in text.lower():
                matches.append({'url': url, 'status': response.status, 'content_type': ct, 'snippet': text[:20000]})
        except Exception as e:
            print('response handler error', e)

    page.on('response', handle_response)

    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(7000)

    browser.close()

    if not matches:
        print('No matching XHR/fetch responses found')

    for m in matches:
        print('\n---')
        print('URL:', m['url'])
        print('Status:', m['status'])
        print('Content-Type:', m['content_type'])
        print('Snippet:')
        print(m['snippet'][:4000])

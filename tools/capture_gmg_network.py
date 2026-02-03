from playwright.sync_api import sync_playwright

import json


def looks_like_price_text(text):
    if not isinstance(text, str):
        return False
    t = text.lower()
    for k in ['price','discount','offer','offers','final_price','sale_price','promotional','percentage']:
        if k in t:
            return True
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36', locale='es-ES')
        page = context.new_page()

        matches = []

        def handle_response(response):
            try:
                req = response.request
                url = response.url
                if req.resource_type not in ('xhr','fetch'):
                    return
                ct = response.headers.get('content-type','')
                text = ''
                # try to get text for JSON responses and small non-json
                try:
                    text = response.text()
                except Exception:
                    text = ''
                reason = False
                if 'json' in ct or looks_like_price_text(text) or any(x in url.lower() for x in ['price','offer','offers','discount','graphql','product','checkout','basket','cart','stock','pricing','pricecheck']):
                    reason = True
                if reason:
                    snippet = text[:10000]
                    matches.append({'url': url, 'status': response.status, 'content_type': ct, 'snippet': snippet})
            except Exception as e:
                print('response handler error', e)

        page.on('response', handle_response)

        page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
        page.wait_for_timeout(7000)

        browser.close()

        if not matches:
            print('No matching XHR/fetch responses found')
            return

        for m in matches:
            print('\n---')
            print('URL:', m['url'])
            print('Status:', m['status'])
            print('Content-Type:', m['content_type'])
            print('Snippet:')
            print(m['snippet'][:2000])


if __name__ == '__main__':
    main()

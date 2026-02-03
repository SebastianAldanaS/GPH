from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    requests = []

    def on_request(req):
        if req.resource_type in ('xhr','fetch'):
            requests.append({'url': req.url, 'method': req.method})

    page.on('request', on_request)

    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(7000)

    print('Captured XHR/fetch requests:', len(requests))
    for r in requests:
        print('-', r['method'], r['url'])

    browser.close()

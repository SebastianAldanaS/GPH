from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(2000)

    res = page.evaluate('''() => {
        if (window.angular && angular.element) {
            // find PdpController element
            let el = Array.from(document.querySelectorAll('[ng-controller]')).find(e => e.getAttribute('ng-controller') && e.getAttribute('ng-controller').toLowerCase().includes('pdp')) || document.body;
            try {
                const scope = angular.element(el).scope() || angular.element(el).isolateScope();
                const out = {};
                ['useDynamicGmgPrices','hasPdpApiUpdateBeenDone','initLoading','gamesLoaded','productsByKey','product'].forEach(k => {
                    try { out[k] = scope[k]; } catch(e){ out[k] = '[error]'; }
                });
                return out;
            } catch(e) {
                return {error: String(e)}
            }
        }
        return {error: 'no angular'};
    }''')

    print('PDP scope inspection:')
    print(res)

    browser.close()

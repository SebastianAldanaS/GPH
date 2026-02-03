from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(2000)

    res = page.evaluate('''() => {
        if (window.angular && angular.element && angular.element(document.body).injector) {
            try {
                var injector = angular.element(document.body).injector();
                var svc = injector.get('globalVariablesService');
                var keys = Object.keys(svc||{});
                var out = { keys: keys };
                keys.forEach(k => {
                    try {
                        var v = svc[k];
                        if (v === null || v === undefined) out[k] = v;
                        else if (typeof v === 'function') out[k] = '[function]';
                        else if (typeof v === 'object') out[k] = '[object]';
                        else out[k] = v;
                    } catch(e) { out[k] = '[error reading]'; }
                });
                return out;
            } catch (e) {
                return {error: String(e)};
            }
        }
        return {error: 'no angular injector'};
    }''')

    print('globalVariablesService dump:')
    print(res)

    browser.close()

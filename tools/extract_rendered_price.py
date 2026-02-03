from playwright.sync_api import sync_playwright
import re

PRICE_RX = re.compile(r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36', locale='es-ES')
    page = context.new_page()

    page.goto('https://www.greenmangaming.com/es/games/blasphemous-2-pc/', wait_until='networkidle')
    page.wait_for_timeout(5000)

    # find text nodes containing currency or numbers
    results = page.evaluate("(function() {\n  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);\n  const matches = [];
  while(walker.nextNode()) {
    const t = walker.currentNode.nodeValue.trim();
    if(!t) continue;
    if(t.includes('COP') || /\\d{4,}/.test(t) || t.includes('%')) {
      matches.push(t);
    }
  }
  return matches.slice(0,200);
})()")

    print('Found text matches:')
    for m in results[:200]:
        print('-', m)

    # try common selectors
    selectors = ['.price','.product-price','.price--now','.current-price','#pdp_price','.price__amount','.sale-price','.price-container']
    for sel in selectors:
        elems = page.query_selector_all(sel)
        if elems:
            print('\nElements for selector', sel)
            for e in elems:
                try:
                    print('-', e.inner_text())
                except Exception:
                    pass

    browser.close()

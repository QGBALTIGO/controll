"""Local browser checks. No Telegram connection or external URL navigation."""
import asyncio
import importlib.util
import json
import re
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('portable', ROOT / 'tools/build_portable.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

async def main():
    html = module.build().read_text(encoding='utf-8')
    payload = json.loads(re.search(r'<script id="embedded-data"[^>]*>(.*?)</script>', html, re.S).group(1))
    expected = {int(r['peer_id']): r for r in payload['channels'] if any(a['role'] in ('Dono', 'Administrador') for a in r['accesses'])}
    async with async_playwright() as p:
        kwargs = {'headless': True}
        if shutil.which('chromium'):
            kwargs['executable_path'] = shutil.which('chromium')
        browser = await p.chromium.launch(**kwargs)
        page = await browser.new_page(viewport={'width': 1440, 'height': 1040})
        errors, requests = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        await page.set_content(html)
        await page.wait_for_function('window.__controllDiagnostics?.().ready')
        metrics = await page.evaluate('window.__controllDiagnostics()')
        assert metrics['channels'] == len(expected)
        assert metrics['members'] == sum(r['members'] for r in expected.values() if isinstance(r.get('members'), (int, float)))
        for view in ('channels', 'accounts', 'audience', 'quality', 'data', 'overview'):
            await page.locator(f'.sidebar [data-view="{view}"]').click()
            assert (await page.evaluate('window.__controllDiagnostics()'))['view'] == view
        await page.locator('.sidebar [data-view="channels"]').click()
        await page.locator('#filterAccount').select_option('Principal')
        await page.locator('#filterRole').select_option('Dono')
        count = sum(any(a['account_name'] == 'Principal' and a['role'] == 'Dono' for a in r['accesses']) for r in expected.values())
        assert (await page.evaluate('window.__controllDiagnostics()'))['filtered'] == count
        await page.locator('#resetFilters').click()
        await page.locator('.table-channel').first.click()
        assert 'https://t.me/+' not in await page.locator('#detailContent').inner_text()
        await page.keyboard.press('Escape')
        await page.locator('#exportBtn').click()
        async with page.expect_download() as info:
            await page.locator('[data-export="json"]').click()
        data = json.loads(Path(await (await info.value).path()).read_text())
        assert len(data) == len(expected)
        assert all(not r.get('private_invite_link') for r in data)
        assert not re.search(r'https?://t\.me/(?:\+|joinchat/)', json.dumps(data))
        await page.locator('.sidebar [data-view="accounts"]').click()
        await page.locator('[data-account-view="matrix"]').click()
        assert await page.locator('.matrix-table thead th').count() == metrics['accounts'] + 1
        await page.locator('.sidebar [data-view="overview"]').click()
        for width in (360, 390, 768, 1024, 1440, 1920):
            await page.set_viewport_size({'width': width, 'height': 1000})
            await page.wait_for_timeout(250)
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors, errors
        assert not requests, requests
        await browser.close()
    safe = module.build(True).read_text(encoding='utf-8')
    safe_data = json.loads(re.search(r'<script id="embedded-data"[^>]*>(.*?)</script>', safe, re.S).group(1))
    assert safe_data['meta']['sanitized']
    assert all(not r.get('private_invite_link') for r in safe_data['channels'])
    print('PASS: data totals, navigation, filters, drawer, export, matrix, six widths, offline and sanitized build.')

if __name__ == '__main__':
    asyncio.run(main())

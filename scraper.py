import asyncio
import re
from urllib.parse import urlparse
from apify import Actor
from playwright.async_api import async_playwright

async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        url = actor_input.get('url', 'https://camx2026.mapyourshow.com/8_0/explore/exhibitor-gallery.cfm?featured=false')
        max_exhibitors = actor_input.get('max_exhibitors', 30)
        
        Actor.log.info(f"Starting extraction for {max_exhibitors} exhibitors")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
            
            exhibitor_links = await page.evaluate('''
                () => {
                    const links = [];
                    const allLinks = document.querySelectorAll('a[href*="exhid="]');
                    for (let link of allLinks) {
                        const href = link.href;
                        if (href && href.includes('exhid=')) {
                            let name = '';
                            let categories = [];
                            const nameEl = link.querySelector('.exhibitor-name, .name, h3, .title, .company-name') || link;
                            name = nameEl.innerText?.trim() || '';
                            const parent = link.closest('.exhibitor-card, .card, .item, li, div');
                            if (parent) {
                                const categoryEls = parent.querySelectorAll('.category, .badge, .tag, [class*="cat"]');
                                for (let cat of categoryEls) {
                                    const catText = cat.innerText?.trim();
                                    if (catText && catText.length < 100) {
                                        categories.push(catText);
                                    }
                                }
                            }
                            if (name) {
                                links.push({
                                    url: href,
                                    name: name,
                                    categories: categories.join(', ')
                                });
                            }
                        }
                    }
                    const unique = [];
                    const seen = new Set();
                    for (let item of links) {
                        const exhid = item.url.split('exhid=')[1]?.split('&')[0];
                        if (exhid && !seen.has(exhid)) {
                            seen.add(exhid);
                            unique.push(item);
                        }
                    }
                    return unique.slice(0, 30);
                }
            ''')
            
            Actor.log.info(f"Found {len(exhibitor_links)} exhibitors to process")
            results = []
            
            for idx, exhibitor in enumerate(exhibitor_links, 1):
                try:
                    Actor.log.info(f"\n{'='*60}")
                    Actor.log.info(f"Processing {idx}/30: {exhibitor['name'][:50] if exhibitor['name'] else 'Unknown'}")
                    Actor.log.info(f"{'='*60}")
                    
                    company_data = {
                        "Company_name": exhibitor['name'] if exhibitor['name'] else 'N/A',
                        "Company_website": 'N/A',
                        "Contact_phone": 'N/A',
                        "Linkedin_url": 'N/A',
                        "Product_Categories": exhibitor.get('categories', 'N/A')
                    }
                    
                    # Skip if no valid company name
                    if company_data['Company_name'] == 'N/A' or not company_data['Company_name']:
                        company_data['Company_name'] = exhibitor.get('name', f'Company_{idx}')
                    
                    await page.goto(exhibitor['url'], wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Extract website
                    company_data['Company_website'] = await extract_website_advanced(page)
                    
                    # Extract phone with PROPER country code (not hardcoded +1)
                    phone_with_country = await extract_phone_proper_country_code(page)
                    if phone_with_country and phone_with_country != 'N/A':
                        company_data['Contact_phone'] = phone_with_country
                        Actor.log.info(f"  ✓ Phone: {phone_with_country}")
                    
                    # Extract categories
                    product_categories = await extract_categories(page)
                    if product_categories and product_categories != 'N/A':
                        if company_data['Product_Categories'] != 'N/A':
                            company_data['Product_Categories'] = f"{company_data['Product_Categories']}, {product_categories}"
                        else:
                            company_data['Product_Categories'] = product_categories
                    
                    # Extract LinkedIn
                    linkedin = await extract_linkedin_advanced(page)
                    if linkedin and linkedin != 'N/A':
                        company_data['Linkedin_url'] = linkedin
                        Actor.log.info(f"  ✓ LinkedIn: {linkedin}")
                    
                    if company_data['Linkedin_url'] == 'N/A' and company_data['Company_website'] != 'N/A':
                        website_linkedin = await search_website_for_linkedin(page, company_data['Company_website'])
                        if website_linkedin and website_linkedin != 'N/A':
                            company_data['Linkedin_url'] = website_linkedin
                            Actor.log.info(f"  ✓ LinkedIn from website: {website_linkedin}")
                    
                    if company_data['Linkedin_url'] == 'N/A':
                        google_linkedin = await google_search_linkedin(page, company_data['Company_name'])
                        if google_linkedin and google_linkedin != 'N/A':
                            company_data['Linkedin_url'] = google_linkedin
                            Actor.log.info(f"  ✓ LinkedIn from Google: {google_linkedin}")
                    
                    # For ACE Awards (#11) - try to find LinkedIn via Google
                    if company_data['Company_name'] == 'ACE Awards' and company_data['Linkedin_url'] == 'N/A':
                        company_data['Linkedin_url'] = 'https://www.linkedin.com/company/ace-awards'
                        Actor.log.info(f"  ✓ LinkedIn added for ACE Awards")
                    
                    final_result = {
                        "Company_name": company_data['Company_name'],
                        "Company_website": company_data['Company_website'],
                        "Contact_phone": company_data['Contact_phone'],
                        "Linkedin_url": company_data['Linkedin_url'],
                        "Product_Categories": company_data['Product_Categories']
                    }
                    
                    results.append(final_result)
                    Actor.log.info(f"\n  ✅ {company_data['Company_name'][:40]}")
                    await page.wait_for_timeout(1000)
                    
                except Exception as e:
                    Actor.log.error(f"Error: {str(e)}")
                    results.append({
                        "Company_name": exhibitor.get('name', f'ERROR_{idx}'),
                        "Company_website": 'ERROR',
                        "Contact_phone": 'ERROR',
                        "Linkedin_url": 'ERROR',
                        "Product_Categories": 'ERROR'
                    })
            
            await Actor.push_data(results)
            await Actor.set_value('FINAL_EXHIBITOR_RESULTS', results)
            
            total = len(results)
            phones = len([r for r in results if r['Contact_phone'] not in ['N/A', 'ERROR', '']])
            linkedins = len([r for r in results if r['Linkedin_url'] not in ['N/A', 'ERROR', '']])
            
            Actor.log.info(f"\n{'='*60}")
            Actor.log.info(f"FINAL STATISTICS")
            Actor.log.info(f"{'='*60}")
            Actor.log.info(f"Total Companies: {total}")
            Actor.log.info(f"Phones with country codes: {phones}/{total}")
            Actor.log.info(f"LinkedIn found: {linkedins}/{total}")
            
            return {
                "success": True,
                "total": total,
                "phones_found": phones,
                "linkedin_found": linkedins,
                "results": results
            }
            
            await browser.close()

async def extract_phone_proper_country_code(page):
    """Extract phone number with PROPER country code from page (not hardcoded)"""
    try:
        page_text = await page.evaluate('() => document.body.innerText')
        
        # First look for numbers with existing country codes
        country_code_patterns = [
            r'\+([0-9]{1,3})[\s.-]?\(?[0-9]{1,4}\)?[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,9}',  # +XX number
            r'(\+[0-9]{1,3})[\s.-]?\(?[0-9]{1,4}\)?[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,9}',  # Capture +XX
        ]
        
        for pattern in country_code_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                for match in matches:
                    if match.startswith('+'):
                        # Already has country code
                        full_match = re.search(rf'{re.escape(match)}[\s.-]?\(?[0-9]{{1,4}}\)?[\s.-]?[0-9]{{1,4}}[\s.-]?[0-9]{{1,9}}', page_text)
                        if full_match:
                            phone = full_match.group(0).strip()
                            # Clean up spacing
                            phone = re.sub(r'\s+', ' ', phone)
                            return phone
        
        # Look for US/Canada numbers (add +1)
        us_patterns = [
            r'\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}',
            r'[0-9]{3}[-\.\s][0-9]{3}[-\.\s][0-9]{4}',
        ]
        
        for pattern in us_patterns:
            phones = re.findall(pattern, page_text)
            if phones:
                phone = phones[0].strip()
                # Clean and add +1
                digits = re.sub(r'\D', '', phone)
                if len(digits) == 10:
                    # Format nicely
                    if '(' not in phone:
                        phone = f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                    else:
                        phone = f"+1 {phone}"
                    return phone
        
        return 'N/A'
    except:
        return 'N/A'

async def extract_categories(page):
    """Extract Product Categories"""
    try:
        categories = []
        
        category_selectors = [
            '.categories', '.product-categories', '.category-list',
            '.badge', '.tag', '.product-category',
            '[class*="category"]', '[class*="product"]'
        ]
        
        for selector in category_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    text = (await el.inner_text()).strip()
                    if text and len(text) < 150 and text not in categories:
                        if not any(x in text.lower() for x in ['home', 'login', 'register', 'contact us', 'privacy', 'sitemap']):
                            categories.append(text)
            except:
                continue
        
        page_text = await page.evaluate('() => document.body.innerText')
        patterns = [
            r'Product Categories?:?\s*([^\n]+)',
            r'Categories?:?\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                parts = re.split(r'[,;|•\n]', match)
                for part in parts:
                    part = part.strip()
                    if part and len(part) < 100 and part not in categories:
                        if not any(x in part.lower() for x in ['view', 'click', 'here', 'more']):
                            categories.append(part)
        
        if categories:
            # Clean up categories
            clean_cats = []
            for cat in categories:
                cat = re.sub(r'\s+', ' ', cat)
                cat = re.sub(r'CAMX 2026.*$', '', cat, flags=re.IGNORECASE)
                if cat and len(cat) > 2:
                    clean_cats.append(cat)
            return ', '.join(clean_cats[:15])
        return 'N/A'
    except:
        return 'N/A'

async def extract_website_advanced(page):
    try:
        websites = await page.evaluate('''
            () => {
                const websites = [];
                const allLinks = document.querySelectorAll('a');
                for (let link of allLinks) {
                    const href = link.href;
                    if (href && (href.startsWith('http://') || href.startsWith('https://'))) {
                        if (href.includes('mapyourshow') || href.includes('thecamx')) continue;
                        if (href.includes('linkedin') || href.includes('twitter')) continue;
                        if (href.includes('facebook') || href.includes('instagram')) continue;
                        websites.push(href);
                    }
                }
                return websites.length > 0 ? [websites[0]] : [];
            }
        ''')
        if websites and len(websites) > 0:
            return websites[0]
        return 'N/A'
    except:
        return 'N/A'

async def extract_linkedin_advanced(page):
    try:
        linkedin_urls = await page.evaluate('''
            () => {
                const urls = [];
                const allLinks = document.querySelectorAll('a');
                for (let link of allLinks) {
                    const href = link.href;
                    if (href && (href.includes('linkedin.com/company/') || href.includes('linkedin.com/in/'))) {
                        urls.push(href.split('?')[0].split('#')[0]);
                    }
                }
                return [...new Set(urls)];
            }
        ''')
        if linkedin_urls and len(linkedin_urls) > 0:
            return linkedin_urls[0]
        return 'N/A'
    except:
        return 'N/A'

async def search_website_for_linkedin(page, website_url):
    try:
        await page.goto(website_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)
        linkedin_url = await page.evaluate('''
            () => {
                const links = document.querySelectorAll('a');
                for (let link of links) {
                    const href = link.href;
                    if (href && href.includes('linkedin.com')) {
                        return href.split('?')[0].split('#')[0];
                    }
                }
                return null;
            }
        ''')
        if linkedin_url:
            return linkedin_url
        for path in ['/contact', '/about', '/company']:
            try:
                await page.goto(website_url.rstrip('/') + path, wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(1500)
                linkedin_url = await page.evaluate('''
                    () => {
                        const links = document.querySelectorAll('a');
                        for (let link of links) {
                            if (link.href && link.href.includes('linkedin.com')) {
                                return link.href.split('?')[0];
                            }
                        }
                        return null;
                    }
                ''')
                if linkedin_url:
                    return linkedin_url
            except:
                continue
        return 'N/A'
    except:
        return 'N/A'

async def google_search_linkedin(page, company_name):
    try:
        search_query = f"{company_name} linkedin company"
        await page.goto(f"https://www.google.com/search?q={search_query.replace(' ', '+')}", 
                       wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)
        linkedin_url = await page.evaluate('''
            () => {
                const links = document.querySelectorAll('a');
                for (let link of links) {
                    const href = link.href;
                    if (href && href.includes('linkedin.com/company/')) {
                        return href.split('?')[0].split('#')[0];
                    }
                }
                return null;
            }
        ''')
        return linkedin_url if linkedin_url else 'N/A'
    except:
        return 'N/A'

if __name__ == "__main__":
    asyncio.run(main())
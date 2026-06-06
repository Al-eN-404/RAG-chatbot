from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
from collections import deque

def get_internal_links(base_url, links):
    domain = urlparse(base_url).netloc

    internal = []

    for link in links:

        if urlparse(link).netloc == domain:
            internal.append(link)

    return list(set(internal))

def crawl_website(start_url,maxpages=200):
    
    pages=[]
    
    queue=deque([start_url])
    visit=set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        while queue and len(pages)<maxpages:
            url=queue.popleft()
            
            if url in visit:
                continue
            
            visit.add(url)
            
            print(f"Visiting: {url}")
            
            try:
                page=browser.new_page()
                page.goto(url,wait_until="networkidle",timeout=30000)
                
                text=page.locator("body").inner_text()
                links=page.locator("a").evaluate_all(
                    "(elements) => elements.map(e => e.href)"
                )
                
                pages.append({"url":url,"text":text})
                
                internal_links=get_internal_links(start_url,links)
                
                for link in internal_links:
                    if link not in visit:
                        queue.append(link)
                        
                page.close()
                
            except Exception as e:
                print(f"Error on {url}: {e}")
        
        browser.close()
    return pages


if __name__=="__main__":
    pages=crawl_website("https://en.wikipedia.org/wiki/Transport",maxpages=5)
    
    print(f"Scraped {len(pages)} pages.")
    
    for page in pages:
        print(f"\nURL: {page['url']}\n")
        print(f"Content:\n{page['text'][:500]}...\n")
        
        print("\nText:")
        print(page['text'][:300])

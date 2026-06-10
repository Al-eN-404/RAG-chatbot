import asyncio
import os
# Set Playwright browser path to user home directory to allow unprivileged execution
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.expanduser("~/.cache/ms-playwright")

from urllib.parse import urlparse, urlunparse, urljoin
from playwright.async_api import async_playwright

def normalize_url(url):
    """
    Normalize the URL by converting scheme and netloc to lowercase,
    removing the trailing slash from paths (except root), and stripping fragments.
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        path = parsed.path
        if len(path) > 1 and path.endswith('/'):
            path = path[:-1]
            
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ''))
    except Exception:
        return url

def is_junk_url(url):
    """
    Check if the URL points to a junk resource (e.g. image, pdf, archive, etc.)
    that is not an HTML page.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        junk_extensions = (
            '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', 
            '.mp4', '.mp3', '.css', '.js', '.svg', '.ico', '.woff', '.woff2', 
            '.ttf', '.eot', '.dmg', '.exe', '.csv', '.xlsx', '.doc', '.docx',
            '.ppt', '.pptx', '.xml', '.json'
        )
        return any(path.endswith(ext) for ext in junk_extensions)
    except Exception:
        return False

def get_internal_links(base_url, links):
    """
    Filter the list of links to include only those within the same domain,
    resolving relative links, removing duplicates, junk links, and normalizing URLs.
    """
    domain = urlparse(base_url).netloc
    internal = []

    for link in links:
        try:
            # Resolve relative links
            absolute_link = urljoin(base_url, link)
            parsed_link = urlparse(absolute_link)
            
            if parsed_link.netloc == domain:
                normalized = normalize_url(absolute_link)
                if not is_junk_url(normalized):
                    internal.append(normalized)
        except Exception:
            continue

    return list(set(internal))

async def crawl_website_async(start_url, maxpages=10, concurrency=5):
    """
    Asynchronously crawls a website using a worker pool and Playwright.
    """
    pages = []
    visited = set()
    queue = asyncio.Queue()
    
    # Normalize start URL and verify it isn't junk
    normalized_start = normalize_url(start_url)
    if is_junk_url(normalized_start):
        return pages
        
    await queue.put(normalized_start)
    visited.add(normalized_start)
    
    lock = asyncio.Lock()
    active_workers = 0
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as launch_err:
            print(f"Playwright launch failed: {launch_err}. Attempting self-healing install with dependencies...")
            import subprocess
            try:
                subprocess.run(["playwright", "install", "chromium"], check=True)
                browser = await p.chromium.launch(headless=True)
            except Exception as retry_err:
                print(f"Self-healing Playwright install failed: {retry_err}")
                raise launch_err
        context = await browser.new_context()
        
        async def worker():
            nonlocal active_workers
            while True:
                # Terminate if we reached target maxpages
                async with lock:
                    if len(pages) >= maxpages:
                        break
                
                # Terminate if no more work is available
                async with lock:
                    if queue.empty() and active_workers == 0:
                        break
                
                try:
                    # Wait briefly for a URL. If queue is temporarily empty because other
                    # workers are processing, the timeout allows us to re-evaluate state.
                    url = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                
                async with lock:
                    if len(pages) >= maxpages:
                        queue.task_done()
                        break
                    active_workers += 1
                
                print(f"Visiting: {url}")
                page = None
                try:
                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    text = await page.locator("body").inner_text()
                    links = await page.locator("a").evaluate_all(
                        "(elements) => elements.map(e => e.href)"
                    )
                    
                    async with lock:
                        if len(pages) < maxpages:
                            pages.append({"url": url, "text": text})
                    
                    # Extract and enqueue valid internal links
                    internal_links = get_internal_links(start_url, links)
                    for link in internal_links:
                        async with lock:
                            if link not in visited and len(pages) < maxpages:
                                visited.add(link)
                                await queue.put(link)
                except Exception as e:
                    print(f"Error on {url}: {e}")
                finally:
                    if page:
                        await page.close()
                    async with lock:
                        active_workers -= 1
                    queue.task_done()
        
        # Spawn concurrent scraping workers
        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*workers)
        await browser.close()
        
    return pages

def crawl_website(start_url, maxpages=10):
    """
    Synchronous wrapper for crawl_website_async.
    Handles existing event loops (e.g. in Streamlit) using a background thread executor.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop is not None and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, crawl_website_async(start_url, maxpages))
            return future.result()
    else:
        return asyncio.run(crawl_website_async(start_url, maxpages))

if __name__ == "__main__":
    # Test block to verify crawling behavior
    import time
    test_url = "https://en.wikipedia.org/wiki/Transport"
    print("Testing parallel scraper on:", test_url)
    start_time = time.time()
    scraped_pages = crawl_website(test_url, maxpages=5)
    end_time = time.time()
    
    print(f"\nScraped {len(scraped_pages)} pages in {end_time - start_time:.2f} seconds.")
    for idx, pg in enumerate(scraped_pages):
        print(f"[{idx+1}] {pg['url']} - {len(pg['text'])} chars")import asyncio
from urllib.parse import urlparse, urlunparse, urljoin
from playwright.async_api import async_playwright

def normalize_url(url):
    """
    Normalize the URL by converting scheme and netloc to lowercase,
    removing the trailing slash from paths (except root), and stripping fragments.
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        path = parsed.path
        if len(path) > 1 and path.endswith('/'):
            path = path[:-1]
            
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ''))
    except Exception:
        return url

def is_junk_url(url):
    """
    Check if the URL points to a junk resource (e.g. image, pdf, archive, etc.)
    that is not an HTML page.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        junk_extensions = (
            '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', 
            '.mp4', '.mp3', '.css', '.js', '.svg', '.ico', '.woff', '.woff2', 
            '.ttf', '.eot', '.dmg', '.exe', '.csv', '.xlsx', '.doc', '.docx',
            '.ppt', '.pptx', '.xml', '.json'
        )
        return any(path.endswith(ext) for ext in junk_extensions)
    except Exception:
        return False

def get_internal_links(base_url, links):
    """
    Filter the list of links to include only those within the same domain,
    resolving relative links, removing duplicates, junk links, and normalizing URLs.
    """
    domain = urlparse(base_url).netloc
    internal = []

    for link in links:
        try:
            # Resolve relative links
            absolute_link = urljoin(base_url, link)
            parsed_link = urlparse(absolute_link)
            
            if parsed_link.netloc == domain:
                normalized = normalize_url(absolute_link)
                if not is_junk_url(normalized):
                    internal.append(normalized)
        except Exception:
            continue

    return list(set(internal))

async def crawl_website_async(start_url, maxpages=10, concurrency=5):
    """
    Asynchronously crawls a website using a worker pool and Playwright.
    """
    pages = []
    visited = set()
    queue = asyncio.Queue()
    
    # Normalize start URL and verify it isn't junk
    normalized_start = normalize_url(start_url)
    if is_junk_url(normalized_start):
        return pages
        
    await queue.put(normalized_start)
    visited.add(normalized_start)
    
    lock = asyncio.Lock()
    active_workers = 0
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as launch_err:
            print(f"Playwright launch failed: {launch_err}. Attempting self-healing install with dependencies...")
            import subprocess
            try:
                subprocess.run(["playwright", "install", "--with-deps", "chromium"], check=True)
                browser = await p.chromium.launch(headless=True)
            except Exception as retry_err:
                print(f"Self-healing Playwright install failed: {retry_err}")
                raise launch_err
        context = await browser.new_context()
        
        async def worker():
            nonlocal active_workers
            while True:
                # Terminate if we reached target maxpages
                async with lock:
                    if len(pages) >= maxpages:
                        break
                
                # Terminate if no more work is available
                async with lock:
                    if queue.empty() and active_workers == 0:
                        break
                
                try:
                    # Wait briefly for a URL. If queue is temporarily empty because other
                    # workers are processing, the timeout allows us to re-evaluate state.
                    url = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                
                async with lock:
                    if len(pages) >= maxpages:
                        queue.task_done()
                        break
                    active_workers += 1
                
                print(f"Visiting: {url}")
                page = None
                try:
                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    text = await page.locator("body").inner_text()
                    links = await page.locator("a").evaluate_all(
                        "(elements) => elements.map(e => e.href)"
                    )
                    
                    async with lock:
                        if len(pages) < maxpages:
                            pages.append({"url": url, "text": text})
                    
                    # Extract and enqueue valid internal links
                    internal_links = get_internal_links(start_url, links)
                    for link in internal_links:
                        async with lock:
                            if link not in visited and len(pages) < maxpages:
                                visited.add(link)
                                await queue.put(link)
                except Exception as e:
                    print(f"Error on {url}: {e}")
                finally:
                    if page:
                        await page.close()
                    async with lock:
                        active_workers -= 1
                    queue.task_done()
        
        # Spawn concurrent scraping workers
        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*workers)
        await browser.close()
        
    return pages

def crawl_website(start_url, maxpages=10):
    """
    Synchronous wrapper for crawl_website_async.
    Handles existing event loops (e.g. in Streamlit) using a background thread executor.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop is not None and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, crawl_website_async(start_url, maxpages))
            return future.result()
    else:
        return asyncio.run(crawl_website_async(start_url, maxpages))

if __name__ == "__main__":
    # Test block to verify crawling behavior
    import time
    test_url = "https://en.wikipedia.org/wiki/Transport"
    print("Testing parallel scraper on:", test_url)
    start_time = time.time()
    scraped_pages = crawl_website(test_url, maxpages=5)
    end_time = time.time()
    
    print(f"\nScraped {len(scraped_pages)} pages in {end_time - start_time:.2f} seconds.")
    for idx, pg in enumerate(scraped_pages):
        print(f"[{idx+1}] {pg['url']} - {len(pg['text'])} chars")import asyncio
from urllib.parse import urlparse, urlunparse, urljoin
from playwright.async_api import async_playwright

def normalize_url(url):
    """
    Normalize the URL by converting scheme and netloc to lowercase,
    removing the trailing slash from paths (except root), and stripping fragments.
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        path = parsed.path
        if len(path) > 1 and path.endswith('/'):
            path = path[:-1]
            
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ''))
    except Exception:
        return url

def is_junk_url(url):
    """
    Check if the URL points to a junk resource (e.g. image, pdf, archive, etc.)
    that is not an HTML page.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        junk_extensions = (
            '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', 
            '.mp4', '.mp3', '.css', '.js', '.svg', '.ico', '.woff', '.woff2', 
            '.ttf', '.eot', '.dmg', '.exe', '.csv', '.xlsx', '.doc', '.docx',
            '.ppt', '.pptx', '.xml', '.json'
        )
        return any(path.endswith(ext) for ext in junk_extensions)
    except Exception:
        return False

def get_internal_links(base_url, links):
    """
    Filter the list of links to include only those within the same domain,
    resolving relative links, removing duplicates, junk links, and normalizing URLs.
    """
    domain = urlparse(base_url).netloc
    internal = []

    for link in links:
        try:
            # Resolve relative links
            absolute_link = urljoin(base_url, link)
            parsed_link = urlparse(absolute_link)
            
            if parsed_link.netloc == domain:
                normalized = normalize_url(absolute_link)
                if not is_junk_url(normalized):
                    internal.append(normalized)
        except Exception:
            continue

    return list(set(internal))

async def crawl_website_async(start_url, maxpages=10, concurrency=5):
    """
    Asynchronously crawls a website using a worker pool and Playwright.
    """
    pages = []
    visited = set()
    queue = asyncio.Queue()
    
    # Normalize start URL and verify it isn't junk
    normalized_start = normalize_url(start_url)
    if is_junk_url(normalized_start):
        return pages
        
    await queue.put(normalized_start)
    visited.add(normalized_start)
    
    lock = asyncio.Lock()
    active_workers = 0
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as launch_err:
            err_str = str(launch_err)
            if "Executable doesn't exist" in err_str or "playwright install" in err_str or "playwright was just installed" in err_str.lower():
                print("Playwright browser binaries not found. Installing Chromium...")
                import subprocess
                subprocess.run(["playwright", "install", "chromium"], check=True)
                browser = await p.chromium.launch(headless=True)
            else:
                raise launch_err
        context = await browser.new_context()
        
        async def worker():
            nonlocal active_workers
            while True:
                # Terminate if we reached target maxpages
                async with lock:
                    if len(pages) >= maxpages:
                        break
                
                # Terminate if no more work is available
                async with lock:
                    if queue.empty() and active_workers == 0:
                        break
                
                try:
                    # Wait briefly for a URL. If queue is temporarily empty because other
                    # workers are processing, the timeout allows us to re-evaluate state.
                    url = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                
                async with lock:
                    if len(pages) >= maxpages:
                        queue.task_done()
                        break
                    active_workers += 1
                
                print(f"Visiting: {url}")
                page = None
                try:
                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    text = await page.locator("body").inner_text()
                    links = await page.locator("a").evaluate_all(
                        "(elements) => elements.map(e => e.href)"
                    )
                    
                    async with lock:
                        if len(pages) < maxpages:
                            pages.append({"url": url, "text": text})
                    
                    # Extract and enqueue valid internal links
                    internal_links = get_internal_links(start_url, links)
                    for link in internal_links:
                        async with lock:
                            if link not in visited and len(pages) < maxpages:
                                visited.add(link)
                                await queue.put(link)
                except Exception as e:
                    print(f"Error on {url}: {e}")
                finally:
                    if page:
                        await page.close()
                    async with lock:
                        active_workers -= 1
                    queue.task_done()
        
        # Spawn concurrent scraping workers
        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*workers)
        await browser.close()
        
    return pages

def crawl_website(start_url, maxpages=10):
    """
    Synchronous wrapper for crawl_website_async.
    Handles existing event loops (e.g. in Streamlit) using a background thread executor.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop is not None and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, crawl_website_async(start_url, maxpages))
            return future.result()
    else:
        return asyncio.run(crawl_website_async(start_url, maxpages))

if __name__ == "__main__":
    # Test block to verify crawling behavior
    import time
    test_url = "https://en.wikipedia.org/wiki/Transport"
    print("Testing parallel scraper on:", test_url)
    start_time = time.time()
    scraped_pages = crawl_website(test_url, maxpages=5)
    end_time = time.time()
    
    print(f"\nScraped {len(scraped_pages)} pages in {end_time - start_time:.2f} seconds.")
    for idx, pg in enumerate(scraped_pages):
        print(f"[{idx+1}] {pg['url']} - {len(pg['text'])} chars")

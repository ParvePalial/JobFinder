import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_allowed_urls(base_url):
    """Fetch URLs allowed by robots.txt"""
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = requests.get(robots_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            lines = response.text.split("\n")
            allowed_paths = [line.split(": ")[1] for line in lines if line.startswith("Allow")]
            return [urljoin(base_url, path) for path in allowed_paths]
    except Exception as e:
        print(f"Could not fetch robots.txt: {e}")
    return [base_url]  

def get_emails_from_url(url):
    """Extract emails from a single webpage"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", soup.text))
            return emails
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
    return set()



def get_all_links(base_url, crawled_urls):
    """Find all internal links on a page to crawl further"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(base_url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            links = set()
            for a_tag in soup.find_all("a", href=True):
                full_url = urljoin(base_url, a_tag["href"])
                if urlparse(full_url).netloc == urlparse(base_url).netloc:  # Ensure it's internal
                    if full_url not in crawled_urls:
                        links.add(full_url)
            return links
    except requests.RequestException as e:
        print(f"Could not fetch links from {base_url}: {e}")
    return set()


def crawl_and_scrape_emails(start_url, max_depth=2):
    """Crawls allowed URLs and extracts emails recursively"""
    emails_collected = set()
    urls_to_crawl = set(get_allowed_urls(start_url))
    crawled_urls = set()

    for _ in range(max_depth):  # Limit recursion depth to avoid infinite loops
        new_urls = set()
        for url in urls_to_crawl:
            if url not in crawled_urls:
                print(f"Scraping: {url}")
                emails_collected.update(get_emails_from_url(url))
                crawled_urls.add(url)
                new_urls.update(get_all_links(url, crawled_urls))
        urls_to_crawl = new_urls

    return emails_collected

# Example Usage
start_url = "https://www.bajajallianz.com/"  # Replace with your target website
emails = crawl_and_scrape_emails(start_url)
print("\nCollected Emails:", emails)

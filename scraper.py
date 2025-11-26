"""
Scraper Module - Async web scraping for event discovery
Uses httpx for async HTTP requests and BeautifulSoup for HTML parsing
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime
import re


# ============================================================================
# WEBSITE CONFIGURATION - ADD YOUR SOURCES HERE
# ============================================================================
# Each source is a dict with:
#   - name: Display name of the source
#   - url: Base URL to scrape
#   - type: "html" (static) or "api" (JSON endpoint)
#   - selectors: CSS selectors for extracting event data (for HTML type)
#   - enabled: Set to True to activate this source
# ============================================================================

SOURCES = [
    {
        "name": "Agenda Cultural Gencat",
        "url": "https://agenda.cultura.gencat.cat",
        "type": "html",
        "search_url": "https://agenda.cultura.gencat.cat/cerca?text={keywords}",
        "selectors": {
            "event_container": ".event-item",  # UPDATE: CSS selector for event container
            "title": ".event-title",            # UPDATE: CSS selector for title
            "date": ".event-date",              # UPDATE: CSS selector for date
            "location": ".event-location",      # UPDATE: CSS selector for location
            "description": ".event-description", # UPDATE: CSS selector for description
            "link": "a"                         # UPDATE: CSS selector for link
        },
        "enabled": False  # SET TO True WHEN SELECTORS ARE CONFIGURED
    },
    {
        "name": "Surt de Casa",
        "url": "https://www.surtdecasa.cat",
        "type": "html",
        "search_url": "https://www.surtdecasa.cat/cerca?q={keywords}",
        "selectors": {
            "event_container": ".activity-card",
            "title": ".activity-title",
            "date": ".activity-date",
            "location": ".activity-location",
            "description": ".activity-excerpt",
            "link": "a"
        },
        "enabled": False  # SET TO True WHEN SELECTORS ARE CONFIGURED
    },
    {
        "name": "Barcelona Cultura",
        "url": "https://www.barcelona.cat/barcelonacultura",
        "type": "html",
        "search_url": "https://www.barcelona.cat/barcelonacultura/ca/agenda?text={keywords}",
        "selectors": {
            "event_container": ".agenda-item",
            "title": "h3",
            "date": ".date",
            "location": ".location",
            "description": ".description",
            "link": "a"
        },
        "enabled": False  # SET TO True WHEN SELECTORS ARE CONFIGURED
    },
    {
        "name": "Festa Catalunya",
        "url": "https://www.festacatalunya.cat",
        "type": "html",
        "search_url": "https://www.festacatalunya.cat/?s={keywords}",
        "selectors": {
            "event_container": "article",
            "title": ".entry-title",
            "date": ".event-date",
            "location": ".event-location",
            "description": ".entry-summary",
            "link": "a"
        },
        "enabled": False  # SET TO True WHEN SELECTORS ARE CONFIGURED
    },
    # =========================================================================
    # ADD MORE SOURCES BELOW - COPY THE TEMPLATE AND CUSTOMIZE
    # =========================================================================
    # {
    #     "name": "Your Source Name",
    #     "url": "https://example.com",
    #     "type": "html",
    #     "search_url": "https://example.com/search?q={keywords}",
    #     "selectors": {
    #         "event_container": ".event",
    #         "title": ".title",
    #         "date": ".date",
    #         "location": ".location",
    #         "description": ".description",
    #         "link": "a"
    #     },
    #     "enabled": True
    # },
]


# HTTP client configuration
HTTP_TIMEOUT = 15.0  # seconds
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


async def fetch_url(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """Fetch a URL and return its HTML content."""
    try:
        response = await client.get(
            url,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=HTTP_TIMEOUT
        )
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_events_from_html(
    html: str,
    source: dict,
    base_url: str
) -> list[dict]:
    """
    Parse events from HTML using configured CSS selectors.
    
    Args:
        html: Raw HTML content
        source: Source configuration with selectors
        base_url: Base URL for resolving relative links
        
    Returns:
        List of event dictionaries
    """
    events = []
    soup = BeautifulSoup(html, "html.parser")
    selectors = source["selectors"]
    
    # Find all event containers
    containers = soup.select(selectors["event_container"])
    
    for container in containers:
        try:
            # Extract title
            title_elem = container.select_one(selectors["title"])
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:  # Skip if no title found
                continue
            
            # Extract date
            date_elem = container.select_one(selectors["date"])
            date = date_elem.get_text(strip=True) if date_elem else None
            
            # Extract location
            location_elem = container.select_one(selectors["location"])
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Extract description
            desc_elem = container.select_one(selectors["description"])
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract link
            link_elem = container.select_one(selectors["link"])
            link = None
            if link_elem and link_elem.has_attr("href"):
                href = link_elem["href"]
                if href.startswith("http"):
                    link = href
                elif href.startswith("/"):
                    link = f"{base_url.rstrip('/')}{href}"
                else:
                    link = f"{base_url.rstrip('/')}/{href}"
            
            events.append({
                "title": title,
                "date": date,
                "location": location,
                "description": description[:300] if description else None,  # Truncate
                "source_url": link,
                "source_name": source["name"]
            })
            
        except Exception as e:
            print(f"Error parsing event from {source['name']}: {e}")
            continue
    
    return events


def filter_events_by_keywords(
    events: list[dict],
    keywords: list[str]
) -> list[dict]:
    """Filter events that contain any of the keywords."""
    if not keywords:
        return events
    
    filtered = []
    keywords_lower = [k.lower() for k in keywords]
    
    for event in events:
        # Combine all text fields for searching
        text = " ".join([
            event.get("title", "") or "",
            event.get("description", "") or "",
            event.get("location", "") or ""
        ]).lower()
        
        # Check if any keyword matches
        if any(kw in text for kw in keywords_lower):
            filtered.append(event)
    
    return filtered


def filter_events_by_location(
    events: list[dict],
    location: Optional[str]
) -> list[dict]:
    """Filter events by location if specified."""
    if not location:
        return events
    
    location_lower = location.lower()
    filtered = []
    
    for event in events:
        event_location = (event.get("location", "") or "").lower()
        event_title = (event.get("title", "") or "").lower()
        event_desc = (event.get("description", "") or "").lower()
        
        if (location_lower in event_location or 
            location_lower in event_title or 
            location_lower in event_desc):
            filtered.append(event)
    
    return filtered


async def scrape_source(
    client: httpx.AsyncClient,
    source: dict,
    intent: dict
) -> list[dict]:
    """
    Scrape a single source for events matching the intent.
    
    Args:
        client: Async HTTP client
        source: Source configuration
        intent: Extracted query intent
        
    Returns:
        List of matching events
    """
    if not source.get("enabled", False):
        return []
    
    # Build search URL with keywords
    keywords = intent.get("keywords", [])
    keywords_str = " ".join(keywords) if keywords else ""
    
    if source.get("search_url") and keywords_str:
        url = source["search_url"].format(keywords=keywords_str)
    else:
        url = source["url"]
    
    # Fetch HTML
    html = await fetch_url(client, url)
    if not html:
        return []
    
    # Parse events
    events = parse_events_from_html(html, source, source["url"])
    
    # Filter by keywords (in case search URL doesn't filter well)
    events = filter_events_by_keywords(events, keywords)
    
    # Filter by location if specified
    events = filter_events_by_location(events, intent.get("location"))
    
    return events


async def scrape_all_sources(intent: dict) -> dict:
    """
    Scrape all enabled sources for events matching the intent.
    
    Args:
        intent: Extracted query intent with keywords, location, date_range
        
    Returns:
        dict with:
        - content: List of event dictionaries
        - sources_scraped: Number of sources attempted
        - events_found: Total events found
    """
    enabled_sources = [s for s in SOURCES if s.get("enabled", False)]
    
    if not enabled_sources:
        # Return demo data when no sources are configured
        return {
            "content": _get_demo_events(intent),
            "sources_scraped": 0,
            "events_found": 3
        }
    
    all_events = []
    
    async with httpx.AsyncClient() as client:
        # Scrape all sources concurrently
        tasks = [
            scrape_source(client, source, intent)
            for source in enabled_sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                print(f"Scraping error: {result}")
    
    # Remove duplicates based on title similarity
    unique_events = _deduplicate_events(all_events)
    
    return {
        "content": unique_events,
        "sources_scraped": len(enabled_sources),
        "events_found": len(unique_events)
    }


def _deduplicate_events(events: list[dict]) -> list[dict]:
    """Remove duplicate events based on title similarity."""
    seen_titles = set()
    unique = []
    
    for event in events:
        title = event.get("title", "").lower().strip()
        # Simple deduplication - could be improved with fuzzy matching
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique.append(event)
    
    return unique


def _get_demo_events(intent: dict) -> list[dict]:
    """
    Return demo events when no sources are configured.
    This helps test the UI and LLM response generation.
    """
    location = intent.get("location", "Catalunya")
    keywords = intent.get("keywords", [])
    
    demo_events = [
        {
            "title": f"Festa Major de {location}",
            "date": "15-18 d'agost de 2025",
            "location": location,
            "description": "Quatre dies de festa amb concerts, correfocs, gegants i activitats per a tota la família. No et perdis el castell de focs artificials!",
            "source_url": "https://example.com/festa-major",
            "source_name": "Demo"
        },
        {
            "title": "Mercat d'Artesania Local",
            "date": "Cada dissabte",
            "location": f"Plaça Major, {location}",
            "description": "Descobreix productes artesanals de la zona: ceràmica, teixits, productes d'alimentació i molt més.",
            "source_url": "https://example.com/mercat",
            "source_name": "Demo"
        },
        {
            "title": "Ruta de Tapes Gastronòmiques",
            "date": "Del 20 al 27 d'agost",
            "location": f"Diversos restaurants de {location}",
            "description": "Gaudeix de les millors tapes dels restaurants locals amb una experiència culinària única.",
            "source_url": "https://example.com/tapes",
            "source_name": "Demo"
        }
    ]
    
    # Add keyword-relevant demo if specific keywords detected
    if any(kw in ["música", "concert", "jazz"] for kw in keywords):
        demo_events.insert(0, {
            "title": "Festival de Jazz al Carrer",
            "date": "22 d'agost de 2025, 21:00h",
            "location": f"Parc Central, {location}",
            "description": "Concert gratuït amb les millors bandes de jazz de Catalunya. Porta la teva manta i gaudeix sota les estrelles.",
            "source_url": "https://example.com/jazz",
            "source_name": "Demo"
        })
    
    if any(kw in ["nens", "familiar", "infantil", "família"] for kw in keywords):
        demo_events.insert(0, {
            "title": "Taller de Circ per a Nens",
            "date": "Diumenge 24 d'agost, 11:00h",
            "location": f"Centre Cívic de {location}",
            "description": "Activitat gratuïta per a nens de 4 a 12 anys. Aprenen malabars, equilibri i molt més!",
            "source_url": "https://example.com/circ",
            "source_name": "Demo"
        })
    
    return demo_events

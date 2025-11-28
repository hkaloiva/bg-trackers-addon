import httpx
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from settings import settings

logger = logging.getLogger(__name__)

class JackettService:
    def __init__(self):
        self.base_url = settings.jackett_url
        self.api_key = settings.jackett_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def _resolve_link(self, link: str) -> Optional[str]:
        """
        Resolve a Jackett download link to a magnet URI or InfoHash.
        Downloads the .torrent file and extracts the info hash.
        """
        if not link:
            return None
            
        try:
            # If it's an internal docker link (http://jackett:9117), we can access it directly
            # If it's localhost, we might need to adjust, but inside docker container 'jackett' hostname works
            
            # Follow redirects manually to catch magnet links
            # httpx raises UnsupportedProtocol if redirect is to magnet:
            try:
                response = await self.client.get(link, follow_redirects=True)
                response.raise_for_status()
            except httpx.UnsupportedProtocol as e:
                # Check if the error message contains the magnet link or if we can get it from history
                # httpx might raise this when trying to follow the redirect
                # The exception object might not contain the URL directly in a clean way
                # So let's try manual redirect following
                pass
            
            # Manual redirect handling
            resp = await self.client.get(link, follow_redirects=False)
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location", "")
                if location.startswith("magnet:"):
                    return location
                # If it redirects to another http link, follow it (one level deep for now)
                elif location.startswith("http"):
                    resp = await self.client.get(location, follow_redirects=False)
                    if resp.status_code in (301, 302, 303, 307, 308):
                        loc2 = resp.headers.get("Location", "")
                        if loc2.startswith("magnet:"):
                            return loc2
            
            # If we got here, it might be a direct .torrent file (status 200)
            if resp.status_code == 200:
                # Parse .torrent file
                import hashlib
                import bencode
                
                torrent_data = bencode.bdecode(resp.content)
                info = torrent_data.get(b'info')
                if info:
                    info_hash = hashlib.sha1(bencode.bencode(info)).hexdigest()
                    return info_hash
                    
        except Exception as e:
            logger.warning(f"Failed to resolve link {link}: {e}")
            return None
                
        except Exception as e:
            logger.warning(f"Failed to resolve link {link}: {e}")
            return None

    async def search(self, type: str, id: str) -> List[Dict[str, Any]]:
        """
        Search Jackett for content.
        """
        if not self.base_url or not self.api_key:
            logger.warning("Jackett not configured")
            return []

        # ... (existing category logic) ...
        categories = []
        if type == "movie":
            categories = [2000, 2010, 2020, 2030, 2040, 2045, 2050, 2060]
        elif type == "series":
            categories = [5000, 5010, 5020, 5030, 5040, 5045, 5050, 5060, 5070, 5080]
            
        params = {
            "apikey": self.api_key,
            "Category": ",".join(map(str, categories)),
            "Query": id
        }

        url = f"{self.base_url.rstrip('/')}/api/v2.0/indexers/all/results"
        
        try:
            logger.info(f"Searching Jackett: {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("Results", [])
            logger.info(f"Jackett returned {len(results)} results")
            
            parsed_results = self._parse_results(results)
            
            # Resolve links for items missing info_hash/magnet (e.g. ArenaBG)
            # We do this in parallel to be fast
            import asyncio
            
            async def resolve_item(item):
                if not item.get("info_hash") and not item.get("magnet") and item.get("link"):
                    resolved = await self._resolve_link(item["link"])
                    if resolved:
                        if len(resolved) == 40: # InfoHash
                            item["info_hash"] = resolved
                            item["magnet"] = f"magnet:?xt=urn:btih:{resolved}"
                        elif resolved.startswith("magnet:"):
                            item["magnet"] = resolved
                            # Extract hash
                            import re
                            match = re.search(r'xt=urn:btih:([a-zA-Z0-9]+)', resolved)
                            if match:
                                item["info_hash"] = match.group(1)
            
            # Filter items that need resolution
            to_resolve = [item for item in parsed_results if not item.get("info_hash") and item.get("link")]
            if to_resolve:
                logger.info(f"Resolving {len(to_resolve)} torrent links...")
                await asyncio.gather(*[resolve_item(item) for item in to_resolve])
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error searching Jackett: {e}")
            return []

    def _parse_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and normalize Jackett results"""
        parsed = []
        for res in results:
            try:
                # Basic validation
                if not res.get("Link") and not res.get("MagnetUri"):
                    continue
                    
                item = {
                    "title": res.get("Title", "Unknown"),
                    "size": res.get("Size", 0),
                    "seeders": res.get("Seeders", 0),
                    "leechers": res.get("Peers", 0) - res.get("Seeders", 0),
                    "tracker": res.get("Tracker", "Unknown"),
                    "info_hash": res.get("InfoHash"),
                    "magnet": res.get("MagnetUri"),
                    "link": res.get("Link"),
                    "publish_date": res.get("PublishDate"),
                    "category": res.get("CategoryDesc", "")
                }
                
                # If no magnet but link exists, we might need to resolve it later
                # For now, we pass what we have
                
                parsed.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse result: {e}")
                continue
                
        # Sort by quality score then seeders
        def get_quality_score(item):
            title = item["title"].lower()
            score = 0
            if "2160p" in title or "4k" in title: score += 400
            elif "1080p" in title: score += 300
            elif "720p" in title: score += 200
            elif "480p" in title: score += 100
            
            if "bluray" in title or "remux" in title: score += 50
            if "web-dl" in title or "webdl" in title: score += 30
            
            return score + item["seeders"] # Add seeders as tie-breaker/minor factor

        parsed.sort(key=get_quality_score, reverse=True)
        return parsed

# Singleton instance
jackett_service = JackettService()

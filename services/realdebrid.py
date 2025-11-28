import httpx
import logging
from typing import Optional, Dict, Any, List
from settings import settings

logger = logging.getLogger(__name__)

class RealDebridService:
    def __init__(self):
        self.base_url = "https://api.real-debrid.com/rest/1.0"
        self.api_key = settings.realdebrid_api_key
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def check_availability(self, hashes: List[str]) -> Dict[str, bool]:
        """
        Check instant availability of torrent hashes.
        Returns a dict mapping hash -> is_cached (bool)
        """
        if not self.api_key or not hashes:
            return {}

        # RD API allows checking multiple hashes at once via /{hash}/{hash}/...
        # Limit is usually around 100? Let's do chunks if needed, but for now simple.
        
        joined_hashes = "/".join(hashes)
        url = f"{self.base_url}/torrents/instantAvailability/{joined_hashes}"
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            # Format: { "hash": { "rd": [ { ...files... } ] } }
            # If "rd" key exists and is not empty, it's cached.
            
            availability = {}
            for h in hashes:
                # RD returns lowercase hashes
                h_lower = h.lower()
                if h_lower in data and "rd" in data[h_lower] and data[h_lower]["rd"]:
                    availability[h] = True
                else:
                    availability[h] = False
            
            return availability

        except Exception as e:
            logger.error(f"RD Availability check failed: {e}")
            return {}

    async def resolve_magnet(self, magnet: str) -> Optional[str]:
        """
        Add magnet and get direct link.
        This is a multi-step process:
        1. Add magnet
        2. Select files
        3. Unrestrict link
        
        This might be too slow for synchronous stream response.
        """
        # Implementation for on-demand resolution
        pass

# Singleton
rd_service = RealDebridService()

import httpx
import logging
from typing import Optional, Dict, Any, List
from settings import settings

logger = logging.getLogger(__name__)

class TorBoxService:
    def __init__(self):
        self.base_url = "https://api.torbox.app/v1/api"
        self.api_key = settings.torbox_api_key
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def check_availability(self, hashes: List[str]) -> Dict[str, bool]:
        """
        Check instant availability of torrent hashes on TorBox.
        Returns a dict mapping hash -> is_cached (bool)
        """
        if not self.api_key or not hashes:
            return {}

        # TorBox allows checking multiple hashes: ?hash=h1,h2,h3&format=object
        # Limit is not strictly documented but let's be safe with chunks if needed.
        
        joined_hashes = ",".join(hashes)
        url = f"{self.base_url}/torrents/checkcached"
        
        try:
            # format=object returns { "hash": true/false } which is easier to parse
            params = {
                "hash": joined_hashes,
                "format": "object",
                "list_files": "false"
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Response format with format=object:
            # { "success": true, "data": { "hash1": { ... }, "hash2": null } }
            # Wait, documentation says checkcached returns data.
            # Let's handle the standard response structure.
            
            if not data.get("success"):
                logger.warning(f"TorBox check failed: {data.get('detail')}")
                return {}
                
            availability = {}
            result_data = data.get("data", {})
            
            for h in hashes:
                # TorBox might return lowercase or original case
                # We check both to be safe
                val = result_data.get(h) or result_data.get(h.lower())
                
                # If value is not None/Null, it is cached
                if val:
                    availability[h] = True
                else:
                    availability[h] = False
            
            return availability

        except Exception as e:
            logger.error(f"TorBox Availability check failed: {e}")
            return {}

# Singleton
torbox_service = TorBoxService()

import httpx
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class MetadataService:
    def __init__(self):
        self.base_url = "https://v3-cinemeta.strem.io"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_details(self, type: str, id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get title and year for an IMDb ID.
        Returns: (Title, Year)
        """
        try:
            url = f"{self.base_url}/meta/{type}/{id}.json"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            meta = data.get("meta", {})
            title = meta.get("name")
            year = meta.get("year")
            
            # Handle year which might be "1999-2003" or similar
            if year and "-" in str(year):
                year = str(year).split("-")[0]
                
            return title, str(year) if year else None
            
        except Exception as e:
            logger.error(f"Metadata fetch failed for {id}: {e}")
            return None, None

# Singleton
metadata_service = MetadataService()

"""
Stremio Manifest for BG Trackers Unified Search
"""
from settings import settings


def get_manifest():
    """Generate Stremio manifest"""
    return {
        "id": "community.bg-trackers",
        "version": settings.addon_version,
        "name": settings.addon_name,
        "description": "Unified search across Bulgarian torrent trackers (Arena.bg, Zamunda.net) with RealDebrid/AllDebrid support",
        "logo": "https://via.placeholder.com/512x512.png?text=BG",
        "resources": [
            "catalog",
            "stream"
        ],
        "types": ["movie", "series"],
        "idPrefixes": ["tt", "tmdb"],
        "catalogs": [
            {
                "type": "movie",
                "id": "bg-trackers-movies",
                "name": "🇧🇬 BG Movies",
                "extra": [
                    {"name": "search", "isRequired": False},
                    {"name": "genre", "isRequired": False}
                ]
            },
            {
                "type": "series",
                "id": "bg-trackers-series",
                "name": "🇧🇬 BG Series",
                "extra": [
                    {"name": "search", "isRequired": False},
                    {"name": "genre", "isRequired": False}
                ]
            }
        ],
        "behaviorHints": {
            "adult": False,
            "p2p": True,
            "configurable": True,
            "configurationRequired": False
        }
    }

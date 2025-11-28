"""
BG Trackers Unified Search - Stremio Addon
Main application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from settings import settings
from manifest import get_manifest

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.addon_name,
    version=settings.addon_version,
    description="Unified search across Bulgarian torrent trackers"
)

# CORS middleware  
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Landing page"""
    html = f"""
    <html>
        <head>
            <title>{settings.addon_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #1a1a2e;
                    color: #eee;
                }}
                h1 {{ color: #0f3460; }}
                .install-btn {{
                    background: #16213e;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                }}
                .install-btn:hover {{
                    background: #0f3460;
                }}
                .feature {{
                    background: #16213e;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <h1>🇧🇬 {settings.addon_name}</h1>
            <p>Version: {settings.addon_version}</p>
            
            <h2>Features</h2>
            <div class="feature">✅ Multi-tracker search (Zamunda.net, Arena.bg)</div>
            <div class="feature">✅ RealDebrid/AllDebrid integration</div>
            <div class="feature">✅ Quality sorting</div>
            <div class="feature">✅ Seeders/leechers stats</div>
            
            <h2>Installation</h2>
            <a href="stremio://community.bg-trackers/manifest.json" class="install-btn">
                📦 Install in Stremio
            </a>
            
            <h2>Configuration</h2>
            <p>After installation, configure your tracker credentials and debrid services in the addon settings.</p>
            
            <h2>Status</h2>
            <p>🟢 Addon is running</p>
            <p>Jackett: {"🟢 Connected" if settings.jackett_url else "🔴 Not configured"}</p>
            <p>RealDebrid: {"🟢 Configured" if settings.realdebrid_api_key else "🔴 Not configured"}</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/manifest.json")
async def manifest():
    """Return Stremio manifest"""
    return JSONResponse(content=get_manifest())


@app.get("/catalog/{type}/{id}.json")
async def catalog(type: str, id: str):
    """Return catalog metas (placeholder)"""
    logger.info(f"Catalog request: type={type}, id={id}")
    return JSONResponse(content={"metas": []})


from services.jackett import jackett_service
from services.realdebrid import rd_service
from services.torbox import torbox_service
from services.metadata import metadata_service
import asyncio

@app.on_event("shutdown")
async def shutdown_event():
    await jackett_service.close()
    await rd_service.close()
    await torbox_service.close()
    await metadata_service.close()

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string"""
    if not size_bytes:
        return "0B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f}PB"

@app.get("/stream/{type}/{id}.json")
async def stream(type: str, id: str):
    """Return streams for given content"""
    logger.info(f"Stream request: type={type}, id={id}")
    
    search_query = id
    
    # Resolve IMDb ID to Title if possible
    if id.startswith("tt"):
        title, year = await metadata_service.get_details(type, id)
        if title:
            # Construct text query: "Title Year"
            # This is much better for trackers like ArenaBG/Zelka
            search_query = f"{title} {year}" if year else title
            logger.info(f"Resolved {id} to query: '{search_query}'")
    
    # Search Jackett
    results = await jackett_service.search(type, search_query)
    
    # Extract hashes for Debrid checks
    hashes = []
    for res in results:
        if res.get("info_hash"):
            hashes.append(res["info_hash"])
        elif res.get("magnet"):
            import re
            match = re.search(r'xt=urn:btih:([a-zA-Z0-9]+)', res["magnet"])
            if match:
                res["info_hash"] = match.group(1) # Store for later
                hashes.append(match.group(1))

    # Check Debrid availability in parallel
    rd_cache = {}
    torbox_cache = {}
    
    tasks = []
    if settings.realdebrid_api_key and hashes:
        tasks.append(rd_service.check_availability(hashes))
    else:
        tasks.append(asyncio.sleep(0)) # Dummy task
        
    if settings.torbox_api_key and hashes:
        tasks.append(torbox_service.check_availability(hashes))
    else:
        tasks.append(asyncio.sleep(0)) # Dummy task
        
    # Execute checks
    check_results = await asyncio.gather(*tasks)
    
    if settings.realdebrid_api_key and hashes:
        rd_cache = check_results[0] if isinstance(check_results[0], dict) else {}
        
    if settings.torbox_api_key and hashes:
        torbox_cache = check_results[1] if isinstance(check_results[1], dict) else {}

    streams = []
    for res in results:
        info_hash = res.get("info_hash")
        
        # Determine prefix based on cache status
        prefixes = []
        if info_hash:
            if rd_cache.get(info_hash):
                prefixes.append("[RD+]")
            elif settings.realdebrid_api_key:
                prefixes.append("[RD]")
                
            if torbox_cache.get(info_hash):
                prefixes.append("[TB+]")
            elif settings.torbox_api_key:
                prefixes.append("[TB]")
        
        if not prefixes:
            prefixes.append("[P2P]")
            
        prefix_str = " ".join(prefixes)
        
        stream_entry = {
            "name": f"{prefix_str} {res['tracker']}",
            "description": f"💾 {format_size(res['size'])} 👤 {res['seeders']} ⬇️ {res['leechers']}\n{res['title']}",
        }
        
        if info_hash:
            stream_entry["infoHash"] = info_hash
        elif res.get("magnet"):
            stream_entry["url"] = res["magnet"]
        elif res.get("link"):
            stream_entry["url"] = res["link"]
        else:
            continue
            
        streams.append(stream_entry)
    
    if not streams:
        streams.append({
            "name": "BG Trackers",
            "description": "No results found",
            "url": "http://localhost/no-results" # Dummy URL
        })

    return JSONResponse(content={"streams": streams})


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.addon_version}


if __name__ == "__main__":
    logger.info(f"Starting {settings.addon_name} v{settings.addon_version}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )

# Bulgarian Torrent Trackers Unified Search 🇧🇬

A Stremio addon that provides unified search across Bulgarian torrent trackers with automatic RealDebrid/AllDebrid integration.

## Features

- **Multi-Tracker Search**: Search across Arena.bg, Zamunda.net, and other Bulgarian trackers
- **Debrid Integration**: Automatic RealDebrid/AllDebrid support for instant streaming
- **Quality Sorting**: Unified sorting by quality, size, and seeders
- **Categories**: BG Movies, BG Series, BG Music, and more
- **Secure Authentication**: Encrypted storage of tracker credentials

## Supported Trackers

- ✅ Zamunda.net (via Jackett/Prowlarr)
- 🚧 Arena.bg (custom implementation)
- 🚧 Others (coming soon)

## Installation

### Using Docker

```bash
docker run -p 8080:8080 -e RD_API_KEY=your_key greenbluegreen/bg-trackers-addon
```

### From Source

```bash
git clone https://github.com/hkalo iva/bg-trackers-addon
cd bg-trackers-addon
pip install -r requirements.txt
python main.py
```

## Configuration

1. Install the addon in Stremio
2. Configure your tracker credentials
3. (Optional) Add RealDebrid/AllDebrid API key
4. Start searching!

## Technical Details

- **Framework**: FastAPI
- **Tracker Integration**: Jackett/Prowlarr + Custom Scrapers
- **Debrid**: RealDebrid, AllDebrid
- **Caching**: Redis
- **Deployment**: Docker, Koyeb

## Roadmap

- [x] Project setup
- [ ] Jackett/Prowlarr integration
- [ ] Zamunda.net support
- [ ] Arena.bg custom scraper
- [ ] RealDebrid integration
- [ ] AllDebrid integration
- [ ] Stremio catalog
- [ ] Deployment

## Contributing

Bulgarian community contributions welcome!

## License

MIT

## Credits

Created by [@hkaloiva](https://github.com/hkaloiva) for the Bulgarian Stremio community.

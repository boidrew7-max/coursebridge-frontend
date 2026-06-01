# CourseBridge AI

A tool for visualizing articulation agreements between California Community Colleges and UC/CSU systems.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Data Processing

This project includes a scraper for extracting articulation agreements from ASSIST.org.

### Running the CCSF to UC Berkeley Scraper

To run the scraper for City College of San Francisco to UC Berkeley agreements:

```bash
# Run with debug output (saves HTML/screenshots)
DEBUG=true npm run scrape:ccsf-ucberkeley

# Run without debug output
npm run scrape:ccsf-ucberkeley
```

The scraper will:
1. Navigate to assist.org
2. Select City College of San Francisco as the source institution
3. Select UC Berkeley as the target institution
4. Load all agreements for the latest academic year
5. Extract course articulations
6. Save the data to `data/processed/assist_articulations.csv`

## Project Structure

- `/app` - Next.js application pages and components
- `/data` - Storage for scraped and processed data
  - `/data/raw` - Raw scraped data (HTML, screenshots)
  - `/data/processed` - Cleaned CSV data
- `/scripts` - Data processing scripts
- `/public` - Static assets
- `/middleware` - Custom middleware

## Recent updates

- Added deterministic completed-course interpretation for user-entered course text
- Integrated course alias matching and fuzzy recognition for informal inputs like `calc 1`, `microeconomics`, and `econ 1`
- Removed the old browser spellcheck debounce path from the planner UI
- Verified the app builds successfully with `npm run build`

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run scrape:ccsf-ucberkeley` - Run the CCSF to UC Berkeley scraper
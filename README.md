# HVAC Takeoff Pro

A desktop HVAC estimating application built for commercial and residential takeoff work. It supports both imperial and metric units, tracks duct and piping takeoffs, and produces workbook and PDF reports for estimate packages.

Features
- Project-based estimating with database storage
- Imperial and metric unit support
- Duct, pipe, fitting, equipment, labor, and accessory categories
- Material and labor cost summaries
- Excel export for estimate breakdowns
- PDF export for client-ready reports
- Project dashboard with total material, labor, and item counts
- Pricing library for reusable assemblies and unit pricing

Run the app

1. Create and activate a virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Launch app:
   python app.py

Project structure
- `hvac_takeoff/database.py` - SQLite persistence and project data layer
- `hvac_takeoff/calculations.py` - estimate math and formatting helpers
- `hvac_takeoff/app.py` - desktop UI and export logic

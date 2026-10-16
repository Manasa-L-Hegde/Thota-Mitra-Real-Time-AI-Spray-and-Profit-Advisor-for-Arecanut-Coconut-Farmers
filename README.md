# Thota Mitra (ತೋಟ ಮಿತ್ರ) 🌴

> **Status: Pilot validation pipeline built; awaiting multi-season historical diary dataset from partner plantation.**

> **Real-time, Kannada-first decision-support web application for arecanut and coconut farmers in Karnataka.**  
> Helps smallholders decide **when to spray against monsoon fruit rot (koleroga)** and **whether they are making a profit**.  
> *SEVA 2026 Innovation Challenge Entry.*

---

## 🌾 Overview & Design Principles

Arecanut (*Areca catechu*) and coconut (*Cocos nucifera*) plantations in the Western Ghats (Malnad) and Coastal Karnataka face monsoon fruit rot (**Koleroga / Mahali**, caused by *Phytophthora meadii*). Annual crop losses range from **10% to 75%** (*ICAR-CPCRI*).

Because Bordeaux mixture requires a **3 to 4-hour dry rain-free window** to adhere to nut bunches, spraying during continuous torrential downpours washes away expensive fungicide and climbing labour. In wet years (e.g., Sringeri), heavy rains prevented spraying and only 40% of growers could complete timely prophylactic rounds (*Deccan Herald*).

### 🔍 Agronomic Guidance vs. Software Heuristics (Honest Distinction)
To maintain integrity before judges and agronomists:
- **Published ICAR-CPCRI & KAU Guidance**: Provides qualitative disease factors (high humidity, cool temperatures, and alternating sun/heavy rain favor sporulation) and the recommended prophylactic spray schedule (1% Bordeaux mixture on nut bunches before monsoon onset, followed by a second spray at ~40 days during a rain break, and a third if the monsoon extends).
- **Software Heuristic Thresholds (To Be Validated)**: Specific numerical factor weights (35% rain, 30% RH, 20% cloud, 15% temp), numerical humidity cut-offs (82%, 90%), temperature window (20–28°C), and wind speed limits (20 km/h) are **heuristics engineered for software decision support**. They are **NOT** published numeric thresholds from CPCRI. All thresholds are editable in [`config/risk_rules.json`](config/risk_rules.json) and marked `"HEURISTIC_TO_BE_VALIDATED"`.
- **Validation Status**: **Pilot validation with one plantation planned. No clinical accuracy is claimed.**

---

## 📚 Public Data Sources & References

| Parameter | Reference Value / Range | Region & Year | Published Source |
| :--- | :--- | :--- | :--- |
| **Planting Density** | 550 – 600 palms/acre | Karnataka (2.7m × 2.7m) | *Deccan Herald* (CPCRI-based report) |
| **Dry Nut Yield** | 4.5 – 5.0 kg chali/palm | Karnataka bearing gardens | *Deccan Herald* (CPCRI-based report) |
| **Spray Cost** | ~₹18 / palm / round | Malnad & Coastal | *Deccan Herald* (Medicine + climber labour) |
| **Production Cost** | ~₹80,000 / acre (₹140-150/tree) | Traditional Malnad | *Deccan Herald* plantation report |
| **Cultivation Cost** | ~₹2.83 lakh / acre / year | Tumkur & Ramanagara (2021-22) | *Krishikosh* agricultural thesis |
| **Labour Share** | ~75% of total cultivation cost | Kasaragod & Malnad (2023) | *Krishikosh* arecanut economics study |
| **Standard Spray Schedule**| 3 rounds: Pre-monsoon, 40-day follow-up, extended | Kerala & Karnataka | *KAU Package of Practices* & *CPCRI Bulletin* |
| **Drying Time** | 3 to 4 hours rain-free break | Malnad monsoon tracts | *CPCRI Koleroga advisory* |
| **Mandi Price: Kundapura** | ₹44,000 / quintal | Udupi (2026) | *Agmarknet via data.gov.in / ACROP* |
| **Mandi Price: Mangalore** | ₹35,367 / quintal | Dakshina Kannada (1 Aug 2026)| *Agmarknet via data.gov.in / ACROP* |
| **Mandi Price: Holenarsipura**| ₹20,000 / quintal | Hassan (24 Jun 2026) | *Agmarknet via data.gov.in / ACROP* |
| **Mandi Price: K.R. Pet** | ₹17,000 / quintal (Coconut) | Mandya (19 Jun 2026) | *Agmarknet via data.gov.in / ACROP* |

---

## 🚀 Getting Started & Running Locally

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Pip & modern web browser (Chrome, Edge, Firefox, or Safari on Android/iOS)

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/manasa-hegde/thota-mitra.git
cd "Thota Mitra"

# Copy environment settings
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize SQLite Database
```bash
python -m app.db.init_db
```

### 4. Run Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser or Android mobile device.

### 5. Run Automated Tests
```bash
python -m pytest tests -v
```

---

## 📱 What is Built vs Planned

### ✅ What is Built & Working Live (Phases 1 – 6)
- **Real-Time Weather Integration**: Queries Open-Meteo with 3 past days and 7 forecast days, with 30-minute in-memory caching and offline fallback.
- **Transparent Conducive-Conditions Scoring**: 0–100 index with factor breakdown (consecutive rainy days, relative humidity, cloud cover, temperature) and exact rule attribution.
- **Spray-Window Planner**: 7-day timeline evaluating rainfall (mm), wind speed (km/h), rain probability, and consecutive daytime dry streak hours.
- **Interactive UI**:
  - Drag-and-drop Leaflet map pin to select any plantation coordinates.
  - Preset village search for Karnataka plantation belts (Thirthahalli, Sringeri, Sagar, Sirsi, Puttur, Kundapura, Madikeri).
  - Bilingual Kannada / English toggle with strings marked for native-speaker review.
  - Animated SVG circular gauge.
  - Interactive Chart.js 7-day trend chart.
- **Audio Advisory**: "Listen" button with Web Speech API in Kannada (`kn-IN`) and device voice detection fallback.
- **Ask Mitra RAG Assistant**: Strictly grounded in official CPCRI, KAU, and UAS documents with source citation and transparent refusal when unverified.
- **Cost & Profitability Planner**: Form prefilled from published literature ranges, Agmarknet mandi selector, break-even price calculation, and doughnut chart cost breakdown.
- **Farm Diary & SQLite Persistence**: Log outbreaks, sprays, harvests, monkey damages; export diary to CSV.
- **Pilot Historical Validation**: `validation/risk_validation.ipynb` comparing Open-Meteo historical archive data with diary records.
- **Deployment**: Dockerfile and Azure App Service configuration.

### 📋 What is Planned (Future Enhancements)
- Multi-season ground-truth disease validation dataset across 20+ Malnad grower plots.
- Direct automated daily sync with Agmarknet REST API via data.gov.in API key.
- SMS / WhatsApp daily spray window alerts for non-smartphone farmers.
- Computer-vision leaf and nut lesion detector from smartphone camera photos.

---

## ⚠️ Important Agronomic Disclaimer

*Thota Mitra provides decision-support calculations based strictly on public meteorological models (Open-Meteo) and published ICAR-CPCRI / KAU packages of practices. It does NOT provide guarantees of disease freedom. Microclimatic canopy variations, drainage, tree age, and chemical dilution accuracy can alter real-world efficacy. Always verify with local visual inspections and your taluk Horticulture Officer.*

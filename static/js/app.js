// ===================================================================
// THOTA MITRA (ತೋಟ ಮಿತ್ರ) - Client Application Controller
// Full-featured: Leaflet Map, Web Speech, Chart.js, Offline PWA, RAG
// ===================================================================

const AppState = {
  crop: 'arecanut',
  lat: 13.6934,
  lon: 75.2427,
  village: 'Thirthahalli, Shivamogga',
  weatherData: null,
  riskData: null,
  sprayPlan: null,
  map: null,
  marker: null,
  trendChart: null,
  costChart: null,
  isSpeaking: false,
  speechSynth: window.speechSynthesis || null,
  currentUtterance: null,
  defaults: null,
  locationMeta: {
    name: 'Thirthahalli',
    name_kn: 'ತೀರ್ಥಹಳ್ಳಿ',
    taluk: 'Thirthahalli',
    taluk_kn: 'ತೀರ್ಥಹಳ್ಳಿ',
    district: 'Shivamogga',
    district_kn: 'ಶಿವಮೊಗ್ಗ',
    lat: 13.6934,
    lon: 75.2427
  },
};

// Rich offline dictionary of Karnataka arecanut & coconut villages and taluks
let VILLAGE_PRESETS = [
  { name: 'Yalavalli', name_kn: 'ಯಾಲವಳ್ಳಿ', taluk: 'Sirsi', taluk_kn: 'ಶಿರಸಿ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.6542, lon: 74.8724 },
  { name: 'Hegde', name_kn: 'ಹೆಗಡೆ', taluk: 'Kumta', taluk_kn: 'ಕುಮಟಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.4312, lon: 74.4085 },
  { name: 'Kumta', name_kn: 'ಕುಮಟಾ', taluk: 'Kumta', taluk_kn: 'ಕುಮಟಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.4259, lon: 74.4170 },
  { name: 'Divgi', name_kn: 'ದಿವಗಿ', taluk: 'Kumta', taluk_kn: 'ಕುಮಟಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.4530, lon: 74.4100 },
  { name: 'Mirjan', name_kn: 'ಮಿರ್ಜಾನ್', taluk: 'Kumta', taluk_kn: 'ಕುಮಟಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.4850, lon: 74.4200 },
  { name: 'Kalabagh', name_kn: 'ಕಲಭಾಗ್', taluk: 'Kumta', taluk_kn: 'ಕುಮಟಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.4150, lon: 74.4350 },
  { name: 'Vannalli', name_kn: 'ವನ್ನಳ್ಳಿ', taluk: 'Kumta', taluk_kn: 'ಕುಮಟಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.4050, lon: 74.3950 },
  { name: 'Gokarna', name_kn: 'ಗೋಕರ್ಣ', taluk: 'Kumta', taluk_kn: 'ಕುಮಟಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.5479, lon: 74.3188 },
  { name: 'Sirsi', name_kn: 'ಶಿರಸಿ', taluk: 'Sirsi', taluk_kn: 'ಶಿರಸಿ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.6195, lon: 74.8354 },
  { name: 'Siddapura', name_kn: 'ಸಿದ್ಧಾಪುರ', taluk: 'Siddapura', taluk_kn: 'ಸಿದ್ಧಾಪುರ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.3394, lon: 74.8967 },
  { name: 'Yellapur', name_kn: 'ಯಲ್ಲಾಪುರ', taluk: 'Yellapur', taluk_kn: 'ಯಲ್ಲಾಪುರ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.9644, lon: 74.7122 },
  { name: 'Sringeri', name_kn: 'ಶೃಂಗೇರಿ', taluk: 'Sringeri', taluk_kn: 'ಶೃಂಗೇರಿ', district: 'Chikkamagaluru', district_kn: 'ಚಿಕ್ಕಮಗಳೂರು', lat: 13.4194, lon: 75.2570 },
  { name: 'Koppa', name_kn: 'ಕೊಪ್ಪ', taluk: 'Koppa', taluk_kn: 'ಕೊಪ್ಪ', district: 'Chikkamagaluru', district_kn: 'ಚಿಕ್ಕಮಗಳೂರು', lat: 13.5284, lon: 75.3588 },
  { name: 'Thirthahalli', name_kn: 'ತೀರ್ಥಹಳ್ಳಿ', taluk: 'Thirthahalli', taluk_kn: 'ತೀರ್ಥಹಳ್ಳಿ', district: 'Shivamogga', district_kn: 'ಶಿವಮೊಗ್ಗ', lat: 13.6934, lon: 75.2427 },
  { name: 'Sagar', name_kn: 'ಸಾಗರ', taluk: 'Sagar', taluk_kn: 'ಸಾಗರ', district: 'Shivamogga', district_kn: 'ಶಿವಮೊಗ್ಗ', lat: 14.1670, lon: 75.0298 },
  { name: 'Hosanagara', name_kn: 'ಹೊಸನಗರ', taluk: 'Hosanagara', taluk_kn: 'ಹೊಸನಗರ', district: 'Shivamogga', district_kn: 'ಶಿವಮೊಗ್ಗ', lat: 13.9189, lon: 75.0689 },
  { name: 'Puttur', name_kn: 'ಪುತ್ತೂರು', taluk: 'Puttur', taluk_kn: 'ಪುತ್ತೂರು', district: 'Dakshina Kannada', district_kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ', lat: 12.7667, lon: 75.2000 },
  { name: 'Sullia', name_kn: 'ಸುಳ್ಯ', taluk: 'Sullia', taluk_kn: 'ಸುಳ್ಯ', district: 'Dakshina Kannada', district_kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ', lat: 12.5593, lon: 75.3892 },
  { name: 'Bantwal', name_kn: 'ಬಂಟ್ವಾಳ', taluk: 'Bantwal', taluk_kn: 'ಬಂಟ್ವಾಳ', district: 'Dakshina Kannada', district_kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ', lat: 12.8931, lon: 75.0347 },
  { name: 'Belthangady', name_kn: 'ಬೆಳ್ತಂಗಡಿ', taluk: 'Belthangady', taluk_kn: 'ಬೆಳ್ತಂಗಡಿ', district: 'Dakshina Kannada', district_kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ', lat: 13.0031, lon: 75.2982 },
  { name: 'Kundapura', name_kn: 'ಕುಂದಾಪುರ', taluk: 'Kundapura', taluk_kn: 'ಕುಂದಾಪುರ', district: 'Udupi', district_kn: 'ಉಡುಪಿ', lat: 13.6268, lon: 74.6917 },
  { name: 'Udupi', name_kn: 'ಉಡುಪಿ', taluk: 'Udupi', taluk_kn: 'ಉಡುಪಿ', district: 'Udupi', district_kn: 'ಉಡುಪಿ', lat: 13.3409, lon: 74.7421 },
  { name: 'Karkala', name_kn: 'ಕಾರ್ಕಳ', taluk: 'Karkala', taluk_kn: 'ಕಾರ್ಕಳ', district: 'Udupi', district_kn: 'ಉಡುಪಿ', lat: 13.2144, lon: 74.9984 },
  { name: 'Channagiri', name_kn: 'ಚನ್ನಗಿರಿ', taluk: 'Channagiri', taluk_kn: 'ಚನ್ನಗಿರಿ', district: 'Davanagere', district_kn: 'ದಾವಣಗೆರೆ', lat: 14.0270, lon: 75.9280 },
  { name: 'Tiptur', name_kn: 'ತಿಪಟೂರು', taluk: 'Tiptur', taluk_kn: 'ತಿಪಟೂರು', district: 'Tumakuru', district_kn: 'ತುಮಕೂರು', lat: 13.2625, lon: 76.4789 },
  { name: 'Tumakuru', name_kn: 'ತುಮಕೂರು', taluk: 'Tumakuru', taluk_kn: 'ತುಮಕೂರು', district: 'Tumakuru', district_kn: 'ತುಮಕೂರು', lat: 13.3409, lon: 77.1010 },
  { name: 'Arsikere', name_kn: 'ಅರಸೀಕೆರೆ', taluk: 'Arsikere', taluk_kn: 'ಅರಸೀಕೆರೆ', district: 'Hassan', district_kn: 'ಹಾಸನ', lat: 13.3128, lon: 76.2570 },
  { name: 'Holenarsipura', name_kn: 'ಹೊಳೆನರಸೀಪುರ', taluk: 'Holenarsipura', taluk_kn: 'ಹೊಳೆನರಸೀಪುರ', district: 'Hassan', district_kn: 'ಹಾಸನ', lat: 12.7886, lon: 76.2428 },
  { name: 'K.R. Pet', name_kn: 'ಕೆ.ಆರ್. ಪೇಟೆ', taluk: 'Krishnarajpet', taluk_kn: 'ಕೃಷ್ಣರಾಜಪೇಟೆ', district: 'Mandya', district_kn: 'ಮಂಡ್ಯ', lat: 12.8631, lon: 76.4913 },
  { name: 'Honnavar', name_kn: 'ಹೊನ್ನಾವರ', taluk: 'Honnavar', taluk_kn: 'ಹೊನ್ನಾವರ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.2796, lon: 74.4444 },
  { name: 'Bhatkal', name_kn: 'ಭಟ್ಕಳ', taluk: 'Bhatkal', taluk_kn: 'ಭಟ್ಕಳ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 13.9788, lon: 74.5516 },
  { name: 'Ankola', name_kn: 'ಅಂಕೋಲಾ', taluk: 'Ankola', taluk_kn: 'ಅಂಕೋಲಾ', district: 'Uttara Kannada', district_kn: 'ಉತ್ತರ ಕನ್ನಡ', lat: 14.6653, lon: 74.2982 },
  { name: 'Shivamogga', name_kn: 'ಶಿವಮೊಗ್ಗ', taluk: 'Shivamogga', taluk_kn: 'ಶಿವಮೊಗ್ಗ', district: 'Shivamogga', district_kn: 'ಶಿವಮೊಗ್ಗ', lat: 13.9299, lon: 75.5681 },
  { name: 'Mudigere', name_kn: 'ಮೂಡಿಗೆರೆ', taluk: 'Mudigere', taluk_kn: 'ಮೂಡಿಗೆರೆ', district: 'Chikkamagaluru', district_kn: 'ಚಿಕ್ಕಮಗಳೂರು', lat: 13.1367, lon: 75.6416 },
  { name: 'Tarikere', name_kn: 'ತರೀಕೆರೆ', taluk: 'Tarikere', taluk_kn: 'ತರೀಕೆರೆ', district: 'Chikkamagaluru', district_kn: 'ಚಿಕ್ಕಮಗಳೂರು', lat: 13.7139, lon: 75.8164 },
  { name: 'N.R. Pura', name_kn: 'ಎನ್.ಆರ್. ಪುರ', taluk: 'Narasimharajapura', taluk_kn: 'ನರಸಿಂಹರಾಜಪುರ', district: 'Chikkamagaluru', district_kn: 'ಚಿಕ್ಕಮಗಳೂರು', lat: 13.6212, lon: 75.5218 },
  { name: 'Mangalore', name_kn: 'ಮಂಗಳೂರು', taluk: 'Mangalore', taluk_kn: 'ಮಂಗಳೂರು', district: 'Dakshina Kannada', district_kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ', lat: 12.9141, lon: 74.8560 },
  { name: 'Moodabidri', name_kn: 'ಮೂಡುಬಿದಿರೆ', taluk: 'Moodabidri', taluk_kn: 'ಮೂಡುಬಿದಿರೆ', district: 'Dakshina Kannada', district_kn: 'ದಕ್ಷಿಣ ಕನ್ನಡ', lat: 13.0694, lon: 74.9961 },
  { name: 'Madikeri', name_kn: 'ಮಡಿಕೇರಿ', taluk: 'Madikeri', taluk_kn: 'ಮಡಿಕೇರಿ', district: 'Kodagu', district_kn: 'ಕೊಡಗು', lat: 12.4244, lon: 75.7382 },
  { name: 'Somwarpet', name_kn: 'ಸೋಮವಾರಪೇಟೆ', taluk: 'Somwarpet', taluk_kn: 'ಸೋಮವಾರಪೇಟೆ', district: 'Kodagu', district_kn: 'ಕೊಡಗು', lat: 12.5975, lon: 75.8569 }
];

const SAMPLE_QUESTIONS = {
  kn: [
    "ಈ ಆ್ಯಪ್ ಮಳೆ ಅಥವಾ ಸಿಂಪರಣೆ ಎಚ್ಚರಿಕೆ (Alert) ನೀಡುತ್ತದೆಯೇ?",
    "ಸಿಂಪರಣೆ ಕಿಟಕಿ (Spray Window) ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ?",
    "ಮಳೆಗಾಲದಲ್ಲಿ ಬೋರ್ಡೋ ಸಿಂಪರಣೆ ಯಾವಾಗ ಮಾಡಬೇಕು?",
    "ಹವಾಮಾನ ಅನುಕೂಲಕರ ಸೂಚ್ಯಂಕ (Conducive Index) ಎಂದರೇನು?",
    "೧% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ತಯಾರಿಸುವುದು ಹೇಗೆ?",
    "ತೆಂಗಿನ ಸುಳಿ ಕೊಳೆ ರೋಗಕ್ಕೆ ಅಧಿಕೃತ ಮದ್ದು ಏನು?"
  ],
  en: [
    "Will this give spray-window alerts?",
    "How does the spray window work?",
    "When should I spray Bordeaux mixture?",
    "What is the Conducive Conditions Index?",
    "How to prepare 1% Bordeaux mixture?",
    "What is the recommended remedy for Bud Rot?"
  ]
};

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize i18n
  await I18n.init();

  // 2. Initialize Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(err => {
      console.warn('SW registration skipped', err);
    });
  }

  // 3. Setup Navigation Tabs
  setupNavigation();

  // 4. Initialize Map
  initLeafletMap();

  // 5. Setup Event Listeners
  setupEventListeners();

  // 6. Render Sample Question Chips
  renderSampleQuestions();

  // 7. Initial Data Load
  loadDashboardData();

  // 8. Load Mandi Prices for Profit Planner
  loadMandiPrices();
  loadReferenceDefaults();

  // 9. Load Diary Entries
  loadDiaryEntries();

  // 10. Re-render on language change
  window.addEventListener('languageChanged', () => {
    if (AppState.locationMeta) {
      AppState.village = formatLocationTitle(AppState.locationMeta);
      const coordsDisplay = document.getElementById('coordsDisplay');
      if (coordsDisplay) {
        coordsDisplay.textContent = `${AppState.village} (${AppState.lat}°N, ${AppState.lon}°E)`;
      }
    }
    renderSampleQuestions();
    renderDashboardUI();
    renderScheduleUI();
    renderCostInsights();
  });
});

// --- NAVIGATION ---
function setupNavigation() {
  const tabs = document.querySelectorAll('.nav-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetId = tab.getAttribute('data-tab');
      document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
      });
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');

      // Refresh map size if switching to dashboard
      if (targetId === 'tabDashboard' && AppState.map) {
        setTimeout(() => AppState.map.invalidateSize(), 150);
      }
    });
  });
}

// --- LEAFLET MAP ---
function initLeafletMap() {
  const mapEl = document.getElementById('plantationMap');
  if (!mapEl) return;

  AppState.map = L.map('plantationMap', {
    center: [AppState.lat, AppState.lon],
    zoom: 11,
    zoomControl: true
  });

  // OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(AppState.map);

  // Custom plantation pin
  const customIcon = L.divIcon({
    className: 'custom-map-pin',
    html: `<div style="background:#1B4332;color:#FFF;border:2px solid #E9C46A;border-radius:50%;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 3px 8px rgba(0,0,0,0.3);">🌴</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });

  AppState.marker = L.marker([AppState.lat, AppState.lon], {
    draggable: true,
    icon: customIcon
  }).addTo(AppState.map);

  // Dragging pin updates location title to Village Name (Taluk, District) and fetches live weather
  AppState.marker.on('dragend', async (e) => {
    const pos = e.target.getLatLng();
    const coordsDisplay = document.getElementById('coordsDisplay');
    if (coordsDisplay) {
      coordsDisplay.textContent = `⏳ Reverse geocoding (${pos.lat.toFixed(4)}°N, ${pos.lng.toFixed(4)}°E)...`;
    }
    const place = await reverseGeocodeKarnataka(pos.lat, pos.lng);
    updateLocationCoordinates(pos.lat, pos.lng, null, place);
  });

  // Clicking anywhere on Karnataka map updates location title and fetches live weather
  AppState.map.on('click', async (e) => {
    const coordsDisplay = document.getElementById('coordsDisplay');
    if (coordsDisplay) {
      coordsDisplay.textContent = `⏳ Reverse geocoding (${e.latlng.lat.toFixed(4)}°N, ${e.latlng.lng.toFixed(4)}°E)...`;
    }
    const place = await reverseGeocodeKarnataka(e.latlng.lat, e.latlng.lng);
    updateLocationCoordinates(e.latlng.lat, e.latlng.lng, null, place);
  });
}

function formatLocationTitle(place) {
  if (!place) return AppState.village || 'Thirthahalli (Thirthahalli, Shivamogga)';
  const isKn = I18n.currentLang === 'kn';
  const name = isKn ? (place.name_kn || place.name) : place.name;
  const taluk = isKn ? (place.taluk_kn || place.taluk) : place.taluk;
  const district = isKn ? (place.district_kn || place.district) : place.district;

  if (taluk && district) {
    return `${name} (${taluk}, ${district})`;
  } else if (district || taluk) {
    return `${name} (${district || taluk})`;
  }
  return name;
}

function updateLocationCoordinates(lat, lon, label = null, place = null) {
  AppState.lat = parseFloat(lat.toFixed(4));
  AppState.lon = parseFloat(lon.toFixed(4));
  if (place) {
    AppState.locationMeta = place;
    AppState.village = formatLocationTitle(place);
  } else if (label) {
    AppState.village = label;
  }

  if (AppState.marker) {
    AppState.marker.setLatLng([AppState.lat, AppState.lon]);
    AppState.map.setView([AppState.lat, AppState.lon], 12);
  }

  const coordsDisplay = document.getElementById('coordsDisplay');
  if (coordsDisplay) {
    coordsDisplay.textContent = `${AppState.village} (${AppState.lat}°N, ${AppState.lon}°E)`;
  }

  loadDashboardData();
}

// --- SAMPLE QUESTION CHIPS ---
function renderSampleQuestions() {
  const container = document.getElementById('sampleQuestionChips');
  if (!container) return;
  const isKn = I18n.currentLang === 'kn';
  const list = isKn ? SAMPLE_QUESTIONS.kn : SAMPLE_QUESTIONS.en;

  container.innerHTML = list.map(q => `
    <button type="button" class="sample-chip-btn" onclick="askSampleQuestion('${q.replace(/'/g, "\\'")}')">
      ${q}
    </button>
  `).join('');
}

window.askSampleQuestion = function(q) {
  const input = document.getElementById('ragQuestionInput');
  if (input) {
    input.value = q;
    submitRagQuery();
  }
};

// --- EVENT LISTENERS ---
function setupEventListeners() {
  // Language toggle
  const langToggleBtn = document.getElementById('langToggleBtn');
  if (langToggleBtn) {
    langToggleBtn.addEventListener('click', () => I18n.toggleLanguage());
  }

  // Crop toggle (Arecanut vs Coconut)
  const cropToggleBtn = document.getElementById('cropToggleBtn');
  if (cropToggleBtn) {
    cropToggleBtn.addEventListener('click', () => {
      AppState.crop = AppState.crop === 'arecanut' ? 'coconut' : 'arecanut';
      const cropText = AppState.crop === 'arecanut' 
        ? (I18n.currentLang === 'kn' ? '🌴 ಅಡಿಕೆ' : '🌴 Arecanut') 
        : (I18n.currentLang === 'kn' ? '🥥 ತೆಂಗು' : '🥥 Coconut');
      cropToggleBtn.innerHTML = cropText;
      loadDashboardData();
    });
  }

  // GPS "Use My Location"
  const gpsBtn = document.getElementById('gpsBtn');
  if (gpsBtn) {
    gpsBtn.addEventListener('click', () => {
      if (navigator.geolocation) {
        gpsBtn.innerHTML = '⏳ Searching GPS...';
        navigator.geolocation.getCurrentPosition(
          async pos => {
            gpsBtn.innerHTML = '📍 ' + I18n.t('location.use_my_location');
            const place = await reverseGeocodeKarnataka(pos.coords.latitude, pos.coords.longitude);
            updateLocationCoordinates(pos.coords.latitude, pos.coords.longitude, null, place);
          },
          err => {
            gpsBtn.innerHTML = '📍 ' + I18n.t('location.use_my_location');
            alert('Could not retrieve GPS location. Please allow location access or select from preset villages.');
          },
          { timeout: 10000, enableHighAccuracy: true }
        );
      } else {
        alert('Geolocation not supported by this browser.');
      }
    });
  }

  // Village search input & suggestions
  const villageInput = document.getElementById('villageSearchInput');
  const suggestionsBox = document.getElementById('villageSuggestions');

  if (villageInput && suggestionsBox) {
    villageInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        suggestionsBox.style.display = 'none';
        return;
      }
      // Instant local dictionary search: matches village, taluk, district in English or Kannada
      const matches = VILLAGE_PRESETS.filter(v => 
        v.name.toLowerCase().includes(q) ||
        (v.name_kn && v.name_kn.includes(q)) ||
        (v.taluk && v.taluk.toLowerCase().includes(q)) ||
        (v.taluk_kn && v.taluk_kn.includes(q)) ||
        (v.district && v.district.toLowerCase().includes(q)) ||
        (v.district_kn && v.district_kn.includes(q))
      );

      renderLocationSuggestions(matches, suggestionsBox);
      // Concurrently query backend proxy for Open-Meteo & Nominatim geocoding
      searchNominatimKarnataka(q, suggestionsBox);
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
      if (!villageInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
        suggestionsBox.style.display = 'none';
      }
    });
  }

  // "Listen" button for Today's Action Card (Web Speech API)
  const listenBtn = document.getElementById('listenActionBtn');
  if (listenBtn) {
    listenBtn.addEventListener('click', toggleAudioSpeech);
  }

  // Profit Calculator Calculate & Save buttons
  const calcBtn = document.getElementById('calcEconomicsBtn');
  if (calcBtn) calcBtn.addEventListener('click', runEconomicsCalculation);

  document.querySelectorAll('#economicsForm input, #economicsForm select').forEach(el => {
    el.addEventListener('input', debounce(runEconomicsCalculation, 250));
    el.addEventListener('change', debounce(runEconomicsCalculation, 250));
  });

  const saveScenarioBtn = document.getElementById('saveScenarioBtn');
  if (saveScenarioBtn) saveScenarioBtn.addEventListener('click', saveCostScenario);

  // Diary Form submission
  const diaryForm = document.getElementById('diaryForm');
  if (diaryForm) {
    diaryForm.addEventListener('submit', (e) => {
      e.preventDefault();
      saveDiaryEntry();
    });
  }

  // Export Diary CSV
  const exportCsvBtn = document.getElementById('exportDiaryCsvBtn');
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      window.location.href = '/api/diary/export.csv';
    });
  }

  // Ask Mitra RAG
  const askBtn = document.getElementById('askMitraBtn');
  if (askBtn) askBtn.addEventListener('click', submitRagQuery);

  const askInput = document.getElementById('ragQuestionInput');
  if (askInput) {
    askInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') submitRagQuery();
    });
  }

  // Voice Input for Ask Mitra
  const voiceInputBtn = document.getElementById('voiceInputBtn');
  if (voiceInputBtn) {
    voiceInputBtn.addEventListener('click', startSpeechRecognition);
  }

  // Modal Close
  const closeModalBtn = document.getElementById('closeModalBtn');
  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
      document.getElementById('hourlyModal').classList.remove('open');
    });
  }
}

function renderLocationSuggestions(matches, box) {
  if (!matches || !matches.length) {
    box.style.display = 'none';
    return;
  }
  box.replaceChildren();
  const isKn = I18n.currentLang === 'kn';

  matches.slice(0, 10).forEach(m => {
    const row = document.createElement('div');
    row.className = 'suggestion-row';
    row.style.cssText = 'padding:10px 14px;border-bottom:1px solid #EEE;cursor:pointer;line-height:1.4;';

    const vName = isKn ? (m.name_kn || m.name) : m.name;
    const vTaluk = isKn ? (m.taluk_kn || m.taluk) : m.taluk;
    const vDistrict = isKn ? (m.district_kn || m.district) : m.district;

    const formattedLabel = [vName, vTaluk, vDistrict].filter(Boolean).join(', ');
    const coordsStr = `(${m.lat.toFixed(4)}°N, ${m.lon.toFixed(4)}°E)`;

    row.innerHTML = `<span style="font-weight:700;color:var(--c-deep-green);">${vName}</span>${vTaluk ? `, ${vTaluk}` : ''}${vDistrict ? `, ${vDistrict}` : ''} <span style="font-size:12px;color:#888;">${coordsStr}</span>`;

    row.addEventListener('click', () => {
      box.style.display = 'none';
      const input = document.getElementById('villageSearchInput');
      if (input) input.value = formattedLabel;
      updateLocationCoordinates(m.lat, m.lon, null, m);
    });
    box.appendChild(row);
  });
  box.style.display = 'block';
}

const searchNominatimKarnataka = debounce(async (query, box) => {
  if (query.length < 2) return;
  try {
    const response = await fetch(`/api/geocode/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Geocoding unavailable');
    const payload = await response.json();
    const local = VILLAGE_PRESETS.filter(v => 
      `${v.name} ${v.name_kn || ''} ${v.taluk || ''} ${v.district}`.toLowerCase().includes(query.toLowerCase())
    );
    renderLocationSuggestions([...local, ...(payload.results || [])], box);
  } catch (_) { /* Local Karnataka presets remain available offline. */ }
}, 300);

async function reverseGeocodeKarnataka(lat, lon) {
  try {
    const response = await fetch(`/api/geocode/reverse?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
    if (!response.ok) throw new Error('Reverse geocoding unavailable');
    return await response.json();
  } catch (_) {
    return { name: 'Custom Location', name_kn: 'ಕಸ್ಟಮ್ ಸ್ಥಳ', taluk: '', district: '', lat, lon };
  }
}

function debounce(fn, delay) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

window.selectVillagePreset = function(name, lat, lon) {
  const suggestionsBox = document.getElementById('villageSuggestions');
  const villageInput = document.getElementById('villageSearchInput');
  if (suggestionsBox) suggestionsBox.style.display = 'none';
  if (villageInput) villageInput.value = name;
  updateLocationCoordinates(lat, lon, name);
};


// --- DATA FETCHING ---
async function loadDashboardData() {
  showSkeletons();
  try {
    const res = await fetch(`/api/dashboard?lat=${AppState.lat}&lon=${AppState.lon}&crop=${AppState.crop}`);
    if (!res.ok) throw new Error('API response failed');
    const data = await res.json();

    AppState.weatherData = data.weather;
    AppState.riskData = data.risk;
    AppState.sprayPlan = data.spray_plan;

    renderDashboardUI();
    renderScheduleUI();
    renderCharts();
  } catch (err) {
    console.error('Error loading dashboard:', err);
  } finally {
    hideSkeletons();
  }
}

function showSkeletons() {
  document.querySelectorAll('.loading-indicator').forEach(el => el.style.display = 'inline-block');
}
function hideSkeletons() {
  document.querySelectorAll('.loading-indicator').forEach(el => el.style.display = 'none');
}

// --- RENDER DASHBOARD UI ---
function renderDashboardUI() {
  if (!AppState.riskData || !AppState.sprayPlan) return;

  const isKn = I18n.currentLang === 'kn';
  const risk = AppState.riskData;
  const decisions = AppState.sprayPlan.decisions;
  const todayDecision = decisions.length > 0 ? decisions[0] : null;

  // 1. Location Banner
  const coordsDisplay = document.getElementById('coordsDisplay');
  if (coordsDisplay) {
    coordsDisplay.textContent = `${AppState.village} (${AppState.lat}°N, ${AppState.lon}°E)`;
  }

  // 2. Today's Action Card
  const actionCard = document.getElementById('todayActionCard');
  const actionBadge = document.getElementById('actionBadge');
  const actionText = document.getElementById('actionText');
  const actionRuleAttr = document.getElementById('actionRuleAttr');

  if (todayDecision && actionCard) {
    actionCard.className = `card action-card ${todayDecision.recommendation.toLowerCase()}`;
    actionBadge.className = `action-badge ${todayDecision.recommendation.toLowerCase()}`;
    actionBadge.textContent = isKn ? todayDecision.summary_kn.split(':')[0] : todayDecision.recommendation;
    actionText.textContent = isKn ? todayDecision.summary_kn : todayDecision.summary_en;

    actionRuleAttr.innerHTML = `<strong>Weather:</strong> ${AppState.weatherData?.data_source || 'Loading'}<br><strong>Rules:</strong> ${todayDecision.rule_source} | <em>${todayDecision.rules_applied.join(', ')}</em>`;
  }

  // 3. Conducive-Conditions Gauge
  renderRiskGauge(risk.conducive_conditions_index ?? risk.total_risk_score, risk.risk_level, isKn ? risk.risk_label_kn : risk.risk_label_en, risk.badge_color);

  // 4. Risk Factors Breakdown
  const factorsContainer = document.getElementById('riskFactorsContainer');
  if (factorsContainer && risk.factors) {
    factorsContainer.innerHTML = risk.factors.map(f => `
      <div class="factor-item">
        <div class="factor-title">
          <span>${getFactorIcon(f.factor_id)}</span>
          <span>${isKn ? f.factor_name_kn : f.factor_name_en}</span>
        </div>
        <div class="factor-value">${f.raw_value} ${f.unit}</div>
        <div style="font-size:12px;color:#666;margin-top:2px;">
          ${isKn ? f.explanation_kn : f.explanation_en}
        </div>
      </div>
    `).join('');
  }

  // 5. Spray Window 7-Day Timeline Chips
  const timelineContainer = document.getElementById('sprayTimelineContainer');
  if (timelineContainer && decisions) {
    timelineContainer.innerHTML = decisions.map((d, index) => {
      const rec = d.recommendation.toLowerCase();
      const recLabel = rec === 'good' 
        ? (isKn ? 'ಸೂಕ್ತ' : 'GOOD') 
        : (rec === 'avoid' ? (isKn ? 'ಬೇಡ' : 'AVOID') : (isKn ? 'ಗಮನಿಸಿ' : 'MONITOR'));
      
      return `
        <div class="day-chip ${rec} ${index === 0 ? 'active' : ''}" onclick="openHourlyModal('${d.date}')">
          <div class="chip-day-name">${d.day_name}</div>
          <div class="chip-date">${d.date.substring(5)}</div>
          <div class="chip-rec-badge ${rec}">${recLabel}</div>
          <div class="chip-metrics">
            🌧️ ${d.rain_expected_mm} mm<br/>
            💨 ${d.max_wind_kmh} km/h<br/>
            ☀️ ${d.dry_window_hours}h dry
          </div>
        </div>
      `;
    }).join('');
  }
}

function getFactorIcon(factorId) {
  switch (factorId) {
    case 'consecutive_rain': return '🌧️';
    case 'relative_humidity': return '💧';
    case 'cloud_cover': return '☁️';
    case 'temperature': return '🌡️';
    default: return '📊';
  }
}

// --- RISK GAUGE RENDERER ---
function renderRiskGauge(score, level, labelText, color) {
  const container = document.getElementById('gaugeContainer');
  if (!container) return;

  // Arc calculation (semi-circle from 180 to 0 degrees)
  const radius = 70;
  const strokeWidth = 14;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  container.innerHTML = `
    <svg class="gauge-svg" viewBox="0 0 180 110">
      <!-- Background Arc -->
      <path d="M 20 95 A 70 70 0 0 1 160 95" fill="none" stroke="#E0E0E0" stroke-width="${strokeWidth}" stroke-linecap="round"/>
      <!-- Value Arc -->
      <path d="M 20 95 A 70 70 0 0 1 160 95" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round"
            stroke-dasharray="${circumference}" stroke-dashoffset="${strokeDashoffset}" style="transition: stroke-dashoffset 0.8s ease;"/>
    </svg>
    <div class="gauge-score-display">
      <div class="gauge-score-val" style="color:${color}">${score}</div>
      <div class="gauge-score-label" style="color:${color}">${labelText}</div>
      <div style="font-size:12px;color:#777;margin-top:2px;">(0 - 100 Index)</div>
    </div>
  `;
}

// --- SCHEDULE TRACKER ---
function renderScheduleUI() {
  const container = document.getElementById('scheduleTracker');
  if (!container) return;

  const isKn = I18n.currentLang === 'kn';
  container.innerHTML = `
    <div class="schedule-step active">
      <div class="schedule-step-title">1️⃣ ${isKn ? 'ಮುಂಗಾರು ಪೂರ್ವ ಮುನ್ನೆಚ್ಚರಿಕೆ' : 'Round 1: Pre-Monsoon'}</div>
      <div class="schedule-step-desc">${isKn ? 'ಮೇ ಅಂತ್ಯ / ಜೂನ್ ಮೊದಲ ವಾರ: ೧% ಬೋರ್ಡೋ ದ್ರಾವಣ' : 'Late May / Early June: 1% Bordeaux mixture on nut bunches'}</div>
    </div>
    <div class="schedule-step active">
      <div class="schedule-step-title">2️⃣ ${isKn ? 'ಎರಡನೇ ಸಿಂಪರಣೆ (೪೦ ದಿನಗಳ ನಂತರ)' : 'Round 2: 40-Day Follow-Up'}</div>
      <div class="schedule-step-desc">${isKn ? 'ಜುಲೈ ಮಳೆ ಬಿಡುವಿನ ಅವಧಿ: ತೇವಾಂಶ ಮಿತಿ ಮೀರಿದಾಗ' : 'July rain break: Renew protective copper film'}</div>
    </div>
    <div class="schedule-step">
      <div class="schedule-step-title">3️⃣ ${isKn ? 'ಮೂರನೇ ಸಿಂಪರಣೆ (ದೀರ್ಘ ಮಳೆ)' : 'Round 3: Extended Monsoon'}</div>
      <div class="schedule-step-desc">${isKn ? 'ಆಗಸ್ಟ್ / ಸೆಪ್ಟೆಂಬರ್ ಮಳೆ ಮುಂದುವರಿದರೆ' : 'August / September if rains persist'}</div>
    </div>
  `;
}

// --- CHART.JS WEATHER CHART ---
function renderCharts() {
  if (!AppState.weatherData || !AppState.weatherData.daily) return;

  const ctx = document.getElementById('weatherTrendChart');
  if (!ctx) return;

  const daily = AppState.weatherData.daily.slice(3); // 7 forecast days
  const labels = daily.map(d => d.date.substring(5));
  const rainValues = daily.map(d => d.precipitation_sum_mm);
  const rhValues = daily.map(d => d.avg_relative_humidity_pct);
  const windValues = daily.map(d => d.max_wind_speed_kmh);

  if (AppState.trendChart) {
    AppState.trendChart.destroy();
  }

  AppState.trendChart = new Chart(ctx, {
    data: {
      labels: labels,
      datasets: [
        {
          type: 'bar',
          label: I18n.t('chart.rain_mm'),
          data: rainValues,
          backgroundColor: '#2A9D8F',
          borderRadius: 6,
          yAxisID: 'yRain'
        },
        {
          type: 'line',
          label: I18n.t('chart.humidity_pct'),
          data: rhValues,
          borderColor: '#1B4332',
          backgroundColor: 'transparent',
          borderWidth: 2.5,
          tension: 0.3,
          yAxisID: 'yRH'
        },
        {
          type: 'line',
          label: I18n.t('chart.wind_kmh'),
          data: windValues,
          borderColor: '#E9C46A',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [4, 4],
          yAxisID: 'yRain'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        yRain: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: 'Rain (mm) / Wind (km/h)' },
          suggestedMax: 20
        },
        yRH: {
          type: 'linear',
          position: 'right',
          title: { display: true, text: 'Humidity (%)' },
          min: 40,
          max: 100,
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

// --- HOURLY MODAL ---
window.openHourlyModal = function(dateStr) {
  if (!AppState.weatherData || !AppState.weatherData.hourly) return;

  const modal = document.getElementById('hourlyModal');
  const content = document.getElementById('hourlyModalContent');
  const title = document.getElementById('modalDateTitle');

  const matchingHours = AppState.weatherData.hourly.filter(h => h.time.startsWith(dateStr));
  if (!matchingHours.length) return;

  title.textContent = `${I18n.t('hourly_modal.title')} - ${dateStr}`;
  content.innerHTML = matchingHours.map(h => {
    const hour = h.time.substring(11, 16);
    const rainBadge = h.precipitation_mm > 0 ? `🌧️ ${h.precipitation_mm}mm` : '☀️ 0 mm';
    return `
      <div class="hourly-row">
        <strong>${hour}</strong>
        <span>🌡️ ${h.temperature_c}°C</span>
        <span>💧 ${h.relative_humidity_pct}%</span>
        <span>${rainBadge}</span>
        <span>💨 ${h.wind_speed_kmh} km/h</span>
      </div>
    `;
  }).join('');

  modal.classList.add('open');
};

// --- WEB SPEECH SYNTHESIS (KANNADA AUDIO) ---
function toggleAudioSpeech() {
  if (!window.speechSynthesis) {
    showVoiceNotice();
    return;
  }

  const listenBtn = document.getElementById('listenActionBtn');

  if (AppState.isSpeaking) {
    window.speechSynthesis.cancel();
    AppState.isSpeaking = false;
    listenBtn.classList.remove('speaking');
    listenBtn.innerHTML = `🔊 ${I18n.t('today_action.listen_btn')}`;
    return;
  }

  const isKn = I18n.currentLang === 'kn';
  const textToRead = document.getElementById('actionText').textContent;

  // Find Kannada voice if available
  const voices = window.speechSynthesis.getVoices();
  let selectedVoice = voices.find(v => v.lang.includes('kn') || v.name.toLowerCase().includes('kannada'));

  if (isKn && !selectedVoice) {
    // Non-blocking mobile fallback; the visible text advisory remains available.
    showVoiceNotice();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(textToRead);
  utterance.lang = isKn ? 'kn-IN' : 'en-IN';
  if (selectedVoice) utterance.voice = selectedVoice;
  utterance.rate = 0.95; // Slightly slower for clarity

  utterance.onstart = () => {
    AppState.isSpeaking = true;
    listenBtn.classList.add('speaking');
    listenBtn.innerHTML = `⏹️ ${I18n.t('today_action.speaking')}`;
  };

  utterance.onend = utterance.onerror = () => {
    AppState.isSpeaking = false;
    listenBtn.classList.remove('speaking');
    listenBtn.innerHTML = `🔊 ${I18n.t('today_action.listen_btn')}`;
  };

  window.speechSynthesis.speak(utterance);
}

function showVoiceNotice() {
  let notice = document.getElementById('voiceFallbackNotice');
  if (!notice) {
    notice = document.createElement('div');
    notice.id = 'voiceFallbackNotice';
    notice.setAttribute('role', 'status');
    notice.style.cssText = 'position:fixed;left:16px;right:16px;bottom:18px;z-index:9999;background:#fff3cd;color:#5c4300;border:1px solid #e9c46a;border-radius:10px;padding:12px;box-shadow:0 4px 18px rgba(0,0,0,.18);font-size:14px;';
    document.body.appendChild(notice);
  }
  notice.textContent = 'Kannada voice pack not detected on this device — showing text advisory / using fallback audio. ಕನ್ನಡ ಧ್ವನಿ ಪ್ಯಾಕ್ ಕಂಡುಬಂದಿಲ್ಲ — ಪಠ್ಯ ಸಲಹೆ ತೋರಿಸಲಾಗುತ್ತಿದೆ.';
  notice.hidden = false;
  setTimeout(() => { notice.hidden = true; }, 6000);
}

// --- MANDI PRICES & PROFIT PLANNER ---
async function loadMandiPrices() {
  try {
    const res = await fetch('/api/mandi/prices');
    const prices = await res.json();
    const select = document.getElementById('mandiSelect');
    if (!select) return;

    select.innerHTML = prices.map(p => {
      const hasPrice = Number.isFinite(p.modal_price_per_quintal);
      const detail = hasPrice ? `₹${p.modal_price_per_quintal.toLocaleString()}/qtl` : 'Enter live/custom rate';
      return `<option value="${hasPrice ? p.modal_price_per_quintal : 'custom'}" data-market="${p.market}">${p.market} (${p.commodity}) — ${detail} [${p.source}]</option>`;
    }).join('') + `<option value="custom">-- Live / Custom Mandi Rate --</option>`;

    select.addEventListener('change', () => {
      const val = select.value;
      if (val !== 'custom') {
        document.getElementById('inputSellingPrice').value = val;
      }
      const chosen = prices[select.selectedIndex];
      const hint = document.getElementById('mandiPriceStatus');
      if (hint) hint.textContent = chosen ? `${chosen.source}${chosen.date ? ` • ${chosen.date}` : ''}` : 'Enter today’s local mandi rate.';
      document.getElementById('inputSellingPrice').focus();
      runEconomicsCalculation();
    });

    if (prices.length > 0) {
      document.getElementById('inputSellingPrice').value = prices[0].modal_price_per_quintal;
      runEconomicsCalculation();
    }
  } catch (e) {
    console.warn('Failed to load mandi prices', e);
  }
}

async function loadReferenceDefaults() {
  try {
    const res = await fetch('/api/defaults');
    if (!res.ok) return;
    const defaults = await res.json();
    AppState.defaults = defaults;
    VILLAGE_PRESETS = [...(defaults.karnataka_location_presets || []), ...(defaults.popular_villages || [])].map(p => ({
      name: `${p.name_en} (${p.name_kn})`, district: `${p.district_en} / ${p.district_kn}`,
      taluk: p.taluk_en || '', lat: p.lat, lon: p.lon, belt: p.belt
    }));
    const select = document.getElementById('costPresetSelect');
    if (!select) return;
    const presets = defaults.cost_presets || [];
    select.innerHTML = '<option value="">Custom values</option>' + presets.map(p => `<option value="${p.id}">${p.label}</option>`).join('');
    select.addEventListener('change', () => applyCostPreset(select.value));
  } catch (err) { console.warn('Reference defaults unavailable', err); }
}

function applyCostPreset(id) {
  const preset = (AppState.defaults?.cost_presets || []).find(p => p.id === id);
  if (!preset) return;
  const acres = Number(document.getElementById('inputAcres').value || 1);
  if (preset.trees_per_acre) document.getElementById('inputTreesPerAcre').value = preset.trees_per_acre;
  if (preset.yield_per_tree_kg) document.getElementById('inputYield').value = Math.round(acres * preset.trees_per_acre * preset.yield_per_tree_kg);
  if (preset.spray_cost_per_tree_round) document.getElementById('inputSprayCost').value = Math.round(acres * (preset.trees_per_acre || 0) * preset.spray_cost_per_tree_round);
  if (preset.annual_cost_per_acre) {
    // Preserve the editable cost model while setting its total to the cited benchmark.
    document.getElementById('inputManure').value = Math.round(preset.annual_cost_per_acre * 0.25);
    document.getElementById('inputHarvest').value = Math.round(preset.annual_cost_per_acre * 0.45);
  }
  document.getElementById('presetCitation').textContent = `${preset.citation} — ${preset.region}, ${preset.year}. Reference values — edit to match your plantation.`;
  runEconomicsCalculation();
}

async function runEconomicsCalculation() {
  const payload = {
    acres: parseFloat(document.getElementById('inputAcres').value || 1),
    trees_per_acre: parseInt(document.getElementById('inputTreesPerAcre').value || 575),
    labour_wage_per_day: parseFloat(document.getElementById('inputWage').value || 650),
    spray_rounds: parseInt(document.getElementById('inputRounds').value || 3),
    spray_cost_per_round: parseFloat(document.getElementById('inputSprayCost').value || 0),
    manure_fertilizer_cost: parseFloat(document.getElementById('inputManure').value || 35000),
    harvest_labour_cost: parseFloat(document.getElementById('inputHarvest').value || 45000),
    expected_yield_kg: parseFloat(document.getElementById('inputYield').value || 0),
    selling_price_per_qtl: parseFloat(document.getElementById('inputSellingPrice').value || 44000)
  };

  try {
    const res = await fetch('/api/economics/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    displayEconomicsResults(result);
  } catch (e) {
    alert('Error running calculation: ' + e);
  }
}

function displayEconomicsResults(result) {
  const box = document.getElementById('profitResultsBox');
  if (!box) return;

  const isKn = I18n.currentLang === 'kn';
  const fin = result.financial_summary;
  const bd = result.cost_breakdown;

  document.getElementById('resTotalCost').textContent = `₹${fin.total_cultivation_cost.toLocaleString()}`;
  document.getElementById('resRevenue').textContent = `₹${fin.total_revenue.toLocaleString()}`;
  
  const profitEl = document.getElementById('resNetProfit');
  profitEl.textContent = `₹${fin.net_profit.toLocaleString()} (${fin.profit_margin_pct}%)`;
  profitEl.className = `profit-stat-val ${fin.is_profitable ? '' : 'loss'}`;

  document.getElementById('resBreakEven').textContent = `₹${fin.break_even_price_per_qtl.toLocaleString()} /qtl (₹${fin.break_even_price_per_kg}/kg)`;
  document.getElementById('resInsightText').textContent = isKn ? result.plain_insights.kn : result.plain_insights.en;

  box.style.display = 'block';

  // Render Cost Breakdown Chart
  renderCostChart(bd);
}

function renderCostChart(bd) {
  const ctx = document.getElementById('costBreakdownChart');
  if (!ctx) return;

  if (AppState.costChart) AppState.costChart.destroy();

  AppState.costChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: [
        `Spraying (${bd.spraying_pct}%)`,
        `Harvest Labour (${bd.harvest_pct}%)`,
        `Manure / Fert (${bd.manure_pct}%)`,
        `Maintenance Labour (${bd.maintenance_labour_pct}%)`
      ],
      datasets: [{
        data: [
          bd.spraying_cost,
          bd.harvest_labour_cost,
          bd.manure_fertilizer_cost,
          bd.maintenance_labour_cost
        ],
        backgroundColor: ['#2A9D8F', '#E9C46A', '#2D6A4F', '#40916C']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

async function saveCostScenario() {
  const scenarioName = prompt('Enter a name for this scenario (e.g. 2026 Monsoon Strategy):', '2026 Monsoon Strategy');
  if (!scenarioName) return;

  const payload = {
    scenario_name: scenarioName,
    acres: parseFloat(document.getElementById('inputAcres').value || 1),
    trees_per_acre: parseInt(document.getElementById('inputTreesPerAcre').value || 575),
    labour_wage_per_day: parseFloat(document.getElementById('inputWage').value || 650),
    spray_rounds: parseInt(document.getElementById('inputRounds').value || 3),
    manure_fertilizer_cost: parseFloat(document.getElementById('inputManure').value || 35000),
    harvest_labour_cost: parseFloat(document.getElementById('inputHarvest').value || 45000),
    selling_price_per_qtl: parseFloat(document.getElementById('inputSellingPrice').value || 44000)
  };

  try {
    const res = await fetch('/api/economics/save-scenario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert('Scenario successfully saved to plantation records!');
    }
  } catch (e) {
    alert('Failed to save scenario: ' + e);
  }
}

// --- FARM DIARY ---
async function loadDiaryEntries() {
  try {
    const res = await fetch('/api/diary');
    const entries = await res.json();
    renderDiaryTable(entries);
  } catch (e) {
    console.warn('Failed to load diary entries', e);
  }
}

function renderDiaryTable(entries) {
  const tbody = document.getElementById('diaryTableBody');
  if (!tbody) return;

  const isKn = I18n.currentLang === 'kn';

  if (!entries || entries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#888;">No diary records yet. Add your first log entry above.</td></tr>`;
    return;
  }

  tbody.innerHTML = entries.map(e => `
    <tr>
      <td><strong>${e.entry_date}</strong></td>
      <td>${getEventBadge(e.event_type, isKn)}</td>
      <td>${e.severity !== 'None' ? e.severity : '-'}</td>
      <td>${e.affected_trees_count > 0 ? e.affected_trees_count : '-'}</td>
      <td>${e.notes}</td>
    </tr>
  `).join('');
}

function getEventBadge(eventType, isKn) {
  const map = {
    fruit_rot_seen: { en: 'Fruit Rot Seen', kn: 'ಕೊಳೆರೋಗ ಕಂಡುಬಂದಿದೆ', color: '#D32F2F' },
    sprayed: { en: 'Sprayed', kn: 'ಔಷಧ ಸಿಂಪಡಿಸಲಾಗಿದೆ', color: '#2E7D32' },
    harvest: { en: 'Harvest', kn: 'ಕೊಯ್ಲು', color: '#ED6C02' },
    monkey_damage: { en: 'Monkey Damage', kn: 'ಮಂಗಗಳ ಹಾವಳಿ', color: '#795548' },
    fertilizer: { en: 'Fertilizer Applied', kn: 'ಗೊಬ್ಬರ ಹಾಕಲಾಗಿದೆ', color: '#00796B' }
  };
  const item = map[eventType] || { en: eventType, kn: eventType, color: '#666' };
  const label = isKn ? item.kn : item.en;
  return `<span style="background:${item.color};color:#FFF;padding:3px 8px;border-radius:12px;font-size:12px;font-weight:700;">${label}</span>`;
}

async function saveDiaryEntry() {
  const payload = {
    entry_date: document.getElementById('diaryDate').value,
    event_type: document.getElementById('diaryEventType').value,
    severity: document.getElementById('diarySeverity').value,
    affected_trees_count: parseInt(document.getElementById('diaryAffectedTrees').value || 0),
    notes: document.getElementById('diaryNotes').value
  };

  try {
    const res = await fetch('/api/diary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      document.getElementById('diaryForm').reset();
      document.getElementById('diaryDate').value = new Date().toISOString().substring(0, 10);
      loadDiaryEntries();
      alert('Event logged successfully in Farm Diary!');
    }
  } catch (e) {
    alert('Error saving diary entry: ' + e);
  }
}

// --- ASK MITRA RAG ADVISORY ---
async function submitRagQuery() {
  const input = document.getElementById('ragQuestionInput');
  const question = input.value.trim();
  if (!question) return;

  const resultContainer = document.getElementById('ragResponseContainer');
  resultContainer.innerHTML = `<div style="color:#666;font-style:italic;">🔍 Searching CPCRI, KAU, UAS documents...</div>`;

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const data = await res.json();

    const isKn = I18n.currentLang === 'kn';
    const answer = isKn ? (data.answer_kn || data.answer_en) : data.answer_en;

    if (!data.found_in_corpus) {
      resultContainer.innerHTML = `
        <div class="rag-response-card" style="border-left:5px solid #ED6C02;">
          <div style="font-weight:700;color:#D32F2F;margin-bottom:6px;">⚠️ ${isKn ? 'ದಾಖಲೆಗಳಲ್ಲಿ ಉತ್ತರವಿಲ್ಲ' : 'Information Not Verified in Corpus'}</div>
          <div>${answer}</div>
          <div style="font-size:12px;color:#888;margin-top:8px;"><em>${data.disclaimer || 'We refuse to guess or speculate.'}</em></div>
        </div>
      `;
    } else {
      resultContainer.innerHTML = `
        <div class="rag-response-card" style="border-left:5px solid #2E7D32;">
          <div style="font-weight:700;color:#1B4332;margin-bottom:8px;">✅ ${isKn ? 'ಅಧಿಕೃತ ಕೃಷಿ ಮಾಹಿತಿ' : 'Verified Agronomy Guidance'}</div>
          <div style="white-space:pre-line;line-height:1.6;">${answer}</div>
          <div class="rag-sources">
            <strong>${I18n.t('ask_mitra.sources_label')}:</strong>
            ${data.sources.map(s => `<span style="background:#E8F5E9;padding:2px 8px;border-radius:6px;margin-right:4px;">📄 ${s}</span>`).join('')}
          </div>
        </div>
      `;
    }
  } catch (e) {
    resultContainer.innerHTML = `<div style="color:red;">Error fetching answer: ${e}</div>`;
  }
}

function startSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert('Voice input is not supported in this browser. Please type your question.');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = I18n.currentLang === 'kn' ? 'kn-IN' : 'en-IN';
  const micBtn = document.getElementById('voiceInputBtn');
  micBtn.classList.add('listening');

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('ragQuestionInput').value = transcript;
    micBtn.classList.remove('listening');
    submitRagQuery();
  };

  recognition.onerror = recognition.onend = () => {
    micBtn.classList.remove('listening');
  };

  recognition.start();
}

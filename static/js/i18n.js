// ===================================================================
// THOTA MITRA - i18n Translation Manager
// Kannada-first with English toggle, native speaker review tags
// ===================================================================

const I18n = {
  currentLang: localStorage.getItem('thota_mitra_lang') || 'kn',
  translations: {},

  async init() {
    try {
      const [knRes, enRes] = await Promise.all([
        fetch('/locales/kn.json'),
        fetch('/locales/en.json')
      ]);
      this.translations['kn'] = await knRes.json();
      this.translations['en'] = await enRes.json();
    } catch (e) {
      console.warn('Failed to load locale files, falling back to cached strings', e);
    }
    this.applyLanguage(this.currentLang);
  },

  setLanguage(lang) {
    if (lang !== 'kn' && lang !== 'en') return;
    this.currentLang = lang;
    localStorage.setItem('thota_mitra_lang', lang);
    this.applyLanguage(lang);
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
  },

  toggleLanguage() {
    this.setLanguage(this.currentLang === 'kn' ? 'en' : 'kn');
  },

  t(path, fallback = '') {
    const keys = path.split('.');
    let obj = this.translations[this.currentLang];
    for (const key of keys) {
      if (obj && obj[key] !== undefined) {
        obj = obj[key];
      } else {
        // Fallback to English
        let fallbackObj = this.translations['en'];
        for (const fbKey of keys) {
          if (fallbackObj && fallbackObj[fbKey] !== undefined) {
            fallbackObj = fallbackObj[fbKey];
          } else {
            return fallback || path;
          }
        }
        return fallbackObj || fallback || path;
      }
    }
    return obj || fallback || path;
  },

  applyLanguage(lang) {
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = this.t(key);
      if (text) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          el.placeholder = text;
        } else {
          el.textContent = text;
        }
      }
    });

    const langToggleBtn = document.getElementById('langToggleBtn');
    if (langToggleBtn) {
      langToggleBtn.innerHTML = lang === 'kn' ? '🌐 English' : '🌐 ಕನ್ನಡ';
    }
  }
};

window.I18n = I18n;

(function () {
  const STORAGE_PREFIX = 'cours-html:';
  const path = location.pathname.replace(/\\/g, '/');
  const isIndex = /\/?index\.html?$/.test(path) || path.endsWith('/cours-html/');

  function rootPrefix() {
    return path.includes('/bash/') || path.includes('/linux-initiation/') || path.includes('/mininotes/') || path.includes('/fondamentaux-reseaux/')
      ? '../'
      : '';
  }

  function storageKey(name) {
    return STORAGE_PREFIX + name;
  }

  function readStore(name, fallback) {
    try {
      return JSON.parse(localStorage.getItem(storageKey(name)) || JSON.stringify(fallback));
    } catch (_error) {
      return fallback;
    }
  }

  function writeStore(name, value) {
    try {
      localStorage.setItem(storageKey(name), JSON.stringify(value));
    } catch (_error) {
      // The course stays fully usable when localStorage is blocked.
    }
  }

  function readText(name) {
    try {
      return localStorage.getItem(storageKey(name));
    } catch (_error) {
      return null;
    }
  }

  function writeText(name, value) {
    try {
      localStorage.setItem(storageKey(name), value);
    } catch (_error) {
      // The active tab simply will not be remembered.
    }
  }

  function markVisited() {
    if (isIndex) return;
    const visited = readStore('visited', {});
    const rel = path.split('/cours-html/').pop() || path.split('/').pop();
    visited[rel] = { title: document.title, at: new Date().toISOString() };
    writeStore('visited', visited);
  }

  function addHomeLink() {
    if (isIndex || document.querySelector('.course-home-link')) return;
    const link = document.createElement('a');
    link.className = 'course-home-link';
    link.href = rootPrefix() + 'index.html';
    link.setAttribute('aria-label', 'Retourner a la page d accueil des cours');
    link.textContent = '← Accueil';
    document.body.appendChild(link);
  }

  function markIndexCards() {
    if (!isIndex) return;
    const visited = readStore('visited', {});
    document.querySelectorAll('a.card[href]').forEach((card) => {
      const href = card.getAttribute('href');
      if (!visited[href]) return;
      card.classList.add('course-visited');
      if (!card.querySelector('.course-progress-pill')) {
        const pill = document.createElement('span');
        pill.className = 'course-progress-pill';
        pill.textContent = 'Vu';
        card.appendChild(pill);
      }
    });
  }

  function improveClickableElements() {
    document.querySelectorAll('[onclick]').forEach((el) => {
      const tag = el.tagName.toLowerCase();
      if (tag === 'button' || tag === 'a' || tag === 'input' || tag === 'select' || tag === 'textarea') return;
      if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
      if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
      el.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        el.click();
      });
    });

    document.querySelectorAll('button').forEach((btn) => {
      if (btn.getAttribute('aria-label')) return;
      const text = btn.textContent.trim();
      if (text === '⎘' || text.toLowerCase() === 'copier' || text.toLowerCase().includes('copier')) {
        btn.setAttribute('aria-label', 'Copier le bloc de code');
      }
    });
  }

  function rememberTabs() {
    const tabButtons = Array.from(document.querySelectorAll('nav button[onclick], .nav button[onclick]'));
    if (!tabButtons.length) return;

    const key = 'tab:' + path;
    const extractTab = (btn) => {
      const attr = btn.getAttribute('onclick') || '';
      const match = attr.match(/show(?:Tab|Sec)\(['"]([^'"]+)['"]/);
      return match ? match[1] : null;
    };

    tabButtons.forEach((btn) => {
      const tab = extractTab(btn);
      if (!tab) return;
      btn.addEventListener('click', () => writeText(key, tab));
    });

    const saved = readText(key);
    if (!saved) return;
    const target = tabButtons.find((btn) => extractTab(btn) === saved);
    if (target && !target.classList.contains('active')) {
      setTimeout(() => target.click(), 0);
    }
  }

  function syncActiveStateForAssistiveTech() {
    const setCurrent = () => {
      document.querySelectorAll('nav button, .nav button').forEach((btn) => {
        if (btn.classList.contains('active')) btn.setAttribute('aria-current', 'page');
        else btn.removeAttribute('aria-current');
      });
    };
    setCurrent();
    new MutationObserver(setCurrent).observe(document.body, {
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    markVisited();
    addHomeLink();
    markIndexCards();
    improveClickableElements();
    rememberTabs();
    syncActiveStateForAssistiveTech();
  });
}());

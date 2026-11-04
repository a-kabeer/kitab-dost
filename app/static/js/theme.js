/**
 * Kitaab Bank - Zero-FOUC Theme Management Engine
 * Supports: Light, Dark, System Default
 * Fully offline, zero dependencies.
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'kb_theme';
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  function getSavedPreference() {
    return localStorage.getItem(STORAGE_KEY) || 'system';
  }

  function resolveTheme(preference) {
    if (preference === 'system') {
      return mediaQuery.matches ? 'dark' : 'light';
    }
    return preference;
  }

  function applyTheme(preference) {
    const activeTheme = resolveTheme(preference);
    document.documentElement.setAttribute('data-theme', activeTheme);
    document.documentElement.setAttribute('data-theme-preference', preference);
    localStorage.setItem(STORAGE_KEY, preference);
    updateUI(preference, activeTheme);
  }

  function updateUI(preference, activeTheme) {
    // Update theme toggle button text/icon if present
    const labelEls = document.querySelectorAll('[data-theme-label]');
    const iconEls = document.querySelectorAll('[data-theme-icon]');

    const icons = {
      light: '☀️',
      dark: '🌙',
      system: '💻'
    };

    const labels = {
      light: 'Light',
      dark: 'Dark',
      system: 'System'
    };

    iconEls.forEach(el => {
      el.textContent = icons[preference] || '☀️';
    });

    labelEls.forEach(el => {
      el.textContent = labels[preference] || 'Theme';
    });

    // Mark active option in dropdowns
    document.querySelectorAll('[data-theme-set]').forEach(btn => {
      const target = btn.getAttribute('data-theme-set');
      if (target === preference) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  // Setup DOM listeners once loaded
  document.addEventListener('DOMContentLoaded', () => {
    const currentPref = getSavedPreference();
    applyTheme(currentPref);

    // Toggle dropdown open/close
    document.querySelectorAll('[data-theme-toggle]').forEach(toggleBtn => {
      toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const menu = toggleBtn.closest('.theme-selector-wrap').querySelector('.theme-dropdown-menu');
        if (menu) {
          menu.classList.toggle('show');
        }
      });
    });

    // Close theme dropdown on outside click
    document.addEventListener('click', () => {
      document.querySelectorAll('.theme-dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
      });
    });

    // Theme selection buttons
    document.querySelectorAll('[data-theme-set]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const targetTheme = btn.getAttribute('data-theme-set');
        applyTheme(targetTheme);
        document.querySelectorAll('.theme-dropdown-menu.show').forEach(menu => {
          menu.classList.remove('show');
        });
      });
    });

    // React to OS changes when set to system default
    mediaQuery.addEventListener('change', () => {
      if (getSavedPreference() === 'system') {
        applyTheme('system');
      }
    });
  });

  // Expose global helper
  window.KitaabTheme = {
    setTheme: applyTheme,
    getPreference: getSavedPreference
  };
})();

function initI18n() {
  return i18next
    .use(i18nextBrowserLanguageDetector)
    .init({
      debug: false,
      fallbackLng: 'en',
      resources: {
        en: {
          translation: {} // 动态加载
        },
        zh: {
          translation: {} // 动态加载
        }
      },
      detection: {
        order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
        caches: ['cookie', 'localStorage']
      },
      interpolation: {
        escapeValue: false // 禁用对插值内容的 HTML 转义
      }
    });
}

function loadTranslations(lang) {
  return new Promise((resolve, reject) => {
    $.getJSON(`/static/locales/${lang}.json`, (data) => {
      i18next.addResourceBundle(lang, 'translation', data);
      resolve();
    }).fail(reject);
  });
}

$(document).ready(async function() {
  try {
    await initI18n();

    // 加载当前语言的翻译文件
    const currentLng = i18next.language;
    await loadTranslations(currentLng.split('-')[0]); // 处理类似 zh-CN 的情况

    // 初始化界面翻译
    updateContent();

    // 注册语言切换事件
    $('.language-switcher').on('click', 'a', async function(e) {
      e.preventDefault();
      const lng = $(this).data('lng');
      await i18next.changeLanguage(lng);
      await loadTranslations(lng);
      updateContent();
    });

  } catch (err) {
    console.error('i18n initialization failed:', err);
  }
});

function updateContent() {
  // 通用翻译方法
  $('[data-i18n]').each(function() {
    const key = $(this).data('i18n');
    $(this).html(i18next.t(key));
  });

  // 特殊处理占位符等
  $('[data-i18n-placeholder]').each(function() {
    const key = $(this).data('i18n-placeholder');
    $(this).attr('placeholder', i18next.t(key));
  });
}


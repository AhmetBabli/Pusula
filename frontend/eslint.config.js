import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default [
  // 1. Adım: Global yok sayma kuralları (En üstte olmalı)
  { ignores: ['dist', 'node_modules'] },

  // 2. Adım: Proje kodları için yapılandırma
  {
    files: ['**/*.{js,jsx}'],
    
    // Dil ve Ortam Ayarları
    languageOptions: {
      ecmaVersion: 'latest', // Çelişkiyi kaldırdık, en güncel standart
      globals: globals.browser, // Tarayıcı API'lerini (window, document) tanı
      parserOptions: {
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },

    // Eklentilerin (Plugins) Kaydedilmesi
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },

    // Kuralların Tanımlanması (Flat Config Mantığı)
    rules: {
      // Önerilen JavaScript kurallarını buraya yayıyoruz (spread)
      ...js.configs.recommended.rules,
      
      // Önerilen React Hooks kurallarını yayıyoruz
      ...reactHooks.configs.recommended.rules,

      // Senin özel kuralın (Sadece büyük harf ve alt tire ile başlayan kullanılmayanlara izin ver)
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],

      // Vite'in HMR (Hot Module Replacement) mantığının doğru çalışması için kritik kural
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
]
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Aktif çalışma moduna (development/production) göre .env dosyasını yükler
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    
    // Klasör yolu kısaltmaları (Path Aliases)
    resolve: {
      alias: {
        // '@' işaretini otomatik olarak 'src' klasörüne yönlendirir.
        // Kullanımı: import Header from '@/components/layout/Header'
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },

    server: {
      port: 5173,
      // true yapıldığında yerel ağdaki diğer cihazlardan (mobil test)
      // veya Docker container dışından projeye erişilmesine izin verir.
      host: true, 
      
      // strictPort: true, // (Opsiyonel) 5173 doluysa rastgele porta geçmeyi engeller, hata fırlatır.
      
      proxy: {
        '/api': {
          // Backend URL'ini .env dosyasındaki VITE_API_URL değişkeninden alır.
          // Eğer .env'de tanımlı değilse varsayılan olarak 127.0.0.1:8000 kullanır.
          target: env.VITE_API_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,

          // NOT: Eğer backend router'ında (FastAPI) '/api' öneki YOKSA,
          // proxy'nin bu '/api' kısmını silip backend'e temiz yollaması için aşağıdaki satırı açabilirsin:
          // rewrite: (path) => path.replace(/^\/api/, '')
        },
        // Ajan Merkezi'nin canlı WebSocket bağlantısı için — eskiden frontend
        // ws://localhost:8000'e sabit kodlu bağlanıyordu, bu proxy olmadan
        // useAgentWebSocket.ts'nin göreli (aynı origin) bağlantısı dev
        // sunucusunda backend'e ulaşamaz.
        '/ws': {
          target: env.VITE_API_URL || 'http://127.0.0.1:8000',
          ws: true,
          changeOrigin: true,
          secure: false,
        }
      }
    }
  }
})
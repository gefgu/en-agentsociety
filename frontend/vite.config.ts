import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8080'
const usePolling = ['1', 'true', 'yes'].includes((process.env.CHOKIDAR_USEPOLLING || '').toLowerCase())
const pollingInterval = Number(process.env.CHOKIDAR_INTERVAL || 300)

// https://vite.dev/config/
export default defineConfig({
    server: {
        watch: {
            usePolling,
            interval: pollingInterval,
        },
        proxy: {
            '/api/alipay': {
                target: 'https://agentsociety.fiblab.net',
                changeOrigin: true,
            },
            '/api': {
                target: apiProxyTarget,
                changeOrigin: true,
            }
        }
    },
    plugins: [react()],
    base: '/',
    build: {
        outDir: 'dist',
        assetsDir: 'assets',
        sourcemap: false,
    }
})

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@features": path.resolve(__dirname, "./src/features"),
      "@shared": path.resolve(__dirname, "./src/shared"),
      "@core": path.resolve(__dirname, "./src/core"),
    },
  },
  server: {
    port: 3000,
    strictPort: true,
    open: true,
    // HTML5 History API를 위한 설정
    historyApiFallback: true,
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    // 번들 최적화
    rollupOptions: {
      output: {
        // 코드 스플리팅 개선
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['framer-motion', 'clsx', 'react-hot-toast'],
          'chart-vendor': ['recharts'],
          'markdown-vendor': ['react-markdown', 'remark-gfm'],
        },
      },
    },
    // 청크 크기 경고 제한 증가
    chunkSizeWarningLimit: 1000,
  },
  // 프리뷰 서버에서도 라우팅 지원
  preview: {
    port: 3000,
    historyApiFallback: true,
  },
});

import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

const target = process.env.BUILD_TARGET;

const configs = {
  witness: {
    input: path.resolve(__dirname, 'src/witness/witness.js'),
    outDir: '../webapp/static/svelte/witnessView',
    format: 'es',
    entryFileNames: 'witness.js',
    chunkFileNames: '[name]-[hash].js',
    assetFileNames: 'witness.[ext]',
    inlineDynamicImports: false
  },
  recordList: {
    input: path.resolve(__dirname, 'src/records/record-list.js'),
    outDir: '../webapp/static/svelte',
    format: 'iife',
    entryFileNames: 'recordList.js',
    assetFileNames: 'recordList.[ext]',
    inlineDynamicImports: true
  },
  documentSet: {
    input: path.resolve(__dirname, 'src/documentSet/document-set.js'),
    outDir: '../webapp/static/svelte',
    format: 'iife',
    entryFileNames: 'documentSet.js',
    assetFileNames: 'documentSet.[ext]',
    inlineDynamicImports: true
  }
};

const config = configs[target] || configs.regionList;

export default defineConfig({
  plugins: [
    svelte({
      emitCss: true
    })
  ],
  build: {
    outDir: config.outDir,
    emptyOutDir: false,
    sourcemap: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: config.input,
      output: {
        format: config.format,
        name: target,
        entryFileNames: config.entryFileNames,
        chunkFileNames: config.chunkFileNames,
        assetFileNames: config.assetFileNames,
        inlineDynamicImports: config.inlineDynamicImports
      }
    }
  }
});

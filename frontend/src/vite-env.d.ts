/// <reference types="vite/client" />

interface ImportMetaEnv {
  // API Configuration
  readonly VITE_API_BASE_URL: string;
  readonly VITE_API_VERSION: string;

  // App Configuration
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_DESCRIPTION: string;
  readonly VITE_APP_VERSION: string;

  // Features
  readonly VITE_ENABLE_DARK_MODE: string;
  readonly VITE_ENABLE_ANALYTICS: string;
  readonly VITE_ENABLE_DEBUG: string;

  // File Upload
  readonly VITE_MAX_FILE_SIZE: string;
  readonly VITE_ALLOWED_FILE_TYPES: string;

  // AI Providers
  readonly VITE_DEFAULT_AI_PROVIDER: string;
  readonly VITE_ENABLE_AI_FALLBACK: string;

  // UI Configuration
  readonly VITE_DEFAULT_THEME: string;
  readonly VITE_ENABLE_ANIMATIONS: string;
  readonly VITE_TOAST_DURATION: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Global type declarations
declare const __APP_VERSION__: string;

// Module declarations for assets
declare module '*.svg' {
  import type { FC, SVGProps } from 'react';
  export const ReactComponent: FC<SVGProps<SVGSVGElement>>;
  const src: string;
  export default src;
}

declare module '*.png' {
  const src: string;
  export default src;
}

declare module '*.jpg' {
  const src: string;
  export default src;
}

declare module '*.jpeg' {
  const src: string;
  export default src;
}

declare module '*.gif' {
  const src: string;
  export default src;
}

declare module '*.webp' {
  const src: string;
  export default src;
}

declare module '*.ico' {
  const src: string;
  export default src;
}

declare module '*.bmp' {
  const src: string;
  export default src;
}
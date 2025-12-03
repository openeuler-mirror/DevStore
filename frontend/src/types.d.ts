declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}

declare module 'vue' {
  import { ComponentPublicInstance } from 'vue';
  export * from '@vue/runtime-dom';
}

interface ElectronAPI {
  invoke: (channel: string, ...args: any[]) => Promise<any>;
  closeApp: () => void;
  getUsername: () => Promise<string>;
  minimizeWindow: () => void;
  toggleMaximize: () => void;
  closeWindow: () => void;
}

interface Window {
  electronAPI?: ElectronAPI;
}
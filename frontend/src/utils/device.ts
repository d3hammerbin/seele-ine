// Device detection and capabilities utilities

// Device type detection
export const device = {
  // Get user agent string
  getUserAgent: (): string => {
    return navigator.userAgent;
  },

  // Check if mobile device
  isMobile: (): boolean => {
    const userAgent = navigator.userAgent;
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
  },

  // Check if tablet
  isTablet: (): boolean => {
    const userAgent = navigator.userAgent;
    return /iPad|Android(?!.*Mobile)|Tablet/i.test(userAgent);
  },

  // Check if desktop
  isDesktop: (): boolean => {
    return !device.isMobile() && !device.isTablet();
  },

  // Check if touch device
  isTouchDevice: (): boolean => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  },

  // Check if iOS device
  isIOS: (): boolean => {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
  },

  // Check if Android device
  isAndroid: (): boolean => {
    return /Android/i.test(navigator.userAgent);
  },

  // Check if Windows device
  isWindows: (): boolean => {
    return /Windows/i.test(navigator.userAgent);
  },

  // Check if macOS device
  isMacOS: (): boolean => {
    return /Macintosh|MacIntel|MacPPC|Mac68K/i.test(navigator.userAgent);
  },

  // Check if Linux device
  isLinux: (): boolean => {
    return /Linux/i.test(navigator.userAgent) && !device.isAndroid();
  },

  // Get device type
  getType: (): 'mobile' | 'tablet' | 'desktop' => {
    if (device.isMobile()) return 'mobile';
    if (device.isTablet()) return 'tablet';
    return 'desktop';
  },

  // Get operating system
  getOS: (): 'ios' | 'android' | 'windows' | 'macos' | 'linux' | 'unknown' => {
    if (device.isIOS()) return 'ios';
    if (device.isAndroid()) return 'android';
    if (device.isWindows()) return 'windows';
    if (device.isMacOS()) return 'macos';
    if (device.isLinux()) return 'linux';
    return 'unknown';
  },

  // Get device pixel ratio
  getPixelRatio: (): number => {
    return window.devicePixelRatio || 1;
  },

  // Check if high DPI display
  isHighDPI: (): boolean => {
    return device.getPixelRatio() > 1;
  },

  // Get device orientation
  getOrientation: (): 'portrait' | 'landscape' => {
    return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
  },

  // Check if device is in portrait mode
  isPortrait: (): boolean => {
    return device.getOrientation() === 'portrait';
  },

  // Check if device is in landscape mode
  isLandscape: (): boolean => {
    return device.getOrientation() === 'landscape';
  },
};

// Browser detection
export const browser = {
  // Get browser name
  getName: (): string => {
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Edg/')) return 'Edge';
    if (userAgent.includes('Chrome/')) return 'Chrome';
    if (userAgent.includes('Firefox/')) return 'Firefox';
    if (userAgent.includes('Safari/') && !userAgent.includes('Chrome/')) return 'Safari';
    if (userAgent.includes('Opera/') || userAgent.includes('OPR/')) return 'Opera';
    if (userAgent.includes('Trident/')) return 'Internet Explorer';
    
    return 'Unknown';
  },

  // Get browser version
  getVersion: (): string => {
    const userAgent = navigator.userAgent;
    const browserName = browser.getName();
    
    let versionRegex: RegExp;
    
    switch (browserName) {
      case 'Chrome':
        versionRegex = /Chrome\/(\d+\.\d+\.\d+\.\d+)/;
        break;
      case 'Firefox':
        versionRegex = /Firefox\/(\d+\.\d+)/;
        break;
      case 'Safari':
        versionRegex = /Version\/(\d+\.\d+)/;
        break;
      case 'Edge':
        versionRegex = /Edg\/(\d+\.\d+\.\d+\.\d+)/;
        break;
      case 'Opera':
        versionRegex = /(Opera|OPR)\/(\d+\.\d+)/;
        break;
      case 'Internet Explorer':
        versionRegex = /rv:(\d+\.\d+)/;
        break;
      default:
        return 'Unknown';
    }
    
    const match = userAgent.match(versionRegex);
    return match ? match[1] || match[2] : 'Unknown';
  },

  // Check if specific browser
  isChrome: (): boolean => browser.getName() === 'Chrome',
  isFirefox: (): boolean => browser.getName() === 'Firefox',
  isSafari: (): boolean => browser.getName() === 'Safari',
  isEdge: (): boolean => browser.getName() === 'Edge',
  isOpera: (): boolean => browser.getName() === 'Opera',
  isIE: (): boolean => browser.getName() === 'Internet Explorer',

  // Check if browser supports specific features
  supportsWebGL: (): boolean => {
    try {
      const canvas = document.createElement('canvas');
      return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
    } catch {
      return false;
    }
  },

  supportsWebGL2: (): boolean => {
    try {
      const canvas = document.createElement('canvas');
      return !!canvas.getContext('webgl2');
    } catch {
      return false;
    }
  },

  supportsWebRTC: (): boolean => {
    return !!(window.RTCPeerConnection || (window as unknown as { webkitRTCPeerConnection?: unknown }).webkitRTCPeerConnection || (window as unknown as { mozRTCPeerConnection?: unknown }).mozRTCPeerConnection);
  },

  supportsWebAssembly: (): boolean => {
    return typeof WebAssembly === 'object' && typeof WebAssembly.instantiate === 'function';
  },

  supportsServiceWorker: (): boolean => {
    return 'serviceWorker' in navigator;
  },

  supportsWebWorker: (): boolean => {
    return typeof Worker !== 'undefined';
  },

  supportsLocalStorage: (): boolean => {
    try {
      const test = 'test';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  },

  supportsSessionStorage: (): boolean => {
    try {
      const test = 'test';
      sessionStorage.setItem(test, test);
      sessionStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  },

  supportsIndexedDB: (): boolean => {
    return 'indexedDB' in window;
  },

  supportsWebCrypto: (): boolean => {
    return 'crypto' in window && 'subtle' in window.crypto;
  },

  supportsGeolocation: (): boolean => {
    return 'geolocation' in navigator;
  },

  supportsNotifications: (): boolean => {
    return 'Notification' in window;
  },

  supportsPushNotifications: (): boolean => {
    return 'PushManager' in window;
  },

  supportsClipboard: (): boolean => {
    return 'clipboard' in (navigator as unknown as Record<string, unknown>);
  },

  supportsShare: (): boolean => {
    return 'share' in (navigator as unknown as Record<string, unknown>);
  },

  supportsBluetooth: (): boolean => {
    return 'bluetooth' in (navigator as unknown as Record<string, unknown>);
  },

  supportsUSB: (): boolean => {
    return 'usb' in (navigator as unknown as Record<string, unknown>);
  },

  supportsGamepad: (): boolean => {
    return 'getGamepads' in (navigator as unknown as Record<string, unknown>);
  },

  supportsVibration: (): boolean => {
    return 'vibrate' in (navigator as unknown as Record<string, unknown>);
  },

  supportsBattery: (): boolean => {
    return 'getBattery' in (navigator as unknown as Record<string, unknown>);
  },

  supportsNetworkInformation: (): boolean => {
    return 'connection' in (navigator as unknown as Record<string, unknown>);
  },

  supportsDeviceMemory: (): boolean => {
    return 'deviceMemory' in (navigator as unknown as Record<string, unknown>);
  },

  supportsHardwareConcurrency: (): boolean => {
    return 'hardwareConcurrency' in (navigator as unknown as Record<string, unknown>);
  },
};

// Screen and viewport utilities
export const screen = {
  // Get screen dimensions
  getWidth: (): number => window.screen.width,
  getHeight: (): number => window.screen.height,
  getAvailableWidth: (): number => window.screen.availWidth,
  getAvailableHeight: (): number => window.screen.availHeight,
  getColorDepth: (): number => window.screen.colorDepth,
  getPixelDepth: (): number => window.screen.pixelDepth,

  // Get viewport dimensions
  getViewportWidth: (): number => window.innerWidth,
  getViewportHeight: (): number => window.innerHeight,

  // Get document dimensions
  getDocumentWidth: (): number => document.documentElement.scrollWidth,
  getDocumentHeight: (): number => document.documentElement.scrollHeight,

  // Get scroll position
  getScrollX: (): number => window.pageXOffset || document.documentElement.scrollLeft,
  getScrollY: (): number => window.pageYOffset || document.documentElement.scrollTop,

  // Check if element is in viewport
  isInViewport: (element: Element): boolean => {
    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= window.innerHeight &&
      rect.right <= window.innerWidth
    );
  },

  // Get element position relative to viewport
  getElementViewportPosition: (element: Element): {
    top: number;
    left: number;
    right: number;
    bottom: number;
    width: number;
    height: number;
  } => {
    const rect = element.getBoundingClientRect();
    return {
      top: rect.top,
      left: rect.left,
      right: rect.right,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height,
    };
  },

  // Get breakpoint based on viewport width
  getBreakpoint: (): 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' => {
    const width = screen.getViewportWidth();
    
    if (width < 640) return 'xs';
    if (width < 768) return 'sm';
    if (width < 1024) return 'md';
    if (width < 1280) return 'lg';
    if (width < 1536) return 'xl';
    return '2xl';
  },

  // Check if viewport matches breakpoint
  matchesBreakpoint: (breakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'): boolean => {
    return screen.getBreakpoint() === breakpoint;
  },

  // Check if viewport is at least a certain breakpoint
  isAtLeastBreakpoint: (breakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'): boolean => {
    const breakpoints = { xs: 0, sm: 640, md: 768, lg: 1024, xl: 1280, '2xl': 1536 };
    return screen.getViewportWidth() >= breakpoints[breakpoint];
  },
};

// Network utilities
export const network = {
  // Check if online
  isOnline: (): boolean => navigator.onLine,

  // Check if offline
  isOffline: (): boolean => !navigator.onLine,

  // Get connection information (if supported)
  getConnection: (): {
    effectiveType?: string;
    downlink?: number;
    rtt?: number;
    saveData?: boolean;
  } | null => {
    const connection = (navigator as unknown as { connection?: unknown; mozConnection?: unknown; webkitConnection?: unknown }).connection || (navigator as unknown as { connection?: unknown; mozConnection?: unknown; webkitConnection?: unknown }).mozConnection || (navigator as unknown as { connection?: unknown; mozConnection?: unknown; webkitConnection?: unknown }).webkitConnection;
    
    if (!connection) return null;
    
    const conn = connection as unknown as {
      effectiveType?: string;
      downlink?: number;
      rtt?: number;
      saveData?: boolean;
    };
    
    return {
      effectiveType: conn.effectiveType,
      downlink: conn.downlink,
      rtt: conn.rtt,
      saveData: conn.saveData,
    };
  },

  // Check if connection is slow
  isSlowConnection: (): boolean => {
    const connection = network.getConnection();
    if (!connection) return false;
    
    return connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g';
  },

  // Check if data saver is enabled
  isDataSaverEnabled: (): boolean => {
    const connection = network.getConnection();
    return connection?.saveData || false;
  },
};

// Hardware utilities
export const hardware = {
  // Get CPU cores count
  getCPUCores: (): number => {
    return navigator.hardwareConcurrency || 1;
  },

  // Get device memory (if supported)
  getDeviceMemory: (): number | null => {
    return (navigator as unknown as { deviceMemory?: number }).deviceMemory || null;
  },

  // Get battery information (if supported)
  getBattery: async (): Promise<{
    charging: boolean;
    level: number;
    chargingTime: number;
    dischargingTime: number;
  } | null> => {
    try {
      const battery = await (navigator as unknown as { getBattery?: () => Promise<unknown> }).getBattery?.();
      const batteryInfo = battery as unknown as {
        charging?: boolean;
        level?: number;
        chargingTime?: number;
        dischargingTime?: number;
      };
      
      return {
        charging: batteryInfo.charging || false,
        level: batteryInfo.level || 0,
        chargingTime: batteryInfo.chargingTime || 0,
        dischargingTime: batteryInfo.dischargingTime || 0,
      };
    } catch {
      return null;
    }
  },

  // Check if device has keyboard
  hasKeyboard: (): boolean => {
    return !device.isMobile() || device.isTablet();
  },

  // Check if device has mouse
  hasMouse: (): boolean => {
    return !device.isMobile();
  },

  // Check if device has camera
  hasCamera: async (): Promise<boolean> => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.some(device => device.kind === 'videoinput');
    } catch {
      return false;
    }
  },

  // Check if device has microphone
  hasMicrophone: async (): Promise<boolean> => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.some(device => device.kind === 'audioinput');
    } catch {
      return false;
    }
  },

  // Check if device has speakers
  hasSpeakers: async (): Promise<boolean> => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.some(device => device.kind === 'audiooutput');
    } catch {
      return false;
    }
  },
};

// Permissions utilities
export const permissions = {
  // Check permission status
  check: async (permission: PermissionName): Promise<PermissionState> => {
    try {
      const result = await navigator.permissions.query({ name: permission });
      return result.state;
    } catch {
      return 'denied';
    }
  },

  // Request notification permission
  requestNotification: async (): Promise<NotificationPermission> => {
    if (!browser.supportsNotifications()) {
      return 'denied';
    }
    
    return await Notification.requestPermission();
  },

  // Request geolocation permission
  requestGeolocation: (): Promise<GeolocationPosition> => {
    return new Promise((resolve, reject) => {
      if (!browser.supportsGeolocation()) {
        reject(new Error('Geolocation not supported'));
        return;
      }
      
      navigator.geolocation.getCurrentPosition(resolve, reject);
    });
  },

  // Request camera permission
  requestCamera: async (): Promise<MediaStream> => {
    try {
      return await navigator.mediaDevices.getUserMedia({ video: true });
    } catch {
      throw new Error('Camera access denied or not available');
    }
  },

  // Request microphone permission
  requestMicrophone: async (): Promise<MediaStream> => {
    try {
      return await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      throw new Error('Microphone access denied or not available');
    }
  },

  // Request both camera and microphone
  requestCameraAndMicrophone: async (): Promise<MediaStream> => {
    try {
      return await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    } catch {
      throw new Error('Camera and microphone access denied or not available');
    }
  },
};

// Device capabilities summary
export const capabilities = {
  // Get comprehensive device information
  getDeviceInfo: async (): Promise<{
    device: {
      type: string;
      os: string;
      isTouchDevice: boolean;
      pixelRatio: number;
      orientation: string;
    };
    browser: {
      name: string;
      version: string;
    };
    screen: {
      width: number;
      height: number;
      viewportWidth: number;
      viewportHeight: number;
      breakpoint: string;
    };
    network: {
      isOnline: boolean;
      connection: unknown;
    };
    hardware: {
      cpuCores: number;
      deviceMemory: number | null;
      hasCamera: boolean;
      hasMicrophone: boolean;
      hasSpeakers: boolean;
    };
    features: {
      webGL: boolean;
      webGL2: boolean;
      webRTC: boolean;
      webAssembly: boolean;
      serviceWorker: boolean;
      webWorker: boolean;
      localStorage: boolean;
      sessionStorage: boolean;
      indexedDB: boolean;
      webCrypto: boolean;
      geolocation: boolean;
      notifications: boolean;
      clipboard: boolean;
      share: boolean;
    };
  }> => {
    const [hasCamera, hasMicrophone, hasSpeakers] = await Promise.all([
      hardware.hasCamera(),
      hardware.hasMicrophone(),
      hardware.hasSpeakers(),
    ]);
    
    return {
      device: {
        type: device.getType(),
        os: device.getOS(),
        isTouchDevice: device.isTouchDevice(),
        pixelRatio: device.getPixelRatio(),
        orientation: device.getOrientation(),
      },
      browser: {
        name: browser.getName(),
        version: browser.getVersion(),
      },
      screen: {
        width: screen.getWidth(),
        height: screen.getHeight(),
        viewportWidth: screen.getViewportWidth(),
        viewportHeight: screen.getViewportHeight(),
        breakpoint: screen.getBreakpoint(),
      },
      network: {
        isOnline: network.isOnline(),
        connection: network.getConnection(),
      },
      hardware: {
        cpuCores: hardware.getCPUCores(),
        deviceMemory: hardware.getDeviceMemory(),
        hasCamera,
        hasMicrophone,
        hasSpeakers,
      },
      features: {
        webGL: browser.supportsWebGL(),
        webGL2: browser.supportsWebGL2(),
        webRTC: browser.supportsWebRTC(),
        webAssembly: browser.supportsWebAssembly(),
        serviceWorker: browser.supportsServiceWorker(),
        webWorker: browser.supportsWebWorker(),
        localStorage: browser.supportsLocalStorage(),
        sessionStorage: browser.supportsSessionStorage(),
        indexedDB: browser.supportsIndexedDB(),
        webCrypto: browser.supportsWebCrypto(),
        geolocation: browser.supportsGeolocation(),
        notifications: browser.supportsNotifications(),
        clipboard: browser.supportsClipboard(),
        share: browser.supportsShare(),
      },
    };
  },

  // Check if device meets minimum requirements
  meetsMinimumRequirements: (requirements: {
    minViewportWidth?: number;
    minViewportHeight?: number;
    requiresLocalStorage?: boolean;
    requiresWebGL?: boolean;
    requiresWebRTC?: boolean;
    requiresServiceWorker?: boolean;
    requiresNotifications?: boolean;
    requiresGeolocation?: boolean;
  }): boolean => {
    const {
      minViewportWidth,
      minViewportHeight,
      requiresLocalStorage,
      requiresWebGL,
      requiresWebRTC,
      requiresServiceWorker,
      requiresNotifications,
      requiresGeolocation,
    } = requirements;
    
    if (minViewportWidth && screen.getViewportWidth() < minViewportWidth) return false;
    if (minViewportHeight && screen.getViewportHeight() < minViewportHeight) return false;
    if (requiresLocalStorage && !browser.supportsLocalStorage()) return false;
    if (requiresWebGL && !browser.supportsWebGL()) return false;
    if (requiresWebRTC && !browser.supportsWebRTC()) return false;
    if (requiresServiceWorker && !browser.supportsServiceWorker()) return false;
    if (requiresNotifications && !browser.supportsNotifications()) return false;
    if (requiresGeolocation && !browser.supportsGeolocation()) return false;
    
    return true;
  },
};
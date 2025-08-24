// Crypto utilities for client-side encryption and hashing

// Base64 encoding/decoding
export const base64 = {
  // Encode string to base64
  encode: (str: string): string => {
    try {
      return btoa(unescape(encodeURIComponent(str)));
    } catch (error) {
      console.error('Base64 encoding error:', error);
      return '';
    }
  },

  // Decode base64 to string
  decode: (base64Str: string): string => {
    try {
      return decodeURIComponent(escape(atob(base64Str)));
    } catch (error) {
      console.error('Base64 decoding error:', error);
      return '';
    }
  },

  // Encode ArrayBuffer to base64
  encodeArrayBuffer: (buffer: ArrayBuffer): string => {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  },

  // Decode base64 to ArrayBuffer
  decodeToArrayBuffer: (base64Str: string): ArrayBuffer => {
    const binary = atob(base64Str);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  },

  // Check if string is valid base64
  isValid: (str: string): boolean => {
    try {
      return btoa(atob(str)) === str;
    } catch {
      return false;
    }
  },
};

// URL-safe base64 encoding
export const base64Url = {
  // Encode to URL-safe base64
  encode: (str: string): string => {
    return base64.encode(str)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  },

  // Decode from URL-safe base64
  decode: (str: string): string => {
    // Add padding if needed
    let padded = str;
    while (padded.length % 4) {
      padded += '=';
    }
    
    // Replace URL-safe characters
    const base64Str = padded
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    return base64.decode(base64Str);
  },
};

// Simple hash functions (not cryptographically secure)
export const hash = {
  // Simple string hash (djb2 algorithm)
  djb2: (str: string): number => {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) + hash) + str.charCodeAt(i);
    }
    return hash >>> 0; // Convert to unsigned 32-bit integer
  },

  // FNV-1a hash
  fnv1a: (str: string): number => {
    let hash = 2166136261;
    for (let i = 0; i < str.length; i++) {
      hash ^= str.charCodeAt(i);
      hash *= 16777619;
    }
    return hash >>> 0;
  },

  // Simple checksum
  checksum: (str: string): number => {
    let sum = 0;
    for (let i = 0; i < str.length; i++) {
      sum += str.charCodeAt(i);
    }
    return sum;
  },

  // Generate hash string
  hashString: (str: string, algorithm: 'djb2' | 'fnv1a' = 'djb2'): string => {
    const hashValue = algorithm === 'djb2' ? hash.djb2(str) : hash.fnv1a(str);
    return hashValue.toString(16);
  },
};

// Web Crypto API utilities (modern browsers)
export const webCrypto = {
  // Check if Web Crypto API is available
  isSupported: (): boolean => {
    return typeof window !== 'undefined' && 'crypto' in window && 'subtle' in window.crypto;
  },

  // Generate random bytes
  randomBytes: (length: number): Uint8Array => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    return window.crypto.getRandomValues(new Uint8Array(length));
  },

  // Generate random UUID
  randomUUID: (): string => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    
    if ('randomUUID' in window.crypto) {
      return window.crypto.randomUUID();
    }
    
    // Fallback implementation
    const bytes = webCrypto.randomBytes(16);
    bytes[6] = (bytes[6] & 0x0f) | 0x40; // Version 4
    bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant 10
    
    const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
    return [
      hex.slice(0, 8),
      hex.slice(8, 12),
      hex.slice(12, 16),
      hex.slice(16, 20),
      hex.slice(20, 32)
    ].join('-');
  },

  // SHA-256 hash
  sha256: async (data: string | ArrayBuffer): Promise<string> => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    
    const encoder = new TextEncoder();
    const dataBuffer = typeof data === 'string' ? encoder.encode(data) : data;
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', dataBuffer);
    
    return Array.from(new Uint8Array(hashBuffer))
      .map(byte => byte.toString(16).padStart(2, '0'))
      .join('');
  },

  // SHA-1 hash (deprecated, use SHA-256 instead)
  sha1: async (data: string | ArrayBuffer): Promise<string> => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    
    const encoder = new TextEncoder();
    const dataBuffer = typeof data === 'string' ? encoder.encode(data) : data;
    const hashBuffer = await window.crypto.subtle.digest('SHA-1', dataBuffer);
    
    return Array.from(new Uint8Array(hashBuffer))
      .map(byte => byte.toString(16).padStart(2, '0'))
      .join('');
  },

  // Generate key pair for RSA
  generateRSAKeyPair: async (keySize: number = 2048): Promise<CryptoKeyPair> => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    
    return await window.crypto.subtle.generateKey(
      {
        name: 'RSA-OAEP',
        modulusLength: keySize,
        publicExponent: new Uint8Array([1, 0, 1]),
        hash: 'SHA-256',
      },
      true,
      ['encrypt', 'decrypt']
    );
  },

  // Generate AES key
  generateAESKey: async (keySize: number = 256): Promise<CryptoKey> => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    
    return await window.crypto.subtle.generateKey(
      {
        name: 'AES-GCM',
        length: keySize,
      },
      true,
      ['encrypt', 'decrypt']
    );
  },

  // Encrypt data with AES-GCM
  encryptAES: async (data: string, key: CryptoKey): Promise<{ encrypted: ArrayBuffer; iv: Uint8Array }> => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    
    const encoder = new TextEncoder();
    const iv = webCrypto.randomBytes(12); // 96-bit IV for GCM
    const dataBuffer = encoder.encode(data);
    
    const encrypted = await window.crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv,
      },
      key,
      dataBuffer
    );
    
    return { encrypted, iv };
  },

  // Decrypt data with AES-GCM
  decryptAES: async (encryptedData: ArrayBuffer, key: CryptoKey, iv: Uint8Array): Promise<string> => {
    if (!webCrypto.isSupported()) {
      throw new Error('Web Crypto API not supported');
    }
    
    const decrypted = await window.crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv,
      },
      key,
      encryptedData
    );
    
    const decoder = new TextDecoder();
    return decoder.decode(decrypted);
  },
};

// JWT utilities (basic parsing, not for verification)
export const jwt = {
  // Parse JWT token (header and payload only)
  parse: (token: string): { header: Record<string, unknown>; payload: Record<string, unknown>; signature: string } | null => {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return null;
      }
      
      const [headerB64, payloadB64, signature] = parts;
      
      const header = JSON.parse(base64Url.decode(headerB64));
      const payload = JSON.parse(base64Url.decode(payloadB64));
      
      return { header, payload, signature };
    } catch {
      return null;
    }
  },

  // Check if JWT is expired
  isExpired: (token: string): boolean => {
    const parsed = jwt.parse(token);
    if (!parsed || !parsed.payload.exp) {
      return true;
    }
    
    const exp = typeof parsed.payload.exp === 'number' ? parsed.payload.exp : Number(parsed.payload.exp);
    if (isNaN(exp)) return true;
    
    const now = Math.floor(Date.now() / 1000);
    return exp < now;
  },

  // Get JWT expiration date
  getExpirationDate: (token: string): Date | null => {
    const parsed = jwt.parse(token);
    if (!parsed || !parsed.payload.exp) {
      return null;
    }
    
    const exp = typeof parsed.payload.exp === 'number' ? parsed.payload.exp : Number(parsed.payload.exp);
    if (isNaN(exp)) return null;
    
    return new Date(exp * 1000);
  },

  // Get time until expiration in seconds
  getTimeUntilExpiration: (token: string): number => {
    const parsed = jwt.parse(token);
    if (!parsed || !parsed.payload.exp) {
      return 0;
    }
    
    const exp = typeof parsed.payload.exp === 'number' ? parsed.payload.exp : Number(parsed.payload.exp);
    if (isNaN(exp)) return 0;
    
    const now = Math.floor(Date.now() / 1000);
    return Math.max(0, exp - now);
  },
};

// Password utilities
export const password = {
  // Generate random password
  generate: (length: number = 12, options: {
    includeUppercase?: boolean;
    includeLowercase?: boolean;
    includeNumbers?: boolean;
    includeSymbols?: boolean;
    excludeSimilar?: boolean;
  } = {}): string => {
    const {
      includeUppercase = true,
      includeLowercase = true,
      includeNumbers = true,
      includeSymbols = false,
      excludeSimilar = false,
    } = options;
    
    let chars = '';
    
    if (includeUppercase) {
      chars += excludeSimilar ? 'ABCDEFGHJKLMNPQRSTUVWXYZ' : 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    }
    
    if (includeLowercase) {
      chars += excludeSimilar ? 'abcdefghjkmnpqrstuvwxyz' : 'abcdefghijklmnopqrstuvwxyz';
    }
    
    if (includeNumbers) {
      chars += excludeSimilar ? '23456789' : '0123456789';
    }
    
    if (includeSymbols) {
      chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';
    }
    
    if (!chars) {
      throw new Error('At least one character type must be included');
    }
    
    let password = '';
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * chars.length);
      password += chars[randomIndex];
    }
    
    return password;
  },

  // Calculate password strength (0-4)
  getStrength: (password: string): {
    score: number;
    feedback: string[];
    isStrong: boolean;
  } => {
    const feedback: string[] = [];
    let score = 0;
    
    // Length check
    if (password.length >= 8) {
      score++;
    } else {
      feedback.push('Use at least 8 characters');
    }
    
    // Uppercase check
    if (/[A-Z]/.test(password)) {
      score++;
    } else {
      feedback.push('Include uppercase letters');
    }
    
    // Lowercase check
    if (/[a-z]/.test(password)) {
      score++;
    } else {
      feedback.push('Include lowercase letters');
    }
    
    // Number check
    if (/\d/.test(password)) {
      score++;
    } else {
      feedback.push('Include numbers');
    }
    
    // Symbol check
    if (/[^\w\s]/.test(password)) {
      score++;
    } else {
      feedback.push('Include special characters');
    }
    
    // Additional checks
    if (password.length >= 12) {
      score += 0.5;
    }
    
    // Penalize common patterns
    if (/123|abc|qwe|password|admin/i.test(password)) {
      score -= 1;
      feedback.push('Avoid common patterns');
    }
    
    const finalScore = Math.max(0, Math.min(4, Math.floor(score)));
    const isStrong = finalScore >= 3;
    
    return {
      score: finalScore,
      feedback,
      isStrong,
    };
  },
};

// Secure random utilities
export const random = {
  // Generate secure random string
  string: (length: number, charset: string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'): string => {
    if (webCrypto.isSupported()) {
      const bytes = webCrypto.randomBytes(length);
      return Array.from(bytes, byte => charset[byte % charset.length]).join('');
    }
    
    // Fallback to Math.random (less secure)
    let result = '';
    for (let i = 0; i < length; i++) {
      result += charset[Math.floor(Math.random() * charset.length)];
    }
    return result;
  },

  // Generate secure random number
  number: (min: number = 0, max: number = 1): number => {
    if (webCrypto.isSupported()) {
      const range = max - min;
      const bytes = webCrypto.randomBytes(4);
      const randomValue = new DataView(bytes.buffer).getUint32(0, true) / (0xFFFFFFFF + 1);
      return min + (randomValue * range);
    }
    
    // Fallback to Math.random
    return Math.random() * (max - min) + min;
  },

  // Generate secure random integer
  integer: (min: number = 0, max: number = 100): number => {
    return Math.floor(random.number(min, max + 1));
  },

  // Generate secure random boolean
  boolean: (): boolean => {
    return random.integer(0, 1) === 1;
  },

  // Pick random element from array
  pick: <T>(array: T[]): T => {
    const index = random.integer(0, array.length - 1);
    return array[index];
  },

  // Shuffle array securely
  shuffle: <T>(array: T[]): T[] => {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = random.integer(0, i);
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  },
};
// Number formatting utilities
export const formatNumber = (
  value: number,
  options: Intl.NumberFormatOptions = {}
): string => {
  return new Intl.NumberFormat('en-US', options).format(value);
};

// Format currency
export const formatCurrency = (
  value: number,
  currency: string = 'USD',
  locale: string = 'en-US'
): string => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(value);
};

// Format percentage
export const formatPercentage = (
  value: number,
  decimals: number = 2
): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value / 100);
};

// Format large numbers with suffixes (K, M, B)
export const formatLargeNumber = (value: number): string => {
  const suffixes = ['', 'K', 'M', 'B', 'T'];
  let suffixIndex = 0;
  let formattedValue = value;

  while (formattedValue >= 1000 && suffixIndex < suffixes.length - 1) {
    formattedValue /= 1000;
    suffixIndex++;
  }

  const decimals = formattedValue < 10 && suffixIndex > 0 ? 1 : 0;
  return `${formattedValue.toFixed(decimals)}${suffixes[suffixIndex]}`;
};

// Format phone number
export const formatPhoneNumber = (phoneNumber: string): string => {
  const cleaned = phoneNumber.replace(/\D/g, '');
  
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  } else if (cleaned.length === 11 && cleaned[0] === '1') {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  
  return phoneNumber;
};

// Format credit card number
export const formatCreditCard = (cardNumber: string): string => {
  const cleaned = cardNumber.replace(/\D/g, '');
  return cleaned.replace(/(\d{4})(?=\d)/g, '$1 ');
};

// Format social security number
export const formatSSN = (ssn: string): string => {
  const cleaned = ssn.replace(/\D/g, '');
  if (cleaned.length === 9) {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 5)}-${cleaned.slice(5)}`;
  }
  return ssn;
};

// Format postal code
export const formatPostalCode = (postalCode: string, country: string = 'US'): string => {
  const cleaned = postalCode.replace(/\D/g, '');
  
  switch (country.toUpperCase()) {
    case 'US':
      if (cleaned.length === 5) {
        return cleaned;
      } else if (cleaned.length === 9) {
        return `${cleaned.slice(0, 5)}-${cleaned.slice(5)}`;
      }
      break;
    case 'CA':
      if (cleaned.length === 6) {
        return `${cleaned.slice(0, 3)} ${cleaned.slice(3)}`;
      }
      break;
  }
  
  return postalCode;
};

// Format text to title case
export const toTitleCase = (text: string): string => {
  return text.replace(/\w\S*/g, (txt) => 
    txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
  );
};

// Format text to sentence case
export const toSentenceCase = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

// Format name (proper case)
export const formatName = (name: string): string => {
  return name
    .split(' ')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ');
};

// Format address
export const formatAddress = (address: {
  street?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}): string => {
  const parts = [];
  
  if (address.street) parts.push(address.street);
  if (address.city) parts.push(address.city);
  if (address.state) parts.push(address.state);
  if (address.postalCode) parts.push(address.postalCode);
  if (address.country) parts.push(address.country);
  
  return parts.join(', ');
};

// Format email (mask for privacy)
export const maskEmail = (email: string): string => {
  const [username, domain] = email.split('@');
  if (!username || !domain) return email;
  
  const maskedUsername = username.length > 2 
    ? username[0] + '*'.repeat(username.length - 2) + username[username.length - 1]
    : username;
  
  return `${maskedUsername}@${domain}`;
};

// Format phone number (mask for privacy)
export const maskPhoneNumber = (phoneNumber: string): string => {
  const cleaned = phoneNumber.replace(/\D/g, '');
  if (cleaned.length >= 10) {
    const lastFour = cleaned.slice(-4);
    const masked = '*'.repeat(cleaned.length - 4) + lastFour;
    return formatPhoneNumber(masked);
  }
  return phoneNumber;
};

// Format credit card (mask for privacy)
export const maskCreditCard = (cardNumber: string): string => {
  const cleaned = cardNumber.replace(/\D/g, '');
  if (cleaned.length >= 4) {
    const lastFour = cleaned.slice(-4);
    const masked = '*'.repeat(cleaned.length - 4) + lastFour;
    return formatCreditCard(masked);
  }
  return cardNumber;
};

// Format bytes to human readable
export const formatBytes = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

// Format duration in milliseconds
export const formatDuration = (ms: number): string => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
};

// Format list with proper conjunctions
export const formatList = (
  items: string[],
  conjunction: 'and' | 'or' = 'and'
): string => {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} ${conjunction} ${items[1]}`;
  
  const lastItem = items[items.length - 1];
  const otherItems = items.slice(0, -1);
  
  return `${otherItems.join(', ')}, ${conjunction} ${lastItem}`;
};

// Format JSON for display
export const formatJSON = (obj: unknown, indent: number = 2): string => {
  try {
    return JSON.stringify(obj, null, indent);
  } catch {
    return String(obj);
  }
};

// Format error message
export const formatError = (error: unknown): string => {
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object') {
    const errorObj = error as Record<string, unknown>;
    if (typeof errorObj.message === 'string') return errorObj.message;
    if (typeof errorObj.error === 'string') return errorObj.error;
  }
  return 'An unknown error occurred';
};

// Format validation errors
export const formatValidationErrors = (errors: Record<string, string[]>): string => {
  const messages: string[] = [];
  
  Object.entries(errors).forEach(([field, fieldErrors]) => {
    const fieldName = toTitleCase(field.replace(/[_-]/g, ' '));
    fieldErrors.forEach(error => {
      messages.push(`${fieldName}: ${error}`);
    });
  });
  
  return messages.join('; ');
};

// Format URL for display (remove protocol, www)
export const formatDisplayUrl = (url: string): string => {
  try {
    const urlObj = new URL(url);
    let hostname = urlObj.hostname;
    
    if (hostname.startsWith('www.')) {
      hostname = hostname.slice(4);
    }
    
    return hostname + urlObj.pathname + urlObj.search;
  } catch {
    return url;
  }
};

// Format initials from name
export const getInitials = (name: string, maxInitials: number = 2): string => {
  return name
    .split(' ')
    .filter(part => part.length > 0)
    .slice(0, maxInitials)
    .map(part => part[0].toUpperCase())
    .join('');
};

// Format file size with progress
export const formatFileProgress = (loaded: number, total: number): string => {
  const percentage = Math.round((loaded / total) * 100);
  return `${formatBytes(loaded)} / ${formatBytes(total)} (${percentage}%)`;
};

// Format search query highlight
export const highlightSearchTerm = (text: string, searchTerm: string): string => {
  if (!searchTerm.trim()) return text;
  
  const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
};

// Format truncated text with tooltip
export const formatTruncatedText = (
  text: string,
  maxLength: number,
  suffix: string = '...'
): { display: string; isTruncated: boolean } => {
  if (text.length <= maxLength) {
    return { display: text, isTruncated: false };
  }
  
  return {
    display: text.slice(0, maxLength - suffix.length) + suffix,
    isTruncated: true,
  };
};

// Format API response for logging
export const formatApiResponse = (response: unknown): string => {
  if (response && typeof response === 'object') {
    const responseObj = response as Record<string, unknown>;
    const status = responseObj.status;
    const statusText = responseObj.statusText;
    const config = responseObj.config as Record<string, unknown> | undefined;
    return `${config?.method?.toString().toUpperCase() || 'UNKNOWN'} ${config?.url?.toString() || 'UNKNOWN'} - ${status} ${statusText}`;
  }
  return 'Invalid response format';
};
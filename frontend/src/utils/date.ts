import { DATE_FORMATS } from './constants';

// Date formatting utilities
export const formatDate = (
  date: string | Date | number,
  format: string = DATE_FORMATS.DISPLAY_DATE
): string => {
  const dateObj = new Date(date);
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date';
  }

  switch (format) {
    case DATE_FORMATS.ISO:
      return dateObj.toISOString();
    
    case DATE_FORMATS.DATE:
      return dateObj.toISOString().split('T')[0];
    
    case DATE_FORMATS.TIME:
      return dateObj.toTimeString().split(' ')[0];
    
    case DATE_FORMATS.DATETIME:
      return dateObj.toISOString().replace('T', ' ').split('.')[0];
    
    case DATE_FORMATS.DISPLAY_DATE:
      return dateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
      });
    
    case DATE_FORMATS.DISPLAY_DATETIME:
      return dateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    
    case DATE_FORMATS.RELATIVE:
      return getRelativeTime(dateObj);
    
    default:
      return dateObj.toLocaleDateString();
  }
};

// Get relative time (e.g., "2 hours ago", "in 3 days")
export const getRelativeTime = (date: string | Date | number): string => {
  const dateObj = new Date(date);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);
  
  const intervals = [
    { label: 'year', seconds: 31536000 },
    { label: 'month', seconds: 2592000 },
    { label: 'week', seconds: 604800 },
    { label: 'day', seconds: 86400 },
    { label: 'hour', seconds: 3600 },
    { label: 'minute', seconds: 60 },
    { label: 'second', seconds: 1 },
  ];
  
  if (diffInSeconds === 0) {
    return 'just now';
  }
  
  const isPast = diffInSeconds > 0;
  const absDiff = Math.abs(diffInSeconds);
  
  for (const interval of intervals) {
    const count = Math.floor(absDiff / interval.seconds);
    if (count >= 1) {
      const suffix = count === 1 ? '' : 's';
      const timeString = `${count} ${interval.label}${suffix}`;
      return isPast ? `${timeString} ago` : `in ${timeString}`;
    }
  }
  
  return 'just now';
};

// Check if date is today
export const isToday = (date: string | Date | number): boolean => {
  const dateObj = new Date(date);
  const today = new Date();
  
  return (
    dateObj.getDate() === today.getDate() &&
    dateObj.getMonth() === today.getMonth() &&
    dateObj.getFullYear() === today.getFullYear()
  );
};

// Check if date is yesterday
export const isYesterday = (date: string | Date | number): boolean => {
  const dateObj = new Date(date);
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  
  return (
    dateObj.getDate() === yesterday.getDate() &&
    dateObj.getMonth() === yesterday.getMonth() &&
    dateObj.getFullYear() === yesterday.getFullYear()
  );
};

// Check if date is this week
export const isThisWeek = (date: string | Date | number): boolean => {
  const dateObj = new Date(date);
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay());
  startOfWeek.setHours(0, 0, 0, 0);
  
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  endOfWeek.setHours(23, 59, 59, 999);
  
  return dateObj >= startOfWeek && dateObj <= endOfWeek;
};

// Check if date is this month
export const isThisMonth = (date: string | Date | number): boolean => {
  const dateObj = new Date(date);
  const today = new Date();
  
  return (
    dateObj.getMonth() === today.getMonth() &&
    dateObj.getFullYear() === today.getFullYear()
  );
};

// Check if date is this year
export const isThisYear = (date: string | Date | number): boolean => {
  const dateObj = new Date(date);
  const today = new Date();
  
  return dateObj.getFullYear() === today.getFullYear();
};

// Get start of day
export const startOfDay = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  dateObj.setHours(0, 0, 0, 0);
  return dateObj;
};

// Get end of day
export const endOfDay = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  dateObj.setHours(23, 59, 59, 999);
  return dateObj;
};

// Get start of week
export const startOfWeek = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  const day = dateObj.getDay();
  const diff = dateObj.getDate() - day;
  const startDate = new Date(dateObj.setDate(diff));
  startDate.setHours(0, 0, 0, 0);
  return startDate;
};

// Get end of week
export const endOfWeek = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  const day = dateObj.getDay();
  const diff = dateObj.getDate() - day + 6;
  const endDate = new Date(dateObj.setDate(diff));
  endDate.setHours(23, 59, 59, 999);
  return endDate;
};

// Get start of month
export const startOfMonth = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  return new Date(dateObj.getFullYear(), dateObj.getMonth(), 1, 0, 0, 0, 0);
};

// Get end of month
export const endOfMonth = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  return new Date(dateObj.getFullYear(), dateObj.getMonth() + 1, 0, 23, 59, 59, 999);
};

// Add days to date
export const addDays = (date: string | Date | number, days: number): Date => {
  const dateObj = new Date(date);
  dateObj.setDate(dateObj.getDate() + days);
  return dateObj;
};

// Add hours to date
export const addHours = (date: string | Date | number, hours: number): Date => {
  const dateObj = new Date(date);
  dateObj.setHours(dateObj.getHours() + hours);
  return dateObj;
};

// Add minutes to date
export const addMinutes = (date: string | Date | number, minutes: number): Date => {
  const dateObj = new Date(date);
  dateObj.setMinutes(dateObj.getMinutes() + minutes);
  return dateObj;
};

// Get difference in days
export const getDaysDifference = (
  date1: string | Date | number,
  date2: string | Date | number
): number => {
  const dateObj1 = new Date(date1);
  const dateObj2 = new Date(date2);
  const diffTime = Math.abs(dateObj2.getTime() - dateObj1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

// Get difference in hours
export const getHoursDifference = (
  date1: string | Date | number,
  date2: string | Date | number
): number => {
  const dateObj1 = new Date(date1);
  const dateObj2 = new Date(date2);
  const diffTime = Math.abs(dateObj2.getTime() - dateObj1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60));
};

// Get difference in minutes
export const getMinutesDifference = (
  date1: string | Date | number,
  date2: string | Date | number
): number => {
  const dateObj1 = new Date(date1);
  const dateObj2 = new Date(date2);
  const diffTime = Math.abs(dateObj2.getTime() - dateObj1.getTime());
  return Math.ceil(diffTime / (1000 * 60));
};

// Check if date is valid
export const isValidDate = (date: unknown): boolean => {
  return date instanceof Date && !isNaN(date.getTime());
};

// Parse date string
export const parseDate = (dateString: string): Date | null => {
  const date = new Date(dateString);
  return isValidDate(date) ? date : null;
};

// Get timezone offset
export const getTimezoneOffset = (): number => {
  return new Date().getTimezoneOffset();
};

// Convert to UTC
export const toUTC = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  return new Date(dateObj.getTime() + dateObj.getTimezoneOffset() * 60000);
};

// Convert from UTC
export const fromUTC = (date: string | Date | number): Date => {
  const dateObj = new Date(date);
  return new Date(dateObj.getTime() - dateObj.getTimezoneOffset() * 60000);
};

// Get age from birth date
export const getAge = (birthDate: string | Date | number): number => {
  const birth = new Date(birthDate);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  return age;
};

// Format duration (in milliseconds) to human readable
export const formatDuration = (duration: number): string => {
  const seconds = Math.floor(duration / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
};

// Get business days between two dates
export const getBusinessDays = (
  startDate: string | Date | number,
  endDate: string | Date | number
): number => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  let count = 0;
  const current = new Date(start);
  
  while (current <= end) {
    const dayOfWeek = current.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) { // Not Sunday (0) or Saturday (6)
      count++;
    }
    current.setDate(current.getDate() + 1);
  }
  
  return count;
};
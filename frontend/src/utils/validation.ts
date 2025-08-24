import { VALIDATION } from './constants';

// Validation result interface
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Field validation result
export interface FieldValidationResult {
  isValid: boolean;
  error?: string;
}

// Validation rule type
export type ValidationRule<T = unknown> = (value: T) => FieldValidationResult;

// Common validation rules
export const validationRules = {
  // Required field validation
  required: (message = 'This field is required'): ValidationRule => {
    return (value: unknown) => {
      const isEmpty = value === null || value === undefined || 
                     (typeof value === 'string' && value.trim() === '') ||
                     (Array.isArray(value) && value.length === 0);
      
      return {
        isValid: !isEmpty,
        error: isEmpty ? message : undefined,
      };
    };
  },

  // Minimum length validation
  minLength: (min: number, message?: string): ValidationRule<string> => {
    return (value: string) => {
      const isValid = !value || value.length >= min;
      return {
        isValid,
        error: isValid ? undefined : (message || `Must be at least ${min} characters long`),
      };
    };
  },

  // Maximum length validation
  maxLength: (max: number, message?: string): ValidationRule<string> => {
    return (value: string) => {
      const isValid = !value || value.length <= max;
      return {
        isValid,
        error: isValid ? undefined : (message || `Must be no more than ${max} characters long`),
      };
    };
  },

  // Email validation
  email: (message = 'Please enter a valid email address'): ValidationRule<string> => {
    return (value: string) => {
      const isValid = !value || VALIDATION.EMAIL_REGEX.test(value);
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    };
  },

  // Password validation
  password: (message = 'Password must contain at least 8 characters with uppercase, lowercase, number, and special character'): ValidationRule<string> => {
    return (value: string) => {
      const isValid = !value || (value.length >= VALIDATION.PASSWORD_MIN_LENGTH && VALIDATION.PASSWORD_REGEX.test(value));
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    };
  },

  // Phone number validation
  phone: (message = 'Please enter a valid phone number'): ValidationRule<string> => {
    return (value: string) => {
      const isValid = !value || VALIDATION.PHONE_REGEX.test(value.replace(/\D/g, ''));
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    };
  },

  // URL validation
  url: (message = 'Please enter a valid URL'): ValidationRule<string> => {
    return (value: string) => {
      if (!value) return { isValid: true };
      
      try {
        new URL(value);
        return { isValid: true };
      } catch {
        return { isValid: false, error: message };
      }
    };
  },

  // Number validation
  number: (message = 'Please enter a valid number'): ValidationRule<string | number> => {
    return (value: string | number) => {
      if (value === '' || value === null || value === undefined) {
        return { isValid: true };
      }
      
      const isValid = !isNaN(Number(value));
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    };
  },

  // Minimum value validation
  min: (min: number, message?: string): ValidationRule<number> => {
    return (value: number) => {
      const isValid = value === null || value === undefined || value >= min;
      return {
        isValid,
        error: isValid ? undefined : (message || `Must be at least ${min}`),
      };
    };
  },

  // Maximum value validation
  max: (max: number, message?: string): ValidationRule<number> => {
    return (value: number) => {
      const isValid = value === null || value === undefined || value <= max;
      return {
        isValid,
        error: isValid ? undefined : (message || `Must be no more than ${max}`),
      };
    };
  },

  // Pattern validation
  pattern: (regex: RegExp, message = 'Invalid format'): ValidationRule<string> => {
    return (value: string) => {
      const isValid = !value || regex.test(value);
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    };
  },

  // Confirmation field validation (e.g., password confirmation)
  confirmation: (originalValue: unknown, message = 'Values do not match'): ValidationRule => {
    return (value: unknown) => {
      const isValid = value === originalValue;
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    };
  },

  // Custom validation
  custom: (validator: (value: unknown) => boolean, message: string): ValidationRule => {
    return (value: unknown) => {
      const isValid = validator(value);
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    };
  },
};

// Validate single field with multiple rules
export const validateField = (value: unknown, rules: ValidationRule[]): FieldValidationResult => {
  for (const rule of rules) {
    const result = rule(value);
    if (!result.isValid) {
      return result;
    }
  }
  return { isValid: true };
};

// Validate form with schema
export const validateForm = <T extends Record<string, unknown>>(
  data: T,
  schema: Record<keyof T, ValidationRule[]>
): ValidationResult & { fieldErrors: Record<keyof T, string> } => {
  const errors: string[] = [];
  const fieldErrors: Record<keyof T, string> = {} as Record<keyof T, string>;
  
  Object.keys(schema).forEach(field => {
    const fieldKey = field as keyof T;
    const rules = schema[fieldKey];
    const value = data[fieldKey];
    
    const result = validateField(value, rules);
    if (!result.isValid && result.error) {
      errors.push(`${String(field)}: ${result.error}`);
      fieldErrors[fieldKey] = result.error;
    }
  });
  
  return {
    isValid: errors.length === 0,
    errors,
    fieldErrors,
  };
};

// Specific validation functions
export const validators = {
  // Email validation
  isValidEmail: (email: string): boolean => {
    return VALIDATION.EMAIL_REGEX.test(email);
  },

  // Password strength validation
  isStrongPassword: (password: string): boolean => {
    return password.length >= VALIDATION.PASSWORD_MIN_LENGTH && 
           VALIDATION.PASSWORD_REGEX.test(password);
  },

  // Phone number validation
  isValidPhone: (phone: string): boolean => {
    const cleaned = phone.replace(/\D/g, '');
    return VALIDATION.PHONE_REGEX.test(cleaned);
  },

  // Name validation
  isValidName: (name: string): boolean => {
    return name.length >= VALIDATION.NAME_MIN_LENGTH && 
           name.length <= VALIDATION.NAME_MAX_LENGTH &&
           /^[a-zA-Z\s'-]+$/.test(name);
  },

  // Credit card validation (Luhn algorithm)
  isValidCreditCard: (cardNumber: string): boolean => {
    const cleaned = cardNumber.replace(/\D/g, '');
    if (cleaned.length < 13 || cleaned.length > 19) return false;
    
    let sum = 0;
    let isEven = false;
    
    for (let i = cleaned.length - 1; i >= 0; i--) {
      let digit = parseInt(cleaned[i]);
      
      if (isEven) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }
      
      sum += digit;
      isEven = !isEven;
    }
    
    return sum % 10 === 0;
  },

  // Date validation
  isValidDate: (date: string): boolean => {
    const parsed = new Date(date);
    return !isNaN(parsed.getTime());
  },

  // Age validation
  isValidAge: (birthDate: string, minAge = 0, maxAge = 150): boolean => {
    const birth = new Date(birthDate);
    const today = new Date();
    const age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    const actualAge = monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate()) 
      ? age - 1 
      : age;
    
    return actualAge >= minAge && actualAge <= maxAge;
  },

  // File validation
  isValidFile: (file: File, allowedTypes: string[], maxSize: number): boolean => {
    return allowedTypes.includes(file.type) && file.size <= maxSize;
  },

  // JSON validation
  isValidJSON: (jsonString: string): boolean => {
    try {
      JSON.parse(jsonString);
      return true;
    } catch {
      return false;
    }
  },

  // IP address validation
  isValidIP: (ip: string): boolean => {
    const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
    return ipv4Regex.test(ip) || ipv6Regex.test(ip);
  },

  // MAC address validation
  isValidMAC: (mac: string): boolean => {
    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
    return macRegex.test(mac);
  },

  // Hex color validation
  isValidHexColor: (color: string): boolean => {
    const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
    return hexRegex.test(color);
  },

  // Username validation
  isValidUsername: (username: string): boolean => {
    const usernameRegex = /^[a-zA-Z0-9_-]{3,20}$/;
    return usernameRegex.test(username);
  },

  // Slug validation
  isValidSlug: (slug: string): boolean => {
    const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
    return slugRegex.test(slug);
  },
};

// Password strength checker
export const getPasswordStrength = (password: string): {
  score: number;
  feedback: string[];
  strength: 'weak' | 'fair' | 'good' | 'strong';
} => {
  const feedback: string[] = [];
  let score = 0;
  
  if (password.length >= 8) {
    score += 1;
  } else {
    feedback.push('Use at least 8 characters');
  }
  
  if (/[a-z]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Include lowercase letters');
  }
  
  if (/[A-Z]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Include uppercase letters');
  }
  
  if (/\d/.test(password)) {
    score += 1;
  } else {
    feedback.push('Include numbers');
  }
  
  if (/[@$!%*?&]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Include special characters (@$!%*?&)');
  }
  
  if (password.length >= 12) {
    score += 1;
  }
  
  let strength: 'weak' | 'fair' | 'good' | 'strong';
  if (score <= 2) {
    strength = 'weak';
  } else if (score <= 3) {
    strength = 'fair';
  } else if (score <= 4) {
    strength = 'good';
  } else {
    strength = 'strong';
  }
  
  return { score, feedback, strength };
};

// Form validation hook helper
export const createFormValidator = <T extends Record<string, unknown>>(
  schema: Record<keyof T, ValidationRule[]>
) => {
  return (data: T) => validateForm(data, schema);
};

// Async validation (for server-side checks)
export const createAsyncValidator = <T = unknown>(
  validator: (value: T) => Promise<boolean>,
  message: string
): ((value: T) => Promise<FieldValidationResult>) => {
  return async (value: T) => {
    try {
      const isValid = await validator(value);
      return {
        isValid,
        error: isValid ? undefined : message,
      };
    } catch {
      return {
        isValid: false,
        error: 'Validation failed',
      };
    }
  };
};
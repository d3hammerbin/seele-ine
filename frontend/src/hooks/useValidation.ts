// Validation hook
import { useCallback } from 'react';
import type { UseValidationReturn, ValidationRule, ValidationSchema, FormValidationResult } from './types';
import type { ValidationResult, FieldValidationResult } from '../utils/validation';

const useValidation = (): UseValidationReturn => {
  // Validate single value with rules
  const validate = useCallback((value: unknown, rules: ValidationRule[]): ValidationResult => {
    const errors: string[] = [];
    
    for (const rule of rules) {
      if (rule.validator && !rule.validator(value)) {
        errors.push(rule.message);
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
    };
  }, []);

  // Validate single field
  const validateField = useCallback((_field: string, value: unknown, rules: ValidationRule[]): FieldValidationResult => {
    for (const rule of rules) {
      if (rule.validator && !rule.validator(value)) {
        return {
          isValid: false,
          error: rule.message,
        };
      }
    }
    
    return {
      isValid: true,
    };
  }, []);

  // Validate entire form
  const validateForm = useCallback((values: Record<string, unknown>, schema: ValidationSchema): FormValidationResult => {
    const errors: Record<string, string> = {};
    const fieldResults: Record<string, FieldValidationResult> = {};
    
    Object.keys(schema).forEach(field => {
      const rules = schema[field];
      const value = values[field];
      const result = validateField(field, value, rules);
      
      fieldResults[field] = result;
      if (!result.isValid && result.error) {
        errors[field] = result.error;
      }
    });
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors,
      fieldResults,
    };
  }, [validateField]);

  // Email validation
  const isValidEmail = useCallback((email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }, []);

  // Password strength validation
  const isStrongPassword = useCallback((password: string): boolean => {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special char
    const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    return strongPasswordRegex.test(password);
  }, []);

  // Get password strength
  const getPasswordStrength = useCallback((password: string) => {
    let score = 0;
    const feedback: string[] = [];
    const suggestions: string[] = [];
    
    if (password.length >= 8) score += 1;
    else suggestions.push('Use at least 8 characters');
    
    if (/[a-z]/.test(password)) score += 1;
    else suggestions.push('Add lowercase letters');
    
    if (/[A-Z]/.test(password)) score += 1;
    else suggestions.push('Add uppercase letters');
    
    if (/\d/.test(password)) score += 1;
    else suggestions.push('Add numbers');
    
    if (/[@$!%*?&]/.test(password)) score += 1;
    else suggestions.push('Add special characters');
    
    if (score < 3) feedback.push('Weak password');
    else if (score < 4) feedback.push('Fair password');
    else if (score < 5) feedback.push('Good password');
    else feedback.push('Strong password');
    
    return {
      score,
      feedback,
      suggestions,
    };
  }, []);

  return {
    validate,
    validateField,
    validateForm,
    isValidEmail,
    isStrongPassword,
    getPasswordStrength,
  };
};

// Common validation rules
export const validationRules = {
  // Required field
  required: (message = 'This field is required'): ValidationRule => {
    return {
      type: 'required',
      message,
      validator: (value: unknown) => {
        if (value === null || value === undefined || value === '') {
          return false;
        }
        if (typeof value === 'string' && value.trim() === '') {
          return false;
        }
        if (Array.isArray(value) && value.length === 0) {
          return false;
        }
        return true;
      }
    };
  },

  // Minimum length
  minLength: (min: number, message?: string): ValidationRule => {
    return {
      type: 'minLength',
      message: message || `Must be at least ${min} characters long`,
      value: min,
      validator: (value: unknown) => {
        if (value === null || value === undefined) return true;
        const length = typeof value === 'string' ? value.length : String(value).length;
        return length >= min;
      }
    };
  },

  // Maximum length
  maxLength: (max: number, message?: string): ValidationRule => {
    return {
      type: 'maxLength',
      message: message || `Must be no more than ${max} characters long`,
      value: max,
      validator: (value: unknown) => {
        if (value === null || value === undefined) return true;
        const length = typeof value === 'string' ? value.length : String(value).length;
        return length <= max;
      }
    };
  },

  // Email validation
  email: (message = 'Please enter a valid email address'): ValidationRule => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return {
      type: 'email',
      message,
      validator: (value: unknown) => {
        if (!value) return true; // Allow empty values (use required rule separately)
        return emailRegex.test(String(value));
      }
    };
  },

  // URL validation
  url: (message = 'Please enter a valid URL'): ValidationRule => {
    return {
      type: 'url',
      message,
      validator: (value: unknown) => {
        if (!value) return true;
        try {
          new URL(String(value));
          return true;
        } catch {
          return false;
        }
      }
    };
  },

  // Number validation
  number: (message = 'Please enter a valid number'): ValidationRule => {
    return {
      type: 'number',
      message,
      validator: (value: unknown) => {
        if (value === null || value === undefined || value === '') return true;
        return !isNaN(Number(value));
      }
    };
  },

  // Integer validation
  integer: (message = 'Please enter a valid integer'): ValidationRule => {
    return {
      type: 'integer',
      message,
      validator: (value: unknown) => {
        if (value === null || value === undefined || value === '') return true;
        const num = Number(value);
        return !isNaN(num) && Number.isInteger(num);
      }
    };
  },

  // Minimum value
  min: (minimum: number, message?: string): ValidationRule => {
    return {
      type: 'min',
      message: message || `Must be at least ${minimum}`,
      value: minimum,
      validator: (value: unknown) => {
        if (value === null || value === undefined || value === '') return true;
        const num = Number(value);
        return !isNaN(num) && num >= minimum;
      }
    };
  },

  // Maximum value
  max: (maximum: number, message?: string): ValidationRule => {
    return {
      type: 'max',
      message: message || `Must be no more than ${maximum}`,
      value: maximum,
      validator: (value: unknown) => {
        if (value === null || value === undefined || value === '') return true;
        const num = Number(value);
        return !isNaN(num) && num <= maximum;
      }
    };
  },

  // Pattern validation
  pattern: (regex: RegExp, message = 'Invalid format'): ValidationRule => {
    return {
      type: 'pattern',
      message,
      value: regex,
      validator: (value: unknown) => {
        if (!value) return true;
        return regex.test(String(value));
      }
    };
  },

  // Password strength
  passwordStrength: (options: {
    minLength?: number;
    requireUppercase?: boolean;
    requireLowercase?: boolean;
    requireNumbers?: boolean;
    requireSpecialChars?: boolean;
    message?: string;
  } = {}): ValidationRule => {
    const {
      minLength = 8,
      requireUppercase = true,
      requireLowercase = true,
      requireNumbers = true,
      requireSpecialChars = true,
      message,
    } = options;

    return {
      type: 'passwordStrength',
      message: message || 'Password does not meet requirements',
      validator: (value: unknown) => {
        if (!value) return true;
        const password = String(value);

        if (password.length < minLength) return false;
        if (requireUppercase && !/[A-Z]/.test(password)) return false;
        if (requireLowercase && !/[a-z]/.test(password)) return false;
        if (requireNumbers && !/\d/.test(password)) return false;
        if (requireSpecialChars && !/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)) return false;

        return true;
      }
    };
  },

  // Confirm password
  confirmPassword: (passwordField: string, message = 'Passwords do not match'): ValidationRule => {
    return {
      type: 'confirmPassword',
      message,
      validator: (value: unknown, allValues?: unknown) => {
        if (!value || !allValues) return true;
        return value === (allValues as any)[passwordField];
      }
    };
  },

  // Date validation
  date: (message = 'Please enter a valid date'): ValidationRule => {
    return {
      type: 'date',
      message,
      validator: (value: unknown) => {
        if (!value) return true;
        const date = new Date(value as string | number | Date);
        return !isNaN(date.getTime());
      }
    };
  },

  // Future date
  futureDate: (message = 'Date must be in the future'): ValidationRule => {
    return {
      type: 'futureDate',
      message,
      validator: (value: unknown) => {
        if (!value) return true;
        const date = new Date(value as string | number | Date);
        return !isNaN(date.getTime()) && date > new Date();
      }
    };
  },

  // Past date
  pastDate: (message = 'Date must be in the past'): ValidationRule => {
    return {
      type: 'pastDate',
      message,
      validator: (value: unknown) => {
        if (!value) return true;
        const date = new Date(value as string | number | Date);
        return !isNaN(date.getTime()) && date < new Date();
      }
    };
  },

  // File validation
  file: (options: {
    maxSize?: number; // in bytes
    allowedTypes?: string[];
    maxFiles?: number;
    message?: string;
  } = {}): ValidationRule => {
    const { maxSize, allowedTypes, maxFiles = 1, message } = options;

    return {
      type: 'file',
      message: message || 'Invalid file',
      validator: (value: unknown) => {
        if (!value) return true;
        
        const files = Array.isArray(value) ? value : [value];
        
        if (files.length > maxFiles) {
          return false;
        }

        for (const file of files) {
          if (!(file instanceof File)) {
            return false;
          }

          if (maxSize && file.size > maxSize) {
            return false;
          }

          if (allowedTypes && !allowedTypes.includes(file.type as any)) {
            return false;
          }
        }

        return true;
      }
    };
  },

  // Custom validation
  custom: (validator: (value: unknown, allValues?: unknown) => boolean, message = 'Validation failed'): ValidationRule => {
    return {
      type: 'custom',
      message,
      validator: (value: unknown, allValues?: unknown) => {
        try {
          return validator(value, allValues);
        } catch {
          return false;
        }
      }
    };
  },

  // Async validation (for server-side validation)
  async: (message = 'Validation failed'): ValidationRule => {
    return {
      type: 'async',
      message,
      validator: () => {
        // Note: This is a simplified sync version since ValidationRule interface doesn't support async
        // For true async validation, you'd need to extend the ValidationRule interface
        return true; // Placeholder - async validation would need interface changes
      }
    };
  },
};

// Validation utilities
export const validationUtils = {
  // Combine multiple validation rules
  combine: (...rules: ValidationRule[]): ValidationRule => {
    return {
      type: 'combined',
      message: 'Combined validation failed',
      validator: (value: unknown, formValues?: unknown) => {
        return rules.every(rule => {
          if (rule.validator) {
            return rule.validator(value, formValues);
          }
          return true;
        });
      }
    };
  },

  // Conditional validation
  when: (condition: (allValues?: unknown) => boolean, rule: ValidationRule): ValidationRule => {
    return {
      type: 'conditional',
      message: rule.message,
      validator: (value: unknown, allValues?: unknown) => {
        if (condition(allValues)) {
          return rule.validator ? rule.validator(value, allValues) : true;
        }
        return true;
      }
    };
  },

  // Create schema from object
  createSchema: (rules: {
    [key: string]: ValidationRule | ValidationRule[];
  }): ValidationSchema => {
    const schema: ValidationSchema = {};
    for (const [key, rule] of Object.entries(rules)) {
      schema[key] = Array.isArray(rule) ? rule : [rule];
    }
    return schema;
  },

  // Validate single value
  validateValue: (value: unknown, rules: ValidationRule | ValidationRule[], allValues?: unknown): string | null => {
    const ruleArray = Array.isArray(rules) ? rules : [rules];
    
    for (const rule of ruleArray) {
      try {
        if (rule.validator && !rule.validator(value, allValues)) {
          return rule.message;
        }
      } catch (error) {
        return error instanceof Error ? error.message : 'Validation error';
      }
    }
    
    return null;
  },

  // Format validation errors
  formatErrors: <T extends Record<string, unknown>>(errors: Partial<Record<keyof T, string>>): string[] => {
    return Object.entries(errors)
      .filter(([, error]) => error)
      .map(([field, error]) => `${String(field)}: ${error}`);
  },

  // Check if value is empty
  isEmpty: (value: unknown): boolean => {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string') return value.trim() === '';
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'object') return Object.keys(value).length === 0;
    return false;
  },

  // Sanitize input
  sanitize: (value: string): string => {
    return value
      .replace(/[<>"'&]/g, (match) => {
        const entities: Record<string, string> = {
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#x27;',
          '&': '&amp;',
        };
        return entities[match] || match;
      })
      .trim();
  },
};

export default useValidation;
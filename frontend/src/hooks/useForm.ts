// Form hook
import { useState, useCallback, useRef, useEffect } from 'react';
import type { UseFormReturn, FormConfig, ValidationRule, FormErrors, FormTouched } from './types';

interface UseFormOptions<T> {
  initialValues: T;
  validationRules?: Partial<Record<keyof T, ValidationRule[]>>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  validateOnSubmit?: boolean;
  onSubmit?: (values: T) => Promise<void> | void;
  onValidationError?: (errors: FormErrors<T>) => void;
  resetOnSubmit?: boolean;
}

const useForm = <T extends Record<string, unknown>>(options: UseFormOptions<T>): UseFormReturn<T> => {
  const {
    initialValues,
    validationRules = {},
    validateOnChange = true,
    validateOnBlur = true,
    validateOnSubmit = true,
    onSubmit,
    onValidationError,
    resetOnSubmit = false,
  } = options;

  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FormErrors<T>>({});
  const [touched, setTouched] = useState<FormTouched<T>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [submitCount, setSubmitCount] = useState(0);
  const [isDirty, setIsDirty] = useState(false);

  const initialValuesRef = useRef(initialValues);

  // Update initial values ref when it changes
  useEffect(() => {
    initialValuesRef.current = initialValues;
  }, [initialValues]);

  // Check if form is dirty
  useEffect(() => {
    const isFormDirty = Object.keys(values).some(
      key => values[key] !== initialValuesRef.current[key]
    );
    setIsDirty(isFormDirty);
  }, [values]);

  // Validate a single field
  const validateField = useCallback(async (fieldName: keyof T, value: unknown): Promise<string | undefined> => {
    const rules = (validationRules as Record<string, ValidationRule[]>)[fieldName as string];
    if (!rules || rules.length === 0) return undefined;

    for (const rule of rules) {
      try {
        const isValid = await rule.validator?.(value, values);
        if (!isValid) {
          return rule.message;
        }
      } catch {
        return rule.message;
      }
    }

    return undefined;
  }, [validationRules, values]);

  // Validate all fields
  const validateForm = useCallback(async (): Promise<FormErrors<T>> => {
    setIsValidating(true);
    const newErrors: FormErrors<T> = {};

    const validationPromises = Object.keys(validationRules).map(async (fieldName) => {
      const error = await validateField(fieldName as keyof T, values[fieldName]);
      if (error) {
        newErrors[fieldName as keyof T] = error;
      }
    });

    await Promise.all(validationPromises);
    setIsValidating(false);
    return newErrors;
  }, [validationRules, validateField, values]);

  // Set field value
  const setFieldValue = useCallback(async (fieldName: keyof T, value: unknown): Promise<void> => {
    setValues(prev => ({ ...prev, [fieldName]: value }));

    if (validateOnChange) {
      const error = await validateField(fieldName, value);
      setErrors(prev => ({
        ...prev,
        [fieldName]: error,
      }));
    }
  }, [validateField, validateOnChange]);

  // Set field error
  const setFieldError = useCallback((fieldName: keyof T, error: string | undefined): void => {
    setErrors(prev => ({
      ...prev,
      [fieldName]: error,
    }));
  }, []);

  // Set field touched
  const setFieldTouched = useCallback(async (fieldName: keyof T, isTouched = true): Promise<void> => {
    setTouched(prev => ({ ...prev, [fieldName]: isTouched }));

    if (validateOnBlur && isTouched) {
      const error = await validateField(fieldName, values[fieldName]);
      setErrors(prev => ({
        ...prev,
        [fieldName]: error,
      }));
    }
  }, [validateField, validateOnBlur, values]);

  // Handle field change
  const handleChange = useCallback((fieldName: keyof T) => {
    return (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { value, type, checked } = event.target as HTMLInputElement;
      const fieldValue = type === 'checkbox' ? checked : value;
      setFieldValue(fieldName, fieldValue);
    };
  }, [setFieldValue]);

  // Handle field blur
  const handleBlur = useCallback((fieldName: keyof T) => {
    return () => {
      setFieldTouched(fieldName, true);
    };
  }, [setFieldTouched]);

  // Get field props
  const getFieldProps = useCallback((fieldName: keyof T) => {
    return {
      name: fieldName as string,
      value: values[fieldName] || '',
      onChange: handleChange(fieldName),
      onBlur: handleBlur(fieldName),
      error: errors[fieldName],
      touched: touched[fieldName],
    };
  }, [values, errors, touched, handleChange, handleBlur]);

  // Submit form
  const handleSubmit = useCallback(async (event?: React.FormEvent): Promise<void> => {
    if (event) {
      event.preventDefault();
    }

    setSubmitCount(prev => prev + 1);
    setIsSubmitting(true);

    try {
      // Mark all fields as touched
      const allTouched = Object.keys(values).reduce(
        (acc, key) => ({ ...acc, [key]: true }),
        {} as FormTouched<T>
      );
      setTouched(allTouched);

      // Validate form if enabled
      if (validateOnSubmit) {
        const formErrors = await validateForm();
        setErrors(formErrors);

        const hasErrors = Object.values(formErrors).some(error => error);
        if (hasErrors) {
          onValidationError?.(formErrors);
          return;
        }
      }

      // Submit form
      if (onSubmit) {
        await onSubmit(values);
      }

      // Reset form if enabled
      if (resetOnSubmit) {
        reset();
      }
    } catch (error) {
      console.error('Form submission error:', error);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  }, [values, validateOnSubmit, validateForm, onSubmit, onValidationError, resetOnSubmit]);

  // Reset form
  const reset = useCallback((newValues?: Partial<T>): void => {
    const resetValues = newValues ? { ...initialValues, ...newValues } : initialValues;
    setValues(resetValues);
    setErrors({});
    setTouched({});
    setSubmitCount(0);
    setIsDirty(false);
  }, [initialValues]);

  // Set form values
  const setFormValues = useCallback((newValues: Partial<T>): void => {
    setValues(prev => ({ ...prev, ...newValues }));
  }, []);

  // Set form errors
  const setFormErrors = useCallback((newErrors: Partial<FormErrors<T>>): void => {
    setErrors(prev => ({ ...prev, ...newErrors }));
  }, []);

  // Clear form errors
  const clearErrors = useCallback((): void => {
    setErrors({});
  }, []);

  // Check if form is valid
  const isValid = Object.values(errors).every(error => !error);

  // Check if form can be submitted
  const canSubmit = isValid && !isSubmitting && !isValidating;

  // Get form configuration
  const getFormConfig = useCallback((): FormConfig<T> => {
    return {
      values,
      errors,
      touched,
      isSubmitting,
      isValidating,
      isValid,
      isDirty,
      submitCount,
      canSubmit,
    };
  }, [values, errors, touched, isSubmitting, isValidating, isValid, isDirty, submitCount, canSubmit]);

  return {
    // Form state
    values,
    errors,
    touched,
    isSubmitting,
    isValidating,
    isValid,
    isDirty,
    submitCount,
    canSubmit,

    // Field operations
    setFieldValue,
    setFieldError,
    setFieldTouched,
    getFieldProps,

    // Form operations
    handleSubmit,
    reset,
    setFormValues,
    setFormErrors,
    clearErrors,
    validateForm,
    validateField,
    getFormConfig,

    // Event handlers
    handleChange,
    handleBlur,
  };
};

// Form validation utilities
export const formValidators = {
  // Required field validator
  required: (message = 'This field is required'): ValidationRule => ({
    type: 'required',
    validator: (value: unknown) => {
      if (typeof value === 'string') {
        return value.trim().length > 0;
      }
      return value != null && value !== '';
    },
    message,
  }),

  // Minimum length validator
  minLength: (min: number, message?: string): ValidationRule => ({
    type: 'minLength',
    validator: (value: unknown) => {
      if (typeof value === 'string') {
        return value.length >= min;
      }
      return true;
    },
    message: message || `Must be at least ${min} characters`,
  }),

  // Maximum length validator
  maxLength: (max: number, message?: string): ValidationRule => ({
    type: 'maxLength',
    validator: (value: unknown) => {
      if (typeof value === 'string') {
        return value.length <= max;
      }
      return true;
    },
    message: message || `Must be no more than ${max} characters`,
  }),

  // Email validator
  email: (message = 'Please enter a valid email address'): ValidationRule => ({
    type: 'email',
    validator: (value: unknown) => {
      if (typeof value !== 'string') return false;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value);
    },
    message,
  }),

  // URL validator
  url: (message = 'Please enter a valid URL'): ValidationRule => ({
    type: 'url',
    validator: (value: unknown) => {
      if (typeof value !== 'string') return false;
      try {
        new URL(value);
        return true;
      } catch {
        return false;
      }
    },
    message,
  }),

  // Number validator
  number: (message = 'Please enter a valid number'): ValidationRule => ({
    type: 'number',
    validator: (value: unknown) => {
      return !isNaN(Number(value));
    },
    message,
  }),

  // Minimum value validator
  min: (min: number, message?: string): ValidationRule => ({
    type: 'min',
    validator: (value: unknown) => {
      const num = Number(value);
      return !isNaN(num) && num >= min;
    },
    message: message || `Must be at least ${min}`,
  }),

  // Maximum value validator
  max: (max: number, message?: string): ValidationRule => ({
    type: 'max',
    validator: (value: unknown) => {
      const num = Number(value);
      return !isNaN(num) && num <= max;
    },
    message: message || `Must be no more than ${max}`,
  }),

  // Pattern validator
  pattern: (regex: RegExp, message = 'Invalid format'): ValidationRule => ({
    type: 'pattern',
    validator: (value: unknown) => {
      if (typeof value !== 'string') return false;
      return regex.test(value);
    },
    message,
  }),

  // Password strength validator
  passwordStrength: (message = 'Password must contain at least 8 characters, including uppercase, lowercase, number, and special character'): ValidationRule => ({
    type: 'passwordStrength',
    validator: (value: unknown) => {
      if (typeof value !== 'string') return false;
      const hasLength = value.length >= 8;
      const hasUpper = /[A-Z]/.test(value);
      const hasLower = /[a-z]/.test(value);
      const hasNumber = /\d/.test(value);
      const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(value);
      return hasLength && hasUpper && hasLower && hasNumber && hasSpecial;
    },
    message,
  }),

  // Confirm password validator
  confirmPassword: (passwordField: string, message = 'Passwords do not match'): ValidationRule => ({
    type: 'confirmPassword',
    validator: (value: unknown, formValues: unknown) => {
      return value === (formValues as any)[passwordField];
    },
    message,
  }),

  // Custom validator
  custom: (validator: (value: unknown, formValues?: unknown) => boolean | Promise<boolean>, message: string): ValidationRule => ({
    type: 'custom',
    validator,
    message,
  }),

  // Async validator
  async: (validator: (value: unknown, formValues?: unknown) => Promise<boolean>, message: string): ValidationRule => ({
    type: 'async',
    validator,
    message,
  }),
};

// Form utilities
export const formUtils = {
  // Create initial form values from schema
  createInitialValues: <T>(schema: Record<string, unknown>): T => {
    const initialValues = {} as T;
    Object.keys(schema).forEach(key => {
      const field = schema[key];
      if ((field as any).type === 'boolean') {
        (initialValues as Record<string, unknown>)[key] = false;
      } else if ((field as any).type === 'number') {
        (initialValues as Record<string, unknown>)[key] = 0;
      } else if ((field as any).type === 'array') {
        (initialValues as Record<string, unknown>)[key] = [];
      } else {
        (initialValues as Record<string, unknown>)[key] = '';
      }
    });
    return initialValues;
  },

  // Serialize form values for API
  serializeValues: <T>(values: T): Record<string, unknown> => {
    const serialized: Record<string, unknown> = {};
    Object.entries(values as Record<string, unknown>).forEach(([key, value]) => {
      if (value instanceof Date) {
        serialized[key] = value.toISOString();
      } else if (typeof value === 'object' && value !== null) {
        serialized[key] = JSON.stringify(value);
      } else {
        serialized[key] = value;
      }
    });
    return serialized;
  },

  // Deserialize form values from API
  deserializeValues: <T>(data: Record<string, unknown>, schema?: Record<string, unknown>): T => {
    const deserialized = {} as T;
    Object.entries(data).forEach(([key, value]) => {
      if (schema && (schema[key] as any)?.type === 'date' && typeof value === 'string') {
        (deserialized as Record<string, unknown>)[key] = new Date(value);
      } else if (typeof value === 'string' && (value.startsWith('{') || value.startsWith('['))) {
        try {
          (deserialized as Record<string, unknown>)[key] = JSON.parse(value);
        } catch {
          (deserialized as Record<string, unknown>)[key] = value;
        }
      } else {
        (deserialized as Record<string, unknown>)[key] = value;
      }
    });
    return deserialized;
  },

  // Get changed fields
  getChangedFields: <T>(initialValues: T, currentValues: T): Partial<T> => {
    const changed: Partial<T> = {};
    Object.keys(currentValues as Record<string, unknown>).forEach(key => {
      if (currentValues[key as keyof T] !== initialValues[key as keyof T]) {
        changed[key as keyof T] = currentValues[key as keyof T];
      }
    });
    return changed;
  },

  // Validate form data against schema
  validateSchema: <T>(values: T, schema: Record<string, unknown>): FormErrors<T> => {
    const errors: FormErrors<T> = {};
    Object.keys(schema).forEach(key => {
      const field = schema[key];
      const value = (values as Record<string, unknown>)[key];
      
      if ((field as any).required && (!value || (typeof value === 'string' && !value.trim()))) {
        (errors as Record<string, unknown>)[key] = 'This field is required';
      }
    });
    return errors;
  },
};

export default useForm;
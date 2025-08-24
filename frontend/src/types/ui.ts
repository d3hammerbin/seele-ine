// UI Component types
export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type InputSize = 'sm' | 'md' | 'lg';
export type AlertType = 'info' | 'success' | 'warning' | 'error';
export type ToastType = 'info' | 'success' | 'warning' | 'error';
export type ModalSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';

// Button props
export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
  children: React.ReactNode;
}

// Input props
export interface InputProps {
  label?: string;
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  size?: InputSize;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  className?: string;
}

// Select props
export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  label?: string;
  placeholder?: string;
  value?: string | number;
  defaultValue?: string | number;
  options: SelectOption[];
  size?: InputSize;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  helperText?: string;
  onChange?: (value: string | number) => void;
  className?: string;
}

// Modal props
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: ModalSize;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  children: React.ReactNode;
  className?: string;
}

// Alert props
export interface AlertProps {
  type: AlertType;
  title?: string;
  message: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

// Toast notification
export interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  dismissible?: boolean;
  actions?: Array<{
    label: string;
    onClick: () => void;
  }>;
}

// Toast props
export interface ToastProps {
  toast: Toast;
  onDismiss: (id: string) => void;
  className?: string;
}

// Toast container props
export interface ToastContainerProps {
  toasts: Toast[];
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  className?: string;
}

// Loading spinner props
export interface SpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: string;
  className?: string;
}

// Progress bar props
export interface ProgressProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  showLabel?: boolean;
  className?: string;
}

// Badge props
export interface BadgeProps {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
}

// Card props
export interface CardProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  variant?: 'default' | 'outline' | 'filled' | 'destructive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  border?: boolean;
  children: React.ReactNode;
  className?: string;
}

// Table types
export interface TableColumn<T = unknown> {
  key: string;
  title: string;
  dataIndex?: keyof T;
  render?: (value: unknown, record: T, index: number) => React.ReactNode;
  sortable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  fixed?: 'left' | 'right';
}

export interface TableProps<T = unknown> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    onChange: (page: number, pageSize: number) => void;
  };
  rowKey?: string | ((record: T) => string);
  onRow?: (record: T, index: number) => React.HTMLAttributes<HTMLTableRowElement>;
  className?: string;
}

// File upload props
export interface FileUploadProps {
  accept?: string;
  multiple?: boolean;
  maxSize?: number;
  maxFiles?: number;
  disabled?: boolean;
  onUpload: (files: File[]) => void;
  onError?: (error: string) => void;
  children?: React.ReactNode;
  className?: string;
}

// Dropdown menu types
export interface DropdownItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  type?: 'divider' | 'item';
  className?: string;
  keepOpen?: boolean;
  disabled?: boolean;
  danger?: boolean;
  onClick?: () => void;
}

export interface DropdownProps {
  items: DropdownItem[];
  trigger: React.ReactNode;
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end';
  className?: string;
}

// Breadcrumb types
export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  className?: string;
}

// Pagination props
export interface PaginationProps {
  current: number;
  total: number;
  pageSize: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: (total: number, range: [number, number]) => string;
  onChange: (page: number, pageSize: number) => void;
  className?: string;
}

// Theme types
export interface ThemeColors {
  primary: Record<string, string>;
  secondary: Record<string, string>;
  success: Record<string, string>;
  warning: Record<string, string>;
  error: Record<string, string>;
  gray: Record<string, string>;
}

export interface Theme {
  name: string;
  colors: ThemeColors;
  fonts: {
    sans: string[];
    mono: string[];
  };
  spacing: Record<string, string>;
  borderRadius: Record<string, string>;
  shadows: Record<string, string>;
}

// Layout types
export interface LayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

// Navigation types
export interface NavItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  href?: string;
  onClick?: () => void;
  children?: NavItem[];
  badge?: string | number;
  disabled?: boolean;
}

export interface NavigationProps {
  items: NavItem[];
  collapsed?: boolean;
  onToggle?: () => void;
  className?: string;
}
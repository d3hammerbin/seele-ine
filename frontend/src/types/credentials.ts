// Credential-related types
export interface CredentialData {
  id: string;
  userId: string;
  fileName: string;
  originalName: string;
  fileSize: number;
  mimeType: string;
  uploadedAt: string;
  processedAt?: string;
  status: CredentialStatus;
  processingJob?: ProcessingJob;
  extractedData?: ExtractedCredentialData;
  qrData?: QRData;
  ocrData?: OCRData;
  aiAnalysis?: AIAnalysis;
  validationResults?: ValidationResults;
  metadata?: CredentialMetadata;
  tags?: string[];
  notes?: string;
  isArchived: boolean;
  createdAt: string;
  updatedAt: string;
}

export enum CredentialStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ARCHIVED = 'archived'
}

export interface ProcessingJob {
  id: string;
  credentialId: string;
  status: ProcessingJobStatus;
  progress: number;
  startedAt: string;
  completedAt?: string;
  errorMessage?: string;
  steps: ProcessingStep[];
  aiProvider?: string;
  processingTime?: number;
  cost?: number;
  retryCount: number;
  maxRetries: number;
  totalFiles?: number;
  filesProcessed?: number;
  createdAt: string;
}

export enum ProcessingJobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface ProcessingStep {
  name: string;
  status: ProcessingStepStatus;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
  progress: number;
  metadata?: Record<string, unknown>;
}

export enum ProcessingStepStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SKIPPED = 'skipped'
}

export interface ExtractedCredentialData {
  // Personal Information
  fullName?: string;
  firstName?: string;
  lastName?: string;
  dateOfBirth?: string;
  placeOfBirth?: string;
  gender?: string;
  nationality?: string;
  
  // Identification
  credentialNumber?: string;
  curp?: string;
  voterKey?: string;
  
  // Address
  address?: {
    street?: string;
    neighborhood?: string;
    municipality?: string;
    state?: string;
    postalCode?: string;
    country?: string;
  };
  
  // Document Information
  issueDate?: string;
  expirationDate?: string;
  issuingAuthority?: string;
  documentType?: string;
  
  // Additional Data
  maritalStatus?: string;
  occupation?: string;
  
  // Confidence scores
  confidence?: {
    overall: number;
    fields: Record<string, number>;
  };
}

export interface QRData {
  rawData: string;
  parsedData?: Record<string, unknown>;
  format?: string;
  confidence: number;
  position?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface OCRData {
  rawText: string;
  structuredData?: Record<string, unknown>;
  confidence: number;
  language?: string;
  regions?: OCRRegion[];
}

export interface OCRRegion {
  text: string;
  confidence: number;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface AIAnalysis {
  provider: string;
  model: string;
  analysis: Record<string, unknown>;
  confidence: number;
  processingTime: number;
  cost: number;
  timestamp: string;
}

export interface ValidationResults {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  score: number;
  checkedFields: string[];
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  code?: string;
}

export interface ValidationWarning {
  field: string;
  message: string;
  suggestion?: string;
  code?: string;
}

export interface CredentialMetadata {
  imageWidth?: number;
  imageHeight?: number;
  fileFormat?: string;
  colorSpace?: string;
  dpi?: number;
  hasQR?: boolean;
  qrCount?: number;
  textRegions?: number;
  processingVersion?: string;
  [key: string]: unknown;
}

// Request/Response types
export interface CreateCredentialRequest {
  file: File;
  tags?: string[];
  notes?: string;
  processingOptions?: ProcessingOptions;
}

export interface ProcessingOptions {
  enableOCR?: boolean;
  enableQR?: boolean;
  enableAI?: boolean;
  aiProvider?: string;
  ocrLanguage?: string;
  validateData?: boolean;
  extractStructuredData?: boolean;
  concurrency?: number;
}

export interface UpdateCredentialRequest {
  tags?: string[];
  notes?: string;
  isArchived?: boolean;
}

export interface CredentialListParams {
  page?: number;
  limit?: number;
  status?: CredentialStatus;
  search?: string;
  tags?: string[];
  dateFrom?: string;
  dateTo?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface CredentialExportParams {
  format: 'json' | 'csv' | 'xlsx';
  includeImages?: boolean;
  credentialIds?: string[];
  filters?: CredentialListParams;
}
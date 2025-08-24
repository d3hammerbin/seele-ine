// Credential types
export type CredentialType = 'ine_front' | 'ine_back' | 'passport' | 'license' | 'other';
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type ExtractionMethod = 
  | 'tesseract_ocr'
  | 'easyocr'
  | 'paddleocr'
  | 'qr_basic'
  | 'qr_advanced'
  | 'openai_vision'
  | 'deepseek_vision'
  | 'gemini_vision'
  | 'claude_vision'
  | 'hybrid_ai';

export type AiProvider = 'openai' | 'deepseek' | 'gemini' | 'claude';

// Personal information extracted from credentials
export interface PersonalInfo {
  fullName?: string;
  firstName?: string;
  lastName?: string;
  dateOfBirth?: string;
  placeOfBirth?: string;
  gender?: string;
  nationality?: string;
  curp?: string;
  voterKey?: string;
  ocr?: string;
  cic?: string;
  section?: string;
  locality?: string;
  municipality?: string;
  state?: string;
  district?: string;
  issueDate?: string;
  expiryDate?: string;
  address?: {
    street?: string;
    neighborhood?: string;
    municipality?: string;
    state?: string;
    postalCode?: string;
    country?: string;
  };
}

// Processing metrics
export interface ProcessingMetrics {
  processingTime: number;
  confidenceScore: number;
  ocrAccuracy?: number;
  qrValidation?: boolean;
  aiProviderUsed?: AiProvider;
  fallbackUsed?: boolean;
  retryCount?: number;
}

// Quality assessment
export interface QualityScore {
  overall: number;
  imageClarity: number;
  textReadability: number;
  documentIntegrity: number;
  recommendations?: string[];
}

// Processing log entry
export interface ProcessingLog {
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  details?: Record<string, unknown>;
}

// Main credential interface
export interface Credential {
  id: string;
  userId: string;
  credentialType: CredentialType;
  status: ProcessingStatus;
  extractionMethod?: ExtractionMethod;
  
  // File information
  fileName: string;
  fileSize: number;
  mimeType: string;
  fileUrl?: string;
  thumbnailUrl?: string;
  
  // Processing results
  personalInfo?: PersonalInfo;
  rawExtractedData?: Record<string, unknown>;
  
  // Metrics and quality
  processingMetrics?: ProcessingMetrics;
  qualityScore?: QualityScore;
  
  // Error handling
  errorMessage?: string;
  errorDetails?: Record<string, unknown>;
  
  // Processing logs
  processingLogs?: ProcessingLog[];
  
  // Timestamps
  createdAt: string;
  updatedAt: string;
  processedAt?: string;
}

// Upload request types
export interface CredentialUploadRequest {
  file: File;
  credentialType?: CredentialType;
  extractQr?: boolean;
  aiProvider?: AiProvider;
  enableAiFallback?: boolean;
  validateDimensions?: boolean;
}

export interface CredentialValidationRequest {
  file: File;
  checkFormat?: boolean;
  checkDimensions?: boolean;
  checkQuality?: boolean;
}

export interface CredentialClassificationRequest {
  file: File;
  useAiFallback?: boolean;
}

export interface OcrExtractionRequest {
  file: File;
  method?: 'tesseract' | 'easyocr' | 'paddleocr';
  useAiFallback?: boolean;
  aiProvider?: AiProvider;
}

export interface QrExtractionRequest {
  file: File;
  validateIneFormat?: boolean;
}

export interface CredentialProcessingRequest {
  file: File;
  credentialType?: CredentialType;
  extractionMethod?: ExtractionMethod;
  aiProvider?: AiProvider;
  enableAiFallback?: boolean;
  validateQr?: boolean;
  validateDimensions?: boolean;
}

// Response types
export interface CredentialUploadResponse {
  credential: Credential;
  estimatedProcessingTime?: number;
}

export interface CredentialValidationResponse {
  isValid: boolean;
  issues?: string[];
  recommendations?: string[];
  fileInfo: {
    size: number;
    dimensions?: { width: number; height: number };
    format: string;
    quality?: number;
  };
}

export interface CredentialClassificationResponse {
  credentialType: CredentialType;
  confidence: number;
  alternatives?: Array<{
    type: CredentialType;
    confidence: number;
  }>;
}

export interface OcrExtractionResponse {
  extractedText: string;
  confidence: number;
  method: string;
  processingTime: number;
  structuredData?: Record<string, unknown>;
}

export interface QrExtractionResponse {
  qrData: string;
  isValidIne: boolean;
  parsedData?: Record<string, unknown>;
  validationErrors?: string[];
}

// History and statistics
export interface CredentialHistoryParams {
  page?: number;
  limit?: number;
  status?: ProcessingStatus;
  credentialType?: CredentialType;
  dateFrom?: string;
  dateTo?: string;
  search?: string;
}

export interface CredentialStats {
  totalProcessed: number;
  successfulProcessing: number;
  failedProcessing: number;
  averageProcessingTime: number;
  mostUsedExtractionMethod: ExtractionMethod;
  qualityDistribution: {
    excellent: number;
    good: number;
    fair: number;
    poor: number;
  };
  monthlyStats: Array<{
    month: string;
    processed: number;
    successful: number;
    failed: number;
  }>;
}

// Retry operation
export interface CredentialRetryRequest {
  extractionMethod?: ExtractionMethod;
  aiProvider?: AiProvider;
  enableAiFallback?: boolean;
}

// Credential state for Redux
export interface CredentialState {
  credentials: Credential[];
  currentCredential: Credential | null;
  isLoading: boolean;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
  stats: CredentialStats | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
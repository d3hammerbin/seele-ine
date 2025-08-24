// API Services - Re-exports from utils/api with organized structure
import { api } from '../../utils/api';

// API Keys API
export const apiKeysApi = {
  list: () => api.apiKeys.list(),
  create: (data: Record<string, unknown>) => api.apiKeys.create(data),
  update: (id: string, data: Record<string, unknown>) => api.apiKeys.update(id, data),
  delete: (id: string) => api.apiKeys.delete(id),
  rotate: (id: string) => api.apiKeys.rotate(id),
  getUsage: (id: string) => api.apiKeys.getUsage(id),
    getApiKeyStats: (id: string) => api.apiKeys.getApiKeyStats(id),
    toggleApiKeyStatus: (id: string, data: Record<string, unknown>) => api.apiKeys.toggleApiKeyStatus(id, data),
    deleteApiKey: (id: string) => api.apiKeys.delete(id),
    regenerateApiKey: (id: string) => api.apiKeys.regenerate(id),
    createApiKey: (data: Record<string, unknown>) => api.apiKeys.create(data),
    getApiKeys: () => api.apiKeys.list(),
};

// Credentials API
export const credentialsApi = {
  list: (params?: Record<string, unknown>) => api.credentials.list(params),
  get: (id: string) => api.credentials.get(id),
  create: (data: Record<string, unknown>) => api.credentials.create(data),
  update: (id: string, data: Record<string, unknown>) => api.credentials.update(id, data),
  delete: (id: string) => api.credentials.delete(id),
  deleteCredentials: (ids: string[]) => api.credentials.deleteCredentials(ids),
  getCredentials: (params?: Record<string, unknown>) => api.credentials.getCredentials(params),
  uploadFiles: (files: File[]) => api.credentials.uploadFiles(files),
  process: (id: string) => api.credentials.process(id),
  download: (id: string) => api.credentials.download(id),
  export: (params?: Record<string, unknown>) => api.credentials.export(params),
};

// Usage API
export const usageApi = {
  current: () => api.usage.current(),
  history: (params?: Record<string, unknown>) => api.usage.history(params),
  costs: (params?: Record<string, unknown>) => api.usage.costs(params),
  getBillingInfo: () => api.usage.getBillingInfo(),
  getUsageStats: (params?: Record<string, unknown>) => api.usage.getUsageStats(params),
  getUsageData: (params?: Record<string, unknown>) => api.usage.getUsageData(params),
  exportUsageReport: (format: string, filters?: Record<string, unknown>) => api.usage.exportUsageReport(format, filters),
};

// Auth API
export const authApi = {
  login: (credentials: Record<string, unknown>) => api.auth.login(credentials),
  register: (userData: Record<string, unknown>) => api.auth.register(userData),
  logout: (refreshToken: string) => api.auth.logout(refreshToken),
  refresh: (refreshToken: string) => api.auth.refresh(refreshToken),
  forgotPassword: (email: string) => api.auth.forgotPassword(email),
  resetPassword: (data: Record<string, unknown>) => api.auth.resetPassword(data),
  verifyEmail: (token: string) => api.auth.verifyEmail(token),
  resendVerification: () => api.auth.resendVerification(),
};

// Profile API
export const profileApi = {
  get: () => api.profile.get(),
  update: (data: Record<string, unknown>) => api.profile.update(data),
  updatePassword: (data: Record<string, unknown>) => api.profile.updatePassword(data),
  updateEmail: (data: Record<string, unknown>) => api.profile.updateEmail(data),
  delete: () => api.profile.delete(),
};

// System API
export const systemApi = {
  health: () => api.system.health(),
  version: () => api.system.version(),
  providers: () => api.system.providers(),
};

// Export all APIs
export const apiServices = {
  apiKeys: apiKeysApi,
  credentials: credentialsApi,
  usage: usageApi,
  auth: authApi,
  profile: profileApi,
  system: systemApi,
};

export default apiServices;
import axios, { AxiosError } from 'axios';

// Use relative path in production, localhost for development
const API_BASE = import.meta.env.VITE_API_BASE ||
  (import.meta.env.MODE === 'production' ? '' : 'http://localhost:8005');

let authToken: string | null = null;
let unauthorizedHandler: (() => void) | null = null;

function persistToken(token: string, expiresInSeconds?: number) {
  setAuthToken(token);
  if (typeof window !== 'undefined') {
    localStorage.setItem('authToken', token);
    if (typeof expiresInSeconds === 'number' && Number.isFinite(expiresInSeconds)) {
      const ttlMs = Math.max(0, expiresInSeconds) * 1000;
      localStorage.setItem('authTokenExpires', String(Date.now() + ttlMs));
    }
  }
}

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Accept': 'application/json' }
});

api.interceptors.request.use(config => {
  if (authToken) {
    config.headers = config.headers ?? {};
    config.headers['Authorization'] = `Bearer ${authToken}`;
  }
  return config;
});

api.interceptors.response.use(
  response => {
    const refreshedToken = response.headers['x-access-token'];
    if (refreshedToken) {
      const expiresHeader = response.headers['x-token-expires-in'];
      const ttl = expiresHeader ? Number.parseInt(String(expiresHeader), 10) : undefined;
      persistToken(String(refreshedToken), Number.isNaN(ttl) ? undefined : ttl);
    }
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401 && unauthorizedHandler) {
      unauthorizedHandler();
    }
    return Promise.reject(error);
  }
);

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function onUnauthorized(handler: (() => void) | null) {
  unauthorizedHandler = handler;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/api/login', { username, password });
  persistToken(data.access_token, data.expires_in);
  return data;
}

export type PhoneCodePurpose = 'register' | 'reset';

export interface PhoneCodeResponse {
  message: string;
  ttl: number;
  debug_code?: string;
}

export async function sendPhoneCode(phone: string, purpose: PhoneCodePurpose): Promise<PhoneCodeResponse> {
  const { data } = await api.post<PhoneCodeResponse>('/api/auth/phone/send-code', { phone, purpose });
  return data;
}

export interface PhoneRegisterRequest {
  phone: string;
  code: string;
  password: string;
  username?: string;
  full_name?: string;
}

export async function registerWithPhone(payload: PhoneRegisterRequest): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/api/auth/phone/register', {
    phone: payload.phone,
    code: payload.code,
    password: payload.password,
    username: payload.username,
    full_name: payload.full_name,
  });
  persistToken(data.access_token, data.expires_in);
  return data;
}

export interface PhoneResetResponse {
  message: string;
}

export async function resetPasswordByPhone(phone: string, code: string, newPassword: string): Promise<PhoneResetResponse> {
  const { data } = await api.post<PhoneResetResponse>('/api/auth/phone/reset-password', {
    phone,
    code,
    new_password: newPassword,
  });
  return data;
}

export interface CurrentUserResponse {
  username: string;
  full_name?: string;
}

export async function getCurrentUser(): Promise<CurrentUserResponse> {
  const { data } = await api.get<CurrentUserResponse>('/api/me');
  return data;
}

export type Provider = 'OpenAI' | 'Anthropic' | 'Gemini' | 'Qwen';

export interface ProcessResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskResult {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: {
    output_path: string;
    statistics: {
      total_formulas: number;
      display_formulas: number;
      inline_formulas: number;
      formulas?: [string, string][];
    };
    provider: string;
    model: string;
  };
}

export async function uploadSingle(
  file: File,
  provider: Provider,
  includeOriginalImage: boolean,
  imageQuality: number
): Promise<ProcessResponse> {
  const form = new FormData();
  form.append('file', file);
  const params = new URLSearchParams({
    llm_provider: provider.toLowerCase(),
    include_original_image: String(includeOriginalImage),
    image_quality: String(imageQuality)
  });
  const { data } = await api.post<ProcessResponse>(`/api/process?${params.toString()}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
}

export async function getTask(taskId: string): Promise<TaskResult> {
  const { data } = await api.get<TaskResult>(`/api/task/${taskId}`);
  return data;
}

export function getDownloadUrl(outputPath: string): string {
  const filename = outputPath.split('/').pop() || outputPath;
  return `${API_BASE}/api/download/${filename}`;
}

export async function downloadFile(outputPath: string): Promise<Blob> {
  const filename = outputPath.split('/').pop() || outputPath;
  const { data } = await api.get(`/api/download/${filename}`, {
    responseType: 'blob'
  });
  return data;
}

export interface BatchResponse { batch_id: string; total_tasks: number; }
export interface BatchStatus {
  batch_id: string;
  total: number;
  completed: number;
  failed: number;
  processing: number;
  pending: number;
}

export async function uploadBatch(files: File[], provider: Provider): Promise<BatchResponse> {
  const form = new FormData();
  files.forEach(f => form.append('files', f));
  const params = new URLSearchParams({ llm_provider: provider.toLowerCase() });
  const { data } = await api.post<BatchResponse>(`/api/batch?${params.toString()}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
}

export async function getBatchStatus(batchId: string): Promise<BatchStatus> {
  const { data } = await api.get<BatchStatus>(`/api/batch/${batchId}`);
  return data;
}

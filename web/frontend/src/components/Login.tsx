import React, { useEffect, useState } from 'react';
import {
  login,
  registerWithPhone,
  resetPasswordByPhone,
  sendPhoneCode,
  PhoneCodePurpose,
} from '../api/client';

interface LoginProps {
  onSuccess: (token: string, expiresIn: number) => void;
}

type AuthMode = 'login' | 'register' | 'reset';

const MIN_PASSWORD_LENGTH = 6;
const CODE_RESEND_COOLDOWN = 60;

function formatErrorMessage(error: any, fallback: string): string {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }
  if (typeof error?.message === 'string' && error.message.trim().length > 0) {
    return error.message;
  }
  return fallback;
}

export default function Login({ onSuccess }: LoginProps) {
  const [mode, setMode] = useState<AuthMode>('login');

  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [resetSuccessMessage, setResetSuccessMessage] = useState('');

  const [registerForm, setRegisterForm] = useState({
    phone: '',
    code: '',
    username: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [registerLoading, setRegisterLoading] = useState(false);
  const [registerError, setRegisterError] = useState('');
  const [registerInfo, setRegisterInfo] = useState('');
  const [registerCodeLoading, setRegisterCodeLoading] = useState(false);
  const [registerCooldown, setRegisterCooldown] = useState(0);

  const [resetForm, setResetForm] = useState({
    phone: '',
    code: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetInfo, setResetInfo] = useState('');
  const [resetCodeLoading, setResetCodeLoading] = useState(false);
  const [resetCooldown, setResetCooldown] = useState(0);

  useEffect(() => {
    if (registerCooldown <= 0) return;
    const timer = window.setInterval(() => {
      setRegisterCooldown(prev => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [registerCooldown]);

  useEffect(() => {
    if (resetCooldown <= 0) return;
    const timer = window.setInterval(() => {
      setResetCooldown(prev => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [resetCooldown]);

  function changeMode(next: AuthMode) {
    setMode(next);
    setLoginError('');
    setRegisterError('');
    setRegisterInfo('');
    setResetError('');
    setResetInfo('');
    if (next !== 'login') {
      setResetSuccessMessage('');
    }
  }

  async function handleLoginSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoginError('');
    setResetSuccessMessage('');
    setLoginLoading(true);
    try {
      const result = await login(loginUsername, loginPassword);
      onSuccess(result.access_token, result.expires_in);
    } catch (err) {
      setLoginError(formatErrorMessage(err, '登录失败'));
    } finally {
      setLoginLoading(false);
    }
  }

  function ensurePhoneInput(value: string): string {
    return value.trim();
  }

  async function handleSendCode(phone: string, purpose: PhoneCodePurpose, setInfo: (msg: string) => void, setError: (msg: string) => void, setCooldown: (val: number) => void, setLoading: (flag: boolean) => void) {
    const normalized = ensurePhoneInput(phone);
    if (!normalized) {
      setError('请输入手机号');
      return;
    }
    setError('');
    setInfo('');
    setLoading(true);
    try {
      const response = await sendPhoneCode(normalized, purpose);
      const debugCode = response.debug_code ? `（验证码：${response.debug_code}）` : '';
      setInfo(`${response.message}${debugCode}`);
      setCooldown(Math.min(CODE_RESEND_COOLDOWN, Math.max(0, response.ttl)) || CODE_RESEND_COOLDOWN);
    } catch (err) {
      setError(formatErrorMessage(err, '发送验证码失败'));
    } finally {
      setLoading(false);
    }
  }

  async function handleRegisterSubmit(e: React.FormEvent) {
    e.preventDefault();
    setRegisterError('');
    setRegisterInfo('');

    const phone = ensurePhoneInput(registerForm.phone);
    if (!phone) {
      setRegisterError('请输入手机号');
      return;
    }
    if (!registerForm.code.trim()) {
      setRegisterError('请输入验证码');
      return;
    }
    if (!registerForm.password || registerForm.password.length < MIN_PASSWORD_LENGTH) {
      setRegisterError(`密码长度必须不少于${MIN_PASSWORD_LENGTH}位`);
      return;
    }
    if (registerForm.password !== registerForm.confirmPassword) {
      setRegisterError('两次输入的密码不一致');
      return;
    }

    setRegisterLoading(true);
    try {
      const result = await registerWithPhone({
        phone,
        code: registerForm.code.trim(),
        password: registerForm.password,
        username: registerForm.username.trim() || undefined,
        full_name: registerForm.fullName.trim() || undefined,
      });
      onSuccess(result.access_token, result.expires_in);
    } catch (err) {
      setRegisterError(formatErrorMessage(err, '注册失败'));
    } finally {
      setRegisterLoading(false);
    }
  }

  async function handleResetSubmit(e: React.FormEvent) {
    e.preventDefault();
    setResetError('');
    setResetInfo('');

    const phone = ensurePhoneInput(resetForm.phone);
    if (!phone) {
      setResetError('请输入手机号');
      return;
    }
    if (!resetForm.code.trim()) {
      setResetError('请输入验证码');
      return;
    }
    if (!resetForm.newPassword || resetForm.newPassword.length < MIN_PASSWORD_LENGTH) {
      setResetError(`新密码长度必须不少于${MIN_PASSWORD_LENGTH}位`);
      return;
    }
    if (resetForm.newPassword !== resetForm.confirmPassword) {
      setResetError('两次输入的新密码不一致');
      return;
    }

    setResetLoading(true);
    try {
      await resetPasswordByPhone(phone, resetForm.code.trim(), resetForm.newPassword);
      setResetSuccessMessage('密码已重置，请使用新密码登录');
      setResetForm({ phone: '', code: '', newPassword: '', confirmPassword: '' });
      changeMode('login');
    } catch (err) {
      setResetError(formatErrorMessage(err, '重置密码失败'));
    } finally {
      setResetLoading(false);
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          {mode === 'login' && (
            <>
              <h1>图像转Word</h1>
              <p>智能识别，快速转换</p>
            </>
          )}
          {mode === 'register' && (
            <>
              <h1>手机号注册</h1>
              <p>验证手机号，快速创建账号</p>
            </>
          )}
          {mode === 'reset' && (
            <>
              <h1>找回密码</h1>
              <p>通过手机号重置登录密码</p>
            </>
          )}
        </div>

        {mode === 'login' && (
          <form className="login-form" onSubmit={handleLoginSubmit}>
            <div className="form-group">
              <label htmlFor="username">用户名</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <input
                  id="username"
                  type="text"
                  value={loginUsername}
                  onChange={e => setLoginUsername(e.target.value)}
                  placeholder="请输入用户名"
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="password">密码</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <input
                  id="password"
                  type="password"
                  value={loginPassword}
                  onChange={e => setLoginPassword(e.target.value)}
                  placeholder="请输入密码"
                  autoComplete="current-password"
                  required
                />
              </div>
            </div>

            {loginError && (
              <div className="login-error">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>{loginError}</span>
              </div>
            )}

            {resetSuccessMessage && (
              <div className="login-info">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>{resetSuccessMessage}</span>
              </div>
            )}

            <button className="login-button" type="submit" disabled={loginLoading}>
              {loginLoading ? (
                <>
                  <svg className="spinner" width="20" height="20" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" opacity="0.25" />
                    <path d="M12 2 A10 10 0 0 1 22 12" stroke="currentColor" strokeWidth="4" fill="none" strokeLinecap="round" />
                  </svg>
                  登录中...
                </>
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                    <polyline points="10 17 15 12 10 7" />
                    <line x1="15" y1="12" x2="3" y2="12" />
                  </svg>
                  登录
                </>
              )}
            </button>
          </form>
        )}

        {mode === 'register' && (
          <form className="login-form" onSubmit={handleRegisterSubmit}>
            <div className="form-group">
              <label htmlFor="register-phone">手机号</label>
              <div className="input-wrapper has-button">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 16.92V21a2 2 0 0 1-2.18 2A19.86 19.86 0 0 1 3 5.18 2 2 0 0 1 5 3h4.09a1 1 0 0 1 1 .75 12.05 12.05 0 0 0 .57 1.81 1 1 0 0 1-.23 1L9.91 8.09a16 16 0 0 0 6 6l1.53-1.53a1 1 0 0 1 1-.24 12.05 12.05 0 0 0 1.81.57 1 1 0 0 1 .75 1V21" />
                </svg>
                <input
                  id="register-phone"
                  type="tel"
                  value={registerForm.phone}
                  onChange={e => setRegisterForm(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="请输入手机号"
                  required
                />
                <button
                  type="button"
                  className="code-button"
                  onClick={() => handleSendCode(registerForm.phone, 'register', setRegisterInfo, setRegisterError, setRegisterCooldown, setRegisterCodeLoading)}
                  disabled={registerCodeLoading || registerCooldown > 0}
                >
                  {registerCodeLoading ? '发送中...' : registerCooldown > 0 ? `${registerCooldown}s` : '获取验证码'}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-code">验证码</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <input
                  id="register-code"
                  type="text"
                  value={registerForm.code}
                  onChange={e => setRegisterForm(prev => ({ ...prev, code: e.target.value }))}
                  placeholder="请输入验证码"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-username">用户名（可选）</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <input
                  id="register-username"
                  type="text"
                  value={registerForm.username}
                  onChange={e => setRegisterForm(prev => ({ ...prev, username: e.target.value }))}
                  placeholder="不填写默认使用手机号"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-fullname">姓名（可选）</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <input
                  id="register-fullname"
                  type="text"
                  value={registerForm.fullName}
                  onChange={e => setRegisterForm(prev => ({ ...prev, fullName: e.target.value }))}
                  placeholder="请输入姓名"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-password">密码</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <input
                  id="register-password"
                  type="password"
                  value={registerForm.password}
                  onChange={e => setRegisterForm(prev => ({ ...prev, password: e.target.value }))}
                  placeholder={`请输入不少于${MIN_PASSWORD_LENGTH}位密码`}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-confirm-password">确认密码</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <input
                  id="register-confirm-password"
                  type="password"
                  value={registerForm.confirmPassword}
                  onChange={e => setRegisterForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  placeholder="请再次输入密码"
                  required
                />
              </div>
            </div>

            {registerError && (
              <div className="login-error">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>{registerError}</span>
              </div>
            )}

            {registerInfo && (
              <div className="login-info">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>{registerInfo}</span>
              </div>
            )}

            <button className="login-button" type="submit" disabled={registerLoading}>
              {registerLoading ? '注册中...' : '注册并登录'}
            </button>
          </form>
        )}

        {mode === 'reset' && (
          <form className="login-form" onSubmit={handleResetSubmit}>
            <div className="form-group">
              <label htmlFor="reset-phone">手机号</label>
              <div className="input-wrapper has-button">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 16.92V21a2 2 0 0 1-2.18 2A19.86 19.86 0 0 1 3 5.18 2 2 0 0 1 5 3h4.09a1 1 0 0 1 1 .75 12.05 12.05 0 0 0 .57 1.81 1 1 0 0 1-.23 1L9.91 8.09a16 16 0 0 0 6 6l1.53-1.53a1 1 0 0 1 1-.24 12.05 12.05 0 0 0 1.81.57 1 1 0 0 1 .75 1V21" />
                </svg>
                <input
                  id="reset-phone"
                  type="tel"
                  value={resetForm.phone}
                  onChange={e => setResetForm(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="请输入手机号"
                  required
                />
                <button
                  type="button"
                  className="code-button"
                  onClick={() => handleSendCode(resetForm.phone, 'reset', setResetInfo, setResetError, setResetCooldown, setResetCodeLoading)}
                  disabled={resetCodeLoading || resetCooldown > 0}
                >
                  {resetCodeLoading ? '发送中...' : resetCooldown > 0 ? `${resetCooldown}s` : '获取验证码'}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="reset-code">验证码</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <input
                  id="reset-code"
                  type="text"
                  value={resetForm.code}
                  onChange={e => setResetForm(prev => ({ ...prev, code: e.target.value }))}
                  placeholder="请输入验证码"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="reset-password">新密码</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <input
                  id="reset-password"
                  type="password"
                  value={resetForm.newPassword}
                  onChange={e => setResetForm(prev => ({ ...prev, newPassword: e.target.value }))}
                  placeholder={`请输入不少于${MIN_PASSWORD_LENGTH}位的新密码`}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="reset-confirm-password">确认新密码</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <input
                  id="reset-confirm-password"
                  type="password"
                  value={resetForm.confirmPassword}
                  onChange={e => setResetForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  placeholder="请再次输入新密码"
                  required
                />
              </div>
            </div>

            {resetError && (
              <div className="login-error">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>{resetError}</span>
              </div>
            )}

            {resetInfo && (
              <div className="login-info">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>{resetInfo}</span>
              </div>
            )}

            <button className="login-button" type="submit" disabled={resetLoading}>
              {resetLoading ? '重置中...' : '提交新密码'}
            </button>
          </form>
        )}

        <div className="login-footer">
          {mode === 'login' && (
            <>
              <button type="button" className="link-button" onClick={() => changeMode('register')}>
                使用手机号注册
              </button>
              <button type="button" className="link-button" onClick={() => changeMode('reset')}>
                忘记密码？
              </button>
            </>
          )}
          {mode === 'register' && (
            <button type="button" className="link-button" onClick={() => changeMode('login')}>
              已有账号？返回登录
            </button>
          )}
          {mode === 'reset' && (
            <button type="button" className="link-button" onClick={() => changeMode('login')}>
              返回登录
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

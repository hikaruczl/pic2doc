import React, { useCallback, useEffect, useState } from 'react';
import SingleProcess from './components/SingleProcess';
import BatchProcess from './components/BatchProcess';
import Login from './components/Login';
import type { Provider, CurrentUserResponse } from './api/client';
import { getCurrentUser, onUnauthorized, setAuthToken as applyAuthToken } from './api/client';

type Tab = 'single' | 'batch' | 'help';

export default function App() {
  const [tab, setTab] = useState<Tab>('single');
  const [provider, setProvider] = useState<Provider>('Gemini');
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('authToken'));
  const [user, setUser] = useState<CurrentUserResponse | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const clearAuth = useCallback(() => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('authTokenExpires');
    applyAuthToken(null);
    setToken(null);
    setUser(null);
    setTab('single');
  }, []);

  const handleLogout = useCallback(() => {
    clearAuth();
    setAuthError(null);
  }, [clearAuth]);

  useEffect(() => {
    onUnauthorized(() => {
      setAuthError('登录已过期，请重新登录');
      clearAuth();
    });
    return () => onUnauthorized(null);
  }, [clearAuth]);

  useEffect(() => {
    let isMounted = true;
    let retryTimer: number | null = null;

    const bootstrap = async () => {
      const storedToken = localStorage.getItem('authToken');
      const expires = Number(localStorage.getItem('authTokenExpires') || '0');

      if (!storedToken || (expires && expires <= Date.now())) {
        clearAuth();
        if (isMounted) setInitializing(false);
        return;
      }

      applyAuthToken(storedToken);
      setToken(storedToken);

      try {
        const profile = await getCurrentUser();
        if (!isMounted) {
          return;
        }
        setUser(profile);
        setAuthError(null);
        retryTimer = null;
        setInitializing(false);
      } catch (err: any) {
        if (!isMounted) {
          return;
        }
        const status = err?.response?.status;
        if (status === 401) {
          clearAuth();
          retryTimer = null;
          setInitializing(false);
        } else {
          setAuthError('无法验证登录状态，请稍后重试');
          if (retryTimer) {
            window.clearTimeout(retryTimer);
          }
          retryTimer = window.setTimeout(bootstrap, 2000);
        }
      }
    };

    bootstrap();

    return () => {
      isMounted = false;
      if (retryTimer) {
        window.clearTimeout(retryTimer);
      }
    };
  }, [clearAuth]);

  const handleLoginSuccess = useCallback(
    async (newToken: string, expiresIn: number) => {
      localStorage.setItem('authToken', newToken);
      localStorage.setItem('authTokenExpires', String(Date.now() + expiresIn * 1000));
      applyAuthToken(newToken);
      setToken(newToken);
      setInitializing(true);
      try {
        const profile = await getCurrentUser();
        setUser(profile);
        setAuthError(null);
      } catch (err) {
        const status = (err as any)?.response?.status;
        if (status === 401) {
          clearAuth();
          setAuthError('登录凭据无效，请重试');
        } else {
          setAuthError('无法获取用户信息，请稍后再试');
        }
      } finally {
        setInitializing(false);
      }
    },
    [clearAuth]
  );

  if (initializing) {
    return (
      <div className="container">
        <div className="card">
          <p>正在加载...</p>
          {authError && <div className="error">{authError}</div>}
        </div>
      </div>
    );
  }

  if (!token || !user) {
    return (
      <div className="container">
        {authError && <div className="card"><div className="error">{authError}</div></div>}
        <Login onSuccess={handleLoginSuccess} />
      </div>
    );
  }

  return (
    <div className="container">
      <header>
        <div className="header-row">
          <div>
            <h1>图像转Word</h1>
            <p>智能识别数学公式，一键生成Word文档</p>
          </div>
          <div className="user-info">
            <span>{user.full_name || user.username}</span>
            <button className="ghost" onClick={handleLogout}>退出登录</button>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <button className={tab==='single'?'active':''} onClick={()=>setTab('single')}>单图像处理</button>
        <button className={tab==='batch'?'active':''} onClick={()=>setTab('batch')}>批量处理</button>
        <button className={tab==='help'?'active':''} onClick={()=>setTab('help')}>帮助</button>
      </nav>

      {tab === 'single' && (
        <div className="card">
          <div className="field">
            <label>LLM提供商</label>
            <select value={provider} onChange={e => setProvider(e.target.value as Provider)}>
              {(['OpenAI','Anthropic','Gemini','Qwen'] as Provider[]).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <SingleProcess provider={provider} />
        </div>
      )}

      {tab === 'batch' && <BatchProcess />}

      {tab === 'help' && (
        <div className="card">
          <h3>📖 使用说明</h3>
          <div className="help-content">
            <div className="help-section">
              <h4>1. 配置API密钥</h4>
              <p>确保已在 <code>.env</code> 文件中配置所需的API密钥</p>
            </div>
            <div className="help-section">
              <h4>2. 上传图像</h4>
              <p>支持 PNG、JPG、JPEG 和 PDF 格式的文件</p>
            </div>
            <div className="help-section">
              <h4>3. 选择LLM提供商</h4>
              <p>根据您的需求选择合适的模型提供商</p>
            </div>
            <div className="help-section">
              <h4>4. 开始处理</h4>
              <p>点击"开始处理"按钮，等待处理完成后即可下载生成的Word文档</p>
            </div>
          </div>
        </div>
      )}

      <footer>
        <small>图像转Word智能识别系统</small>
      </footer>
    </div>
  );
}

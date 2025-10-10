import React, { useEffect, useRef, useState } from 'react';
import { Provider, TaskResult, uploadSingle, getTask, downloadFile } from '../api/client';

export default function SingleProcess({ provider }: { provider: Provider }) {
  const [file, setFile] = useState<File | null>(null);
  const [includeImage, setIncludeImage] = useState(true);
  const [quality, setQuality] = useState(95);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [result, setResult] = useState<TaskResult['result'] | null>(null);
  const poller = useRef<number | null>(null);

  useEffect(() => () => { if (poller.current) window.clearInterval(poller.current); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) { setMessage('请先选择图像文件'); return; }
    setSubmitting(true); setProgress(0); setMessage('任务提交中...'); setResult(null);
    try {
      const { task_id } = await uploadSingle(file, provider, includeImage, quality);
      setMessage('任务已提交，开始处理...');
      poller.current = window.setInterval(async () => {
        try {
          const status = await getTask(task_id);
          setProgress(status.progress ?? 0);
          setMessage(status.message);
          if (status.status === 'completed') {
            setResult(status.result!);
            if (poller.current) window.clearInterval(poller.current);
            setSubmitting(false);
          } else if (status.status === 'failed') {
            if (poller.current) window.clearInterval(poller.current);
            setSubmitting(false);
          }
        } catch (err: any) {
          if (poller.current) window.clearInterval(poller.current);
          setMessage(err?.response?.data?.detail || err?.message || '获取任务状态失败');
          setSubmitting(false);
        }
      }, 1500);
    } catch (err: any) {
      setMessage(err?.response?.data?.detail || err?.message || '提交失败');
      setSubmitting(false);
    }
  }

  async function handleDownload() {
    if (!result) return;
    try {
      const blob = await downloadFile(result.output_path);
      const filename = result.output_path.split('/').pop() || 'document.docx';
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setMessage(err?.response?.data?.detail || err?.message || '下载失败');
    }
  }

  return (
    <>
      <form onSubmit={onSubmit}>
        <div className="field">
          <label>选择图像文件</label>
          <input type="file" accept=".png,.jpg,.jpeg,.pdf" onChange={e => setFile(e.target.files?.[0] || null)} />
          {file && <div className="file-info">已选择: {file.name}</div>}
        </div>

        <div className="grid">
          <div className="field">
            <label>
              <input type="checkbox" checked={includeImage} onChange={e => setIncludeImage(e.target.checked)} />
              <span>在Word中包含原始图像</span>
            </label>
          </div>
          <div className="field">
            <label>图像质量: {quality}%</label>
            <input type="range" min={70} max={100} step={5} value={quality} onChange={e => setQuality(parseInt(e.target.value))} />
          </div>
        </div>

        <button className="primary" disabled={submitting} type="submit">
          {submitting ? '处理中...' : '开始处理'}
        </button>
      </form>

      {(submitting || message) && (
        <div className="status">
          <div className="progress"><div className="bar" style={{ width: `${progress}%` }} /></div>
          <div className="message">{message}</div>
        </div>
      )}

      {result && (
        <div className="result">
          <h3>✅ 处理完成</h3>
          <div className="result-stats">
            <div className="stat-item">
              <span className="stat-label">总公式数</span>
              <span className="stat-value">{result.statistics.total_formulas}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">显示公式</span>
              <span className="stat-value">{result.statistics.display_formulas}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">行内公式</span>
              <span className="stat-value">{result.statistics.inline_formulas}</span>
            </div>
          </div>

          <button className="primary download-btn" onClick={handleDownload} type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            下载Word文档
          </button>

          {Array.isArray(result.statistics.formulas) && result.statistics.formulas.length > 0 && (
            <details className="formula-details">
              <summary>查看识别的公式 ({result.statistics.formulas.length}个)</summary>
              <ol className="formula-list">
                {result.statistics.formulas.slice(0, 10).map(([t, latex], i) => (
                  <li key={i}>
                    <span className="formula-type">[{t}]</span>
                    <code>{latex}</code>
                  </li>
                ))}
                {result.statistics.formulas.length > 10 && (
                  <li className="more-formulas">...还有 {result.statistics.formulas.length - 10} 个公式</li>
                )}
              </ol>
            </details>
          )}
        </div>
      )}
    </>
  );
}

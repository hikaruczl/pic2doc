import React, { useEffect, useRef, useState } from 'react';
import { Provider, uploadBatch, getBatchStatus } from '../api/client';

const PROVIDERS: Provider[] = ['OpenAI', 'Anthropic', 'Gemini', 'Qwen'];

export default function BatchProcess() {
  const [files, setFiles] = useState<File[]>([]);
  const [provider, setProvider] = useState<Provider>('Gemini');
  const [submitting, setSubmitting] = useState(false);
  const [summary, setSummary] = useState('');
  const poller = useRef<number | null>(null);

  useEffect(() => () => { if (poller.current) window.clearInterval(poller.current); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files.length) { setSummary('请上传至少一个文件'); return; }
    setSubmitting(true); setSummary('任务提交中...');
    try {
      const { batch_id, total_tasks } = await uploadBatch(files, provider);
      setSummary(`批处理任务已提交，总文件数: ${total_tasks}`);
      poller.current = window.setInterval(async () => {
        try {
          const s = await getBatchStatus(batch_id);
          setSummary(`总: ${s.total} | ✅ 完成: ${s.completed} | ⏳ 处理中: ${s.processing} | 💤 待处理: ${s.pending} | ❌ 失败: ${s.failed}`);
          if (s.completed + s.failed >= s.total) {
            if (poller.current) window.clearInterval(poller.current);
            setSubmitting(false);
          }
        } catch (err: any) {
          if (poller.current) window.clearInterval(poller.current);
          setSummary(err?.response?.data?.detail || err?.message || '获取批处理状态失败');
          setSubmitting(false);
        }
      }, 1500);
    } catch (err: any) {
      setSummary(err?.response?.data?.detail || err?.message || '提交失败');
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <form onSubmit={onSubmit}>
        <div className="field">
          <label>选择多个图像文件</label>
          <input
            type="file"
            accept=".png,.jpg,.jpeg,.pdf"
            multiple
            onChange={e => setFiles(Array.from(e.target.files || []))}
          />
          {files.length > 0 && <div className="file-info">已选择 {files.length} 个文件</div>}
        </div>

        <div className="field">
          <label>LLM提供商</label>
          <select value={provider} onChange={e => setProvider(e.target.value as Provider)}>
            {PROVIDERS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <button className="primary" disabled={submitting} type="submit">
          {submitting ? '处理中...' : '批量处理'}
        </button>
      </form>

      {summary && (
        <div className="status">
          <div className="message">{summary}</div>
        </div>
      )}
    </div>
  );
}

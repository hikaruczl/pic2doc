import React, { useEffect, useRef, useState } from 'react';
import { Provider, uploadBatch, getBatchStatus, BatchStatus, downloadFile } from '../api/client';

const PROVIDERS: Provider[] = ['OpenAI', 'Anthropic', 'Gemini', 'Qwen'];

export default function BatchProcess() {
  const [files, setFiles] = useState<File[]>([]);
  const [provider, setProvider] = useState<Provider>('Gemini');
  const [mergeDocuments, setMergeDocuments] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [summary, setSummary] = useState('');
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const poller = useRef<number | null>(null);

  useEffect(() => () => { if (poller.current) window.clearInterval(poller.current); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files.length) { setSummary('请上传至少一个文件'); return; }
    setSubmitting(true); setSummary('任务提交中...'); setBatchStatus(null);
    try {
      const { batch_id, total_tasks } = await uploadBatch(files, provider, mergeDocuments);
      setSummary(mergeDocuments
        ? `合并任务已提交，共 ${files.length} 个文件将合并为一个文档`
        : `批处理任务已提交，总文件数: ${total_tasks}`
      );
      poller.current = window.setInterval(async () => {
        try {
          const s = await getBatchStatus(batch_id);
          setBatchStatus(s);
          console.log('批量处理状态:', s); // 添加调试日志
          console.log('任务列表:', s.tasks); // 添加调试日志
          if (s.merge_mode) {
            setSummary(`合并处理: ${s.processing > 0 ? '⏳ 处理中' : s.completed > 0 ? '✅ 完成' : s.failed > 0 ? '❌ 失败' : '💤 等待中'}`);
          } else {
            setSummary(`总: ${s.total} | ✅ 完成: ${s.completed} | ⏳ 处理中: ${s.processing} | 💤 待处理: ${s.pending} | ❌ 失败: ${s.failed}`);
          }
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

  async function handleDownload(outputPath: string, filename: string) {
    try {
      const blob = await downloadFile(outputPath);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setSummary(err?.response?.data?.detail || err?.message || '下载失败');
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

        <div className="field">
          <label>
            <input
              type="checkbox"
              checked={mergeDocuments}
              onChange={e => setMergeDocuments(e.target.checked)}
            />
            <span>合并为单个文档</span>
          </label>
          <div className="field-hint">
            {mergeDocuments
              ? '所有图像将处理后合并到一个Word文档中'
              : '每个图像将生成独立的Word文档'}
          </div>
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

      {batchStatus && batchStatus.tasks && batchStatus.tasks.length > 0 && (
        <div className="batch-results">
          <h3>{batchStatus.merge_mode ? '处理结果' : '任务详情'}</h3>
          <div className="task-list">
            {batchStatus.tasks.map((task) => {
              const filename = batchStatus.merge_mode
                ? `合并文档 (${files.length} 个图像)`
                : task.file_path.split('/').pop() || '';
              return (
                <div key={task.task_id} className="task-item">
                  <div className="task-info">
                    <span className="task-filename">{filename}</span>
                    <span className={`task-status status-${task.status}`}>
                      {task.status === 'completed' && '✅ 完成'}
                      {task.status === 'processing' && '⏳ 处理中'}
                      {task.status === 'pending' && '💤 等待中'}
                      {task.status === 'failed' && '❌ 失败'}
                    </span>
                  </div>
                  {task.status === 'failed' && (
                    <div className="task-error">{task.message}</div>
                  )}
                  {task.status === 'completed' && task.result && (
                    <div className="task-actions">
                      <span className="task-stats">
                        公式数: {task.result.statistics.total_formulas}
                        {task.result.images_processed && ` | 已处理: ${task.result.images_processed} 个图像`}
                      </span>
                      <button
                        className="secondary"
                        onClick={() => handleDownload(task.result!.output_path, task.result!.output_path.split('/').pop() || 'document.docx')}
                      >
                        下载
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect, useCallback } from 'react';
import { Upload, FileSpreadsheet, Database, Trash2, Eye, EyeOff, CheckCircle, AlertCircle, X, Table, Zap, ArrowRight, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import type { UploadedTable, FilePreview, UploadResult, AutoDetectResult, DataMapping } from '../types';

const TYPE_LABELS: Record<string, string> = { sales: 'Sales Data', marketing: 'Marketing Data', inventory: 'Inventory Data', unknown: 'Unknown' };
const TYPE_COLORS: Record<string, string> = { sales: 'bg-green-500/15 text-green-400 border-green-500/30', marketing: 'bg-blue-500/15 text-blue-400 border-blue-500/30', inventory: 'bg-purple-500/15 text-purple-400 border-purple-500/30', unknown: 'bg-slate-500/15 text-slate-400 border-slate-500/30' };

export default function DataUploadPage() {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [tableName, setTableName] = useState('');
  const [preview, setPreview] = useState<FilePreview | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [autoDetect, setAutoDetect] = useState<AutoDetectResult | null>(null);
  const [mappings, setMappings] = useState<DataMapping[]>([]);
  const [tables, setTables] = useState<UploadedTable[]>([]);
  const [viewingTable, setViewingTable] = useState<{ name: string; data: { columns: string[]; rows: Array<Record<string, unknown>>; total_rows: number } } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'upload' | 'tables'>('upload');
  const [mappingApplied, setMappingApplied] = useState(false);

  const loadTables = useCallback(async () => {
    try {
      const [tablesRes, mappingsRes] = await Promise.all([api.getUploadedTables(), api.getMappings()]);
      setTables(tablesRes.tables || []);
      setMappings(mappingsRes.mappings || []);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { loadTables(); }, [loadTables]);

  const getMappedType = (tname: string) => mappings.find(m => m.table_name === tname)?.mapped_type;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setDragActive(false);
    if (e.dataTransfer.files?.[0]) selectFile(e.dataTransfer.files[0]);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) selectFile(e.target.files[0]);
  };

  const selectFile = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (!['csv', 'xlsx', 'xls', 'sql'].includes(ext)) { setError('Unsupported file type. Use CSV, Excel, or SQL.'); return; }
    setSelectedFile(file);
    setTableName(file.name.replace(/\.[^.]+$/, '').replace(/[^a-zA-Z0-9_]/g, '_'));
    setUploadResult(null); setAutoDetect(null); setError(''); setMappingApplied(false);
    if (ext !== 'sql') {
      try {
        setLoading(true);
        const [prevRes, detectRes] = await Promise.all([api.previewFile(file), api.autoDetectMapping(file)]);
        setPreview(prevRes);
        setAutoDetect(detectRes);
      } catch (e: unknown) { setError(e instanceof Error ? e.message : 'Preview failed'); }
      finally { setLoading(false); }
    } else { setPreview(null); setAutoDetect(null); }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      setLoading(true); setError('');
      const res = await api.uploadFile(selectedFile, tableName || undefined);
      setUploadResult(res);
      if (autoDetect && autoDetect.detected_type !== 'unknown') {
        await api.applyMapping({
          table_name: tableName || res.table_name,
          mapped_type: autoDetect.detected_type,
          column_mapping: Object.fromEntries(Object.entries(autoDetect.field_mappings).map(([k, v]) => [v.uploaded_column, k])),
        });
        setMappingApplied(true);
      }
      setSelectedFile(null); setPreview(null); setAutoDetect(null); setTableName('');
      loadTables(); setActiveTab('tables');
    } catch (e: unknown) { setError(e instanceof Error ? e.message : 'Upload failed'); }
    finally { setLoading(false); }
  };

  const handleViewTable = async (tname: string) => {
    try { setLoading(true); const res = await api.getTableData(tname, 100); setViewingTable({ name: tname, data: res }); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Failed to load table'); }
    finally { setLoading(false); }
  };

  const handleDeleteTable = async (tname: string) => {
    if (!confirm(`Delete table "${tname}"?`)) return;
    try { await api.deleteTable(tname); if (viewingTable?.name === tname) setViewingTable(null); loadTables(); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Delete failed'); }
  };

  const clearSelection = () => { setSelectedFile(null); setPreview(null); setAutoDetect(null); setTableName(''); setUploadResult(null); setError(''); };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-300">Data Upload</h1>
        <p className="text-slate-400 mt-1">Upload CSV, Excel, or SQL files — the system auto-detects and maps your data to KPIs</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <span className="text-red-300 text-sm">{error}</span>
          <button onClick={() => setError('')} className="ml-auto text-red-400 hover:text-red-300"><X className="w-4 h-4" /></button>
        </div>
      )}

      {mappingApplied && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-3 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-green-400" />
          <span className="text-green-300 text-sm">Data mapped successfully! The dashboard now reflects your uploaded data.</span>
        </div>
      )}

      {uploadResult && !mappingApplied && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg px-4 py-3 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-blue-400" />
          <span className="text-blue-300 text-sm">File uploaded. Go to "Uploaded Tables" to view and map your data to the dashboard.</span>
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-700">
        <button onClick={() => setActiveTab('upload')} className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${activeTab === 'upload' ? 'border-blue-500 text-blue-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
          <Upload className="w-4 h-4 inline mr-1.5" /> Upload File
        </button>
        <button onClick={() => setActiveTab('tables')} className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${activeTab === 'tables' ? 'border-blue-500 text-blue-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
          <Table className="w-4 h-4 inline mr-1.5" /> Uploaded Tables ({tables.length})
        </button>
      </div>

      {activeTab === 'upload' && (
        <div className="space-y-6">
          <div className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 cursor-pointer ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/50'}`} onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop} onClick={() => document.getElementById('file-input')?.click()}>
            <input id="file-input" type="file" accept=".csv,.xlsx,.xls,.sql" onChange={handleFileInput} className="hidden" />
            <Upload className="w-10 h-10 text-slate-500 mx-auto mb-3" />
            <p className="text-slate-300 font-medium">Drop your file here or click to browse</p>
            <p className="text-slate-500 text-sm mt-1">CSV, Excel (.xlsx), or SQL files up to 50MB</p>
          </div>

          {selectedFile && (
            <div className="bg-navy-800 border border-slate-700 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
                <div className="flex items-center gap-3">
                  {selectedFile.name.endsWith('.sql') ? <Database className="w-5 h-5 text-purple-400" /> : <FileSpreadsheet className="w-5 h-5 text-green-400" />}
                  <div>
                    <p className="text-sm font-medium text-slate-300">{selectedFile.name}</p>
                    <p className="text-xs text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
                <button onClick={clearSelection} className="text-slate-400 hover:text-slate-300 p-1"><X className="w-4 h-4" /></button>
              </div>

              <div className="px-4 py-3 border-b border-slate-700">
                <label className="block text-xs text-slate-400 mb-1">Table Name</label>
                <input type="text" value={tableName} onChange={(e) => setTableName(e.target.value)} placeholder="my_custom_table" className="w-full bg-navy-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono" />
              </div>

              {autoDetect && autoDetect.detected_type !== 'unknown' && (
                <div className="p-4 border-b border-slate-700">
                  <div className="flex items-center gap-2 mb-3">
                    <Zap className="w-4 h-4 text-yellow-400" />
                    <h3 className="text-sm font-medium text-slate-300">Auto-Detected Mapping</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${TYPE_COLORS[autoDetect.detected_type] || TYPE_COLORS.unknown}`}>
                      {TYPE_LABELS[autoDetect.detected_type] || autoDetect.detected_type}
                    </span>
                    <span className="text-xs text-slate-400">{Math.round(autoDetect.confidence * 100)}% confidence</span>
                  </div>
                  <div className="space-y-1.5">
                    {Object.entries(autoDetect.field_mappings).map(([field, mapping]) => (
                      <div key={field} className="flex items-center gap-2 text-xs">
                        <span className="bg-navy-900 text-blue-400 px-2 py-0.5 rounded font-mono">{mapping.uploaded_column}</span>
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                        <span className="text-slate-300 font-medium">{field}</span>
                        <span className="text-slate-500">({Math.round(mapping.confidence * 100)}%)</span>
                      </div>
                    ))}
                  </div>
                  {autoDetect.missing_fields.length > 0 && (
                    <p className="text-xs text-yellow-400/80 mt-2">Missing optional fields: {autoDetect.missing_fields.join(', ')}</p>
                  )}
                  {autoDetect.unmapped_columns.length > 0 && (
                    <p className="text-xs text-slate-500 mt-1">Unmapped columns: {autoDetect.unmapped_columns.join(', ')}</p>
                  )}
                  <p className="text-xs text-green-400/80 mt-2 flex items-center gap-1"><Zap className="w-3 h-3" /> This data will be connected to the dashboard automatically after upload</p>
                </div>
              )}

              {autoDetect && autoDetect.detected_type === 'unknown' && (
                <div className="p-4 border-b border-slate-700">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-slate-400" />
                    <p className="text-sm text-slate-400">Could not auto-detect KPI mapping. File will be uploaded but won't connect to the dashboard.</p>
                  </div>
                </div>
              )}

              {preview && (
                <div className="p-4">
                  <h3 className="text-sm font-medium text-slate-300 mb-3">Preview — {preview.total_rows.toLocaleString()} rows, {preview.total_columns} columns</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead><tr className="border-b border-slate-700">{Object.keys(preview.preview[0] || {}).map((k) => (<th key={k} className="px-2 py-1.5 text-left text-slate-400 font-medium whitespace-nowrap">{k}</th>))}</tr></thead>
                      <tbody>{preview.preview.slice(0, 5).map((row, i) => (<tr key={i} className="border-b border-slate-800">{Object.values(row).map((v, j) => (<td key={j} className="px-2 py-1.5 text-slate-300 whitespace-nowrap max-w-[150px] truncate">{v === null ? <span className="text-slate-600">null</span> : String(v)}</td>))}</tr>))}</tbody>
                    </table>
                  </div>
                </div>
              )}

              {selectedFile.name.endsWith('.sql') && !preview && (
                <div className="p-4"><p className="text-sm text-slate-400">SQL file will be executed directly against the database.</p></div>
              )}

              <div className="px-4 py-3 border-t border-slate-700 flex justify-end">
                <button onClick={handleUpload} disabled={loading} className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-300 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition flex items-center gap-2">
                  {loading ? (<><span className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" /> Processing...</>) : (<><Upload className="w-4 h-4" /> {autoDetect?.detected_type !== 'unknown' ? 'Upload & Connect to Dashboard' : 'Upload to Database'}</>)}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'tables' && (
        <div className="space-y-4">
          {tables.length === 0 ? (
            <div className="text-center py-12"><Table className="w-10 h-10 text-slate-600 mx-auto mb-3" /><p className="text-slate-400">No uploaded tables yet</p><button onClick={() => setActiveTab('upload')} className="mt-2 text-blue-400 hover:text-blue-300 text-sm">Upload your first file</button></div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tables.map((t) => {
                const mtype = getMappedType(t.table_name);
                return (
                  <div key={t.table_name} className="bg-navy-800 border border-slate-700 rounded-xl p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Database className="w-4 h-4 text-blue-400" />
                        <h3 className="text-sm font-mono font-medium text-slate-300">{t.table_name}</h3>
                      </div>
                      <div className="flex gap-1">
                        <button onClick={() => handleViewTable(t.table_name)} className="p-1.5 text-slate-400 hover:text-blue-400 rounded transition" title="View"><Eye className="w-3.5 h-3.5" /></button>
                        <button onClick={() => handleDeleteTable(t.table_name)} className="p-1.5 text-slate-400 hover:text-red-400 rounded transition" title="Delete"><Trash2 className="w-3.5 h-3.5" /></button>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      {mtype ? (
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border ${TYPE_COLORS[mtype] || TYPE_COLORS.unknown}`}>
                          <Zap className="w-2.5 h-2.5 inline mr-0.5" />{TYPE_LABELS[mtype] || mtype} — Connected
                        </span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded-full border bg-slate-500/10 text-slate-400 border-slate-500/30">Not mapped</span>
                      )}
                    </div>
                    <div className="mt-2 text-xs text-slate-400">
                      <p>{t.row_count.toLocaleString()} rows · {(t.columns || []).length} columns</p>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(t.columns || []).slice(0, 4).map((c) => (<span key={c.name} className="text-[10px] bg-navy-900 text-slate-400 px-1.5 py-0.5 rounded font-mono">{c.name}</span>))}
                      {(t.columns || []).length > 4 && <span className="text-[10px] text-slate-500">+{(t.columns || []).length - 4} more</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {viewingTable && (
            <div className="bg-navy-800 border border-slate-700 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
                <h3 className="text-sm font-medium text-slate-300 font-mono">{viewingTable.name} — {viewingTable.data.total_rows?.toLocaleString()} rows</h3>
                <button onClick={() => setViewingTable(null)} className="text-slate-400 hover:text-slate-300"><EyeOff className="w-4 h-4" /></button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b border-slate-700">{viewingTable.data.columns?.map((c) => (<th key={c} className="px-2 py-1.5 text-left text-slate-400 font-medium whitespace-nowrap">{c}</th>))}</tr></thead>
                  <tbody>{viewingTable.data.rows?.map((row, i) => (<tr key={i} className="border-b border-slate-700 hover:bg-navy-900">{Object.values(row).map((v, j) => (<td key={j} className="px-2 py-1.5 text-slate-300 whitespace-nowrap max-w-[200px] truncate">{v === null ? <span className="text-slate-500">null</span> : String(v)}</td>))}</tr>))}</tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

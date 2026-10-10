import React, { useState, useEffect } from 'react';
import { X, Save, FileText, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function SiteNoteModal({ domain, initialNote, onClose, onSaveSuccess }) {
  const [note, setNote] = useState(initialNote || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setNote(initialNote || '');
  }, [initialNote]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.post('/dashboard/sites/note', {
        domain: domain,
        note: note
      });
      onSaveSuccess(domain, note);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save note');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-sky-500/10 rounded-xl text-sky-400 border border-sky-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Catatan Optimasi Iklan</h3>
              <p className="text-xs text-sky-400 font-mono font-medium">{domain}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 flex-1">
          {error && (
            <div className="p-3 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Catatan Strategi & Optimasi (Google Ads / GAM)
            </label>
            <textarea
              rows={6}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Contoh: Target India Display, Max CPC Rp 3, Target CPA Rp 2.500, ECPC OFF..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all font-sans leading-relaxed"
              autoFocus
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-950/50 border-t border-slate-800 flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-all cursor-pointer"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 text-xs font-bold text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 rounded-xl shadow-lg shadow-sky-600/20 transition-all flex items-center space-x-2 cursor-pointer"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Menyimpan...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Simpan Catatan</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

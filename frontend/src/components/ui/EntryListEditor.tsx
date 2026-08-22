import React, { useState } from 'react';
import { Plus, Pencil, Trash2, X, Check } from 'lucide-react';

export interface EntryFieldDef {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'month' | 'checkbox';
  placeholder?: string;
  required?: boolean;
}

interface EntryListEditorProps {
  icon: React.ElementType;
  title: string;
  fields: EntryFieldDef[];
  items: Record<string, any>[];
  onChange: (items: Record<string, any>[]) => void;
  renderSummary: (item: Record<string, any>) => { primary: string; secondary?: string };
  addLabel: string;
  emptyLabel: string;
  saveLabel: string;
  cancelLabel: string;
}

/** Şirkete/pozisyona bağlı olmayan, genel amaçlı tekrarlanan-kayıt editörü —
 * iş deneyimi ve sertifika girdileri için kullanılıyor (ProfileIntake +
 * ProfileView). Her kayıt bir kart olarak listelenir; "+ Ekle" veya kalem
 * ikonu, fields prop'una göre üretilen küçük bir forma açılır. */
export function EntryListEditor({
  icon: Icon, title, fields, items, onChange, renderSummary,
  addLabel, emptyLabel, saveLabel, cancelLabel,
}: EntryListEditorProps) {
  // null: kapalı, -1: yeni kayıt ekleniyor, >=0: o index düzenleniyor
  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [draft, setDraft] = useState<Record<string, any>>({});

  const openNew = () => {
    const empty: Record<string, any> = {};
    fields.forEach(f => { empty[f.key] = f.type === 'checkbox' ? false : ''; });
    setDraft(empty);
    setEditingIdx(-1);
  };

  const openEdit = (idx: number) => {
    setDraft({ ...items[idx] });
    setEditingIdx(idx);
  };

  const cancel = () => {
    setEditingIdx(null);
    setDraft({});
  };

  const save = () => {
    const missingRequired = fields.some(f => f.required && f.type !== 'checkbox' && !String(draft[f.key] || '').trim());
    if (missingRequired) return;
    if (editingIdx === -1) {
      onChange([...items, draft]);
    } else if (editingIdx !== null) {
      onChange(items.map((it, i) => (i === editingIdx ? draft : it)));
    }
    cancel();
  };

  const remove = (idx: number) => onChange(items.filter((_, i) => i !== idx));

  const renderForm = (key: string) => (
    <div key={key} className="bg-surface-container-lowest border border-primary-container/30 rounded-lg p-4 space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {fields.map(f => (
          <div key={f.key} className={f.type === 'textarea' ? 'md:col-span-2 space-y-1.5' : 'space-y-1.5'}>
            {f.type !== 'checkbox' && (
              <label className="text-xs font-label text-on-surface-variant">{f.label}{f.required ? ' *' : ''}</label>
            )}
            {f.type === 'textarea' ? (
              <textarea
                value={draft[f.key] || ''}
                onChange={e => setDraft({ ...draft, [f.key]: e.target.value })}
                placeholder={f.placeholder}
                rows={2}
                className="w-full bg-surface-container-highest border border-outline-variant/15 rounded-md px-3 py-2 text-sm text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-primary-container resize-none"
              />
            ) : f.type === 'checkbox' ? (
              <label className="flex items-center gap-2 text-sm font-label text-on-surface-variant cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={!!draft[f.key]}
                  onChange={e => setDraft({ ...draft, [f.key]: e.target.checked })}
                  className="rounded border-outline-variant/30"
                />
                {f.label}
              </label>
            ) : (
              <input
                type={f.type === 'month' ? 'month' : 'text'}
                value={draft[f.key] || ''}
                onChange={e => setDraft({ ...draft, [f.key]: e.target.value })}
                placeholder={f.placeholder}
                className="w-full bg-surface-container-highest border border-outline-variant/15 rounded-md px-3 py-2 text-sm text-on-surface placeholder-on-surface-variant/40 focus:outline-none focus:border-primary-container"
              />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={cancel} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-label text-on-surface-variant hover:text-on-surface transition-colors">
          <X className="w-3.5 h-3.5" /> {cancelLabel}
        </button>
        <button type="button" onClick={save} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-label text-white bg-primary-container rounded-md hover:bg-blue-700 transition-colors">
          <Check className="w-3.5 h-3.5" /> {saveLabel}
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-3">
      <label className="font-label text-sm text-on-surface-variant flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5" /> {title}
      </label>

      {items.length === 0 && editingIdx === null && (
        <p className="text-xs text-on-surface-variant/60 italic">{emptyLabel}</p>
      )}

      <div className="space-y-2">
        {items.map((item, idx) => {
          if (editingIdx === idx) return renderForm(`edit-${idx}`);
          const { primary, secondary } = renderSummary(item);
          return (
            <div key={idx} className="flex items-start justify-between gap-3 bg-surface-container-lowest border border-outline-variant/15 rounded-lg px-4 py-3">
              <div className="min-w-0">
                <div className="text-sm font-label text-on-surface truncate">{primary}</div>
                {secondary && <div className="text-xs text-on-surface-variant mt-0.5 truncate">{secondary}</div>}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button type="button" onClick={() => openEdit(idx)} className="p-1.5 text-on-surface-variant hover:text-primary transition-colors" aria-label="edit">
                  <Pencil className="w-3.5 h-3.5" />
                </button>
                <button type="button" onClick={() => remove(idx)} className="p-1.5 text-on-surface-variant hover:text-error transition-colors" aria-label="delete">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {editingIdx === -1 && renderForm('new')}

      {editingIdx === null && (
        <button type="button" onClick={openNew} className="flex items-center gap-1.5 text-sm font-label text-primary hover:underline">
          <Plus className="w-4 h-4" /> {addLabel}
        </button>
      )}
    </div>
  );
}

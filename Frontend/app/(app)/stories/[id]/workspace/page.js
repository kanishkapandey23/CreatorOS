'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Save, Sparkles, History, Users, X, Copy, Check } from 'lucide-react';
import { workspaceService } from '@/services/workspace.service';
import { storyService } from '@/services/story.service';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const SECTIONS = [
  { id: 'hook', label: 'Hook', hint: 'A single line that stops the scroll.' },
  { id: 'experience', label: 'Experience', hint: 'What happened, in your voice.' },
  { id: 'conflict', label: 'Conflict', hint: 'The friction or tension that mattered.' },
  { id: 'lesson', label: 'Lesson', hint: 'What you took away — quietly.' },
  { id: 'cta', label: 'Call to action', hint: 'A small invitation, not a sales line.' },
];

export default function ContentWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const { data: story } = useQuery({ queryKey: ['story', params.id], queryFn: () => storyService.get(params.id) });
  const { data: draft } = useQuery({ queryKey: ['draft', params.id], queryFn: () => workspaceService.getDraft(params.id) });
  const [sections, setSections] = useState({ hook: '', experience: '', conflict: '', lesson: '', cta: '' });
  const [savedAt, setSavedAt] = useState(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [polishedText, setPolishedText] = useState('');
  const [isPolishing, setIsPolishing] = useState(false);

  // Dynamic Sidebar States
  const [suggestions, setSuggestions] = useState([
    'Soften the hook by 4 words',
    'Move lesson before conflict',
    'Add a sensory detail'
  ]);
  const [isFetchingSuggestions, setIsFetchingSuggestions] = useState(false);
  const [history, setHistory] = useState([]);
  const [collaborators, setCollaborators] = useState(['colleague@creatoros.co']);
  const [inviteEmail, setInviteEmail] = useState('');

  const handleRestoreHistory = (historyItem) => {
    setSections(historyItem.sections);
    toast.success(`Restored draft to checkpoint from ${new Date(historyItem.timestamp).toLocaleTimeString()}`);
  };

  const handleRemoveSuggestion = (suggestion) => {
    setSuggestions(prev => prev.filter(s => s !== suggestion));
  };

  const handleInvite = (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(inviteEmail)) {
      toast.error('Please enter a valid email address');
      return;
    }
    
    if (collaborators.includes(inviteEmail.trim())) {
      toast.error('Editor already invited');
      return;
    }
    
    setCollaborators(prev => [...prev, inviteEmail.trim()]);
    toast.success(`Invitation sent to ${inviteEmail.trim()}`);
    setInviteEmail('');
  };

  const handleRemoveCollaborator = (email) => {
    setCollaborators(prev => prev.filter(c => c !== email));
    toast.success(`Removed editor: ${email}`);
  };

  const assembledText = [
    sections.hook,
    sections.experience,
    sections.conflict,
    sections.lesson,
    sections.cta
  ].filter(val => val && val.trim()).join('\n\n');

  const handleOpenPreview = async () => {
    setIsPreviewOpen(true);
    setIsPolishing(true);
    try {
      const res = await workspaceService.getPolishedPreview(params.id, sections);
      setPolishedText(res.polishedText);
    } catch (err) {
      toast.error("Failed to generate polished preview");
      setPolishedText(assembledText);
    } finally {
      setIsPolishing(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(polishedText || assembledText);
    setCopied(true);
    toast.success('Polished draft copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  useEffect(() => {
    if (draft?.sections) setSections(draft.sections);
  }, [draft]);

  // Autosave-ready (debounced placeholder)
  useEffect(() => {
    const t = setTimeout(async () => {
      try {
        const res = await workspaceService.saveDraft({ storyId: params.id, sections });
        setSavedAt(res.savedAt);
        
        // Add to history
        setHistory(prev => {
          if (prev.some(h => h.timestamp === res.savedAt)) return prev;
          return [{ timestamp: res.savedAt, sections: JSON.parse(JSON.stringify(sections)) }, ...prev].slice(0, 5);
        });
        
        // Fetch AI suggestions
        setIsFetchingSuggestions(true);
        const sugRes = await workspaceService.getSuggestions(params.id);
        if (sugRes.suggestions && sugRes.suggestions.length > 0) {
          setSuggestions(sugRes.suggestions);
        }
      } catch (err) {
        console.error("Autosave/Suggestions error:", err);
      } finally {
        setIsFetchingSuggestions(false);
      }
    }, 800);
    return () => clearTimeout(t);
  }, [sections, params.id]);

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col xl:flex-row">
      <div className="min-w-0 flex-1">
        <div className="sticky top-14 z-10 border-b border-line bg-canvas/85 px-5 py-3 backdrop-blur-md md:px-8">
          <div className="mx-auto flex max-w-3xl items-center justify-between">
            <button onClick={() => router.back()} className="inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted hover:text-ink"><ArrowLeft className="h-3.5 w-3.5" /> Back to story</button>
            <div className="flex items-center gap-3 text-[11.5px] text-ink-subtle">
              <Save className="h-3.5 w-3.5" />{savedAt ? `Saved ${new Date(savedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Autosaving…'}
            </div>
          </div>
        </div>

        <div className="mx-auto max-w-3xl px-5 py-10 md:px-8 md:py-12">
          <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Workspace</p>
          <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-tight tracking-tight text-ink md:text-[40px]">{story?.title || 'Untitled story'}</h1>
          <p className="mt-2 text-[14px] text-ink-muted">Write the piece, section by section. Nothing here is final.</p>

          <div className="mt-10 space-y-8">
            {SECTIONS.map((sec) => (
              <section key={sec.id}>
                <div className="flex items-baseline justify-between">
                  <h2 className="font-display text-[18px] font-semibold text-ink">{sec.label}</h2>
                  <span className="text-[11.5px] text-ink-subtle">{sec.hint}</span>
                </div>
                <textarea
                  value={sections[sec.id]}
                  onChange={(e) => setSections({ ...sections, [sec.id]: e.target.value })}
                  placeholder="Start writing…"
                  className="mt-2 min-h-[120px] w-full resize-y rounded-2xl border border-line bg-card px-5 py-4 text-[15px] leading-relaxed text-ink shadow-soft placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand/30"
                />
              </section>
            ))}
          </div>

          <div className="mt-12 flex items-center justify-between border-t border-line pt-6">
            <p className="text-[12px] text-ink-subtle">Your draft is private. Only you can see it.</p>
            <Button onClick={handleOpenPreview} className="h-10 rounded-xl bg-ink px-4 text-[13px] text-white hover:bg-ink/90">Preview</Button>
          </div>
        </div>
      </div>

      <aside className="hidden w-[320px] shrink-0 border-l border-line bg-card xl:block">
        <div className="sticky top-14 space-y-5 p-5">
          <div>
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle">
              <Sparkles className="h-3.5 w-3.5 text-brand" /> AI suggestions
              {isFetchingSuggestions && <span className="h-2 w-2 rounded-full bg-brand animate-pulse" />}
            </div>
            <div className="mt-3 space-y-2">
              {suggestions.map((s, idx) => (
                <div 
                  key={idx} 
                  className={`relative group rounded-xl border border-line bg-canvas hover:bg-secondary/20 px-3 py-2.5 transition-colors ${
                    isFetchingSuggestions ? 'opacity-50' : ''
                  }`}
                >
                  <div className="text-[12.5px] leading-relaxed text-ink-muted pr-4">{s}</div>
                  <button
                    onClick={() => handleRemoveSuggestion(s)}
                    className="absolute right-2 top-2 text-ink-subtle hover:text-ink opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded"
                    title="Dismiss suggestion"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
              {suggestions.length === 0 && (
                <div className="rounded-xl border border-dashed border-line bg-canvas/30 px-3 py-3 text-[12px] text-ink-subtle text-center">
                  No new suggestions. Keep writing!
                </div>
              )}
            </div>
            <p className="mt-2 text-[11px] text-ink-subtle">Suggestions will arrive here. Take what helps. Ignore the rest.</p>
          </div>
          <div className="soft-divider" />
          <div>
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle"><History className="h-3.5 w-3.5" /> Version history</div>
            <p className="mt-1.5 text-[12px] text-ink-muted">Every save creates a quiet checkpoint.</p>
            <div className="mt-3 space-y-1.5">
              {history.length === 0 ? (
                <div className="rounded-xl border border-dashed border-line bg-canvas/30 px-3 py-3 text-[12px] text-ink-subtle text-center">
                  No checkpoints yet. Type to save.
                </div>
              ) : (
                history.map((h, i) => (
                  <button
                    key={h.timestamp}
                    onClick={() => handleRestoreHistory(h)}
                    className="w-full text-left flex items-center justify-between rounded-xl bg-canvas/60 hover:bg-secondary/40 px-3 py-2 border border-line/40 transition-colors group"
                  >
                    <div className="flex flex-col min-w-0">
                      <span className="text-[12px] font-medium text-ink-muted group-hover:text-ink">
                        Checkpoint {history.length - i}
                      </span>
                      <span className="text-[10px] text-ink-subtle">
                        {new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                    <span className="text-[10px] font-medium text-brand opacity-0 group-hover:opacity-100 transition-opacity">
                      Restore
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
          <div className="soft-divider" />
          <div>
            <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle"><Users className="h-3.5 w-3.5" /> Collaboration</div>
            <div className="mt-3 space-y-3">
              {/* Invite Input */}
              <form onSubmit={handleInvite} className="flex gap-2">
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="editor@example.com"
                  className="h-8 min-w-0 flex-1 rounded-lg border border-line bg-canvas px-2.5 text-[12px] text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-brand/30"
                />
                <Button type="submit" className="h-8 rounded-lg bg-ink px-3 text-[11px] text-white hover:bg-ink/90">Invite</Button>
              </form>

              {/* Collaborators List */}
              <div className="space-y-1.5">
                {collaborators.map((email) => (
                  <div key={email} className="flex items-center justify-between rounded-xl bg-canvas/60 px-3 py-1.5 border border-line/40">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="h-5 w-5 shrink-0 rounded-full bg-brand/10 text-brand text-[9.5px] font-bold flex items-center justify-center">
                        {email.charAt(0).toUpperCase()}
                      </div>
                      <span className="truncate text-[12px] text-ink-muted">{email}</span>
                    </div>
                    <button 
                      onClick={() => handleRemoveCollaborator(email)}
                      className="text-ink-subtle hover:text-red-500 p-0.5 rounded transition-colors"
                      title="Remove editor"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Dynamic Preview Modal */}
      {isPreviewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl bg-canvas border border-line rounded-2xl shadow-pop flex flex-col max-h-[85vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-line bg-card/40">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-brand" />
                <h3 className="font-display text-[16px] font-semibold text-ink">Assembled Post Preview</h3>
              </div>
              <button 
                onClick={() => setIsPreviewOpen(false)}
                className="rounded-lg p-1.5 text-ink-muted hover:bg-secondary hover:text-ink transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 bg-card/10">
              {isPolishing ? (
                <div className="flex flex-col items-center justify-center py-12 gap-3">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand border-t-transparent" />
                  <p className="text-[13.5px] text-ink-muted">Agent 2 is analyzing trends and polishing your draft...</p>
                </div>
              ) : !(polishedText || assembledText).trim() ? (
                <p className="text-[13.5px] italic text-ink-subtle text-center py-10">Start writing sections to see your preview polished here!</p>
              ) : (
                <div className="bg-white border border-line/60 rounded-xl p-5 shadow-soft font-sans text-[14.5px] leading-relaxed text-ink whitespace-pre-wrap select-text text-left">
                  {polishedText || assembledText}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-line bg-card/40 flex items-center justify-between">
              <span className="text-[11.5px] text-ink-subtle">
                {(polishedText || assembledText).split(/\s+/).filter(Boolean).length} words · {(polishedText || assembledText).length} characters
              </span>
              <div className="flex gap-2">
                <Button 
                  onClick={() => setIsPreviewOpen(false)} 
                  variant="outline" 
                  className="h-9 rounded-xl border-line text-[12.5px] hover:bg-secondary/40"
                >
                  Close
                </Button>
                <Button 
                  onClick={handleCopy}
                  disabled={isPolishing || !(polishedText || assembledText).trim()}
                  className="h-9 rounded-xl bg-ink text-white hover:bg-ink/90 text-[12.5px] font-semibold gap-1.5"
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied!' : 'Copy Polished Post'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

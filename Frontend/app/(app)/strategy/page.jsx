'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, Send, BookOpen, ArrowUpRight, MessageSquare, 
  Check, RotateCcw, Info, User, HelpCircle, Copy, CheckCircle2 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { strategyService } from '@/services/strategy.service';

const easing = { duration: 0.35, ease: [0.22, 1, 0.36, 1] };

export default function StrategyPage() {
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [refining, setRefining] = useState(false);
  const [copiedHook, setCopiedHook] = useState(null);
  
  const chatEndRef = useRef(null);

  // Fetch memories list
  const { data: memories = [], isLoading: loadingMemories } = useQuery({
    queryKey: ['memories'],
    queryFn: () => strategyService.listMemories(),
  });

  // Fetch session details if activeSessionId is set
  const { data: session = null, isLoading: loadingSession } = useQuery({
    queryKey: ['chatSession', activeSessionId],
    queryFn: () => strategyService.getSessionDetails(activeSessionId),
    enabled: !!activeSessionId,
    refetchInterval: (data) => (data?.status === 'active' ? 3000 : false), // Poll active chats
  });

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session?.messages]);

  // Start new strategy session
  const startSessionMutation = useMutation({
    mutationFn: (memoryId) => strategyService.startSession(memoryId),
    onSuccess: (data) => {
      setActiveSessionId(data.id);
      queryClient.invalidateQueries(['chatSession', data.id]);
      toast.success('Strategy session initiated');
    },
    onError: () => {
      toast.error('Failed to start strategy session');
    }
  });

  // Send message to agent
  const sendMessageMutation = useMutation({
    mutationFn: ({ sessionId, msg }) => strategyService.sendMessage(sessionId, msg),
    onSuccess: (data) => {
      setInputMessage('');
      queryClient.invalidateQueries(['chatSession', activeSessionId]);
      queryClient.invalidateQueries(['workspace']); // Refresh workspace stories count
      if (data.isCompleted) {
        toast.success('Opportunity structured successfully!');
      }
    },
    onSettled: () => {
      setSending(false);
    }
  });

  // Submit refinement feedback
  const feedbackMutation = useMutation({
    mutationFn: ({ oppId, fb }) => strategyService.submitFeedback(oppId, fb),
    onSuccess: () => {
      queryClient.invalidateQueries(['chatSession', activeSessionId]);
      setFeedbackText('');
      toast.success('Opportunity hooks refined!');
    },
    onSettled: () => {
      setRefining(false);
    }
  });

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || sending) return;
    setSending(true);
    sendMessageMutation.mutate({ sessionId: activeSessionId, msg: inputMessage });
  };

  const handleRefineOpportunity = (e) => {
    e.preventDefault();
    if (!feedbackText.trim() || refining || !session?.opportunity_id) return;
    
    setRefining(true);
    feedbackMutation.mutate({ oppId: session.opportunity_id, fb: feedbackText });
  };

  const handleCopyHook = (hook, index) => {
    navigator.clipboard.writeText(hook);
    setCopiedHook(index);
    toast.success('Hook copied to clipboard');
    setTimeout(() => setCopiedHook(null), 2000);
  };

  // Get active opportunity details for the right panel
  const [activeOpportunity, setActiveOpportunity] = useState(null);
  useEffect(() => {
    if (session?.status === 'completed' && session?.opportunity_id) {
      strategyService.getStory(session.opportunity_id).then((detail) => {
        setActiveOpportunity({
          id: session.opportunity_id,
          ...detail,
          hooks: detail.hooks || [],
          structure: detail.structure || [],
        });
      }).catch((err) => {
        console.error("Failed to load opportunity", err);
      });
    } else {
      setActiveOpportunity(null);
    }
  }, [session]);

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col lg:flex-row overflow-hidden">
      {/* 1. Left Panel: Memory Timeline */}
      <aside className="w-full lg:w-[320px] shrink-0 border-r border-line bg-card flex flex-col h-[calc(100vh-3.5rem)]">
        <div className="p-5 border-b border-line bg-canvas/30">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Engine</p>
          <h2 className="mt-1 font-display text-[18px] font-semibold text-ink">Creator Memories</h2>
          <p className="mt-1 text-[12.5px] text-ink-muted">Select a memory to strategize content.</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loadingMemories ? (
            <p className="text-[12.5px] text-ink-subtle p-3 text-center">Loading memories timeline…</p>
          ) : memories.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-6 text-center border border-dashed border-line rounded-2xl bg-canvas/40">
              <BookOpen className="h-6 w-6 text-ink-subtle" />
              <p className="mt-2 text-[13px] font-semibold text-ink">No memories yet</p>
              <p className="mt-1 text-[12px] text-ink-muted">Complete a reflection to surface structured memories.</p>
            </div>
          ) : (
            memories.map((m) => (
              <div 
                key={m.id} 
                className={`group p-4 border rounded-2xl bg-canvas/60 hover:bg-canvas transition-colors duration-250 ${
                  session?.memory?.id === m.id ? 'border-brand ring-1 ring-brand/10' : 'border-line'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="outline" className="rounded-full border-line bg-card text-[10px] font-normal uppercase text-ink-subtle">
                    {m.memory_type.replace('_', ' ')}
                  </Badge>
                  <span className="text-[10px] text-ink-subtle">{m.createdAt.split(' ')[0]}</span>
                </div>
                
                <h4 className="mt-2 font-display text-[14px] font-semibold text-ink leading-snug group-hover:text-brand transition-colors">
                  {m.event}
                </h4>
                
                {m.turning_point && (
                  <p className="mt-1.5 text-[12px] text-ink-muted leading-relaxed italic border-l border-line pl-2">
                    Turning point: {m.turning_point}
                  </p>
                )}
                
                <div className="mt-3 flex flex-wrap gap-1">
                  {m.topic.map(t => (
                    <Badge key={t} variant="secondary" className="rounded-full text-[9.5px] py-0 px-2 font-normal text-ink-muted bg-secondary/80">
                      #{t}
                    </Badge>
                  ))}
                </div>

                <div className="mt-3.5 pt-3 border-t border-line/65 flex justify-end">
                  <Button 
                    onClick={() => startSessionMutation.mutate(m.id)}
                    disabled={startSessionMutation.isPending}
                    size="sm" 
                    className="h-8 rounded-lg bg-ink text-white hover:bg-ink/90 text-[11.5px] px-3 gap-1"
                  >
                    Strategize <ArrowUpRight className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* 2. Center Panel: Interactive Chat with Agent 2 */}
      <section className="flex-1 border-r border-line bg-canvas flex flex-col h-[calc(100vh-3.5rem)]">
        {/* Header info */}
        <div className="px-6 py-4 border-b border-line bg-card/40 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-brand-soft text-brand flex items-center justify-center">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-display text-[15px] font-semibold text-ink">
                {session ? session.title : 'Creative Strategy Agent'}
              </h3>
              <p className="text-[11.5px] text-ink-muted leading-none">
                {session ? `Session status: ${session.status}` : 'A content framework strategist'}
              </p>
            </div>
          </div>
          
          {session && (
            <Button 
              onClick={() => startSessionMutation.mutate(session.memory?.id)}
              variant="outline" 
              className="h-8 rounded-lg border-line text-[11.5px] gap-1 hover:bg-secondary/40"
            >
              <RotateCcw className="h-3 w-3" /> Restart
            </Button>
          )}
        </div>

        {/* Chat Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!activeSessionId ? (
            <div className="h-full flex flex-col items-center justify-center max-w-md mx-auto text-center px-4">
              <div className="h-12 w-12 rounded-2xl bg-secondary text-ink flex items-center justify-center shadow-soft">
                <MessageSquare className="h-5.5 w-5.5" />
              </div>
              <h3 className="mt-4 font-display text-[18px] font-semibold text-ink">Unlock your stories</h3>
              <p className="mt-2 text-[13.5px] leading-relaxed text-ink-muted">
                AI should manage your content journey, not replace your creativity. Select a memory from the timeline or start a brainstorming session.
              </p>
              <div className="mt-6 flex flex-wrap gap-2.5 justify-center">
                <Button 
                  onClick={() => startSessionMutation.mutate(null)}
                  className="rounded-xl bg-ink text-white hover:bg-ink/90 text-[13px] h-10 px-4"
                >
                  Start blank brainstorm
                </Button>
              </div>
            </div>
          ) : (
            <>
              {session?.messages.map((m) => (
                <div 
                  key={m.id} 
                  className={`flex gap-3 max-w-xl ${m.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
                >
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 text-white ${
                    m.role === 'user' ? 'bg-ink' : 'bg-brand'
                  }`}>
                    {m.role === 'user' ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                  </div>
                  
                  <div className={`rounded-2xl px-4 py-3 shadow-soft border ${
                    m.role === 'user' 
                      ? 'bg-card border-line text-ink text-[14px] leading-relaxed' 
                      : 'bg-white border-line/60 text-ink text-[14.5px] leading-relaxed whitespace-pre-wrap'
                  }`}>
                    {m.content}
                  </div>
                </div>
              ))}
              
              {sending && (
                <div className="flex gap-3 max-w-xl">
                  <div className="h-8 w-8 rounded-full bg-brand flex items-center justify-center text-white">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div className="bg-white border border-line/60 rounded-2xl px-4 py-3 shadow-soft flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-ink-subtle animate-bounce" />
                    <span className="h-2 w-2 rounded-full bg-ink-subtle animate-bounce delay-150" />
                    <span className="h-2 w-2 rounded-full bg-ink-subtle animate-bounce delay-300" />
                  </div>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </>
          )}
        </div>

        {/* Input box */}
        {activeSessionId && (
          <div className="p-4 border-t border-line bg-card/30">
            <form onSubmit={handleSendMessage} className="flex gap-2 max-w-3xl mx-auto">
              <input 
                disabled={session?.status === 'completed' || sending}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={
                  session?.status === 'completed' 
                    ? "Session completed. Opportunities structured." 
                    : "Type your answer here..."
                }
                className="flex-1 rounded-xl border border-line bg-card px-4 py-2.5 text-[14px] placeholder:text-ink-subtle text-ink shadow-soft focus:outline-none focus:ring-1 focus:ring-brand"
              />
              <Button 
                type="submit"
                disabled={session?.status === 'completed' || !inputMessage.trim() || sending}
                className="rounded-xl bg-ink hover:bg-ink/90 text-white px-4 h-10 shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        )}
      </section>

      {/* 3. Right Panel: Retrieved Context & Content Opportunities */}
      <aside className="w-full lg:w-[350px] shrink-0 bg-card flex flex-col h-[calc(100vh-3.5rem)] overflow-y-auto">
        <div className="p-5 border-b border-line bg-canvas/30">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-ink-subtle">Context</p>
          <h2 className="mt-1 font-display text-[18px] font-semibold text-ink">Active Strategy Panel</h2>
        </div>

        <div className="p-5 space-y-6">
          {/* Active Story Framework */}
          {session?.framework && (
            <div className="p-4 rounded-2xl border border-dashed border-line bg-canvas/40">
              <div className="flex items-center gap-2 text-[11.5px] font-medium uppercase tracking-wider text-ink-subtle">
                <Info className="h-3.5 w-3.5 text-brand" /> Retrieved Framework
              </div>
              <h4 className="mt-2 font-display text-[14.5px] font-bold text-ink">{session.framework.title}</h4>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-ink-muted whitespace-pre-line bg-canvas p-3 rounded-xl border border-line/60">
                {session.framework.content}
              </p>
            </div>
          )}

          {/* Generated Opportunity Card */}
          {session?.status === 'completed' && activeOpportunity && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-5 rounded-2xl border border-brand/35 bg-white shadow-soft relative overflow-hidden"
            >
              <div className="pointer-events-none absolute -right-16 -top-16 h-36 w-36 rounded-full bg-brand-soft blur-2xl" />
              
              <div className="relative">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4.5 w-4.5 text-brand" />
                  <span className="text-[11.5px] font-medium text-brand">Opportunity Structured</span>
                </div>
                
                <h4 className="mt-3 font-display text-[16px] font-bold text-ink leading-snug">
                  {activeOpportunity.title}
                </h4>
                
                {/* Scroll stopper hooks */}
                <div className="mt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">Hook Options</p>
                  <div className="mt-2 space-y-2">
                    {activeOpportunity.hooks ? (
                      activeOpportunity.hooks.map((h, i) => (
                        <div key={i} className="flex gap-1.5 items-start bg-secondary/50 rounded-xl p-2.5 border border-line/50 text-[12.5px] text-ink relative group">
                          <p className="flex-1 pr-6 leading-relaxed">{h}</p>
                          <button 
                            onClick={() => handleCopyHook(h, i)}
                            className="absolute right-2 top-2 text-ink-subtle hover:text-ink transition-colors opacity-0 group-hover:opacity-100"
                          >
                            {copiedHook === i ? <Check className="h-3.5 w-3.5 text-brand" /> : <Copy className="h-3.5 w-3.5" />}
                          </button>
                        </div>
                      ))
                    ) : (
                      <div className="text-[12.5px] text-ink-muted">No hooks generated. Add custom feedback below to create them.</div>
                    )}
                  </div>
                </div>
                
                {/* Structure blueprint */}
                <div className="mt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">Structure Blueprint</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {(activeOpportunity.structure ?? []).map((step, idx) => (
                      <div key={step} className="flex items-center gap-1">
                        <Badge variant="secondary" className="rounded-full text-[10.5px] font-normal text-ink-muted capitalize bg-secondary py-0.5">
                          {idx + 1}. {step}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Direct action links */}
                <div className="mt-6 flex gap-2">
                  <Button 
                    asChild
                    className="flex-1 h-9 rounded-xl bg-ink text-white text-[12.5px] hover:bg-ink/90 font-medium gap-1"
                  >
                    <a href={`/stories/${activeOpportunity.id}/workspace`}>
                      Open Workspace <ArrowUpRight className="h-3.5 w-3.5" />
                    </a>
                  </Button>
                </div>

                {/* Feedback refiner form */}
                <div className="mt-6 pt-5 border-t border-line">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-subtle">Refine Opportunity (Feedback Loop)</p>
                  <form onSubmit={handleRefineOpportunity} className="mt-2.5 space-y-2">
                    <textarea 
                      value={feedbackText}
                      onChange={(e) => setFeedbackText(e.target.value)}
                      placeholder="e.g. make the hooks more casual, or focus more on the coding struggle..."
                      className="w-full min-h-[75px] resize-none text-[12.5px] bg-canvas border border-line rounded-xl px-3 py-2 text-ink shadow-soft placeholder:text-ink-subtle focus:outline-none focus:ring-1 focus:ring-brand"
                    />
                    <Button 
                      type="submit"
                      disabled={!feedbackText.trim() || refining}
                      size="sm"
                      className="w-full h-8.5 rounded-lg bg-card text-ink border border-line text-[11.5px] font-semibold hover:bg-secondary/60 gap-1.5"
                    >
                      {refining ? 'Refining...' : 'Refine Hooks'}
                    </Button>
                  </form>
                </div>
              </div>
            </motion.div>
          )}

          {session && session.status !== 'completed' && (
            <div className="h-44 flex flex-col items-center justify-center text-center p-6 border border-dashed border-line rounded-2xl bg-canvas/30 text-ink-subtle">
              <HelpCircle className="h-6 w-6" />
              <p className="mt-2 text-[13px] font-medium">Answer the questions</p>
              <p className="mt-1 text-[12px] text-ink-muted">Complete the questioning loop on the center panel to package your content opportunity.</p>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

import { useRef, useEffect, useState, useCallback } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useWhisper } from '@/hooks/useWhisper'
import { TransactionProposalCard } from '@/components/features/TransactionProposalCard'
import { Button, Input } from '@fluentui/react-components'
import { MessageSquare, X, Trash2, Send, Mic, MicOff, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'

export function WhisperFAB() {
  const { username } = useAuth()
  const { messages, loading, sendMessage, confirmProposal, rejectProposal, clearHistory } =
    useWhisper(username ?? 'default')

  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, open])

  useEffect(() => {
    return () => { recorderRef.current?.stream?.getTracks().forEach(t => t.stop()) }
  }, [])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
        .find(t => MediaRecorder.isTypeSupported(t)) ?? ''
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {})
      chunksRef.current = []
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const mime = recorder.mimeType || 'audio/webm'
        const ext = mime.includes('mp4') ? 'mp4' : mime.includes('ogg') ? 'ogg' : 'webm'
        const blob = new Blob(chunksRef.current, { type: mime })
        if (blob.size < 1000) { toast.warning('Recording too short.'); return }
        const form = new FormData()
        form.append('audio', blob, `recording.${ext}`)
        setTranscribing(true)
        try {
          const { data } = await api.post<{ text: string }>('/api/whisper/transcribe', form)
          const text = data.text?.trim()
          if (text) setInput(text)
          else toast.warning('Nothing detected — try speaking louder.')
        } catch (err: unknown) {
          const status = (err as { response?: { status?: number } })?.response?.status
          if (status === 503) toast.error('No transcription API key configured.', { duration: 6000 })
          else toast.error('Transcription failed — please try again.')
        } finally { setTranscribing(false) }
      }
      recorder.start(250)
      recorderRef.current = recorder
      setRecording(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes('Permission') || msg.includes('NotAllowed') || msg.includes('not-allowed')) {
        toast.error('Microphone permission denied.')
      } else {
        toast.error('Could not access microphone.')
      }
    }
  }, [])

  const stopRecording = useCallback(() => {
    recorderRef.current?.stop()
    setRecording(false)
  }, [])

  const toggleMic = () => { if (recording) stopRecording(); else startRecording() }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    if (recording) stopRecording()
    setInput('')
    await sendMessage(text)
  }

  async function handleConfirm(proposalId: string, messageId: string) {
    try {
      await confirmProposal(proposalId, messageId)
      window.dispatchEvent(new CustomEvent('transaction-created'))
      toast.success('Transaction saved!')
    } catch { toast.error('Something went wrong') }
  }

  async function handleReject(proposalId: string, messageId: string) {
    try { await rejectProposal(proposalId, messageId) }
    catch { toast.error('Something went wrong') }
  }

  const micBusy = recording || transcribing

  return (
    <>
      {/* Backdrop (mobile only when open) */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20 md:bg-transparent"
          onClick={() => setOpen(false)}
        />
      )}

      <div className={cn(
        'fixed z-50 flex flex-col items-end gap-2',
        'bottom-0 right-0 md:bottom-4 md:right-4'
      )}>
        {/* Chat panel */}
        {open && (
          <div
            className={cn(
              'bg-background border shadow-xl flex flex-col overflow-hidden',
              'md:rounded-lg md:max-h-[min(600px,80vh)]',
              'fixed md:static',
              'inset-0 md:inset-auto',
              'w-full md:w-[380px]'
            )}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <header className="px-4 py-3 border-b flex items-center justify-between shrink-0">
              <div>
                <h2 className="text-sm font-semibold">Whisper</h2>
                <p className="text-xs text-muted-foreground">Log expenses by chat</p>
              </div>
              <div className="flex items-center gap-1">
                {messages.length > 0 && (
                  showClearConfirm ? (
                    <div className="flex items-center gap-1 text-xs mr-1">
                      <span className="text-muted-foreground">Clear?</span>
                      <Button size="small" appearance="primary" onClick={() => { clearHistory(); setShowClearConfirm(false) }}>Yes</Button>
                      <Button size="small" appearance="outline" onClick={() => setShowClearConfirm(false)}>No</Button>
                    </div>
                  ) : (
                    <Button size="small" appearance="subtle" icon={<Trash2 size={12} />} onClick={() => setShowClearConfirm(true)} title="Clear conversation" />
                  )
                )}
                <Button size="small" appearance="subtle" icon={<X size={16} />} onClick={() => setOpen(false)} title="Close" />
              </div>
            </header>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
              {messages.length === 0 && !loading && (
                <div className="flex items-center justify-center h-24 text-muted-foreground text-xs">
                  Tell Whisper what you spent — even multiple items at once!
                </div>
              )}

              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={cn('flex flex-col', msg.role === 'user' ? 'items-end' : 'items-start')}
                >
                  {msg.role === 'user' && msg.text && (
                    <div className="bg-primary text-primary-foreground rounded-xl rounded-br-sm px-3 py-1.5 max-w-[260px] text-sm">
                      {msg.text}
                    </div>
                  )}
                  {msg.role === 'whisper' && msg.text && (
                    <div className="bg-muted rounded-xl rounded-bl-sm px-3 py-1.5 max-w-[260px] text-sm">
                      {msg.text}
                    </div>
                  )}
                  {msg.role === 'whisper' && msg.response && (
                    <div className="w-full space-y-2">
                      <div className="bg-muted rounded-xl rounded-bl-sm px-3 py-1.5 text-xs inline-block max-w-[260px]">
                        {msg.response.persona_message}
                      </div>
                      <div className="flex gap-2 overflow-x-auto pb-1 snap-x">
                        {msg.response.proposals.map(p => (
                          <div key={p.proposal_id} className="snap-start shrink-0">
                            <TransactionProposalCard
                              messageId={msg.id}
                              proposalResult={p}
                              status={msg.statuses?.[p.proposal_id]}
                              onConfirm={handleConfirm}
                              onReject={handleReject}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="flex gap-1 px-3 py-2 bg-muted rounded-xl w-fit">
                    <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="border-t p-3 shrink-0">
              <form onSubmit={handleSubmit} className="flex gap-1.5">
                <Button
                  type="button"
                  size="small"
                  appearance={recording ? 'primary' : 'outline'}
                  icon={
                    transcribing ? <Loader2 size={14} className="animate-spin" />
                    : recording ? <MicOff size={14} />
                    : <Mic size={14} />
                  }
                  onClick={toggleMic}
                  disabled={loading || transcribing}
                  title={recording ? 'Stop recording' : 'Start recording'}
                  className={cn(recording && 'animate-pulse')}
                  style={recording ? { backgroundColor: '#dc2626', borderColor: '#dc2626' } : undefined}
                />
                <Input
                  size="small"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={recording ? 'Listening… tap mic when done' : transcribing ? 'Transcribing…' : 'e.g. 5 JOD food, 3 JOD snacks'}
                  disabled={loading || micBusy}
                  className="flex-1 text-sm"
                  style={recording ? { borderColor: '#dc2626' } : undefined}
                />
                <Button
                  type="submit"
                  size="small"
                  appearance="primary"
                  icon={<Send size={14} />}
                  disabled={loading || micBusy || !input.trim()}
                />
              </form>
            </div>
          </div>
        )}

        {/* FAB button — hidden on mobile when panel is open */}
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          className={cn(
            'flex items-center justify-center w-14 h-14 rounded-full shadow-lg transition-colors shrink-0',
            'text-white',
            open && 'hidden md:flex',
            open ? 'bg-muted-foreground hover:bg-foreground' : 'bg-primary hover:bg-primary/90'
          )}
          title={open ? 'Close Whisper' : 'Open Whisper'}
        >
          {open ? <X size={20} /> : <MessageSquare size={20} />}
        </button>
      </div>
    </>
  )
}

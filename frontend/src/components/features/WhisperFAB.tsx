import { useRef, useEffect, useState, useCallback } from 'react'
import { useWhisper } from '@/hooks/useWhisper'
import { useAuth } from '@/hooks/useAuth'
import { TransactionProposalCard } from '@/components/features/TransactionProposalCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { MessageSquare, Send, Mic, MicOff, Loader2, X, Trash2 } from 'lucide-react'
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
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [speechRecFailed, setSpeechRecFailed] = useState(false)
  const hasMessages = messages.length > 0

  const useSpeechRecognition = !!(
    typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition)
  ) && !speechRecFailed

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, open])

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort()
      recorderRef.current?.stream?.getTracks().forEach(t => t.stop())
    }
  }, [])

  const startMediaRecorder = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
      const mimeType = types.find(t => MediaRecorder.isTypeSupported(t)) || ''
      const options = mimeType ? { mimeType } : {}
      const recorder = new MediaRecorder(stream, options)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const mt = recorder.mimeType || 'audio/webm'
        const ext = mt.includes('mp4') ? 'mp4' : mt.includes('ogg') ? 'ogg' : 'webm'
        const blob = new Blob(chunksRef.current, { type: mt })

        if (blob.size < 1000) {
          toast.warning('Recording too short.')
          return
        }

        const form = new FormData()
        form.append('audio', blob, `recording.${ext}`)
        setTranscribing(true)
        try {
          const { data } = await api.post<{ text: string }>('/api/whisper/transcribe', form)
          const text = data.text?.trim()
          if (text) {
            setInput(text)
          } else {
            toast.warning("Nothing detected — try speaking louder or closer to the mic.")
          }
        } catch (err: unknown) {
          const status = (err as { response?: { status?: number } })?.response?.status
          if (status === 503) {
            toast.error(
              'No transcription API key configured. Add GROQ_API_KEY (free) or OPENAI_API_KEY to .env and restart.',
              { duration: 8000 }
            )
          } else {
            toast.error('Transcription failed — please try again.')
          }
        } finally {
          setTranscribing(false)
        }
      }

      recorder.start(250)
      recorderRef.current = recorder
      setRecording(true)
    } catch (err: unknown) {
      const name = err instanceof DOMException ? err.name
        : err instanceof Error ? err.name : ''
      const msg = err instanceof Error ? err.message : String(err)
      console.error('getUserMedia error:', { name, message: msg, err })

      if (name === 'NotAllowedError' || msg.match(/permission|notallowed|not.allowed|denied/i)) {
        toast.error('Microphone permission denied. Allow mic access in your browser settings.')
      } else if (name === 'NotFoundError') {
        toast.error('No microphone found on this device.')
      } else if (name === 'NotReadable') {
        toast.error('Mic is busy — close other apps using the mic.')
      } else if (name === 'OverconstrainedError' || msg.match(/overconstrained|constraint/i)) {
        toast.error('Mic not available — try with simpler audio settings.')
      } else if (name === 'TypeError' || msg.match(/undefined|null/i)) {
        if (!navigator.mediaDevices) {
          if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
            toast.error('Microphone requires HTTPS. Access the site via https://')
          } else {
            toast.error('Microphone API blocked. Disable privacy extensions (Brave Shields, etc.) for this site.')
          }
        } else {
          toast.error('Microphone not supported in this browser.')
        }
      } else if (name === 'SecurityError' || msg.match(/secure|https/i)) {
        toast.error('Mic requires a secure connection (HTTPS).')
      } else {
        toast.error(`Microphone error: ${msg}`)
      }
    }
  }, [])

  const startSpeechRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return false

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let final = ''
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript
        } else {
          interim += event.results[i][0].transcript
        }
      }
      setInput(final + (interim ? ` ${interim}` : ''))
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('SpeechRecognition error:', event.error)
      if (event.error === 'not-allowed') {
        toast.error('Microphone permission denied. Allow mic access in your browser settings.')
        setRecording(false)
      } else if (event.error === 'no-speech') {
        toast.warning('No speech detected.')
        setRecording(false)
      } else if (event.error === 'network') {
        setSpeechRecFailed(true)
        toast.error('Real-time speech unavailable (Brave Shields blocks it). Falling back to server transcription…')
        setRecording(false)
        startMediaRecorder()
      } else {
        setSpeechRecFailed(true)
        toast.error(`Speech recognition error: ${event.error}. Falling back to server transcription…`)
        setRecording(false)
        startMediaRecorder()
      }
    }

    recognition.onend = () => {
      setRecording(false)
    }

    recognition.start()
    recognitionRef.current = recognition
    setRecording(true)
    return true
  }, [startMediaRecorder])

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    if (recorderRef.current) {
      recorderRef.current.stop()
    }
    setRecording(false)
  }, [])

  const toggleMic = useCallback(() => {
    if (recording) {
      stopRecording()
    } else if (useSpeechRecognition) {
      startSpeechRecognition()
    } else {
      startMediaRecorder()
    }
  }, [recording, stopRecording, useSpeechRecognition, startSpeechRecognition, startMediaRecorder])

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
    } catch {
      toast.error('Something went wrong')
    }
  }

  async function handleReject(proposalId: string, messageId: string) {
    try {
      await rejectProposal(proposalId, messageId)
    } catch {
      toast.error('Something went wrong')
    }
  }

  const micBusy = recording || transcribing

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20 md:bg-transparent"
          onClick={() => setOpen(false)}
        />
      )}

      <div className={cn(
        'fixed z-50 flex flex-col items-end gap-2',
        'bottom-0 right-0 md:bottom-4 md:right-4',
      )}>
        {open && (
          <div
            className="bg-background border shadow-xl flex flex-col overflow-hidden
                       md:rounded-lg md:max-h-[min(600px,80vh)]
                       fixed md:static
                       inset-0 md:inset-auto
                       w-full md:w-[380px]"
            onClick={(e) => e.stopPropagation()}
          >
            <header className="px-4 py-3 border-b flex items-center justify-between shrink-0">
              <div>
                <h2 className="text-sm font-semibold">Whisper</h2>
                <p className="text-xs text-muted-foreground">Log expenses, transfer money, ask about balances</p>
              </div>
              <div className="flex items-center gap-1">
                {hasMessages && (
                  showClearConfirm ? (
                    <div className="flex items-center gap-1 text-xs mr-1">
                      <span className="text-muted-foreground">Clear?</span>
                      <Button size="small" appearance="primary" onClick={() => { clearHistory(); setShowClearConfirm(false) }}>
                        Yes
                      </Button>
                      <Button size="small" appearance="secondary" onClick={() => setShowClearConfirm(false)}>
                        No
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="small"
                      appearance="ghost"
                      onClick={() => setShowClearConfirm(true)}
                      title="Clear conversation"
                    >
                      <Trash2 size={12} />
                    </Button>
                  )
                )}
                <Button
                  size="small"
                  appearance="ghost"
                  onClick={() => setOpen(false)}
                  title="Close"
                >
                  <X size={16} />
                </Button>
              </div>
            </header>

            <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
              {messages.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center h-28 text-muted-foreground text-xs gap-1 px-4 text-center">
                  <span>Tell Whisper what you spent or earned,</span>
                  <span>ask &ldquo;how much do I have?&rdquo;,</span>
                  <span>or say &ldquo;move 100 from savings to cash&rdquo;.</span>
                </div>
              )}

              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  {msg.role === 'user' && msg.text && (
                    <div className="bg-primary text-primary-foreground rounded-xl rounded-br-sm px-3 py-1.5 max-w-[260px] text-sm">
                      {msg.text}
                    </div>
                  )}
                  {msg.role === 'whisper' && msg.response && (
                    <TransactionProposalCard
                      messageId={msg.id}
                      response={msg.response}
                      status={msg.status}
                      onConfirm={handleConfirm}
                      onReject={handleReject}
                    />
                  )}
                  {msg.role === 'whisper' && msg.text && (
                    <div className="bg-muted rounded-xl rounded-bl-sm px-3 py-1.5 max-w-[260px] text-sm">
                      {msg.text}
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

            <div className="border-t p-3 shrink-0">
              <form onSubmit={handleSubmit} className="flex gap-1.5">
                <Button
                  type="button"
                  size="small"
                  appearance={recording ? 'primary' : 'secondary'}
                  onClick={toggleMic}
                  disabled={loading || transcribing}
                  title={recording ? 'Stop recording' : 'Start recording'}
                  className={cn(recording && 'animate-pulse')}
                  style={recording ? { backgroundColor: '#dc2626', borderColor: '#dc2626' } : undefined}
                >
                  {transcribing
                    ? <Loader2 size={14} className="animate-spin" />
                    : recording
                      ? <MicOff size={14} />
                      : <Mic size={14} />
                  }
                </Button>

                <Input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={
                    recording ? 'Listening… tap mic when done'
                    : transcribing ? 'Transcribing…'
                    : 'e.g. 50 JOD on groceries · move 100 to savings'
                  }
                  disabled={loading || micBusy}
                  className="flex-1 text-sm"
                  style={recording ? { borderColor: '#dc2626' } : undefined}
                />

                <Button
                  type="submit"
                  size="small"
                  appearance="primary"
                  disabled={loading || micBusy || !input.trim()}
                >
                  <Send size={14} />
                </Button>
              </form>
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={() => setOpen(!open)}
          className={cn(
            'flex items-center justify-center w-12 h-12 rounded-full shadow-lg transition-colors shrink-0',
            'text-white',
            open && 'hidden md:flex',
            open
              ? 'bg-muted-foreground hover:bg-foreground'
              : 'bg-primary hover:bg-primary/90',
          )}
          title={open ? 'Close Whisper' : 'Open Whisper'}
        >
          {open ? <X size={20} /> : <MessageSquare size={20} />}
        </button>
      </div>
    </>
  )
}

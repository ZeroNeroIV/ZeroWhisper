import { useRef, useEffect, useState, useCallback } from 'react'
import { useWhisper } from '@/hooks/useWhisper'
import { useAuth } from '@/hooks/useAuth'
import { TransactionProposalCard } from '@/components/features/TransactionProposalCard'
import { Button, Input } from '@fluentui/react-components'
import { Send, Mic, MicOff, Loader2, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'

export default function WhisperPage() {
  const { username } = useAuth()
  const { messages, loading, sendMessage, confirmProposal, rejectProposal, clearHistory } =
    useWhisper(username ?? 'default')

  const [input, setInput] = useState('')
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const [showClearConfirm, setShowClearConfirm] = useState(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    return () => {
      recorderRef.current?.stream?.getTracks().forEach(t => t.stop())
    }
  }, [])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const mimeType = recorder.mimeType || 'audio/webm'
        const ext = mimeType.includes('ogg') ? 'ogg' : 'webm'
        const blob = new Blob(chunksRef.current, { type: mimeType })

        if (blob.size < 1000) {
          toast.warning('Recording too short — hold the mic while speaking.')
          return
        }

        const form = new FormData()
        form.append('audio', blob, `recording.${ext}`)
        setTranscribing(true)
        try {
          const { data } = await api.post<{ text: string }>('/api/whisper/transcribe', form)
          const text = data.text?.trim()
          if (text) {
            setInput(prev => (prev ? prev + ' ' + text : text))
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

      recorder.start()
      recorderRef.current = recorder
      setRecording(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes('Permission') || msg.includes('NotAllowed') || msg.includes('not-allowed')) {
        toast.error('Microphone permission denied. Allow it in your browser settings.')
      } else {
        toast.error('Could not access microphone.')
      }
    }
  }, [])

  const stopRecording = useCallback(() => {
    recorderRef.current?.stop()
    setRecording(false)
  }, [])

  const toggleMic = () => {
    if (recording) stopRecording()
    else startRecording()
  }

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
    <div className="flex flex-col h-full">
      <header className="px-6 py-4 border-b flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Whisper</h1>
          <p className="text-sm text-muted-foreground">Tell me what you spent and I&apos;ll log it for you</p>
        </div>
        {messages.length > 0 && (
          showClearConfirm ? (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Clear history?</span>
              <Button size="small" appearance="primary" onClick={() => { clearHistory(); setShowClearConfirm(false) }}>
                Yes
              </Button>
              <Button size="small" appearance="outline" onClick={() => setShowClearConfirm(false)}>
                Cancel
              </Button>
            </div>
          ) : (
            <Button
              size="small"
              appearance="subtle"
              icon={<Trash2 size={14} />}
              onClick={() => setShowClearConfirm(true)}
              title="Clear conversation history"
            />
          )
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            Start a conversation — tell Whisper what you spent.
          </div>
        )}

        {messages.map(msg => (
          <div
            key={msg.id}
            className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            {msg.role === 'user' && msg.text && (
              <div className="bg-primary text-primary-foreground rounded-2xl rounded-br-sm px-4 py-2 max-w-xs">
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
              <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2 max-w-md text-sm">
                {msg.text}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex gap-1 px-4 py-3 bg-muted rounded-2xl w-fit">
              <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Button
            type="button"
            appearance={recording ? 'primary' : 'outline'}
            icon={
              transcribing
                ? <Loader2 size={16} className="animate-spin" />
                : recording
                  ? <MicOff size={16} />
                  : <Mic size={16} />
            }
            onClick={toggleMic}
            disabled={loading || transcribing}
            title={recording ? 'Stop recording' : 'Hold to record'}
            className={cn(recording && 'animate-pulse')}
            style={recording ? { backgroundColor: '#dc2626', borderColor: '#dc2626' } : undefined}
          />

          <Input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={
              recording ? 'Recording… tap mic to stop'
              : transcribing ? 'Transcribing…'
              : 'e.g. Spent 50 JOD on groceries'
            }
            disabled={loading || micBusy}
            className="flex-1"
            style={recording ? { borderColor: '#dc2626' } : undefined}
          />

          <Button
            type="submit"
            appearance="primary"
            icon={<Send size={16} />}
            disabled={loading || micBusy || !input.trim()}
          />
        </form>
        <p className="text-xs text-muted-foreground mt-2">
          Tap mic to record, or type — e.g. &quot;Spent 50 JOD on groceries&quot;
        </p>
      </div>
    </div>
  )
}

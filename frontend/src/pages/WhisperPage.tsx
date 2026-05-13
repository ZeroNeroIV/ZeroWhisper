import { useRef, useEffect, useState } from 'react'
import { useWhisper } from '@/hooks/useWhisper'
import { TransactionProposalCard } from '@/components/features/TransactionProposalCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

export default function WhisperPage() {
  const { messages, loading, sendMessage, confirmProposal, rejectProposal } = useWhisper()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
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

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="px-6 py-4 border-b">
        <h1 className="text-xl font-semibold">Whisper</h1>
        <p className="text-sm text-muted-foreground">Tell me what you spent and I&apos;ll log it for you</p>
      </header>

      {/* Message list */}
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

        {/* Typing indicator */}
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

      {/* Input bar */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="e.g. Spent 50 JOD on groceries"
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={loading || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2">
          Try: &quot;Add 20 USD for Netflix&quot; or &quot;Spent 50 JOD on groceries&quot;
        </p>
      </div>
    </div>
  )
}

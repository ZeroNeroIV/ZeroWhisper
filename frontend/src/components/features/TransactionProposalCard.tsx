import { useState } from 'react'
import { Card, Button, Badge } from '@fluentui/react-components'
import { CheckCircle2 } from 'lucide-react'
import type { WhisperResponse } from '@/hooks/useWhisper'

interface Props {
  messageId: string
  response: WhisperResponse
  status?: 'confirmed' | 'rejected'
  onConfirm: (proposalId: string, messageId: string) => Promise<void>
  onReject: (proposalId: string, messageId: string) => Promise<void>
}

export function TransactionProposalCard({ messageId, response, status, onConfirm, onReject }: Props) {
  const [busy, setBusy] = useState(false)
  const { proposal_id, proposal, persona_message, spending_context } = response
  const confidencePct = Math.round(proposal.confidence * 100)

  async function handleConfirm() {
    setBusy(true)
    try {
      await onConfirm(proposal_id, messageId)
    } finally {
      setBusy(false)
    }
  }

  async function handleReject() {
    setBusy(true)
    try {
      await onReject(proposal_id, messageId)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="max-w-md w-full p-4">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-xs font-bold select-none">
            W
          </div>
          <span className="text-sm font-medium">Whisper</span>
          <span className="ml-auto text-xs bg-muted text-muted-foreground rounded-full px-2 py-0.5">
            {confidencePct}% confident
          </span>
        </div>

        {/* Persona message */}
        <p className="text-sm text-foreground">{persona_message}</p>

        {/* Spending context */}
        {spending_context && (
          <p className="text-xs text-muted-foreground">
            You&apos;ve spent {spending_context.this_month_total} JOD on {spending_context.category} this month ({spending_context.transaction_count} transaction{spending_context.transaction_count !== 1 ? 's' : ''})
          </p>
        )}

        {/* Proposal details */}
        <div className="rounded-md border bg-muted/40 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Amount</span>
            <span className="text-sm font-semibold">
              {proposal.amount_original} {proposal.currency_original}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Category</span>
            <Badge appearance="tint" className="text-xs">{proposal.category}</Badge>
          </div>
          <div className="flex items-start justify-between gap-2">
            <span className="text-xs text-muted-foreground shrink-0">Description</span>
            <span className="text-xs text-right">{proposal.description}</span>
          </div>
        </div>

        {/* Actions */}
        {status === 'confirmed' ? (
          <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4" />
            Transaction saved!
          </div>
        ) : status === 'rejected' ? (
          <p className="text-sm text-muted-foreground">Proposal dismissed</p>
        ) : (
          <div className="flex gap-2">
            <Button
              size="small"
              appearance="primary"
              style={{ backgroundColor: '#16a34a' }}
              disabled={busy}
              onClick={handleConfirm}
            >
              Confirm
            </Button>
            <Button
              size="small"
              appearance="outline"
              disabled={busy}
              onClick={handleReject}
            >
              Reject
            </Button>
          </div>
        )}
      </div>
    </Card>
  )
}

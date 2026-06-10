import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ArrowRight, CheckCircle2 } from 'lucide-react'
import type { WhisperResponse } from '@/hooks/useWhisper'
import { useCategories } from '@/hooks/useCategories'
import { renderCategoryLabel } from '@/lib/category'

interface Props {
  messageId: string
  response: WhisperResponse
  status?: 'confirmed' | 'rejected'
  onConfirm: (proposalId: string, messageId: string) => Promise<void>
  onReject: (proposalId: string, messageId: string) => Promise<void>
}

export function TransactionProposalCard({ messageId, response, status, onConfirm, onReject }: Props) {
  const [busy, setBusy] = useState(false)
  const { categories, fetchCategories } = useCategories()
  const { proposal_id, proposal, persona_message, spending_context } = response

  const isProposal = response.action !== 'reply' && !!proposal && !!proposal_id

  useEffect(() => {
    if (isProposal) fetchCategories()
  }, [fetchCategories, isProposal])

  // Plain agent reply — balance answers, spending summaries, clarifications.
  if (!isProposal) {
    return (
      <div className="bg-muted rounded-xl rounded-bl-sm px-3 py-1.5 max-w-[280px] text-sm whitespace-pre-wrap">
        {persona_message}
      </div>
    )
  }

  const isTransfer = proposal.kind === 'transfer'
  const confidencePct = Math.round(proposal.confidence * 100)

  async function handleConfirm() {
    setBusy(true)
    try {
      await onConfirm(proposal_id!, messageId)
    } finally {
      setBusy(false)
    }
  }

  async function handleReject() {
    setBusy(true)
    try {
      await onReject(proposal_id!, messageId)
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

          {isTransfer ? (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Transfer</span>
              <span className="text-xs font-medium flex items-center gap-1">
                {proposal.from_wallet_name}
                <ArrowRight className="w-3 h-3 text-muted-foreground" />
                {proposal.to_wallet_name}
              </span>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Category</span>
                {renderCategoryLabel(proposal.category ?? '', categories)}
              </div>
              {proposal.wallet_name && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Wallet</span>
                  <span className="text-xs font-medium">{proposal.wallet_name}</span>
                </div>
              )}
            </>
          )}

          {proposal.description && (
            <div className="flex items-start justify-between gap-2">
              <span className="text-xs text-muted-foreground shrink-0">Description</span>
              <span className="text-xs text-right">{proposal.description}</span>
            </div>
          )}
          {proposal.transaction_date && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Date</span>
              <span className="text-xs font-medium">{proposal.transaction_date}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        {status === 'confirmed' ? (
          <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4" />
            {isTransfer ? 'Transfer completed!' : 'Transaction saved!'}
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
              appearance="secondary"
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



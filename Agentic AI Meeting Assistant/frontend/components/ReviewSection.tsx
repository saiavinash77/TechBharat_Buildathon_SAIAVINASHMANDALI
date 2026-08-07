'use client'

import { useState } from 'react'
import { Check, X, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { reviewActionItem, dispatchMeeting, askQuestion } from '@/lib/api'
import type { ActionItem, MeetingData, DispatchResult } from '@/lib/api'

interface ReviewSectionProps {
  meetingData: MeetingData
  onDispatchComplete: (results: DispatchResult[]) => void
}

export function ReviewSection({ meetingData, onDispatchComplete }: ReviewSectionProps) {
  const [items, setItems] = useState<ActionItem[]>(
    meetingData.review?.payload?.items || []
  )
  const [qaQuestion, setQaQuestion] = useState('')
  const [qaAnswer, setQaAnswer] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [isDispatching, setIsDispatching] = useState(false)

  const payload = meetingData.review?.payload || {}

  const handleReview = async (itemId: string, decision: 'APPROVED' | 'REJECTED') => {
    const item = items.find(i => i.id === itemId)
    if (!item) return

    const ghInput = document.getElementById(`gh-${itemId}`) as HTMLInputElement
    const ownerInput = document.getElementById(`owner-${itemId}`) as HTMLInputElement
    const priInput = document.getElementById(`pri-${itemId}`) as HTMLSelectElement
    const dueInput = document.getElementById(`due-${itemId}`) as HTMLInputElement

    try {
      const updated = await reviewActionItem(meetingData.meeting_id, itemId, {
        reviewer_name: 'Demo Reviewer',
        decision,
        github_assignee_login: ghInput?.value || undefined,
        final_owner_name: ownerInput?.value || undefined,
        priority: (priInput?.value as 'HIGH' | 'MEDIUM' | 'LOW') || undefined,
        resolved_due_date: dueInput?.value || undefined,
      })
      setItems(items.map(i => i.id === itemId ? updated : i))
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Review failed')
    }
  }

  const handleDispatch = async () => {
    setIsDispatching(true)
    try {
      const results = await dispatchMeeting(meetingData.meeting_id)
      onDispatchComplete(results)
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Dispatch failed')
    } finally {
      setIsDispatching(false)
    }
  }

  const handleAskQuestion = async () => {
    if (!qaQuestion.trim()) return
    setIsAsking(true)
    setQaAnswer('Thinking...')
    try {
      const response = await askQuestion(meetingData.meeting_id, qaQuestion)
      setQaAnswer(response.answer)
    } catch (error) {
      setQaAnswer('Error: ' + (error instanceof Error ? error.message : 'Q&A failed'))
    } finally {
      setIsAsking(false)
    }
  }

  const getBadgeVariant = (classification: string) => {
    if (classification === 'EXPLICIT_COMMITMENT') return 'commitment'
    if (classification === 'NEEDS_CONFIRMATION') return 'needs-confirmation'
    return 'discussion'
  }

  const getBadgeLabel = (classification: string) => {
    if (classification === 'EXPLICIT_COMMITMENT') return 'Explicit commitment'
    if (classification === 'NEEDS_CONFIRMATION') return 'Needs confirmation'
    return 'Discussion only'
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start gap-4 flex-wrap">
          <div>
            <CardTitle>Review before dispatch</CardTitle>
            <p className="text-sm text-text-secondary mt-1">Meeting ID: {meetingData.meeting_id}</p>
          </div>
          <Button
            variant="success"
            size="sm"
            onClick={handleDispatch}
            disabled={isDispatching}
          >
            {isDispatching ? 'Dispatching...' : 'Dispatch approved to GitHub'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Executive summary</h3>
          <p className="text-text-secondary">{payload.summary || 'Analyzed.'}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-background border border-border border-l-4 border-l-primary rounded-md p-4">
            <h4 className="font-semibold mb-2">Decisions</h4>
            <ul className="text-sm text-text-secondary space-y-1">
              {(payload.decisions?.length || 0) > 0 ? (
                payload.decisions?.map((d, i) => <li key={i}>{d}</li>)
              ) : (
                <li>None detected</li>
              )}
            </ul>
          </div>
          <div className="bg-background border border-border border-l-4 border-l-primary rounded-md p-4">
            <h4 className="font-semibold mb-2">Open questions</h4>
            <ul className="text-sm text-text-secondary space-y-1">
              {(payload.open_questions?.length || 0) > 0 ? (
                payload.open_questions?.map((q, i) => <li key={i}>{q}</li>)
              ) : (
                <li>None detected</li>
              )}
            </ul>
          </div>
          <div className="bg-background border border-border border-l-4 border-l-primary rounded-md p-4">
            <h4 className="font-semibold mb-2">Risks / blockers</h4>
            <ul className="text-sm text-text-secondary space-y-1">
              {payload.risks_or_blockers && payload.risks_or_blockers.length > 0 ? (
                payload.risks_or_blockers.map((r, i) => <li key={i}>{r}</li>)
              ) : (
                <li>None detected</li>
              )}
            </ul>
          </div>
        </div>

        <div className="space-y-4">
          {items.map((item, idx) => (
            <div
              key={item.id}
              className="bg-background border border-border rounded-lg p-5"
            >
              <div className="flex justify-between items-start gap-4 mb-3">
                <h4 className="font-semibold text-base">
                  {idx + 1}. {item.title}
                </h4>
                <div className="flex gap-2 flex-wrap">
                  {item.review_status === 'APPROVED' && (
                    <Badge variant="approved">Approved</Badge>
                  )}
                  {item.review_status === 'REJECTED' && (
                    <Badge variant="rejected">Rejected</Badge>
                  )}
                  <Badge variant={getBadgeVariant(item.classification)}>
                    {getBadgeLabel(item.classification)}
                  </Badge>
                </div>
              </div>

              <blockquote className="italic text-text-secondary text-sm border-l-3 border-l-primary pl-3 mb-3">
                "{item.quote_provenance || 'N/A'}"
              </blockquote>

              <p className="text-sm text-text-secondary mb-4">
                Speaker: {item.speaker_name || '?'} · Confidence: {item.confidence_score ?? '—'}
              </p>

              {item.classification === 'DISCUSSION_ONLY' && (
                <p className="text-warning text-sm mb-4 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Blocked from GitHub — discussion only
                </p>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="text-xs font-medium text-text-secondary uppercase tracking-wider block mb-2">
                    GitHub assignee
                  </label>
                  <Input
                    id={`gh-${item.id}`}
                    defaultValue={item.github_assignee_login || item.suggested_github_login || ''}
                    placeholder="github-username"
                  />
                  {item.suggested_github_login && !item.github_assignee_login && (
                    <p className="text-success text-xs mt-1">
                      Roster match: @{item.suggested_github_login}
                    </p>
                  )}
                </div>
                <div>
                  <label className="text-xs font-medium text-text-secondary uppercase tracking-wider block mb-2">
                    Owner name
                  </label>
                  <Input
                    id={`owner-${item.id}`}
                    defaultValue={item.final_owner_name || item.proposed_owner_name || ''}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-text-secondary uppercase tracking-wider block mb-2">
                    Priority
                  </label>
                  <select
                    id={`pri-${item.id}`}
                    className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                    defaultValue={item.priority || 'MEDIUM'}
                  >
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-text-secondary uppercase tracking-wider block mb-2">
                    Due date
                  </label>
                  <Input
                    id={`due-${item.id}`}
                    type="date"
                    defaultValue={item.due_date || ''}
                  />
                </div>
              </div>

              <div className="flex gap-2 flex-wrap">
                <Button
                  variant="success"
                  size="sm"
                  onClick={() => handleReview(item.id, 'APPROVED')}
                >
                  <Check className="h-4 w-4 mr-1" />
                  Approve
                </Button>
                <Button
                  variant="error"
                  size="sm"
                  onClick={() => handleReview(item.id, 'REJECTED')}
                >
                  <X className="h-4 w-4 mr-1" />
                  Reject
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 pt-6 border-t border-border">
          <h3 className="text-lg font-semibold mb-2">Ask about this meeting</h3>
          <p className="text-sm text-text-secondary mb-4">
            Evidence-backed answers from the transcript only.
          </p>
          <div className="flex gap-3 flex-wrap">
            <Input
              placeholder="e.g. What did Rahul commit to?"
              value={qaQuestion}
              onChange={(e) => setQaQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
              className="flex-1 min-w-[200px]"
            />
            <Button onClick={handleAskQuestion} disabled={isAsking}>
              {isAsking ? 'Asking...' : 'Ask'}
            </Button>
          </div>
          {qaAnswer && (
            <div className="mt-4 p-4 bg-background border border-border rounded-md text-sm">
              {qaAnswer}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

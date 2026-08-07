'use client'

import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import type { DispatchResult, AuditEvent } from '@/lib/api'

interface ResultsSectionProps {
  results: DispatchResult[]
  auditEvents: AuditEvent[]
}

export function ResultsSection({ results, auditEvents }: ResultsSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Dispatch results & audit</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 mb-6">
          {results.length === 0 ? (
            <div className="p-4 bg-success/10 border border-success/30 rounded-md text-sm">
              No approved items to dispatch. Approve items first.
            </div>
          ) : (
            results.map((result, idx) => (
              <div
                key={idx}
                className="p-4 bg-success/10 border border-success/30 rounded-md text-sm"
              >
                <span className="font-medium">{result.title || result.action_item_id}</span>
                {' — '}
                {result.status}
                {result.dry_run && ' (DRY RUN — set DRY_RUN=false for live issues)'}
                {result.html_url && (
                  <>
                    {' '}
                    <a
                      href={result.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      View
                    </a>
                  </>
                )}
              </div>
            ))
          )}
        </div>

        <div>
          <h3 className="font-semibold mb-3">
            Audit log ({auditEvents.length} events)
          </h3>
          <div className="space-y-2">
            {auditEvents.slice(-8).reverse().map((event, idx) => (
              <div
                key={idx}
                className="p-3 bg-success/10 border border-success/30 rounded-md text-sm"
              >
                <code className="text-xs">{event.event_type}</code>
                {' · '}
                {event.actor_type}
                {event.actor_name && ` (${event.actor_name})`}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

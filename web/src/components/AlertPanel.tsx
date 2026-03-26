import type { Alert, Signal } from '../types'

interface AlertPanelProps {
  alerts: Alert[]
  signals: Signal[]
  onApproveSignal: (signalId: string, action: 'approve' | 'reject') => void
}

export function AlertPanel({ alerts, signals, onApproveSignal }: AlertPanelProps) {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val)
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const hasAlerts = alerts.length > 0 || signals.length > 0

  return (
    <div className="bg-trader-card border border-trader-border rounded-lg">
      <div className="p-3 border-b border-trader-border flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          🔔 Alerts & Signals
          {signals.length > 0 && (
            <span className="bg-trader-red text-white text-xs px-2 py-0.5 rounded-full">
              {signals.length} pending
            </span>
          )}
        </h3>
        <span className="text-xs text-trader-muted">
          {alerts.length + signals.length} items
        </span>
      </div>

      <div className="max-h-48 overflow-y-auto">
        {!hasAlerts ? (
          <div className="p-6 text-center text-trader-muted">
            <div className="text-2xl mb-2">✨</div>
            <p className="text-sm">All caught up! No alerts or pending signals.</p>
          </div>
        ) : (
          <div className="divide-y divide-trader-border">
            {/* Pending Signals */}
            {signals.map((signal) => (
              <div key={signal.id} className="p-3 bg-trader-yellow/5">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-trader-yellow font-semibold">⚡</span>
                    <span className="font-semibold">{signal.symbol}</span>
                    <span className={`text-sm ${signal.action === 'SELL' ? 'text-trader-red' : 'text-trader-green'}`}>
                      {signal.action}
                    </span>
                  </div>
                  <span className="text-xs text-trader-muted">{formatTime(signal.created_at)}</span>
                </div>

                <div className="text-sm mb-2">
                  {signal.reason}
                </div>

                {signal.quantity && signal.price && (
                  <div className="bg-trader-bg rounded p-2 mb-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-trader-muted">Action:</span>
                      <span className="font-medium">
                        {signal.action} {signal.quantity} shares @ ~{formatCurrency(signal.price)}
                      </span>
                    </div>
                    {signal.portfolio_impact && (
                      <>
                        <div className="flex justify-between mt-1">
                          <span className="text-trader-muted">Proceeds:</span>
                          <span className="font-medium">
                            {formatCurrency(signal.quantity * signal.price)}
                          </span>
                        </div>
                        {signal.portfolio_impact.concentration_after && (
                          <div className="flex justify-between mt-1">
                            <span className="text-trader-muted">Concentration:</span>
                            <span className="font-medium">
                              {signal.portfolio_impact.concentration_before} → {signal.portfolio_impact.concentration_after}
                            </span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => onApproveSignal(signal.id, 'approve')}
                    className="flex-1 py-1.5 bg-trader-green/20 hover:bg-trader-green/30 text-trader-green rounded text-xs font-medium transition-colors"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => onApproveSignal(signal.id, 'reject')}
                    className="flex-1 py-1.5 bg-trader-red/20 hover:bg-trader-red/30 text-trader-red rounded text-xs font-medium transition-colors"
                  >
                    ✗ Reject
                  </button>
                </div>

                <div className="mt-2 text-xs text-trader-muted">
                  Confidence: {signal.confidence}% | Auto-execute in 5:00
                </div>
              </div>
            ))}

            {/* Regular Alerts */}
            {alerts.map((alert) => (
              <div key={alert.id} className="p-3 flex items-start gap-3">
                <span className={`text-lg ${
                  alert.severity === 'action_required' ? 'text-trader-red' :
                  alert.severity === 'warning' ? 'text-trader-yellow' :
                  'text-trader-blue'
                }`}>
                  {alert.type === 'approaching_target' ? '🎯' :
                   alert.type === 'risk_alert' ? '⚠️' : 'ℹ️'}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold">{alert.symbol}</span>
                    <span className="text-xs text-trader-muted">{formatTime(alert.created_at)}</span>
                  </div>
                  <p className="text-sm">{alert.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

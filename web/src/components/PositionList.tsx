import { useState } from 'react'
import type { Position, Portfolio } from '../types'

interface PositionListProps {
  portfolio: Portfolio | null
  selectedPosition: Position | null
  onSelectPosition: (pos: Position | null) => void
  onUpdate: () => void
}

export function PositionList({ portfolio, selectedPosition, onSelectPosition, onUpdate }: PositionListProps) {
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null)
  const [strategyInput, setStrategyInput] = useState('')
  const [isCreatingStrategy, setIsCreatingStrategy] = useState(false)

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(val)
  }

  const formatPct = (val: number) => {
    const sign = val >= 0 ? '+' : ''
    return `${sign}${(val * 100).toFixed(1)}%`
  }

  const handleExpand = (position: Position) => {
    if (expandedSymbol === position.symbol) {
      setExpandedSymbol(null)
      onSelectPosition(null)
    } else {
      setExpandedSymbol(position.symbol)
      onSelectPosition(position)
    }
  }

  const handleCreateStrategy = async (symbol: string) => {
    if (!strategyInput.trim()) return

    try {
      const res = await fetch('http://localhost:8000/api/strategies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: strategyInput,
          symbol,
          approval_mode: 'hybrid',
        }),
      })

      if (res.ok) {
        setStrategyInput('')
        setIsCreatingStrategy(false)
        onUpdate()
      }
    } catch (err) {
      console.error('Failed to create strategy:', err)
    }
  }

  const handleQuickAction = async (symbol: string, action: string) => {
    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `${action} ${symbol}` }),
      })

      if (res.ok) {
        onUpdate()
      }
    } catch (err) {
      console.error('Failed to execute action:', err)
    }
  }

  if (!portfolio || portfolio.positions.length === 0) {
    return (
      <div className="bg-trader-card border border-trader-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Your Positions</h2>
        <div className="text-center py-8 text-trader-muted">
          <div className="text-4xl mb-3">📂</div>
          <p>No positions imported yet.</p>
          <p className="text-sm mt-2">Import your portfolio to get started.</p>
          <button
            onClick={() => {}}
            className="mt-4 px-4 py-2 bg-trader-blue hover:bg-blue-600 rounded-lg text-white font-medium transition-colors"
          >
            Import Portfolio
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-trader-card border border-trader-border rounded-lg overflow-hidden flex flex-col" style={{ maxHeight: '60vh' }}>
      <div className="p-4 border-b border-trader-border flex items-center justify-between">
        <h2 className="text-lg font-semibold">Your Positions</h2>
        <span className="text-sm text-trader-muted">{portfolio.positions.length} positions</span>
      </div>

      <div className="overflow-y-auto flex-1">
        {portfolio.positions.map((pos) => {
          const isExpanded = expandedSymbol === pos.symbol
          const isPositive = pos.unrealized_pnl >= 0
          const hasStrategy = pos.strategy && pos.strategy.status === 'active'

          return (
            <div
              key={pos.symbol}
              className={`border-b border-trader-border last:border-b-0 transition-colors ${isExpanded ? 'bg-trader-bg/50' : 'hover:bg-trader-bg/30'}`}
            >
              {/* Main Row */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => handleExpand(pos)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${hasStrategy ? 'bg-trader-green status-active' : 'bg-gray-500'}`} />
                    <div>
                      <div className="font-semibold text-lg">{pos.symbol}</div>
                      <div className="text-sm text-trader-muted">
                        {pos.quantity.toFixed(0)} shares @ {formatCurrency(pos.avg_cost)} avg
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="font-semibold">{formatCurrency(pos.market_value)}</div>
                    <div className={`text-sm ${isPositive ? 'text-trader-green' : 'text-trader-red'}`}>
                      {formatPct(pos.unrealized_pnl_pct)} ({formatCurrency(pos.unrealized_pnl)})
                    </div>
                  </div>

                  <div className="text-right min-w-[100px]">
                    {pos.strategy ? (
                      <div className="text-sm">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${pos.strategy.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                          {pos.strategy.status === 'active' ? '✓' : '⏸️'} {pos.strategy.description.slice(0, 20)}...
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs text-trader-muted italic">No strategy</span>
                    )}
                  </div>

                  <div className="text-trader-muted">
                    {isExpanded ? '▼' : '▶'}
                  </div>
                </div>
              </div>

              {/* Expanded Detail */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-trader-border/50">
                  <div className="pt-4 grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-trader-bg rounded-lg p-3">
                      <div className="text-xs text-trader-muted mb-1">Current Price</div>
                      <div className="text-lg font-semibold">{formatCurrency(pos.current_price)}</div>
                    </div>
                    <div className="bg-trader-bg rounded-lg p-3">
                      <div className="text-xs text-trader-muted mb-1">Portfolio Weight</div>
                      <div className={`text-lg font-semibold ${pos.portfolio_weight > 0.25 ? 'text-trader-yellow' : ''}`}>
                        {(pos.portfolio_weight * 100).toFixed(1)}%
                        {pos.portfolio_weight > 0.25 && ' ⚠️'}
                      </div>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="mb-4">
                    <div className="text-xs text-trader-muted mb-2">Quick Actions</div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleQuickAction(pos.symbol, 'Sell 50% of'); }}
                        className="px-3 py-1.5 bg-trader-green/20 hover:bg-trader-green/30 text-trader-green rounded text-sm transition-colors"
                      >
                        Sell 50%
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleQuickAction(pos.symbol, 'Set stop loss on'); }}
                        className="px-3 py-1.5 bg-trader-red/20 hover:bg-trader-red/30 text-trader-red rounded text-sm transition-colors"
                      >
                        Set Stop Loss
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleQuickAction(pos.symbol, 'Set price alert for'); }}
                        className="px-3 py-1.5 bg-trader-blue/20 hover:bg-trader-blue/30 text-trader-blue rounded text-sm transition-colors"
                      >
                        Set Alert
                      </button>
                    </div>
                  </div>

                  {/* Strategy Section */}
                  {pos.strategy ? (
                    <div className="bg-trader-bg rounded-lg p-3 mb-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">Active Strategy</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${pos.strategy.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                          {pos.strategy.status}
                        </span>
                      </div>
                      <p className="text-sm text-trader-muted mb-2">{pos.strategy.description}</p>
                      <div className="flex gap-2">
                        <button className="text-xs px-2 py-1 bg-trader-border hover:bg-trader-border/80 rounded transition-colors">
                          Edit
                        </button>
                        <button className="text-xs px-2 py-1 bg-trader-border hover:bg-trader-border/80 rounded transition-colors">
                          {pos.strategy.status === 'active' ? 'Pause' : 'Resume'}
                        </button>
                        <button className="text-xs px-2 py-1 bg-trader-red/20 hover:bg-trader-red/30 text-trader-red rounded transition-colors">
                          Remove
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-trader-bg/50 rounded-lg p-3">
                      {!isCreatingStrategy ? (
                        <button
                          onClick={(e) => { e.stopPropagation(); setIsCreatingStrategy(true); }}
                          className="w-full py-2 border-2 border-dashed border-trader-border hover:border-trader-blue text-trader-muted hover:text-trader-blue rounded-lg transition-colors"
                        >
                          + Add Exit Strategy
                        </button>
                      ) : (
                        <div onClick={(e) => e.stopPropagation()}>
                          <textarea
                            value={strategyInput}
                            onChange={(e) => setStrategyInput(e.target.value)}
                            placeholder="Describe your strategy (e.g., 'Sell 50% at $800, let rest run')"
                            className="w-full bg-trader-bg border border-trader-border rounded-lg px-3 py-2 text-sm mb-2 focus:outline-none focus:border-trader-blue"
                            rows={2}
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleCreateStrategy(pos.symbol)}
                              disabled={!strategyInput.trim()}
                              className="px-3 py-1.5 bg-trader-blue hover:bg-blue-600 disabled:opacity-50 rounded text-sm transition-colors"
                            >
                              Create Strategy
                            </button>
                            <button
                              onClick={() => { setIsCreatingStrategy(false); setStrategyInput(''); }}
                              className="px-3 py-1.5 bg-trader-border hover:bg-trader-border/80 rounded text-sm transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Cash Row */}
      <div className="p-4 border-t border-trader-border bg-trader-bg/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-xl">💵</div>
            <div>
              <div className="font-medium">Cash</div>
              <div className="text-sm text-trader-muted">Available to trade</div>
            </div>
          </div>
          <div className="font-semibold">{formatCurrency(portfolio.cash)}</div>
        </div>
      </div>
    </div>
  )
}

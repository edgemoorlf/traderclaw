import { useState, useRef, useEffect } from 'react'
import type { Portfolio, Position, StrategySuggestion, StrategyPreview } from '../types'

interface AIChatProps {
  portfolio: Portfolio | null
  selectedPosition: Position | null
  onStrategyCreated: () => void
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  actions?: { label: string; template: string }[]
  strategyPreview?: StrategyPreview
  timestamp: Date
}

export function AIChat({ portfolio, selectedPosition, onStrategyCreated }: AIChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'What would you like to do?',
      actions: [
        { label: '📈 Take profits on my winners', template: 'Take profits on' },
        { label: '🛡️ Protect my positions', template: 'Set stop loss on' },
        { label: '💰 Invest idle cash', template: 'Find opportunities for' },
        { label: '📋 Create portfolio-wide rule', template: 'Create rule:' },
      ],
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [currentPreview, setCurrentPreview] = useState<StrategyPreview | null>(null)
  const [clarifications, setClarifications] = useState<Record<string, string>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Update context when position is selected
  useEffect(() => {
    if (selectedPosition) {
      const contextMsg: Message = {
        role: 'assistant',
        content: `Selected ${selectedPosition.symbol}: ${selectedPosition.quantity} shares @ $${selectedPosition.avg_cost.toFixed(2)}, currently ${selectedPosition.unrealized_pnl_pct >= 0 ? '+' : ''}${(selectedPosition.unrealized_pnl_pct * 100).toFixed(1)}%`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, contextMsg])
    }
  }, [selectedPosition?.symbol])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMsg: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      // First, parse the strategy
      const parseRes = await fetch('http://localhost:8000/api/strategies/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: input,
          symbol: selectedPosition?.symbol,
        }),
      })

      if (parseRes.ok) {
        const preview = await parseRes.json()
        setCurrentPreview(preview)

        const assistantMsg: Message = {
          role: 'assistant',
          content: `I understand you want to: "${preview.interpretation}"`,
          strategyPreview: preview,
          timestamp: new Date(),
        }

        setMessages(prev => [...prev, assistantMsg])
        setShowPreview(true)
      }
    } catch (err) {
      console.error('Failed to parse:', err)
      const errorMsg: Message = {
        role: 'assistant',
        content: 'Sorry, I had trouble understanding that. Could you rephrase?',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = (template: string) => {
    const symbol = selectedPosition?.symbol || ''
    setInput(`${template} ${symbol}`.trim())
  }

  const handleConfirmStrategy = async () => {
    if (!currentPreview) return

    try {
      const res = await fetch('http://localhost:8000/api/strategies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: input,
          symbol: selectedPosition?.symbol,
          clarifications,
        }),
      })

      if (res.ok) {
        const result = await res.json()
        const confirmMsg: Message = {
          role: 'assistant',
          content: `✅ Strategy created! ${result.message}`,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, confirmMsg])
        setShowPreview(false)
        setCurrentPreview(null)
        setClarifications({})
        onStrategyCreated()
      }
    } catch (err) {
      console.error('Failed to create strategy:', err)
    }
  }

  return (
    <div className="bg-trader-card border border-trader-border rounded-lg flex flex-col" style={{ height: '60vh' }}>
      <div className="p-4 border-b border-trader-border flex items-center justify-between">
        <h2 className="text-lg font-semibold">🤖 AI Assistant</h2>
        <span className="text-xs text-trader-muted">Natural language commands</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-trader-blue text-white'
                  : 'bg-trader-bg text-trader-text'
              }`}
            >
              <p className="text-sm">{msg.content}</p>

              {/* Quick Action Buttons */}
              {msg.actions && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.actions.map((action, i) => (
                    <button
                      key={i}
                      onClick={() => handleQuickAction(action.template)}
                      className="px-3 py-1.5 bg-trader-border/50 hover:bg-trader-border rounded text-xs transition-colors"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}

              {/* Strategy Preview */}
              {msg.strategyPreview && (
                <div className="mt-3 bg-trader-card border border-trader-border rounded-lg p-3">
                  <div className="font-medium text-trader-green mb-2">
                    {msg.strategyPreview.title}
                  </div>
                  <ul className="text-xs space-y-1 text-trader-muted">
                    {msg.strategyPreview.readable_rules.map((rule, i) => (
                      <li key={i}>• {rule}</li>
                    ))}
                  </ul>
                  <div className="mt-2 text-xs">
                    Confidence: {msg.strategyPreview.confidence}%
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-trader-bg rounded-lg p-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-trader-blue rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-trader-blue rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div className="w-2 h-2 bg-trader-blue rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Clarification Panel */}
      {showPreview && currentPreview && currentPreview.ambiguities.length > 0 && (
        <div className="p-3 bg-trader-yellow/10 border-t border-trader-yellow/30">
          <div className="text-sm font-medium text-trader-yellow mb-2">
            I need clarification:
          </div>
          {currentPreview.ambiguities.map((ambiguity, idx) => (
            <div key={idx} className="mb-2">
              <div className="text-xs text-trader-muted mb-1">
                What did you mean by "{ambiguity.term}"?
              </div>
              <div className="flex flex-wrap gap-2">
                {ambiguity.options.map((option) => (
                  <button
                    key={option}
                    onClick={() => setClarifications(prev => ({ ...prev, [ambiguity.term]: option }))}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      clarifications[ambiguity.term] === option
                        ? 'bg-trader-blue text-white'
                        : 'bg-trader-bg hover:bg-trader-border'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirmation Actions */}
      {showPreview && currentPreview && (
        <div className="p-3 border-t border-trader-border flex gap-2">
          <button
            onClick={handleConfirmStrategy}
            className="flex-1 py-2 bg-trader-green hover:bg-green-600 rounded-lg text-sm font-medium transition-colors"
          >
            ✓ Create Strategy
          </button>
          <button
            onClick={() => { setShowPreview(false); setCurrentPreview(null); }}
            className="flex-1 py-2 bg-trader-border hover:bg-trader-border/80 rounded-lg text-sm transition-colors"
          >
            ✗ Cancel
          </button>
        </div>
      )}

      {/* Input */}
      {!showPreview && (
        <div className="p-4 border-t border-trader-border">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={selectedPosition ? `Ask about ${selectedPosition.symbol}...` : "Type a command (e.g., 'Sell 50% of NVDA')..."}
              className="flex-1 bg-trader-bg border border-trader-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-trader-blue"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 bg-trader-blue hover:bg-blue-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
            >
              Send
            </button>
          </div>
          <div className="mt-2 text-xs text-trader-muted">
            Try: "Sell NVDA if it drops 10%" or "Set trailing stop on AAPL"
          </div>
        </div>
      )}
    </div>
  )
}

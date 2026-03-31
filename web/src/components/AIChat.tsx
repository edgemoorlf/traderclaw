import { useState, useRef, useEffect } from 'react'
import type { Portfolio, Position, StrategyPreview } from '../types'
import { API_BASE } from '../api'

interface AIChatProps {
  portfolio: Portfolio | null
  selectedPosition: Position | null
  onStrategyCreated: () => void
}

interface Suggestion {
  id: string
  title: string
  description: string
  actions: { label: string; template: string }[]
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  suggestions?: Suggestion[]
  strategyPreview?: StrategyPreview
  showCreateStrategy?: boolean
  timestamp: Date
}

export function AIChat({ portfolio, selectedPosition, onStrategyCreated }: AIChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Ask me anything about your portfolio or a specific stock. When you're ready to set up a rule or strategy, just say so.",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [pendingStrategy, setPendingStrategy] = useState<{ description: string; symbol?: string } | null>(null)
  const [currentPreview, setCurrentPreview] = useState<StrategyPreview | null>(null)
  const [clarifications, setClarifications] = useState<Record<string, string>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (selectedPosition) {
      fetchSuggestions(selectedPosition.symbol)
    }
  }, [selectedPosition?.symbol])

  const fetchSuggestions = async (symbol: string) => {
    try {
      const res = await fetch(`${API_BASE}/positions/${symbol}/suggestions`)
      if (!res.ok) return
      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Here are some strategy ideas for your ${symbol} position:`,
        suggestions: data.suggestions,
        timestamp: new Date(),
      }])
    } catch (err) {
      console.error('Failed to fetch suggestions:', err)
    }
  }

  const isStrategyIntent = (text: string) => {
    const keywords = ['create strategy', 'set rule', 'set stop', 'set alert', 'sell when', 'buy when', 'if it drops', 'if it reaches', 'trailing stop', 'take profit', 'exit rule', 'entry rule']
    return keywords.some(k => text.toLowerCase().includes(k))
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userInput = input
    setMessages(prev => [...prev, { role: 'user', content: userInput, timestamp: new Date() }])
    setInput('')
    setIsLoading(true)

    try {
      if (isStrategyIntent(userInput)) {
        await handleStrategyParse(userInput)
      } else {
        const res = await fetch(`${API_BASE}/chat?message=${encodeURIComponent(userInput)}`, { method: 'POST' })
        if (res.ok) {
          const data = await res.json()
          // Check if the user is asking for suggestions/what to do
          const askingSuggestions = /what should|suggest|what (can|do) i|strategy|ideas|options|advice|建议|持仓|怎么|如何|应该/i.test(userInput)
          const symbol = selectedPosition?.symbol || extractSymbol(userInput)

          setMessages(prev => [...prev, {
            role: 'assistant',
            content: data.response,
            showCreateStrategy: data.actions?.length > 0,
            timestamp: new Date(),
          }])

          // Auto-fetch suggestions if user is asking what to do with a position
          if (askingSuggestions && symbol && portfolio?.positions.some(p => p.symbol === symbol)) {
            await fetchSuggestions(symbol)
          }
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const extractSymbol = (text: string): string | null => {
    const match = text.match(/\b[A-Z]{2,5}\b/)
    return match ? match[0] : null
  }

  const handleStrategyParse = async (description: string) => {
    const res = await fetch(`${API_BASE}/strategies/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, symbol: selectedPosition?.symbol }),
    })
    if (res.ok) {
      const preview = await res.json()
      setCurrentPreview(preview)
      setPendingStrategy({ description, symbol: selectedPosition?.symbol })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Here's what I'll set up: "${preview.interpretation}"`,
        strategyPreview: preview,
        timestamp: new Date(),
      }])
    }
  }

  const handleConfirmStrategy = async () => {
    if (!pendingStrategy || !currentPreview) return
    try {
      const res = await fetch(`${API_BASE}/strategies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...pendingStrategy, clarifications, approval_mode: 'hybrid' }),
      })
      if (res.ok) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: "✅ Strategy saved. I'll monitor this and alert you when conditions are met.",
          timestamp: new Date(),
        }])
        setCurrentPreview(null)
        setPendingStrategy(null)
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
        <h2 className="text-lg font-semibold">AI Assistant</h2>
        <span className="text-xs text-trader-muted">Powered by DeepSeek + Gemini</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[90%] rounded-lg p-3 ${msg.role === 'user' ? 'bg-trader-blue text-white' : 'bg-trader-bg text-trader-text'}`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

              {/* Strategy suggestions */}
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="mt-3 space-y-2">
                  {msg.suggestions.map((s) => (
                    <div key={s.id} className="bg-trader-card border border-trader-border rounded-lg p-3">
                      <div className="font-medium text-sm mb-1">{s.title}</div>
                      <div className="text-xs text-trader-muted mb-2">{s.description}</div>
                      <div className="flex flex-wrap gap-2">
                        {s.actions.map((action, i) => (
                          <button
                            key={i}
                            onClick={() => setInput(action.template)}
                            className="px-2 py-1 bg-trader-border/50 hover:bg-trader-blue/20 hover:text-trader-blue border border-trader-border rounded text-xs transition-colors"
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Strategy preview card */}
              {msg.strategyPreview && (
                <div className="mt-3 bg-trader-card border border-trader-border rounded-lg p-3">
                  <div className="font-medium text-trader-green mb-2">{msg.strategyPreview.title}</div>
                  <ul className="text-xs space-y-1 text-trader-muted">
                    {msg.strategyPreview.readable_rules.map((rule, i) => (
                      <li key={i}>• {rule}</li>
                    ))}
                  </ul>
                  <div className="mt-2 text-xs text-trader-muted">Confidence: {msg.strategyPreview.confidence}%</div>
                </div>
              )}

              {/* Offer to create strategy after AI analysis */}
              {msg.showCreateStrategy && !currentPreview && (
                <button
                  onClick={() => setInput('Create a strategy based on this analysis')}
                  className="mt-3 px-3 py-1.5 bg-trader-border/50 hover:bg-trader-border rounded text-xs transition-colors"
                >
                  + Turn this into a strategy
                </button>
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

      {/* Clarifications for pending strategy */}
      {currentPreview && currentPreview.ambiguities.length > 0 && (
        <div className="p-3 bg-trader-yellow/10 border-t border-trader-yellow/30">
          <div className="text-sm font-medium text-trader-yellow mb-2">Clarify before saving:</div>
          {currentPreview.ambiguities.map((ambiguity, idx) => (
            <div key={idx} className="mb-2">
              <div className="text-xs text-trader-muted mb-1">What did you mean by "{ambiguity.term}"?</div>
              <div className="flex flex-wrap gap-2">
                {ambiguity.options.map((option) => (
                  <button
                    key={option}
                    onClick={() => setClarifications(prev => ({ ...prev, [ambiguity.term]: option }))}
                    className={`px-2 py-1 text-xs rounded transition-colors ${clarifications[ambiguity.term] === option ? 'bg-trader-blue text-white' : 'bg-trader-bg hover:bg-trader-border'}`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirm/cancel strategy */}
      {currentPreview && (
        <div className="p-3 border-t border-trader-border flex gap-2">
          <button
            onClick={handleConfirmStrategy}
            className="flex-1 py-2 bg-trader-green hover:bg-green-600 rounded-lg text-sm font-medium transition-colors"
          >
            ✓ Save Strategy
          </button>
          <button
            onClick={() => { setCurrentPreview(null); setPendingStrategy(null) }}
            className="flex-1 py-2 bg-trader-border hover:bg-trader-border/80 rounded-lg text-sm transition-colors"
          >
            ✗ Cancel
          </button>
        </div>
      )}

      {/* Input */}
      {!currentPreview && (
        <div className="p-4 border-t border-trader-border">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={selectedPosition ? `Ask about ${selectedPosition.symbol} or click a suggestion above...` : 'Ask about your portfolio or a stock...'}
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
            Ask questions first. Say "set stop loss" or "sell when it reaches X" to create a rule.
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect, useCallback } from 'react'
import { PositionList } from './components/PositionList'
import { AIChat } from './components/AIChat'
import { AlertPanel } from './components/AlertPanel'
import { Header } from './components/Header'
import type { Portfolio, Alert, Signal, Position } from './types'
import './App.css'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [signals, setSignals] = useState<Signal[]>([])
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  // Fetch portfolio data
  const fetchPortfolio = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/portfolio`)
      if (res.ok) {
        const data = await res.json()
        setPortfolio(data)
      }
    } catch (err) {
      console.error('Failed to fetch portfolio:', err)
    }
  }, [])

  // Fetch alerts and signals
  const fetchAlertsAndSignals = useCallback(async () => {
    try {
      const [alertsRes, signalsRes] = await Promise.all([
        fetch(`${API_BASE}/alerts`),
        fetch(`${API_BASE}/signals/pending`),
      ])
      if (alertsRes.ok) setAlerts(await alertsRes.json())
      if (signalsRes.ok) setSignals(await signalsRes.json())
    } catch (err) {
      console.error('Failed to fetch alerts:', err)
    }
  }, [])

  // WebSocket connection
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8000/ws')

    websocket.onopen = () => {
      setIsConnected(true)
      console.log('WebSocket connected')
    }

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'portfolio_update') {
        setPortfolio(message.data)
      } else if (message.type === 'signal_updated') {
        fetchAlertsAndSignals()
      }
    }

    websocket.onclose = () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [fetchAlertsAndSignals])

  // Initial data fetch
  useEffect(() => {
    fetchPortfolio()
    fetchAlertsAndSignals()
    const interval = setInterval(fetchAlertsAndSignals, 30000)
    return () => clearInterval(interval)
  }, [fetchPortfolio, fetchAlertsAndSignals])

  const handleApproveSignal = async (signalId: string, action: 'approve' | 'reject') => {
    try {
      const res = await fetch(`${API_BASE}/signals/${signalId}/${action}`, {
        method: 'POST',
      })
      if (res.ok) {
        fetchAlertsAndSignals()
        fetchPortfolio()
      }
    } catch (err) {
      console.error('Failed to approve signal:', err)
    }
  }

  return (
    <div className="min-h-screen bg-trader-bg text-trader-text">
      <Header
        portfolio={portfolio}
        isConnected={isConnected}
      />

      <main className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-4" style={{ height: 'calc(100vh - 80px)' }}>
        {/* Left Column - Positions */}
        <div className="flex flex-col gap-4 overflow-hidden">
          <PositionList
            portfolio={portfolio}
            selectedPosition={selectedPosition}
            onSelectPosition={setSelectedPosition}
            onUpdate={fetchPortfolio}
          />
        </div>

        {/* Right Column - AI Chat */}
        <div className="flex flex-col gap-4 overflow-hidden">
          <AIChat
            portfolio={portfolio}
            selectedPosition={selectedPosition}
            onStrategyCreated={fetchPortfolio}
          />
        </div>

        {/* Bottom - Alerts */}
        <div className="lg:col-span-2">
          <AlertPanel
            alerts={alerts}
            signals={signals}
            onApproveSignal={handleApproveSignal}
          />
        </div>
      </main>
    </div>
  )
}

export default App

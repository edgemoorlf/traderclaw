import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AlertPanel } from '../../web/src/components/AlertPanel'
import type { Alert, Signal } from '../../web/src/types'

const makeAlert = (overrides: Partial<Alert> = {}): Alert => ({
  id: 'a1',
  type: 'risk_alert',
  symbol: 'AAPL',
  message: 'Position is overweight',
  severity: 'warning',
  data: {},
  created_at: '2026-03-27T10:00:00Z',
  ...overrides,
})

const makeSignal = (overrides: Partial<Signal> = {}): Signal => ({
  id: 's1',
  symbol: 'NVDA',
  action: 'SELL',
  quantity: 10,
  price: 800,
  reason: 'Take profits',
  confidence: 85,
  position_context: {},
  portfolio_impact: { concentration_before: '33%', concentration_after: '16%' },
  status: 'pending',
  created_at: '2026-03-27T10:00:00Z',
  ...overrides,
})

describe('AlertPanel', () => {
  it('shows empty state when no alerts or signals', () => {
    render(<AlertPanel alerts={[]} signals={[]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText(/All caught up/i)).toBeInTheDocument()
  })

  it('shows item count in header', () => {
    render(<AlertPanel alerts={[makeAlert()]} signals={[makeSignal()]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText('2 items')).toBeInTheDocument()
  })

  it('shows pending badge when signals exist', () => {
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText('1 pending')).toBeInTheDocument()
  })

  it('does not show pending badge when no signals', () => {
    render(<AlertPanel alerts={[makeAlert()]} signals={[]} onApproveSignal={vi.fn()} />)
    expect(screen.queryByText(/pending/)).not.toBeInTheDocument()
  })

  it('renders signal symbol and action', () => {
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText('NVDA')).toBeInTheDocument()
    expect(screen.getByText('SELL')).toBeInTheDocument()
  })

  it('renders signal reason', () => {
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText('Take profits')).toBeInTheDocument()
  })

  it('renders approve and reject buttons for signals', () => {
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText(/Approve/i)).toBeInTheDocument()
    expect(screen.getByText(/Reject/i)).toBeInTheDocument()
  })

  it('calls onApproveSignal with approve when approve clicked', () => {
    const onApprove = vi.fn()
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={onApprove} />)
    fireEvent.click(screen.getByText(/Approve/i))
    expect(onApprove).toHaveBeenCalledWith('s1', 'approve')
  })

  it('calls onApproveSignal with reject when reject clicked', () => {
    const onApprove = vi.fn()
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={onApprove} />)
    fireEvent.click(screen.getByText(/Reject/i))
    expect(onApprove).toHaveBeenCalledWith('s1', 'reject')
  })

  it('renders alert message', () => {
    render(<AlertPanel alerts={[makeAlert()]} signals={[]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText('Position is overweight')).toBeInTheDocument()
  })

  it('renders alert symbol', () => {
    render(<AlertPanel alerts={[makeAlert()]} signals={[]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText('AAPL')).toBeInTheDocument()
  })

  it('renders multiple signals', () => {
    const signals = [
      makeSignal({ id: 's1', symbol: 'NVDA' }),
      makeSignal({ id: 's2', symbol: 'AAPL', action: 'BUY' }),
    ]
    render(<AlertPanel alerts={[]} signals={signals} onApproveSignal={vi.fn()} />)
    expect(screen.getByText('NVDA')).toBeInTheDocument()
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('2 pending')).toBeInTheDocument()
  })

  it('shows concentration impact when portfolio_impact has data', () => {
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText(/33%/)).toBeInTheDocument()
    expect(screen.getByText(/16%/)).toBeInTheDocument()
  })

  it('shows confidence percentage', () => {
    render(<AlertPanel alerts={[]} signals={[makeSignal()]} onApproveSignal={vi.fn()} />)
    expect(screen.getByText(/Confidence: 85%/)).toBeInTheDocument()
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PositionList } from '../../web/src/components/PositionList'
import type { Portfolio, Position } from '../../web/src/types'

const makePosition = (overrides: Partial<Position> = {}): Position => ({
  symbol: 'AAPL',
  quantity: 100,
  avg_cost: 150,
  current_price: 180,
  market_value: 18000,
  unrealized_pnl: 3000,
  unrealized_pnl_pct: 0.2,
  portfolio_weight: 0.18,
  ...overrides,
})

const makePortfolio = (positions: Position[] = [makePosition()]): Portfolio => ({
  total_value: 100000,
  cash: 10000,
  positions,
  daily_change: 500,
  daily_change_pct: 0.5,
})

describe('PositionList', () => {
  const defaultProps = {
    selectedPosition: null,
    onSelectPosition: vi.fn(),
    onUpdate: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty state when portfolio is null', () => {
    render(<PositionList portfolio={null} {...defaultProps} />)
    expect(screen.getByText(/No positions imported yet/i)).toBeInTheDocument()
  })

  it('shows empty state when portfolio has no positions', () => {
    render(<PositionList portfolio={makePortfolio([])} {...defaultProps} />)
    expect(screen.getByText(/No positions imported yet/i)).toBeInTheDocument()
  })

  it('shows Import Portfolio button in empty state', () => {
    render(<PositionList portfolio={null} {...defaultProps} />)
    expect(screen.getByText('Import Portfolio')).toBeInTheDocument()
  })

  it('renders position symbol', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    expect(screen.getByText('AAPL')).toBeInTheDocument()
  })

  it('renders position count', () => {
    const portfolio = makePortfolio([makePosition(), makePosition({ symbol: 'NVDA' })])
    render(<PositionList portfolio={portfolio} {...defaultProps} />)
    expect(screen.getByText('2 positions')).toBeInTheDocument()
  })

  it('renders market value', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    expect(screen.getByText('$18,000.00')).toBeInTheDocument()
  })

  it('renders cash row', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    expect(screen.getByText('Cash')).toBeInTheDocument()
    expect(screen.getByText('$10,000.00')).toBeInTheDocument()
  })

  it('shows No strategy label when position has no strategy', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    expect(screen.getByText('No strategy')).toBeInTheDocument()
  })

  it('shows strategy description when position has active strategy', () => {
    const pos = makePosition({
      strategy: {
        id: 'strat1',
        name: 'My Strategy',
        description: 'Sell at $200 target price',
        approval_mode: 'hybrid',
        status: 'active',
      },
    })
    render(<PositionList portfolio={makePortfolio([pos])} {...defaultProps} />)
    expect(screen.getByText(/Sell at \$200 target/)).toBeInTheDocument()
  })

  it('calls onSelectPosition when row is clicked', () => {
    const onSelect = vi.fn()
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} onSelectPosition={onSelect} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ symbol: 'AAPL' }))
  })

  it('expands position detail on click', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    expect(screen.getByText('Current Price')).toBeInTheDocument()
    expect(screen.getByText('Portfolio Weight')).toBeInTheDocument()
  })

  it('collapses position detail on second click', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    const row = screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!
    fireEvent.click(row)
    fireEvent.click(row)
    expect(screen.queryByText('Current Price')).not.toBeInTheDocument()
  })

  it('shows quick action buttons when expanded', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    expect(screen.getByText('Sell 50%')).toBeInTheDocument()
    expect(screen.getByText('Set Stop Loss')).toBeInTheDocument()
    expect(screen.getByText('Set Alert')).toBeInTheDocument()
  })

  it('shows Add Exit Strategy button when no strategy and expanded', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    expect(screen.getByText('+ Add Exit Strategy')).toBeInTheDocument()
  })

  it('shows strategy textarea when Add Exit Strategy is clicked', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    fireEvent.click(screen.getByText('+ Add Exit Strategy'))
    expect(screen.getByPlaceholderText(/Describe your strategy/i)).toBeInTheDocument()
  })

  it('shows Create Strategy button disabled when textarea is empty', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    fireEvent.click(screen.getByText('+ Add Exit Strategy'))
    const btn = screen.getByText('Create Strategy') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it('enables Create Strategy button when text is entered', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    fireEvent.click(screen.getByText('+ Add Exit Strategy'))
    fireEvent.change(screen.getByPlaceholderText(/Describe your strategy/i), {
      target: { value: 'Sell at $200' },
    })
    const btn = screen.getByText('Create Strategy') as HTMLButtonElement
    expect(btn.disabled).toBe(false)
  })

  it('hides strategy form when Cancel is clicked', () => {
    render(<PositionList portfolio={makePortfolio()} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    fireEvent.click(screen.getByText('+ Add Exit Strategy'))
    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByPlaceholderText(/Describe your strategy/i)).not.toBeInTheDocument()
  })

  it('shows concentration warning when portfolio_weight > 25%', () => {
    const pos = makePosition({ portfolio_weight: 0.3 })
    render(<PositionList portfolio={makePortfolio([pos])} {...defaultProps} />)
    fireEvent.click(screen.getByText('AAPL').closest('[class*="cursor-pointer"]')!)
    expect(screen.getByText(/⚠️/)).toBeInTheDocument()
  })
})

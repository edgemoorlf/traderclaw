import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AIChat } from '../../web/src/components/AIChat'
import type { Portfolio, Position } from '../../web/src/types'

const makePosition = (overrides: Partial<Position> = {}): Position => ({
  symbol: 'NVDA',
  quantity: 80,
  avg_cost: 400,
  current_price: 800,
  market_value: 64000,
  unrealized_pnl: 32000,
  unrealized_pnl_pct: 1.0,
  portfolio_weight: 0.33,
  ...overrides,
})

const makePortfolio = (): Portfolio => ({
  total_value: 200000,
  cash: 20000,
  positions: [makePosition()],
  daily_change: 1000,
  daily_change_pct: 0.5,
})

const mockPreview = {
  title: 'Profit Taking Strategy',
  interpretation: 'Sell 50% of NVDA when it reaches $900',
  ambiguities: [],
  impact: { shares_to_sell: 40, estimated_proceeds: 36000 },
  confidence: 85,
  readable_rules: ['WHEN NVDA reaches $900', 'SELL 40 shares (50%)'],
}

describe('AIChat', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the AI Assistant heading', () => {
    render(<AIChat portfolio={null} selectedPosition={null} onStrategyCreated={vi.fn()} />)
    expect(screen.getByText(/AI Assistant/i)).toBeInTheDocument()
  })

  it('shows initial greeting message', () => {
    render(<AIChat portfolio={null} selectedPosition={null} onStrategyCreated={vi.fn()} />)
    expect(screen.getByText(/What would you like to do/i)).toBeInTheDocument()
  })

  it('renders quick action buttons in initial message', () => {
    render(<AIChat portfolio={null} selectedPosition={null} onStrategyCreated={vi.fn()} />)
    expect(screen.getByText(/Take profits on my winners/i)).toBeInTheDocument()
    expect(screen.getByText(/Protect my positions/i)).toBeInTheDocument()
    expect(screen.getByText(/Invest idle cash/i)).toBeInTheDocument()
  })

  it('renders text input and Send button', () => {
    render(<AIChat portfolio={null} selectedPosition={null} onStrategyCreated={vi.fn()} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByText('Send')).toBeInTheDocument()
  })

  it('Send button is disabled when input is empty', () => {
    render(<AIChat portfolio={null} selectedPosition={null} onStrategyCreated={vi.fn()} />)
    expect(screen.getByText('Send')).toBeDisabled()
  })

  it('Send button is enabled when input has text', () => {
    render(<AIChat portfolio={null} selectedPosition={null} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell NVDA' } })
    expect(screen.getByText('Send')).not.toBeDisabled()
  })

  it('clicking a quick action populates the input', () => {
    render(<AIChat portfolio={null} selectedPosition={null} onStrategyCreated={vi.fn()} />)
    fireEvent.click(screen.getByText(/Protect my positions/i))
    expect((screen.getByRole('textbox') as HTMLInputElement).value).toMatch(/Set stop loss on/i)
  })

  it('quick action appends selected position symbol when one is selected', () => {
    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.click(screen.getByText(/Take profits on my winners/i))
    expect((screen.getByRole('textbox') as HTMLInputElement).value).toContain('NVDA')
  })

  it('shows context message when a position is selected', () => {
    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    expect(screen.getByText(/Selected NVDA/i)).toBeInTheDocument()
  })

  it('input placeholder changes when position is selected', () => {
    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    expect(screen.getByPlaceholderText(/Ask about NVDA/i)).toBeInTheDocument()
  })

  it('sends user message and shows it in chat', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPreview,
    }))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText('Sell half at $900')).toBeInTheDocument()
    })
  })

  it('clears input after sending', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPreview,
    }))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect((screen.queryByRole('textbox') as HTMLInputElement | null)?.value ?? '').toBe('')
    })
  })

  it('shows strategy preview after successful parse', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPreview,
    }))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText('Profit Taking Strategy')).toBeInTheDocument()
      expect(screen.getByText(/Confidence: 85%/)).toBeInTheDocument()
    })
  })

  it('shows Create Strategy and Cancel buttons after preview', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPreview,
    }))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText(/Create Strategy/i)).toBeInTheDocument()
      expect(screen.getByText(/Cancel/i)).toBeInTheDocument()
    })
  })

  it('hides preview and shows input again when Cancel is clicked', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPreview,
    }))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => screen.getByText(/Cancel/i))
    fireEvent.click(screen.getByText(/Cancel/i))

    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.queryByText(/Create Strategy/i)).not.toBeInTheDocument()
  })

  it('shows error message when parse request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText(/trouble understanding/i)).toBeInTheDocument()
    })
  })

  it('shows clarification panel when ambiguities exist', async () => {
    const previewWithAmbiguity = {
      ...mockPreview,
      ambiguities: [
        { term: 'high price', options: ['$800', '$850', '$900'], default: '$800', context: 'Current price is $800' },
      ],
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => previewWithAmbiguity,
    }))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell at high price' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText(/I need clarification/i)).toBeInTheDocument()
      expect(screen.getAllByText(/high price/i).length).toBeGreaterThan(0)
    })
  })

  it('calls onStrategyCreated after confirming strategy', async () => {
    const onStrategyCreated = vi.fn()
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => mockPreview })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'strat1', message: 'Strategy created for NVDA' }) })
    )

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={onStrategyCreated} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => screen.getByText(/Create Strategy/i))
    fireEvent.click(screen.getByText(/Create Strategy/i))

    await waitFor(() => {
      expect(onStrategyCreated).toHaveBeenCalled()
    })
  })

  it('shows success message after strategy is created', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => mockPreview })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'strat1', message: 'Strategy created for NVDA' }) })
    )

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Sell half at $900' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => screen.getByText(/Create Strategy/i))
    fireEvent.click(screen.getByText(/Create Strategy/i))

    await waitFor(() => {
      expect(screen.getByText(/Strategy created/i)).toBeInTheDocument()
    })
  })

  it('sends Enter key to trigger send', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockPreview,
    }))

    render(<AIChat portfolio={makePortfolio()} selectedPosition={makePosition()} onStrategyCreated={vi.fn()} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'Sell NVDA' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('Sell NVDA')).toBeInTheDocument()
    })
  })
})

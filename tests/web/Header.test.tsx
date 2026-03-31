import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Header } from '../../web/src/components/Header'

const basePortfolio = {
  total_value: 100000,
  daily_change: 1500,
  daily_change_pct: 1.5,
}

describe('Header', () => {
  it('renders app title', () => {
    render(<Header portfolio={null} isConnected={false} />)
    expect(screen.getByText(/TraderClaw/i)).toBeInTheDocument()
  })

  it('shows Disconnected when not connected', () => {
    render(<Header portfolio={basePortfolio} isConnected={false} />)
    expect(screen.getByText('Disconnected')).toBeInTheDocument()
  })

  it('shows System Active when connected', () => {
    render(<Header portfolio={basePortfolio} isConnected={true} />)
    expect(screen.getByText('System Active')).toBeInTheDocument()
  })

  it('renders nothing portfolio-related when portfolio is null', () => {
    render(<Header portfolio={null} isConnected={false} />)
    expect(screen.queryByText('Portfolio Value')).not.toBeInTheDocument()
  })

  it('shows portfolio value when provided', () => {
    render(<Header portfolio={basePortfolio} isConnected={true} />)
    expect(screen.getByText('Portfolio Value')).toBeInTheDocument()
    expect(screen.getByText('$100,000')).toBeInTheDocument()
  })

  it('shows positive daily change with up arrow', () => {
    render(<Header portfolio={basePortfolio} isConnected={true} />)
    expect(screen.getByText(/▲/)).toBeInTheDocument()
    expect(screen.getByText(/\+1\.50%/)).toBeInTheDocument()
  })

  it('shows negative daily change with down arrow', () => {
    render(<Header portfolio={{ ...basePortfolio, daily_change: -500, daily_change_pct: -0.5 }} isConnected={true} />)
    expect(screen.getByText(/▼/)).toBeInTheDocument()
    expect(screen.getByText(/-0\.50%/)).toBeInTheDocument()
  })
})

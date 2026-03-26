interface HeaderProps {
  portfolio: {
    total_value: number;
    daily_change: number;
    daily_change_pct: number;
  } | null;
  isConnected: boolean;
}

export function Header({ portfolio, isConnected }: HeaderProps) {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);
  };

  const isPositive = (portfolio?.daily_change || 0) >= 0;

  return (
    <header className="bg-trader-card border-b border-trader-border px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-green-400 bg-clip-text text-transparent">
            📊 TraderClaw
          </div>
          <span className="text-sm text-trader-muted">AI Trading Assistant</span>
        </div>

        {portfolio && (
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-sm text-trader-muted">Portfolio Value</div>
              <div className="text-xl font-semibold">
                {formatCurrency(portfolio.total_value)}
              </div>
            </div>

            <div className="text-right">
              <div className="text-sm text-trader-muted">Today's Change</div>
              <div className={`text-lg font-semibold flex items-center gap-1 ${isPositive ? 'text-trader-green' : 'text-trader-red'}`}>
                {isPositive ? '▲' : '▼'}
                {formatCurrency(Math.abs(portfolio.daily_change))}
                <span className="text-sm">({portfolio.daily_change_pct >= 0 ? '+' : ''}{portfolio.daily_change_pct.toFixed(2)}%)</span>
              </div>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 bg-trader-bg rounded-lg">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-trader-green status-active' : 'bg-trader-red'}`} />
              <span className="text-xs text-trader-muted">
                {isConnected ? 'System Active' : 'Disconnected'}
              </span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

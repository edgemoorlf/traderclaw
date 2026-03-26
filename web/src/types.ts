export interface Position {
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  portfolio_weight: number;
  strategy?: {
    id: string;
    name: string;
    description: string;
    approval_mode: string;
    status: 'active' | 'paused';
  };
}

export interface Portfolio {
  total_value: number;
  cash: number;
  positions: Position[];
  daily_change: number;
  daily_change_pct: number;
}

export interface Alert {
  id: string;
  type: 'approaching_target' | 'signal_pending' | 'risk_alert';
  symbol: string;
  message: string;
  severity: 'info' | 'warning' | 'action_required';
  data: Record<string, any>;
  created_at: string;
}

export interface Signal {
  id: string;
  symbol: string;
  action: string;
  quantity?: number;
  price?: number;
  reason: string;
  confidence: number;
  position_context: Record<string, any>;
  portfolio_impact: Record<string, any>;
  status: 'pending' | 'approved' | 'rejected' | 'executed';
  created_at: string;
}

export interface StrategySuggestion {
  id: string;
  title: string;
  description: string;
  actions: {
    label: string;
    template: string;
  }[];
}

export interface StrategyPreview {
  title: string;
  interpretation: string;
  ambiguities: {
    term: string;
    options: string[];
    default: string;
    context: string;
  }[];
  impact: {
    shares_to_sell?: number;
    estimated_proceeds?: number;
    remaining_shares?: number;
    concentration_before?: string;
    concentration_after?: string;
  };
  confidence: number;
  readable_rules: string[];
}

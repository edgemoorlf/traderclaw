export const API_BASE = `/api`
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
export const WS_BASE = `${wsProtocol}//${window.location.host}/ws`

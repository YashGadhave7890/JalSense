/**
 * Formatting and utility functions for JalSense
 */

export function formatLitres(val: number | null | undefined, compact = false): string {
  if (val === null || val === undefined || isNaN(val)) return '0 L'
  if (compact && Math.abs(val) >= 1_000_000) {
    return `${(val / 1_000_000).toFixed(2)} ML`
  }
  if (compact && Math.abs(val) >= 100_000) {
    return `${(val / 1_000).toFixed(1)}k L`
  }
  return `${Math.round(val).toLocaleString('en-IN')} L`
}

export function formatPercentage(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined || isNaN(val)) return '0%'
  return `${val.toFixed(decimals)}%`
}

export function formatTemperature(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '0.0 °C'
  return `${val.toFixed(1)} °C`
}

export function formatLpcd(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '0.0 LPCD'
  return `${val.toFixed(1)} LPCD`
}

export function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  } catch {
    return dateStr
  }
}

export function getRiskBadgeClasses(risk: string): { bg: string; text: string; border: string; dot: string } {
  const r = (risk || 'LOW').toUpperCase()
  switch (r) {
    case 'CRITICAL':
      return {
        bg: 'bg-red-50',
        text: 'text-red-700',
        border: 'border-red-200',
        dot: 'bg-red-600'
      }
    case 'HIGH':
      return {
        bg: 'bg-orange-50',
        text: 'text-orange-700',
        border: 'border-orange-200',
        dot: 'bg-orange-600'
      }
    case 'MODERATE':
      return {
        bg: 'bg-amber-50',
        text: 'text-amber-700',
        border: 'border-amber-200',
        dot: 'bg-amber-600'
      }
    case 'LOW':
    default:
      return {
        bg: 'bg-emerald-50',
        text: 'text-emerald-700',
        border: 'border-emerald-200',
        dot: 'bg-emerald-600'
      }
  }
}

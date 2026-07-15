import type { Language } from './schemas'

export function formatNumber(value: number, language: Language): string {
  return new Intl.NumberFormat(language === 'he' ? 'he-IL' : 'en-IL', {
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatPercent(value: number, language: Language, fractionDigits = 1): string {
  return new Intl.NumberFormat(language === 'he' ? 'he-IL' : 'en-IL', {
    style: 'percent',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value)
}

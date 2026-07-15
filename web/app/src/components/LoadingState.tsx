import type { Language } from '../domain/schemas'
import { translate } from '../i18n/translations'

interface LoadingStateProps {
  language: Language
  kind?: 'data' | 'map'
}

export function LoadingState({ language, kind = 'data' }: LoadingStateProps) {
  return (
    <div className="loading-state" role="status">
      <span className="loading-spinner" aria-hidden="true" />
      <span>{translate(language, kind === 'map' ? 'loadingMap' : 'loadingData')}</span>
    </div>
  )
}

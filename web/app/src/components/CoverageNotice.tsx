import { formatNumber, formatPercent } from '../domain/format'
import type { Coverage, Language } from '../domain/schemas'
import { translate } from '../i18n/translations'

interface CoverageNoticeProps {
  coverage: Coverage
  language: Language
}

export function CoverageNotice({ coverage, language }: CoverageNoticeProps) {
  const isPartial = coverage.mappedActualVoterShare < 0.95

  return (
    <section className={`coverage-notice${isPartial ? ' coverage-notice--warning' : ''}`} aria-live="polite">
      <div className="coverage-heading">
        <span>{translate(language, 'mappedCoverage')}</span>
        <strong>{formatPercent(coverage.mappedActualVoterShare, language)}</strong>
      </div>
      <div
        className="coverage-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(coverage.mappedActualVoterShare * 100)}
      >
        <span style={{ inlineSize: `${coverage.mappedActualVoterShare * 100}%` }} />
      </div>
      <p>
        {formatNumber(coverage.mappedActualVoters, language)} {translate(language, 'mappedVotes')} ·{' '}
        {formatNumber(coverage.pendingActualVoters, language)} {translate(language, 'pendingVotes')}
      </p>
      {isPartial ? (
        <div className="coverage-explainer">
          <strong>{translate(language, 'partialDataTitle')}</strong>
          <span>{translate(language, 'partialDataBody')}</span>
        </div>
      ) : null}
    </section>
  )
}

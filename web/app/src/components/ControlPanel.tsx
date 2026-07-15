import type {
  ElectionCatalog,
  GeographyMode,
  GeographyModeCatalog,
  Language,
} from '../domain/schemas'
import { translate } from '../i18n/translations'

interface ControlPanelProps {
  language: Language
  elections: ElectionCatalog[]
  geographyModes: GeographyModeCatalog[]
  electionId: string
  geographyMode: GeographyMode
  onElectionChange: (electionId: string) => void
  onGeographyModeChange: (mode: GeographyMode) => void
}

export function ControlPanel({
  language,
  elections,
  geographyModes,
  electionId,
  geographyMode,
  onElectionChange,
  onGeographyModeChange,
}: ControlPanelProps) {
  return (
    <section className="control-panel" aria-label={`${translate(language, 'election')} / ${translate(language, 'geography')}`}>
      <label className="field">
        <span>{translate(language, 'election')}</span>
        <select value={electionId} onChange={(event) => onElectionChange(event.target.value)}>
          {elections.map((election) => (
            <option key={election.id} value={election.id}>
              {election.label[language]}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>{translate(language, 'geography')}</span>
        <select
          value={geographyMode}
          onChange={(event) => onGeographyModeChange(event.target.value as GeographyMode)}
        >
          {geographyModes.map((mode) => (
            <option key={mode.id} value={mode.id}>
              {mode.label[language]}
            </option>
          ))}
        </select>
      </label>
    </section>
  )
}

import type { FilterSpecification } from 'maplibre-gl'
import type { ResultRecord } from './schemas'

const WEST_BANK_LOCALITY_CODE_MIN = 3500
const WEST_BANK_LOCALITY_CODE_MAX_EXCLUSIVE = 4000

export function mayHaveDisplayMarker(record: ResultRecord): boolean {
  if (record.geographyType === 'custom') {
    return true
  }

  const localityCode = Number(record.localityId?.replace(/^loc:/, '') ?? record.code)
  return (
    Number.isInteger(localityCode) &&
    localityCode >= WEST_BANK_LOCALITY_CODE_MIN &&
    localityCode < WEST_BANK_LOCALITY_CODE_MAX_EXCLUSIVE
  )
}

export function buildMarkerVisibilityFilter(records: ResultRecord[]): FilterSpecification {
  const customIdsWithData = records
    .filter((record) => record.geographyType === 'custom')
    .map((record) => record.id)

  return [
    'any',
    ['!=', ['get', 'geographyType'], 'custom'],
    ['in', ['get', 'id'], ['literal', customIdsWithData]],
  ]
}

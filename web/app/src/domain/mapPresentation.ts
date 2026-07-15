import type { FilterSpecification } from 'maplibre-gl'
import type { ResultRecord } from './schemas'

const WEST_BANK_LOCALITY_CODE_MIN = 3500
const WEST_BANK_LOCALITY_CODE_MAX_EXCLUSIVE = 4000
const KINNERET_GEOGRAPHY_IDS = ['loc:9920', 'stat2022:9920']

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

export function buildMarkerVisibilityFilter(
  records: ResultRecord[],
  hiddenGeographyIds: string[] = [],
): FilterSpecification {
  const customIdsWithData = records
    .filter((record) => record.geographyType === 'custom')
    .map((record) => record.id)
  const excludedIds = [...new Set(hiddenGeographyIds)].toSorted()

  return [
    'all',
    ['!', ['in', ['get', 'id'], ['literal', excludedIds]]],
    [
      'any',
      ['!=', ['get', 'geographyType'], 'custom'],
      ['in', ['get', 'id'], ['literal', customIdsWithData]],
    ],
  ]
}

export function buildPolygonVisibilityFilter(
  hiddenGeographyIds: string[],
): FilterSpecification {
  const excludedIds = [...new Set([...KINNERET_GEOGRAPHY_IDS, ...hiddenGeographyIds])].toSorted()

  return [
    'all',
    ['!=', ['get', 'displayMode'], 'marker'],
    ['!', ['in', ['get', 'id'], ['literal', excludedIds]]],
  ]
}

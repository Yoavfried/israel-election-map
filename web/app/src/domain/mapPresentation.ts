import type { FilterSpecification } from 'maplibre-gl'
import type { ResultRecord } from './schemas'

const WEST_BANK_LOCALITY_CODE_MIN = 3500
const WEST_BANK_LOCALITY_CODE_MAX_EXCLUSIVE = 4000
const SPECIAL_POINT_PROXY_LOCALITY_CODES = new Set([1791, 1792, 1793, 1794, 3488])

export function mayHaveDisplayMarker(record: ResultRecord): boolean {
  if (record.geographyType === 'custom') {
    return true
  }

  const localityCode = Number(record.localityId?.replace(/^loc:/, '') ?? record.code)
  return (
    Number.isInteger(localityCode) &&
    (SPECIAL_POINT_PROXY_LOCALITY_CODES.has(localityCode) ||
      (localityCode >= WEST_BANK_LOCALITY_CODE_MIN &&
        localityCode < WEST_BANK_LOCALITY_CODE_MAX_EXCLUSIVE))
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
  const excludedIds = [...new Set(hiddenGeographyIds)].toSorted()

  return [
    'all',
    ['!=', ['get', 'displayMode'], 'marker'],
    ['!=', ['get', 'localityCode'], '9920'],
    ['!', ['in', ['get', 'id'], ['literal', excludedIds]]],
  ]
}

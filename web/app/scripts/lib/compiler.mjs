import Papa from 'papaparse'

const RESULT_CORE_LAST_COLUMN = 'winning_vote_share'
const DEFAULT_PARTY_SATURATION = 58
const DEFAULT_PARTY_LIGHTNESS = 46
const POINT_PROXY_MAX_VERTICES = 12

export function parseCsv(text, sourceName = 'CSV input') {
  const parsed = Papa.parse(text, {
    header: true,
    skipEmptyLines: 'greedy',
    transformHeader: (header) => header.replace(/^\uFEFF/, '').trim(),
  })

  if (parsed.errors.length > 0) {
    const message = parsed.errors
      .slice(0, 5)
      .map((error) => `row ${error.row ?? '?'}: ${error.message}`)
      .join('; ')
    throw new Error(`${sourceName} could not be parsed: ${message}`)
  }

  return parsed.data
}

export function numberValue(value, fieldName = 'value') {
  if (value === '' || value === null || value === undefined) {
    return 0
  }

  const parsed = Number(String(value).replaceAll(',', '').trim())
  if (!Number.isFinite(parsed)) {
    throw new Error(`Expected a number for ${fieldName}, received ${JSON.stringify(value)}`)
  }
  return parsed
}

export function cleanNumericCode(value) {
  return String(value ?? '').trim().replace(/\.0+$/, '')
}

export function isWestBankSettlementCode(value) {
  const code = Number(cleanNumericCode(value))
  return Number.isInteger(code) && code >= 3500 && code < 4000
}

export function isPointLikeGeometry(geometry) {
  return coordinatePositionCount(geometry?.coordinates) <= POINT_PROXY_MAX_VERTICES
}

export function buildMetadataIndex(rows, mode) {
  const index = new Map()
  for (const row of rows) {
    const id = mode === 'statistical-area' ? row.stat_area_id : row.locality_id
    if (!id) {
      throw new Error(`Missing ${mode} ID in geography metadata`)
    }
    index.set(id, {
      id,
      localityId: row.locality_id,
      localityCode: cleanNumericCode(row.locality_code),
      nameHe: row.locality_name_he || '',
      nameEn: row.locality_name_en || row.locality_name_he || '',
      statAreaNumber: cleanNumericCode(row.stat_2022),
      yishuvStat2022: cleanNumericCode(row.yishuv_stat_2022),
    })
  }
  return index
}

export function buildCustomMetadataIndex(featureCollection) {
  assertFeatureCollection(featureCollection, 'custom geography')
  const index = new Map()
  for (const feature of featureCollection.features) {
    const properties = feature.properties ?? {}
    const id = properties.custom_id
    if (!id) {
      throw new Error('Custom geography feature is missing custom_id')
    }
    index.set(id, {
      id,
      customKey: properties.custom_key || id,
      nameHe: properties.name_he || id,
      nameEn: properties.name_en || properties.name_he || id,
      note: properties.note || '',
    })
  }
  return index
}

export function pruneGeography(featureCollection, mode, customFeatureCollection) {
  assertFeatureCollection(featureCollection, mode)
  assertFeatureCollection(customFeatureCollection, 'custom geography')

  const features = featureCollection.features.map((feature) => {
    const properties = feature.properties ?? {}
    const id = mode === 'statistical-area' ? properties.stat_area_id : properties.locality_id
    if (!id) {
      throw new Error(`${mode} feature is missing its stable ID`)
    }

    const statAreaNumber = cleanNumericCode(properties.stat_2022)
    const displayMode =
      isWestBankSettlementCode(properties.locality_code) && isPointLikeGeometry(feature.geometry)
        ? 'marker'
        : 'polygon'
    return {
      type: 'Feature',
      id,
      properties: {
        id,
        geographyType: mode,
        localityId: properties.locality_id,
        localityCode: cleanNumericCode(properties.locality_code),
        nameHe: properties.locality_name_he || '',
        nameEn: properties.locality_name_en || properties.locality_name_he || '',
        displayMode,
        ...(mode === 'statistical-area' ? { statAreaNumber } : {}),
      },
      geometry: roundGeometry(feature.geometry),
    }
  })

  for (const feature of customFeatureCollection.features) {
    const properties = feature.properties ?? {}
    const id = properties.custom_id
    if (!id) {
      throw new Error('Custom geography feature is missing custom_id')
    }
    features.push({
      type: 'Feature',
      id,
      properties: {
        id,
        geographyType: 'custom',
        customKey: properties.custom_key || id,
        nameHe: properties.name_he || id,
        nameEn: properties.name_en || properties.name_he || id,
        displayMode: 'marker',
      },
      geometry: roundGeometry(feature.geometry),
    })
  }

  return {
    type: 'FeatureCollection',
    features,
  }
}

export function buildDisplayMarkers(featureCollection) {
  assertFeatureCollection(featureCollection, 'display geography')

  return {
    type: 'FeatureCollection',
    features: featureCollection.features
      .filter((feature) => feature.properties?.displayMode === 'marker')
      .map((feature) => ({
        type: 'Feature',
        id: feature.id,
        properties: { ...feature.properties },
        geometry: {
          type: 'Point',
          coordinates: geometryBoundsCenter(feature.geometry),
        },
      })),
  }
}

export function buildCoverage(summaryRow) {
  if (!summaryRow) {
    throw new Error('Missing election coverage summary')
  }

  return {
    totalRows: numberValue(summaryRow.rows, 'rows'),
    totalActualVoters: numberValue(summaryRow.total_actual_voters, 'total_actual_voters'),
    mappedRows: numberValue(summaryRow.mapped_geographic_rows, 'mapped_geographic_rows'),
    mappedActualVoters: numberValue(
      summaryRow.mapped_geographic_actual_voters,
      'mapped_geographic_actual_voters',
    ),
    mappedActualVoterShare: numberValue(
      summaryRow.mapped_actual_voter_share,
      'mapped_actual_voter_share',
    ),
    pendingRows: numberValue(
      summaryRow.pending_or_missing_geocode_rows,
      'pending_or_missing_geocode_rows',
    ),
    pendingActualVoters: numberValue(
      summaryRow.pending_or_missing_geocode_actual_voters,
      'pending_or_missing_geocode_actual_voters',
    ),
    unmappedRows: numberValue(summaryRow.unmapped_rows, 'unmapped_rows'),
    unmappedActualVoters: numberValue(summaryRow.unmapped_actual_voters, 'unmapped_actual_voters'),
  }
}

export function buildResultPayload({
  electionId,
  mode,
  primaryRows,
  customRows,
  metadataById,
  customMetadataById,
  coverage,
  partyOverrides = {},
  excludedPartyColumns = [],
}) {
  const primaryType = mode === 'statistical-area' ? 'statistical-area' : 'locality'
  const records = []
  const excludedColumns = new Set(excludedPartyColumns)
  const partyIds = inferPartyColumns(primaryRows, customRows).filter(
    (partyId) => !excludedColumns.has(partyId),
  )

  for (const row of primaryRows) {
    const id = mode === 'statistical-area' ? row.stat_area_id : row.locality_id
    const metadata = metadataById.get(id)
    if (!id || !metadata) {
      throw new Error(`${electionId} ${mode} result has no matching metadata for ${id || '(blank ID)'}`)
    }
    records.push(buildResultRecord(row, id, primaryType, metadata, partyIds))
  }

  for (const row of customRows) {
    const id = row.custom_geography_id || row.geography_id
    const metadata = customMetadataById.get(id)
    if (!id || !metadata) {
      throw new Error(`${electionId} custom result has no matching geometry for ${id || '(blank ID)'}`)
    }
    records.push(buildResultRecord(row, id, 'custom', metadata, partyIds))
  }

  const duplicateIds = findDuplicateIds(records)
  if (duplicateIds.length > 0) {
    throw new Error(`${electionId} ${mode} results contain duplicate IDs: ${duplicateIds.join(', ')}`)
  }

  const parties = partyIds.map((partyId) => buildPartyDefinition(electionId, partyId, partyOverrides[partyId]))

  return {
    schemaVersion: 1,
    electionId,
    geographyMode: mode,
    coverage,
    parties,
    records,
  }
}

function buildResultRecord(row, id, geographyType, metadata, partyColumns) {
  const partyVotes = Object.fromEntries(
    partyColumns.map((partyId) => [partyId, numberValue(row[partyId], `${id}.${partyId}`)]),
  )
  const eligibleVoters = numberValue(row.eligible_voters, `${id}.eligible_voters`)
  const actualVoters = numberValue(row.actual_voters, `${id}.actual_voters`)
  const validVotes = numberValue(row.valid_votes, `${id}.valid_votes`)
  const partyVoteTotal = Object.values(partyVotes).reduce((sum, votes) => sum + votes, 0)
  if (partyVoteTotal !== validVotes) {
    throw new Error(
      `${id} party-vote total (${partyVoteTotal}) does not match valid_votes (${validVotes})`,
    )
  }
  const rankedParties = Object.entries(partyVotes).toSorted((left, right) => right[1] - left[1])
  const [winningPartyId = '', winningVotes = 0] = rankedParties[0] ?? []
  const runnerUpVotes = rankedParties[1]?.[1] ?? 0
  const statAreaNumber = cleanNumericCode(metadata.statAreaNumber)
  const names =
    geographyType === 'statistical-area'
      ? {
          he: `${metadata.nameHe} · אזור סטטיסטי ${statAreaNumber}`,
          en: `${metadata.nameEn} · Statistical area ${statAreaNumber}`,
        }
      : { he: metadata.nameHe, en: metadata.nameEn }

  return {
    id,
    geographyType,
    names,
    code:
      geographyType === 'statistical-area'
        ? metadata.yishuvStat2022 || id
        : metadata.localityCode || metadata.customKey || id,
    localityId: metadata.localityId || null,
    totals: {
      contributingRows: numberValue(row.contributing_rows, `${id}.contributing_rows`),
      contributingKalpis: numberValue(row.contributing_kalpis, `${id}.contributing_kalpis`),
      eligibleVoters,
      actualVoters,
      validVotes,
      invalidVotes: numberValue(row.invalid_votes, `${id}.invalid_votes`),
      turnout: eligibleVoters > 0 ? actualVoters / eligibleVoters : 0,
    },
    winner: {
      partyId: winningPartyId,
      votes: winningVotes,
      runnerUpVotes,
      marginVotes: winningVotes - runnerUpVotes,
      voteShare: validVotes > 0 ? winningVotes / validVotes : 0,
    },
    partyVotes,
  }
}

function inferPartyColumns(...rowGroups) {
  const partyIds = new Set()
  for (const rows of rowGroups) {
    const firstRow = rows[0]
    if (!firstRow) {
      continue
    }
    const columns = Object.keys(firstRow)
    const coreEnd = columns.indexOf(RESULT_CORE_LAST_COLUMN)
    if (coreEnd < 0) {
      throw new Error(`Results are missing required column ${RESULT_CORE_LAST_COLUMN}`)
    }
    for (const column of columns.slice(coreEnd + 1)) {
      if (column) {
        partyIds.add(column)
      }
    }
  }
  return [...partyIds]
}

function buildPartyDefinition(electionId, partyId, override = {}) {
  return {
    id: partyId,
    ballotLetter: partyId,
    names: {
      he: override.nameHe || partyId,
      en: override.nameEn || partyId,
    },
    color: override.color || stablePartyColor(electionId, partyId),
    colorStatus: override.color ? 'reviewed' : 'provisional',
  }
}

export function stablePartyColor(electionId, partyId) {
  let hash = 2166136261
  for (const character of `${electionId}:${partyId}`) {
    hash ^= character.codePointAt(0)
    hash = Math.imul(hash, 16777619)
  }
  const hue = Math.abs(hash) % 360
  return `hsl(${hue} ${DEFAULT_PARTY_SATURATION}% ${DEFAULT_PARTY_LIGHTNESS}%)`
}

function findDuplicateIds(records) {
  const seen = new Set()
  const duplicates = new Set()
  for (const record of records) {
    if (seen.has(record.id)) {
      duplicates.add(record.id)
    }
    seen.add(record.id)
  }
  return [...duplicates]
}

function geometryBoundsCenter(geometry) {
  const bounds = {
    minX: Number.POSITIVE_INFINITY,
    minY: Number.POSITIVE_INFINITY,
    maxX: Number.NEGATIVE_INFINITY,
    maxY: Number.NEGATIVE_INFINITY,
  }

  const visit = (coordinates) => {
    if (!Array.isArray(coordinates)) {
      return
    }
    if (
      coordinates.length >= 2 &&
      typeof coordinates[0] === 'number' &&
      typeof coordinates[1] === 'number'
    ) {
      bounds.minX = Math.min(bounds.minX, coordinates[0])
      bounds.minY = Math.min(bounds.minY, coordinates[1])
      bounds.maxX = Math.max(bounds.maxX, coordinates[0])
      bounds.maxY = Math.max(bounds.maxY, coordinates[1])
      return
    }
    for (const child of coordinates) {
      visit(child)
    }
  }

  visit(geometry?.coordinates)
  if (![bounds.minX, bounds.minY, bounds.maxX, bounds.maxY].every(Number.isFinite)) {
    throw new Error('Display marker geometry has no coordinates')
  }
  return [
    Number(((bounds.minX + bounds.maxX) / 2).toFixed(6)),
    Number(((bounds.minY + bounds.maxY) / 2).toFixed(6)),
  ]
}

function coordinatePositionCount(coordinates) {
  if (!Array.isArray(coordinates)) {
    return Number.POSITIVE_INFINITY
  }
  if (
    coordinates.length >= 2 &&
    typeof coordinates[0] === 'number' &&
    typeof coordinates[1] === 'number'
  ) {
    return 1
  }

  let count = 0
  for (const child of coordinates) {
    count += coordinatePositionCount(child)
    if (count > POINT_PROXY_MAX_VERTICES) {
      return count
    }
  }
  return count
}

function roundGeometry(geometry) {
  if (!geometry) {
    return geometry
  }
  if (geometry.type === 'GeometryCollection') {
    return { ...geometry, geometries: geometry.geometries.map(roundGeometry) }
  }
  return { ...geometry, coordinates: roundCoordinates(geometry.coordinates) }
}

function roundCoordinates(value) {
  if (!Array.isArray(value)) {
    return value
  }
  if (value.length > 0 && typeof value[0] === 'number') {
    return value.map((coordinate) => Number(coordinate.toFixed(6)))
  }
  return value.map(roundCoordinates)
}

function assertFeatureCollection(value, label) {
  if (!value || value.type !== 'FeatureCollection' || !Array.isArray(value.features)) {
    throw new Error(`${label} input is not a GeoJSON FeatureCollection`)
  }
}

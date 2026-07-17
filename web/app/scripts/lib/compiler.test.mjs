import { describe, expect, it } from 'vitest'
import {
  aliasJoinedCompositeResults,
  buildCompositeMetadataIndex,
  buildDisplayMarkers,
  buildHiddenLocalityIds,
  buildPartyRegistryIndex,
  buildResultPayload,
  isPointLikeGeometry,
  isPointProxyLocalityCode,
  isWestBankSettlementCode,
  parseCsv,
  pruneGeography,
  stablePartyColor,
} from './compiler.mjs'

const coverage = {
  totalRows: 1,
  totalActualVoters: 80,
  mappedRows: 1,
  mappedActualVoters: 80,
  mappedActualVoterShare: 1,
  pendingRows: 0,
  pendingActualVoters: 0,
  unmappedRows: 0,
  unmappedActualVoters: 0,
}

function registryFor(electionId, parties) {
  return buildPartyRegistryIndex(
    parties.map(({ sourceColumn, ballotLetter = sourceColumn, totalVotes, nameHe, nameEn = '' }) => ({
      election: electionId,
      source_column: sourceColumn,
      ballot_letter: ballotLetter,
      total_votes: String(totalVotes),
      list_name_he: nameHe,
      display_name_he: nameHe,
      display_name_en: nameEn,
      wikipedia_he_url: '',
      wikipedia_en_url: '',
    })),
  ).get(electionId)
}

describe('web data compiler', () => {
  it('parses UTF-8 BOM CSV headers', () => {
    expect(parseCsv('\ufeffid,name\n1,שלום\n')).toEqual([{ id: '1', name: 'שלום' }])
  })

  it('adds stable feature IDs and custom geometries', () => {
    const source = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            stat_area_id: 'stat2022:100001',
            locality_id: 'loc:10',
            locality_code: 3616,
            locality_name_he: 'תירוש',
            locality_name_en: 'TIROSH',
            stat_2022: 1,
          },
          geometry: {
            type: 'Polygon',
            coordinates: [[[35.3, 31.7], [35.4, 31.7], [35.4, 31.8], [35.3, 31.7]]],
          },
        },
      ],
    }
    const custom = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: { custom_id: 'custom:test', name_he: 'בדיקה', name_en: 'Test' },
          geometry: {
            type: 'Polygon',
            coordinates: [[[34.3, 31.3], [34.4, 31.3], [34.4, 31.4], [34.3, 31.3]]],
          },
        },
      ],
    }

    const output = pruneGeography(source, 'statistical-area', custom)
    expect(output.features.map((feature) => feature.id)).toEqual([
      'stat2022:100001',
      'custom:test',
    ])
    expect(output.features.map((feature) => feature.properties.displayMode)).toEqual([
      'marker',
      'marker',
    ])

    const markers = buildDisplayMarkers(output)
    expect(markers.features.map((feature) => feature.id)).toEqual([
      'stat2022:100001',
      'custom:test',
    ])
    expect(markers.features.map((feature) => feature.geometry)).toEqual([
      { type: 'Point', coordinates: [35.35, 31.75] },
      { type: 'Point', coordinates: [34.35, 31.35] },
    ])
  })

  it('limits fixed-size official markers to West Bank locality codes', () => {
    expect(isWestBankSettlementCode('3555')).toBe(true)
    expect(isWestBankSettlementCode(3825)).toBe(true)
    expect(isWestBankSettlementCode('3000')).toBe(false)
    expect(isWestBankSettlementCode('4000')).toBe(false)
    expect(isPointProxyLocalityCode('1791')).toBe(true)
    expect(isPointProxyLocalityCode('1794')).toBe(true)
    expect(isPointProxyLocalityCode('3488')).toBe(true)
    expect(isPointProxyLocalityCode('3000')).toBe(false)

    const pointProxyRing = Array.from({ length: 9 }, (_, index) => [index, index])
    const detailedRing = Array.from({ length: 14 }, (_, index) => [index, index])

    expect(
      isPointLikeGeometry({ type: 'Polygon', coordinates: [pointProxyRing] }),
    ).toBe(true)
    expect(
      isPointLikeGeometry({ type: 'Polygon', coordinates: [detailedRing] }),
    ).toBe(false)
  })

  it('keeps audited detailed West Bank display geometry polygonal', () => {
    const source = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            locality_id: 'loc:3605',
            locality_code: 3605,
            locality_name_he: '3605',
            locality_name_en: 'MASU\'A',
            display_geometry_source: 'arcgis_systematics_elections2019',
          },
          geometry: {
            type: 'Polygon',
            coordinates: [[[35, 32], [35.1, 32], [35.1, 32.1], [35, 32]]],
          },
        },
      ],
    }
    const empty = { type: 'FeatureCollection', features: [] }

    const output = pruneGeography(source, 'locality', empty)

    expect(output.features[0].properties.displayMode).toBe('polygon')
    expect(buildDisplayMarkers(output).features).toHaveLength(0)
  })

  it('adds reviewed composite localities and hides their components only in active elections', () => {
    const localities = {
      type: 'FeatureCollection',
      features: ['3720', '3778'].map((code) => ({
        type: 'Feature',
        properties: {
          locality_id: `loc:${code}`,
          locality_code: code,
          locality_name_he: code,
          locality_name_en: code,
        },
        geometry: {
          type: 'Polygon',
          coordinates: [[[35, 32], [35.1, 32], [35.1, 32.1], [35, 32]]],
        },
      })),
    }
    const composites = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {
            composite_locality_id: 'composite:test',
            elections: 'K17|K18',
            component_locality_codes: '3720|3778',
            component_locality_ids: 'loc:3720|loc:3778',
            name_he: 'בדיקה',
            name_en: 'Test composite',
            host_locality_code: '3720',
            included_locality_names_he: 'מצורף',
            included_locality_names_en: 'Included locality',
          },
          geometry: {
            type: 'MultiPolygon',
            coordinates: [
              [[[35, 32], [35.02, 32], [35.02, 32.02], [35, 32]]],
              [[[35.2, 32.2], [35.22, 32.2], [35.22, 32.22], [35.2, 32.2]]],
            ],
          },
        },
      ],
    }
    const empty = { type: 'FeatureCollection', features: [] }
    const output = pruneGeography(localities, 'locality', empty, composites)

    expect(output.features.map((feature) => feature.id)).toEqual([
      'loc:3720',
      'loc:3778',
      'composite:test',
    ])
    expect(buildHiddenLocalityIds(output, 'K17')).toEqual(['loc:3720', 'loc:3778'])
    expect(buildHiddenLocalityIds(output, 'K25')).toEqual(['composite:test'])
    expect(output.features.find((feature) => feature.id === 'composite:test')?.properties.displayMode).toBe(
      'marker',
    )
    expect(buildCompositeMetadataIndex(composites).get('composite:test')?.nameEn).toBe(
      'Test composite',
    )
    expect(buildCompositeMetadataIndex(composites).get('composite:test')).toMatchObject({
      localityCode: '3720',
      includedNames: { he: ['מצורף'], en: ['Included locality'] },
    })
    expect(buildDisplayMarkers(output).features.at(-1)?.geometry).toEqual({
      type: 'MultiPoint',
      coordinates: [
        [35.01, 32.01],
        [35.21, 32.21],
      ],
    })
  })

  it('aliases a host result to an active joined-register composite', () => {
    const geography = {
      type: 'FeatureCollection',
      features: [
        {
          id: 'composite:joined-k19-567',
          properties: {
            id: 'composite:joined-k19-567',
            isComposite: true,
            compositeKind: 'joined_polling_register',
            activeElections: ['K19'],
            hostLocalityId: 'loc:567',
            componentLocalityIds: ['loc:567', 'loc:493', 'loc:566'],
          },
          geometry: null,
        },
      ],
    }
    const rows = [
      { locality_id: 'loc:10' },
      { locality_id: 'loc:567' },
    ]

    expect(aliasJoinedCompositeResults(rows, geography, 'K19')).toEqual([
      { locality_id: 'loc:10' },
      { locality_id: 'composite:joined-k19-567' },
    ])
    expect(aliasJoinedCompositeResults(rows, geography, 'K20')).toEqual(rows)
    expect(() =>
      aliasJoinedCompositeResults([...rows, { locality_id: 'loc:493' }], geography, 'K19'),
    ).toThrow(/would hide standalone result loc:493/)
  })

  it('compiles dynamic ballot-letter columns into typed records', () => {
    const row = {
      election: 'K25',
      locality_id: 'loc:10',
      contributing_rows: '1',
      contributing_kalpis: '1',
      eligible_voters: '100',
      actual_voters: '80',
      valid_votes: '79',
      invalid_votes: '1',
      winning_ballot_letter: 'אמת',
      winning_votes: '50',
      runner_up_votes: '29',
      margin_votes: '21',
      winning_vote_share: '0.632911',
      אמת: '50',
      מחל: '29',
    }
    const metadata = new Map([
      [
        'loc:10',
        {
          id: 'loc:10',
          localityId: 'loc:10',
          localityCode: '10',
          nameHe: 'תירוש',
          nameEn: 'TIROSH',
          statAreaNumber: '',
          yishuvStat2022: '',
        },
      ],
    ])
    const payload = buildResultPayload({
      electionId: 'K25',
      mode: 'locality',
      primaryRows: [row],
      customRows: [],
      metadataById: metadata,
      customMetadataById: new Map(),
      coverage,
      partyColorsByBallotLetter: { אמת: '#C62828', מחל: '#2455A4' },
      partyOverrides: { מחל: { color: '#123456' } },
      partyRegistry: registryFor('K25', [
        { sourceColumn: 'אמת', totalVotes: 100, nameHe: 'העבודה', nameEn: 'Labor' },
        { sourceColumn: 'מחל', totalVotes: 58, nameHe: 'הליכוד', nameEn: 'Likud' },
      ]),
      envelopeRows: [
        {
          election: row.election,
          envelope_id: 'envelope:official',
          envelope_name_he: 'מעטפות חיצוניות',
          envelope_name_en: 'Envelope votes',
          contributing_rows: row.contributing_rows,
          contributing_kalpis: row.contributing_kalpis,
          eligible_voters: row.eligible_voters,
          actual_voters: row.actual_voters,
          valid_votes: row.valid_votes,
          invalid_votes: row.invalid_votes,
          winning_ballot_letter: row.winning_ballot_letter,
          winning_votes: row.winning_votes,
          runner_up_votes: row.runner_up_votes,
          margin_votes: row.margin_votes,
          winning_vote_share: row.winning_vote_share,
          אמת: row.אמת,
          מחל: row.מחל,
        },
      ],
    })

    expect(payload.records[0].partyVotes).toEqual({ אמת: 50, מחל: 29 })
    expect(payload.records[0].totals.turnout).toBe(0.8)
    expect(payload.parties).toHaveLength(2)
    expect(payload.parties[0].names).toEqual({ he: 'העבודה', en: 'Labor' })
    expect(payload.parties.find((party) => party.id === 'אמת')).toMatchObject({
      color: '#C62828',
      colorStatus: 'reviewed',
    })
    expect(payload.parties.find((party) => party.id === 'מחל')).toMatchObject({
      color: '#123456',
      colorStatus: 'reviewed',
    })
    expect(payload.envelope?.geographyType).toBe('envelope')
  })

  it('keeps fallback party colors deterministic by ballot letter', () => {
    expect(stablePartyColor('אמת')).toBe(stablePartyColor('אמת'))
    expect(stablePartyColor('אמת')).not.toBe(stablePartyColor('מחל'))
  })

  it('excludes declared source metadata and recomputes the winner', () => {
    const row = {
      election: 'K18',
      locality_id: 'loc:921',
      contributing_rows: '1',
      contributing_kalpis: '1',
      eligible_voters: '137',
      actual_voters: '5',
      valid_votes: '4',
      invalid_votes: '1',
      winning_ballot_letter: 'ת. עדכון',
      winning_votes: '12',
      runner_up_votes: '1',
      margin_votes: '11',
      winning_vote_share: '3',
      אמת: '1',
      מחל: '3',
      פח: '0',
      'ת. עדכון': '12',
    }
    const metadata = new Map([
      [
        'loc:921',
        {
          id: 'loc:921',
          localityId: 'loc:921',
          localityCode: '921',
          nameHe: 'שער מנשה',
          nameEn: "SHA'AR MENASHE",
          statAreaNumber: '',
          yishuvStat2022: '',
        },
      ],
    ])
    const payload = buildResultPayload({
      electionId: 'K18',
      mode: 'locality',
      primaryRows: [row],
      customRows: [],
      metadataById: metadata,
      customMetadataById: new Map(),
      coverage,
      partyRegistry: registryFor('K18', [
        { sourceColumn: 'אמת', totalVotes: 1, nameHe: 'העבודה' },
        { sourceColumn: 'מחל', totalVotes: 3, nameHe: 'הליכוד' },
        { sourceColumn: 'פח', totalVotes: 0, nameHe: 'מהפך בחינוך' },
      ]),
      excludedPartyColumns: ['פח', 'ת. עדכון'],
      validatePartyTotals: true,
    })

    expect(payload.records[0].winner).toEqual({
      partyId: 'מחל',
      votes: 3,
      runnerUpVotes: 1,
      marginVotes: 2,
      voteShare: 0.75,
    })
    expect(payload.parties.map((party) => party.id)).not.toContain('ת. עדכון')
    expect(payload.parties.map((party) => party.id)).not.toContain('פח')
  })

  it('keeps source columns distinct from corrected official ballot letters', () => {
    const registry = registryFor('K19', [
      {
        sourceColumn: 'מרץ',
        ballotLetter: 'מרצ',
        totalVotes: 172403,
        nameHe: 'מרצ',
        nameEn: 'Meretz',
      },
    ])

    expect(registry.get('מרץ')).toMatchObject({
      sourceColumn: 'מרץ',
      ballotLetter: 'מרצ',
      displayNameHe: 'מרצ',
    })
  })
})

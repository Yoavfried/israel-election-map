import { describe, expect, it } from 'vitest'
import {
  buildDisplayMarkers,
  buildResultPayload,
  isPointLikeGeometry,
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

    const pointProxyRing = Array.from({ length: 9 }, (_, index) => [index, index])
    const detailedRing = Array.from({ length: 14 }, (_, index) => [index, index])

    expect(
      isPointLikeGeometry({ type: 'Polygon', coordinates: [pointProxyRing] }),
    ).toBe(true)
    expect(
      isPointLikeGeometry({ type: 'Polygon', coordinates: [detailedRing] }),
    ).toBe(false)
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
    })

    expect(payload.records[0].partyVotes).toEqual({ אמת: 50, מחל: 29 })
    expect(payload.records[0].totals.turnout).toBe(0.8)
    expect(payload.parties).toHaveLength(2)
  })

  it('keeps fallback party colors deterministic', () => {
    expect(stablePartyColor('K25', 'אמת')).toBe(stablePartyColor('K25', 'אמת'))
    expect(stablePartyColor('K24', 'אמת')).not.toBe(stablePartyColor('K25', 'אמת'))
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
      excludedPartyColumns: ['ת. עדכון'],
    })

    expect(payload.records[0].winner).toEqual({
      partyId: 'מחל',
      votes: 3,
      runnerUpVotes: 1,
      marginVotes: 2,
      voteShare: 0.75,
    })
    expect(payload.parties.map((party) => party.id)).not.toContain('ת. עדכון')
  })
})

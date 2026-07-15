import { describe, expect, it } from 'vitest'
import { buildMarkerVisibilityFilter, mayHaveDisplayMarker } from './mapPresentation'
import type { ResultRecord } from './schemas'

describe('map presentation rules', () => {
  it('recognizes records eligible for custom and West Bank marker proxies', () => {
    expect(mayHaveDisplayMarker(record('custom:gaza', 'custom', null, 'GAZA'))).toBe(true)
    expect(mayHaveDisplayMarker(record('loc:3616', 'locality', 'loc:3616', '3616'))).toBe(true)
    expect(
      mayHaveDisplayMarker(record('stat2022:36160001', 'statistical-area', 'loc:3616', '36160001')),
    ).toBe(true)
    expect(mayHaveDisplayMarker(record('loc:3000', 'locality', 'loc:3000', '3000'))).toBe(false)
  })

  it('includes custom markers only when that election has a result record', () => {
    const filter = buildMarkerVisibilityFilter([
      record('custom:hebron', 'custom', null, 'HEBRON'),
      record('loc:3616', 'locality', 'loc:3616', '3616'),
    ])

    expect(filter).toEqual([
      'any',
      ['!=', ['get', 'geographyType'], 'custom'],
      ['in', ['get', 'id'], ['literal', ['custom:hebron']]],
    ])
  })
})

function record(
  id: string,
  geographyType: ResultRecord['geographyType'],
  localityId: string | null,
  code: string,
): ResultRecord {
  return {
    id,
    geographyType,
    names: { en: id, he: id },
    code,
    localityId,
    totals: {
      contributingRows: 1,
      contributingKalpis: 1,
      eligibleVoters: 1,
      actualVoters: 1,
      validVotes: 1,
      invalidVotes: 0,
      turnout: 1,
    },
    winner: {
      partyId: 'party',
      votes: 1,
      runnerUpVotes: 0,
      marginVotes: 1,
      voteShare: 1,
    },
    partyVotes: { party: 1 },
  }
}

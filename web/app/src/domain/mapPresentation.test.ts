import { describe, expect, it } from 'vitest'
import {
  buildMarkerVisibilityFilter,
  buildPolygonVisibilityFilter,
  mayHaveDisplayMarker,
} from './mapPresentation'
import type { ResultRecord } from './schemas'

describe('map presentation rules', () => {
  it('recognizes records eligible for custom and West Bank marker proxies', () => {
    expect(mayHaveDisplayMarker(record('custom:gaza', 'custom', null, 'GAZA'))).toBe(true)
    expect(mayHaveDisplayMarker(record('loc:3616', 'locality', 'loc:3616', '3616'))).toBe(true)
    expect(
      mayHaveDisplayMarker(record('stat2022:36160001', 'statistical-area', 'loc:3616', '36160001')),
    ).toBe(true)
    expect(mayHaveDisplayMarker(record('loc:1791', 'locality', 'loc:1791', '1791'))).toBe(true)
    expect(mayHaveDisplayMarker(record('loc:3488', 'locality', 'loc:3488', '3488'))).toBe(true)
    expect(mayHaveDisplayMarker(record('loc:3000', 'locality', 'loc:3000', '3000'))).toBe(false)
  })

  it('includes custom markers only with data and excludes election-hidden markers', () => {
    const filter = buildMarkerVisibilityFilter(
      [
        record('custom:hebron', 'custom', null, 'HEBRON'),
        record('loc:3616', 'locality', 'loc:3616', '3616'),
      ],
      ['loc:3778', 'loc:3720'],
    )

    expect(filter).toEqual([
      'all',
      ['!', ['in', ['get', 'id'], ['literal', ['loc:3720', 'loc:3778']]]],
      [
        'any',
        ['!=', ['get', 'geographyType'], 'custom'],
        ['in', ['get', 'id'], ['literal', ['custom:hebron']]],
      ],
    ])
  })

  it('keeps Kinneret and election-hidden locality polygons out of the fill layer', () => {
    expect(buildPolygonVisibilityFilter(['loc:628', 'loc:9920'])).toEqual([
      'all',
      ['!=', ['get', 'displayMode'], 'marker'],
      ['!=', ['get', 'localityCode'], '9920'],
      ['!', ['in', ['get', 'id'], ['literal', ['loc:628', 'loc:9920']]]],
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

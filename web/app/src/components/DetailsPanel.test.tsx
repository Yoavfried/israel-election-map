import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import type { Party, ResultRecord } from '../domain/schemas'
import { DetailsPanel } from './DetailsPanel'

const parties: Party[] = Array.from({ length: 10 }, (_, index) => {
  const number = index + 1
  return {
    id: `P${number}`,
    ballotLetter: `P${number}`,
    names: { en: `List ${number}`, he: `רשימה ${number}` },
    listNameHe: `רשימה ${number}`,
    wikipedia: { en: null, he: null },
    color: '#336655',
    colorStatus: 'provisional',
  }
})

const record: ResultRecord = {
  id: 'loc:10',
  geographyType: 'locality',
  names: { en: 'Test locality', he: 'יישוב בדיקה' },
  code: '10',
  localityId: 'loc:10',
  totals: {
    contributingRows: 1,
    contributingKalpis: 1,
    eligibleVoters: 100,
    actualVoters: 90,
    validVotes: 45,
    invalidVotes: 0,
    turnout: 0.9,
  },
  winner: {
    partyId: 'P1',
    votes: 9,
    runnerUpVotes: 8,
    marginVotes: 1,
    voteShare: 0.2,
  },
  partyVotes: Object.fromEntries(
    parties.map((party, index) => [party.id, Math.max(9 - index, 0)]),
  ),
}

describe('DetailsPanel', () => {
  it('renders the complete party result, including rows after eight and zero votes', () => {
    const html = renderToStaticMarkup(
      <DetailsPanel language="en" record={record} parties={parties} />,
    )

    expect(html.match(/<li/g)).toHaveLength(10)
    expect(html.match(/<dt>/g)).toHaveLength(3)
    expect(html).toContain('List 10')
    expect(html).toContain('<span class="party-votes">0</span>')
    expect(html).not.toContain('<dt>Lead</dt>')
  })
})

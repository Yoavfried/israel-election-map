import { describe, expect, it } from 'vitest'
import { AppCatalogSchema, ElectionResultsSchema } from './schemas'

const coverage = {
  totalRows: 100,
  totalActualVoters: 10_000,
  mappedRows: 80,
  mappedActualVoters: 8_000,
  mappedActualVoterShare: 0.8,
  pendingRows: 20,
  pendingActualVoters: 2_000,
  unmappedRows: 20,
  unmappedActualVoters: 2_000,
}

describe('web data contracts', () => {
  it('accepts a versioned catalog', () => {
    const catalog = AppCatalogSchema.parse({
      schemaVersion: 1,
      buildId: '12345678abcdef00',
      generatedAt: '2026-07-14T10:00:00.000Z',
      source: {
        geographyVintage: 2022,
        electionRange: { first: 'K17', last: 'K25' },
        assignmentStatus: 'partial',
        resultColumnExclusions: [],
      },
      bounds: [
        [34.2, 29.4],
        [35.9, 33.4],
      ],
      partyColorPolicy: { status: 'provisional', description: 'Pending review' },
      geographyModes: [
        {
          id: 'statistical-area',
          label: { en: 'Statistical areas', he: 'אזורים סטטיסטיים' },
          geometryUrl: 'geographies/statistical-areas.geojson',
          markerGeometryUrl: 'geographies/statistical-area-markers.geojson',
          featureCount: 3_857,
          markerFeatureCount: 100,
        },
        {
          id: 'locality',
          label: { en: 'Localities', he: 'יישובים' },
          geometryUrl: 'geographies/localities.geojson',
          markerGeometryUrl: 'geographies/locality-markers.geojson',
          featureCount: 1_329,
          markerFeatureCount: 100,
        },
      ],
      elections: [
        {
          id: 'K25',
          number: 25,
          dateLabel: '2022',
          label: { en: 'Knesset 25', he: 'הכנסת ה־25' },
          coverage,
          resultUrls: {
            'statistical-area': 'results/k25/statistical-areas.json',
            locality: 'results/k25/localities.json',
          },
        },
      ],
      assets: [{ path: 'result.json', bytes: 12, sha256: 'a'.repeat(64) }],
    })

    expect(catalog.elections[0].id).toBe('K25')
  })

  it('rejects coverage values above 100 percent', () => {
    const result = ElectionResultsSchema.safeParse({
      schemaVersion: 1,
      electionId: 'K25',
      geographyMode: 'locality',
      coverage: { ...coverage, mappedActualVoterShare: 1.01 },
      parties: [],
      records: [],
    })

    expect(result.success).toBe(false)
  })
})

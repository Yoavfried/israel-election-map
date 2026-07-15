import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { ControlPanel } from './ControlPanel'

describe('ControlPanel', () => {
  it('renders localized election and geography options', () => {
    const coverage = {
      totalRows: 1,
      totalActualVoters: 1,
      mappedRows: 1,
      mappedActualVoters: 1,
      mappedActualVoterShare: 1,
      pendingRows: 0,
      pendingActualVoters: 0,
      unmappedRows: 0,
      unmappedActualVoters: 0,
    }
    const html = renderToStaticMarkup(
      <ControlPanel
        language="he"
        elections={[
          {
            id: 'K25',
            number: 25,
            dateLabel: '2022',
            label: { en: 'Knesset 25', he: 'הכנסת ה־25' },
            coverageByMode: {
              'statistical-area': coverage,
              locality: coverage,
            },
            resultUrls: { 'statistical-area': 'stat.json', locality: 'locality.json' },
          },
        ]}
        geographyModes={[
          {
            id: 'statistical-area',
            label: { en: 'Statistical areas', he: 'אזורים סטטיסטיים' },
            geometryUrl: 'stat.geojson',
            markerGeometryUrl: 'stat-markers.geojson',
            featureCount: 1,
            markerFeatureCount: 1,
          },
          {
            id: 'locality',
            label: { en: 'Localities', he: 'יישובים' },
            geometryUrl: 'localities.geojson',
            markerGeometryUrl: 'locality-markers.geojson',
            featureCount: 1,
            markerFeatureCount: 1,
          },
        ]}
        electionId="K25"
        geographyMode="statistical-area"
        onElectionChange={() => undefined}
        onGeographyModeChange={() => undefined}
      />,
    )

    expect(html).toContain('הכנסת ה־25')
    expect(html).toContain('אזורים סטטיסטיים')
    expect(html).toContain('יישובים')
  })
})

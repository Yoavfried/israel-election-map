import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { AppCatalogSchema, ElectionResultsSchema } from './schemas'

const dataRoot = resolve(import.meta.dirname, '..', '..', 'public', 'data', 'v2')

describe('generated web data', () => {
  it('matches the runtime schemas and asset checksums', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))

    await Promise.all(
      catalog.assets.map(async (asset) => {
        const bytes = await readFile(resolve(dataRoot, asset.path))
        expect(bytes.byteLength, asset.path).toBe(asset.bytes)
        expect(createHash('sha256').update(bytes).digest('hex'), asset.path).toBe(asset.sha256)
      }),
    )

    expect(catalog.elections).toHaveLength(9)
    expect(catalog.buildId).toHaveLength(16)
  })

  it('joins every result record to a stable feature ID', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))

    for (const mode of catalog.geographyModes) {
      await readAndValidateGeography(mode)
    }

    for (const election of catalog.elections) {
      for (const mode of catalog.geographyModes) {
        const geography = election.geographiesByMode[mode.id]
        const geometryIds = await readAndValidateGeography(geography)
        const payload = ElectionResultsSchema.parse(
          await readJson(resolve(dataRoot, election.resultUrls[mode.id])),
        )
        expect(payload.electionId).toBe(election.id)
        expect(payload.geographyMode).toBe(mode.id)
        if (mode.id === 'statistical-area') {
          expect(geography.vintage).toBe(election.statisticalAreaVintage)
        }
        expect(payload.envelope?.geographyType).toBe('envelope')
        expect(new Set(payload.records.map((record) => record.id)).size).toBe(payload.records.length)
        for (const record of payload.records) {
          expect(geometryIds.has(record.id), `${election.id}/${mode.id}/${record.id}`).toBe(true)
        }
        for (const hiddenId of payload.hiddenGeographyIds) {
          expect(geometryIds.has(hiddenId), `${election.id}/${mode.id}/${hiddenId}`).toBe(true)
          expect(payload.records.some((record) => record.id === hiddenId)).toBe(false)
        }
        if (mode.id === 'locality') {
          expect(payload.coverage.mappedActualVoterShare).toBe(1)
          expect(payload.coverage.pendingRows).toBe(0)
        }
      }
    }
  })

  it('keeps Maale Adumim historical election areas separate', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const cases = [
      { electionId: 'K18', vintage: 2008, ballotCounts: [null, 4, 2] },
      { electionId: 'K20', vintage: 2011, ballotCounts: [1, 4, 6] },
    ]

    for (const testCase of cases) {
      const election = catalog.elections.find((entry) => entry.id === testCase.electionId)
      if (!election) {
        throw new Error(`Missing ${testCase.electionId} catalog entry`)
      }
      const geography = (await readJson(
        resolve(dataRoot, election.geographiesByMode['statistical-area'].geometryUrl),
      )) as { features: Array<{ id?: string }> }
      const payload = ElectionResultsSchema.parse(
        await readJson(resolve(dataRoot, election.resultUrls['statistical-area'])),
      )
      const geometryIds = new Set(geography.features.map((feature) => feature.id))
      const recordsById = new Map(payload.records.map((record) => [record.id, record]))

      for (const [index, expectedBallots] of testCase.ballotCounts.entries()) {
        const areaNumber = index + 1
        const id = `stat${testCase.vintage}:3616000${areaNumber}`
        expect(geometryIds.has(id), `${testCase.electionId}/${id}`).toBe(true)
        if (expectedBallots !== null) {
          expect(recordsById.get(id)?.totals.contributingKalpis, id).toBe(expectedBallots)
        }
      }
    }
  })

  it('retains neutral Israeli land footprints in locality geometry', async () => {
    const geometry = (await readJson(
      resolve(dataRoot, 'geographies', 'localities.geojson'),
    )) as {
      features: Array<{
        id?: string
        properties?: { displayMode?: string; nameEn?: string }
      }>
    }
    const featuresById = new Map(geometry.features.map((feature) => [feature.id, feature]))

    for (const id of ['loc:9971', 'loc:9936', 'loc:5568', 'loc:5569', 'loc:9920']) {
      const feature = featuresById.get(id)
      expect(feature, id).toBeDefined()
      expect(feature?.properties?.displayMode, id).toBe('polygon')
      expect(feature?.properties?.nameEn, id).not.toBe('nan')
    }
  })

  it('ships one lightweight land backdrop for statistical-area maps', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const backdropUrls = new Set(
      catalog.elections.map(
        (election) => election.geographiesByMode['statistical-area'].backdropGeometryUrl,
      ),
    )

    expect(backdropUrls.size).toBe(1)
    const backdropUrl = [...backdropUrls][0]
    expect(backdropUrl).toBe('geographies/statistical-area-backdrop.geojson')
    if (!backdropUrl) {
      throw new Error('Missing statistical-area backdrop URL')
    }
    expect(catalog.assets.some((asset) => asset.path === backdropUrl)).toBe(true)

    const backdrop = (await readJson(resolve(dataRoot, backdropUrl))) as {
      features: Array<{
        id?: string
        geometry?: { type?: string; coordinates?: unknown[] }
      }>
    }
    expect(backdrop.features).toHaveLength(1)
    expect(backdrop.features[0].geometry?.type).toMatch(/^(Multi)?Polygon$/)
    expect(backdrop.features[0].geometry?.coordinates?.length).toBeGreaterThan(0)
  })

  it('uses detailed West Bank footprints while preserving reviewed proxy markers', async () => {
    const geometry = (await readJson(
      resolve(dataRoot, 'geographies', 'localities.geojson'),
    )) as {
      features: Array<{
        id?: string
        properties?: { displayMode?: string }
        geometry?: { type?: string }
      }>
    }
    const markers = (await readJson(
      resolve(dataRoot, 'geographies', 'locality-markers.geojson'),
    )) as {
      features: Array<{ id?: string; geometry?: { type?: string; coordinates?: unknown[] } }>
    }
    const featuresById = new Map(geometry.features.map((feature) => [feature.id, feature]))
    const markersById = new Map(markers.features.map((feature) => [feature.id, feature]))

    for (const id of [
      'loc:3488',
      'loc:3570',
      'loc:3605',
      'loc:3607',
      'loc:3649',
      'loc:3654',
      'loc:3784',
      'loc:3824',
      'composite:shaar-shomron',
    ]) {
      expect(featuresById.get(id)?.properties?.displayMode, id).toBe('polygon')
      expect(markersById.has(id), id).toBe(false)
    }

    for (const id of ['loc:3782', 'loc:3785', 'loc:3786', 'loc:3825', 'loc:1794']) {
      expect(featuresById.get(id)?.properties?.displayMode, id).toBe('marker')
      expect(markersById.get(id)?.geometry?.type, id).toBe('Point')
    }

    const yitavJoin = markersById.get('composite:joined-k25-3607')
    expect(yitavJoin?.geometry?.type).toBe('MultiPoint')
    expect(yitavJoin?.geometry?.coordinates).toHaveLength(2)
  })

  it('uses one combined tribal marker and shows only result-bearing statistical markers', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const tribalAreaIds = [
      'stat2011:9390001',
      'stat2011:9560001',
      'stat2011:9570001',
      'stat2011:9580001',
      'stat2011:9600001',
      'stat2011:9610001',
      'stat2011:9630001',
      'stat2011:9640001',
      'stat2011:9650001',
      'stat2011:9660001',
      'stat2011:9670001',
      'stat2011:9680001',
      'stat2011:9690001',
      'stat2011:9700001',
      'stat2011:9720001',
      'stat2011:9760001',
      'stat2011:9860001',
      'stat2011:10410001',
      'stat2011:11690001',
      'stat2011:11700001',
      'stat2011:12340001',
    ]
    const evacuatedGazaAreaIds = [
      'stat1995:5405001',
      'stat1995:5407001',
      'stat1995:5408001',
      'stat1995:5410001',
      'stat1995:5423001',
      'stat1995:5424001',
      'stat1995:5425001',
      'stat1995:5426001',
      'stat1995:5427001',
      'stat1995:5428001',
      'stat1995:5429001',
      'stat1995:5431001',
      'stat1995:5432001',
      'stat1995:5433001',
      'stat1995:5434001',
      'stat1995:5435001',
    ]
    const expectedActiveMarkers: Record<string, string[]> = {
      K17: ['custom:tribal_negev'],
      K18: ['custom:tribal_negev'],
      K19: ['custom:tribal_negev'],
      K20: ['custom:tribal_negev'],
      K21: ['custom:tribal_negev'],
      K22: ['custom:tribal_negev', 'stat2011:37850001'],
      K23: ['custom:tribal_negev', 'stat2011:37850001'],
      K24: ['custom:tribal_negev', 'stat2011:37820001', 'stat2011:37850001'],
      K25: ['custom:tribal_negev', 'stat2011:37820001', 'stat2011:37850001'],
    }

    for (const election of catalog.elections) {
      const asset = election.geographiesByMode['statistical-area']
      const geometry = (await readJson(resolve(dataRoot, asset.geometryUrl))) as {
        features: Array<{
          id?: string
          properties?: { displayMode?: string }
        }>
      }
      const markers = (await readJson(resolve(dataRoot, asset.markerGeometryUrl))) as {
        features: Array<{ id?: string }>
      }
      const payload = ElectionResultsSchema.parse(
        await readJson(resolve(dataRoot, election.resultUrls['statistical-area'])),
      )
      const featuresById = new Map(geometry.features.map((feature) => [feature.id, feature]))
      const markerIds = new Set(markers.features.map((feature) => feature.id))
      const resultIds = new Set(payload.records.map((record) => record.id))
      const activeMarkerIds = [...markerIds]
        .filter((id): id is string => Boolean(id))
        .filter((id) => resultIds.has(id) && !payload.hiddenGeographyIds.includes(id))
        .toSorted()

      expect(activeMarkerIds, election.id).toEqual(expectedActiveMarkers[election.id])
      expect(featuresById.get('custom:hebron')?.properties?.displayMode, election.id).toBe(
        'polygon',
      )
      expect(markerIds.has('custom:hebron'), election.id).toBe(false)
      expect(featuresById.get('custom:tribal_negev')?.properties?.displayMode, election.id).toBe(
        'marker',
      )
      expect(markerIds.has('custom:tribal_negev'), election.id).toBe(true)
      expect(resultIds.has('custom:tribal_negev'), election.id).toBe(true)

      if (Number(election.id.slice(1)) <= 18) {
        expect(resultIds.has('custom:hebron'), election.id).toBe(true)
      } else {
        expect(resultIds.has('custom:hebron'), election.id).toBe(false)
        expect(featuresById.get('stat2011:38230001')?.properties?.displayMode).toBe('polygon')
        expect(markerIds.has('stat2011:38230001'), election.id).toBe(false)
        for (const id of tribalAreaIds) {
          expect(featuresById.get(id)?.properties?.displayMode, `${election.id}/${id}`).toBe('marker')
          expect(markerIds.has(id), `${election.id}/${id}`).toBe(true)
          expect(resultIds.has(id), `${election.id}/${id}`).toBe(false)
          expect(payload.hiddenGeographyIds, `${election.id}/${id}`).toContain(id)
        }
      }
      if (election.id === 'K17') {
        for (const id of evacuatedGazaAreaIds) {
          expect(payload.hiddenGeographyIds, id).toContain(id)
          expect(resultIds.has(id), id).toBe(false)
        }
      }
    }
  })

  it('renders K17 Yehud area 8 on the reviewed historical component polygon', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const election = catalog.elections.find((candidate) => candidate.id === 'K17')
    if (!election) {
      throw new Error('Missing K17 catalog entry')
    }
    const geometry = (await readJson(
      resolve(dataRoot, 'geographies', 'statistical-areas-1995.geojson'),
    )) as {
      features: Array<{
        id?: string
        properties?: { displayMode?: string }
        geometry?: { type?: string; coordinates?: unknown }
      }>
    }
    const markers = (await readJson(
      resolve(dataRoot, 'geographies', 'statistical-area-markers-1995.geojson'),
    )) as {
      features: Array<{ id?: string }>
    }
    const payload = ElectionResultsSchema.parse(
      await readJson(resolve(dataRoot, election.resultUrls['statistical-area'])),
    )
    const component = geometry.features.find((feature) => feature.id === 'stat1995:1062001')
    const target = geometry.features.find((feature) => feature.id === 'stat1995:9400008')
    const markerIds = new Set(markers.features.map((feature) => feature.id))
    const result = payload.records.find((record) => record.id === 'stat1995:9400008')

    expect(target?.properties?.displayMode).toBe('polygon')
    expect(target?.geometry?.type).toMatch(/Polygon/)
    expect(target?.geometry).toEqual(component?.geometry)
    expect(component?.properties?.displayMode).toBe('marker')
    expect(markerIds.has('stat1995:9400008')).toBe(false)
    expect(markerIds.has('stat1995:1062001')).toBe(true)
    expect(payload.hiddenGeographyIds).toContain('stat1995:1062001')
    expect(result?.names.he).toBe('יהוד · אזור סטטיסטי 8')
    expect(result?.names.en).toBe('Yehud · Statistical area 8')
  })

  it('applies reviewed election-specific locality display rules', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const geometry = (await readJson(
      resolve(dataRoot, 'geographies', 'localities.geojson'),
    )) as {
      features: Array<{
        id?: string
        properties?: { nameHe?: string }
      }>
    }
    const featuresById = new Map(geometry.features.map((feature) => [feature.id, feature]))

    expect(featuresById.get('loc:3620')?.properties?.nameHe).toBe('נערן')
    expect(featuresById.has('loc:3786')).toBe(true)
    expect(featuresById.has('loc:3825')).toBe(true)

    for (const election of catalog.elections) {
      const payload = ElectionResultsSchema.parse(
        await readJson(resolve(dataRoot, election.resultUrls.locality)),
      )
      expect(payload.hiddenGeographyIds, election.id).toContain('loc:3786')
      expect(payload.hiddenGeographyIds, election.id).toContain('loc:3825')

      const naranRecord = payload.records.find((record) => record.id === 'loc:3620')
      if (Number(election.id.slice(1)) <= 21) {
        expect(naranRecord?.names, election.id).toEqual({ he: 'נירן', en: 'NIRAN' })
      } else {
        expect(naranRecord, election.id).toBeUndefined()
      }
    }
  })

  it('shows reviewed joined-register unions only in their evidence elections', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const payloads = new Map(
      await Promise.all(
        catalog.elections.map(async (election) => [
          election.id,
          ElectionResultsSchema.parse(
            await readJson(resolve(dataRoot, election.resultUrls.locality)),
          ),
        ] as const),
      ),
    )

    for (const electionId of ['K19', 'K20', 'K25']) {
      const payload = payloads.get(electionId)
      const compositeId = `composite:joined-${electionId.toLowerCase()}-567`
      expect(payload?.records.find((record) => record.id === compositeId)).toMatchObject({
        names: { he: 'צרעה', en: "ZOR'A" },
        includedNames: {
          he: ['דייר ראפאת', 'גבעת שמש'],
          en: ['DEIR RAFAT', "GIV'AT SHEMESH"],
        },
        code: '567',
      })
      for (const componentId of ['loc:567', 'loc:493', 'loc:566']) {
        expect(payload?.hiddenGeographyIds, `${electionId}/${componentId}`).toContain(componentId)
      }
    }

    const k21 = payloads.get('K21')
    expect(k21?.records.some((record) => record.id.startsWith('composite:joined-'))).toBe(false)
    expect(k21?.records.some((record) => record.id === 'loc:567')).toBe(true)
  })

  it('keeps Ganne Modiin inside Modiin Illit through K20', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))

    for (const election of catalog.elections) {
      const localityPayload = ElectionResultsSchema.parse(
        await readJson(resolve(dataRoot, election.resultUrls.locality)),
      )
      const statisticalPayload = ElectionResultsSchema.parse(
        await readJson(resolve(dataRoot, election.resultUrls['statistical-area'])),
      )
      const historicalElection = Number(election.id.slice(1)) <= 20
      const compositeId = `composite:joined-${election.id.toLowerCase()}-3797`

      if (historicalElection) {
        expect(localityPayload.records.find((record) => record.id === compositeId)).toMatchObject({
          code: '3797',
          includedNames: { he: ['גני מודיעין'], en: ["GANNE MODI'IN"] },
        })
        expect(localityPayload.hiddenGeographyIds).toContain('loc:3797')
        expect(localityPayload.hiddenGeographyIds).toContain('loc:3823')
      } else {
        expect(localityPayload.records.some((record) => record.id === compositeId)).toBe(false)
      }

      if (election.id === 'K19' || election.id === 'K20') {
        expect(statisticalPayload.hiddenGeographyIds).toContain('stat2011:38230001')
      } else {
        expect(statisticalPayload.hiddenGeographyIds).not.toContain('stat2011:38230001')
      }
    }
  })

  it('keeps reviewed party colors scoped away from reused ballot letters', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const payloads = new Map(
      await Promise.all(
        catalog.elections.map(async (election) => [
          election.id,
          ElectionResultsSchema.parse(
            await readJson(resolve(dataRoot, election.resultUrls.locality)),
          ),
        ] as const),
      ),
    )
    const party = (electionId: string, ballotLetter: string) =>
      payloads.get(electionId)?.parties.find((candidate) => candidate.ballotLetter === ballotLetter)

    expect(party('K17', 'טב')).toMatchObject({ color: '#F4A261', colorStatus: 'reviewed' })
    expect(party('K17', 'זך')).toMatchObject({ color: '#8BC34A', colorStatus: 'reviewed' })
    expect(party('K17', 'עם')).toMatchObject({ color: '#20A4A8', colorStatus: 'reviewed' })
    expect(party('K17', 'קנ')).toMatchObject({ color: '#00A651', colorStatus: 'reviewed' })
    expect(party('K17', 'רק')).toMatchObject({ color: '#00A651', colorStatus: 'reviewed' })
    expect(party('K17', 'פ')).toMatchObject({ color: '#2455A4', colorStatus: 'reviewed' })
    expect(party('K17', 'חץ')).toMatchObject({ color: '#7B2CBF', colorStatus: 'reviewed' })
    expect(party('K17', 'ק')).toMatchObject({ color: '#8B1E1E', colorStatus: 'reviewed' })
    expect(party('K17', 'קז')).toMatchObject({ color: '#202020', colorStatus: 'reviewed' })
    expect(party('K17', 'נץ')).toMatchObject({ color: '#F2C94C', colorStatus: 'reviewed' })
    expect(party('K17', 'ה')).toMatchObject({ color: '#4B5563', colorStatus: 'reviewed' })
    expect(party('K19', 'ו')).toMatchObject({ color: '#8B1E1E', colorStatus: 'reviewed' })
    expect(party('K23', 'נץ')).toMatchObject({ color: '#F2C94C', colorStatus: 'reviewed' })
    expect(party('K25', 'ל')).toMatchObject({ color: '#5DADE2', colorStatus: 'reviewed' })
    expect(party('K25', 'ד')).toMatchObject({ color: '#E67E22', colorStatus: 'reviewed' })
    expect(party('K25', 'ת')).toMatchObject({ color: '#00A651', colorStatus: 'reviewed' })

    expect(party('K22', 'רק')?.colorStatus).toBe('provisional')
    expect(party('K25', 'זך')?.colorStatus).toBe('provisional')
    expect(party('K25', 'קנ')?.colorStatus).toBe('provisional')
  })

  it('applies the reviewed K17-K25 Hebrew display names', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const payloadFor = async (electionId: string) => {
      const election = catalog.elections.find((candidate) => candidate.id === electionId)
      if (!election) {
        throw new Error(`Missing ${electionId} in generated catalog`)
      }
      return ElectionResultsSchema.parse(
        await readJson(resolve(dataRoot, election.resultUrls.locality)),
      )
    }
    const k17 = await payloadFor('K17')
    const k18 = await payloadFor('K18')
    const k19 = await payloadFor('K19')
    const laterPayloads = {
      K20: await payloadFor('K20'),
      K21: await payloadFor('K21'),
      K22: await payloadFor('K22'),
      K23: await payloadFor('K23'),
      K24: await payloadFor('K24'),
      K25: await payloadFor('K25'),
    }
    const expectedK17 = {
      אמת: 'העבודה-מימד', ג: 'יהדות התורה', ד: 'בל"ד', ה: 'ברית עולם', ו: 'חד"ש',
      ז: 'לחם', זה: 'עתיד אחד', זך: 'גיל', חץ: 'חץ', טב: 'האיחוד הלאומי-מפד"ל',
      יש: 'שינוי', כ: 'חזית יהודית לאומית', כן: 'קדימה', כץ: 'צומת', ל: 'ישראל ביתנו',
      מחל: 'הליכוד', מרצ: 'מרצ', נץ: 'חרות', עם: 'רע"מ-תע"ל', פ: 'תפנית', פז: 'לב',
      פכ: 'עוז לעניים', פץ: 'כוח הכסף', ף: 'מתקדמת', צה: 'הציונות החדשה', ק: 'דע"ם',
      קז: 'רע"ש', קנ: 'עלה ירוק', קפ: 'המפלגה הלאומית הערבית', רק: 'הירוקים', שס: 'ש"ס',
    }
    const expectedK18 = {
      אמת: 'העבודה', אר: 'אור בראשון', ב: 'הבית היהודי', ג: 'יהדות התורה', ד: 'בל"ד',
      ה: 'המפלגה הירוקה', ו: 'חד"ש', זך: 'גיל', חי: 'ישראל חזקה', ט: 'האיחוד הלאומי',
      ים: 'הישראלים', ינ: 'לב', יק: 'ניצולי השואה', כן: 'קדימה', ל: 'ישראל ביתנו',
      מחל: 'הליכוד-אח"י', מרצ: 'מרצ', נ: 'עלי"ה', נפ: 'אחריות', נץ: 'לזוז',
      נר: 'לוחמי חברה', עם: 'רע"מ-תע"ל', פ: 'כח להשפיע', פי: 'ברית עולם', פק: 'רע"ש',
      ץ: 'צומת', צי: 'צבר', ק: 'דע"ם', קנ: 'עלה ירוק', קפ: 'כוח הכסף', קץ: 'מתקדמת',
      רק: 'הירוקים', שס: 'ש"ס',
    }
    const expectedK19 = {
      אמת: 'העבודה', ד: 'בל"ד', הי: 'מורשת אבות', ו: 'חד"ש', ז: 'ארץ חדשה',
      זך: 'דור בוני הארץ', כן: 'קדימה', ני: 'אור בראשון', נק: 'מתקדמת',
      פ: 'הפיראטים', פז: 'כח להשפיע', פי: 'מפלגת כלכלה', צק: 'צדק חברתי',
      ק: 'דע"ם', קנ: 'עלה ירוק', רק: 'הירוקים', שס: 'ש"ס',
    }
    const expectedLaterNames = {
      K20: {
        ז: 'מפלגת כלכלה', זך: 'דמוקראטורה', יז: 'מנהיגות חברתית', יץ: "אלאמל לתג'ייר - התקווה לשינוי",
        נז: 'ובזכותן', נץ: 'פרח', ף: 'הפיראטים', קנ: 'עלה ירוק', קץ: 'יחד - העם איתנו',
        רק: 'הירוקים', שס: 'ש"ס',
      },
      K21: {
        אמת: 'העבודה', ז: 'זהות', זץ: 'צומת', י: 'ישר', יז: 'הגוש התנ"כי', ין: 'איחוד בני הברית',
        יץ: 'אחריות למייסדים', נץ: 'מגן', נר: 'גשר', ן: 'בט"ח', ןנ: 'מנהיגות חברתית',
        פה: 'כחול לבן', ףז: 'הפיראטים', צק: 'צדק חברתי', ץ: 'דע"ם', ץי: 'אני ואתה',
        ק: 'צדק לכל', ר: 'הרשימה הערבית', שס: 'ש"ס',
      },
      K22: {
        ז: 'עוצמה כלכלית', זכ: 'דמוקראטורה', זץ: 'צומת', י: 'מנהיגות חברתית', יז: 'אדום לבן',
        יק: 'הגוש התנ"כי', כי: 'האחדות העממית - אלוחדה אלשעביה', כף: 'עוצמה יהודית',
        נ: 'מתקדמת', פה: 'כחול לבן', ףז: 'הפיראטים', צ: 'צדק', ץ: 'דע"ם', קך: 'סדר חדש',
        קץ: 'קמ"ה', רק: 'הימין החילוני', שס: 'ש"ס',
      },
      K23: {
        ז: 'עוצמה ליברלית', י: 'החזון', יז: 'אדום לבן', יף: 'כבוד האדם', יק: 'הגוש התנ"כי',
        יר: 'מנהיגות חברתית', כ: 'הלב היהודי', כן: 'אני ואתה', נז: 'הכח להשפיע', ני: 'קמ"ה',
        נץ: 'עוצמה יהודית', נק: 'מתקדמת', פה: 'כחול לבן', ףז: 'הפיראטים', ץ: 'דע"ם',
        ק: 'ישראליסט', קי: 'שמע', קך: 'סדר חדש', קץ: 'משפט צדק', שס: 'ש"ס',
      },
      K24: {
        אמת: 'העבודה', ג: 'יהדות התורה', זץ: 'צומת', ט: 'הציונות הדתית', יז: 'הכלכלית החדשה',
        ינ: 'ברית השותפות', יף: 'כבוד האדם', יק: 'הגוש התנ"כי', יר: 'מנהיגות חברתית',
        כ: 'הלב היהודי', כך: 'אני ואתה', כן: 'כחול לבן', נ: 'קמ"ה', ני: 'עולם חדש',
        נר: 'אנחנו', עם: 'רע"מ', ףז: 'הפיראטים', צכ: 'מד"ע', צף: 'חץ', ץ: 'דע"ם',
        ק: 'הבלתי אפשרי, אפשרי', קי: 'שמע', קך: 'סדר חדש', קץ: 'משפט צדק', ר: 'רפא', שס: 'ש"ס',
      },
      K25: {
        אמת: 'העבודה', אצ: 'חופש כלכלי', ג: 'יהדות התורה', ד: 'בל"ד', ז: 'שחר כוח חברתי',
        זך: 'קמ"ה', זנ: 'כח להשפיע', זץ: 'צומת', ט: 'הציונות הדתית - עוצמה יהודית',
        י: 'ישראל חופשית דמוקרטית', יז: 'הכלכלית החדשה', יק: 'הגוש התנ"כי', נז: 'כבוד האדם',
        ני: 'נתיב', נף: 'שמע', נץ: 'העצמאים החדשים', נק: 'יש כיוון', נר: 'אנחנו', עם: 'רע"מ',
        ף: 'הפיראטים', צ: 'צעירים בוערים', ץ: 'מנהיגות חברתית', קי: 'הלב היהודי',
        קך: 'סדר חדש', קנ: 'כל קול קובע', רז: 'שלושים ארבעים', שס: 'ש"ס', ת: 'עלה ירוק',
      },
    }

    expect(k17.parties).toHaveLength(31)
    expect(k18.parties).toHaveLength(33)
    for (const [partyId, nameHe] of Object.entries(expectedK17)) {
      expect(k17.parties.find((party) => party.id === partyId)?.names.he, `K17/${partyId}`).toBe(nameHe)
    }
    for (const [partyId, nameHe] of Object.entries(expectedK18)) {
      expect(k18.parties.find((party) => party.id === partyId)?.names.he, `K18/${partyId}`).toBe(nameHe)
    }
    for (const [partyId, nameHe] of Object.entries(expectedK19)) {
      expect(k19.parties.find((party) => party.id === partyId)?.names.he, `K19/${partyId}`).toBe(nameHe)
    }
    for (const electionId of Object.keys(expectedLaterNames) as Array<keyof typeof expectedLaterNames>) {
      const expectedNames = expectedLaterNames[electionId]
      for (const [partyId, nameHe] of Object.entries(expectedNames)) {
        expect(
          laterPayloads[electionId].parties.find((party) => party.id === partyId)?.names.he,
          `${electionId}/${partyId}`,
        ).toBe(nameHe)
      }
    }
    expect(k18.parties.some((party) => party.id === 'פח')).toBe(false)
    expect(k19.parties.some((party) => party.id === 'זה')).toBe(false)
    expect(k19.parties.some((party) => party.id === 'פך')).toBe(false)
    expect(catalog.source.resultColumnExclusions).toContainEqual({
      electionId: 'K18',
      column: 'פח',
      reason: expect.stringContaining('did not run'),
    })
    for (const column of ['זה', 'פך']) {
      expect(catalog.source.resultColumnExclusions).toContainEqual({
        electionId: 'K19',
        column,
        reason: expect.stringContaining('did not run'),
      })
    }
    const laterExclusions = {
      K20: ['יך'],
      K21: ['זנ', 'נך', 'ץז'],
      K22: ['זן', 'כ', 'נץ'],
      K23: ['זץ'],
      K24: ['רק'],
    }
    for (const electionId of Object.keys(laterExclusions) as Array<keyof typeof laterExclusions>) {
      const columns = laterExclusions[electionId]
      for (const column of columns) {
        expect(laterPayloads[electionId].parties.some((party) => party.id === column)).toBe(false)
        expect(catalog.source.resultColumnExclusions).toContainEqual({
          electionId,
          column,
          reason: expect.stringContaining('did not run'),
        })
      }
    }
    expect(
      [k17, k18, k19, ...Object.values(laterPayloads)]
        .reduce((total, payload) => total + payload.parties.length, 0),
    ).toBe(297)
  })

  it('publishes recovered K17 turnout while keeping envelope turnout unavailable', async () => {
    const catalog = AppCatalogSchema.parse(await readJson(resolve(dataRoot, 'catalog.json')))
    const payloadFor = async (electionId: string) => {
      const election = catalog.elections.find((candidate) => candidate.id === electionId)
      if (!election) {
        throw new Error(`Missing ${electionId} in generated catalog`)
      }
      return ElectionResultsSchema.parse(
        await readJson(resolve(dataRoot, election.resultUrls.locality)),
      )
    }
    const k17 = await payloadFor('K17')
    const k18 = await payloadFor('K18')

    expect(k17.records.length).toBeGreaterThan(0)
    expect(
      k17.records.every(
        (record) =>
          record.totals.eligibleVoters >= record.totals.actualVoters &&
          record.totals.turnout !== null,
      ),
    ).toBe(true)
    expect(k17.envelope?.totals.turnout).toBeNull()
    expect(k18.records.some((record) => record.totals.turnout !== null)).toBe(true)
  })
})

async function readAndValidateGeography(asset: {
  geometryUrl: string
  markerGeometryUrl: string
  featureCount: number
  markerFeatureCount: number
}): Promise<Set<string>> {
  const geometry = (await readJson(resolve(dataRoot, asset.geometryUrl))) as {
    type: string
    features: Array<{ id?: string }>
  }
  expect(geometry.type).toBe('FeatureCollection')
  expect(geometry.features).toHaveLength(asset.featureCount)
  const ids = new Set(geometry.features.map((feature) => feature.id).filter(Boolean) as string[])
  expect(ids.size).toBe(geometry.features.length)

  const markers = (await readJson(resolve(dataRoot, asset.markerGeometryUrl))) as {
    type: string
    features: Array<{
      id?: string
      properties?: { displayMode?: string }
      geometry?: { type?: string }
    }>
  }
  expect(markers.type).toBe('FeatureCollection')
  expect(markers.features).toHaveLength(asset.markerFeatureCount)
  expect(new Set(markers.features.map((feature) => feature.id)).size).toBe(
    markers.features.length,
  )
  for (const marker of markers.features) {
    expect(ids.has(marker.id ?? '')).toBe(true)
    expect(marker.properties?.displayMode).toBe('marker')
    expect(['Point', 'MultiPoint']).toContain(marker.geometry?.type)
  }
  return ids
}
async function readJson(path: string): Promise<unknown> {
  return JSON.parse(await readFile(path, 'utf8'))
}

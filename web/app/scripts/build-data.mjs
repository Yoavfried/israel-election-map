import { createHash } from 'node:crypto'
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises'
import { dirname, isAbsolute, relative, resolve } from 'node:path'
import {
  applyStatisticalDisplayGroups,
  aliasJoinedCompositeResults,
  buildCoverage,
  buildCompositeMetadataIndex,
  buildCustomMetadataIndex,
  buildDisplayMarkers,
  buildHiddenLocalityIds,
  buildMetadataIndex,
  buildMunicipalityFallbackDisplay,
  buildPartyRegistryIndex,
  buildResultPayload,
  parseCsv,
  pruneGeography,
} from './lib/compiler.mjs'

const APP_ROOT = resolve(import.meta.dirname, '..')
const REPOSITORY_ROOT = resolve(APP_ROOT, '..', '..')
const DEFAULT_SOURCE_ROOT = resolve(REPOSITORY_ROOT, 'data', 'processed')
const DEFAULT_OUTPUT_ROOT = resolve(APP_ROOT, 'public', 'data', 'v2')
const HISTORICAL_STATISTICAL_AREA_VINTAGES = [1995, 2008, 2011]

async function main() {
  const options = parseArguments(process.argv.slice(2))
  const sourceRoot = resolveOption(options.source, DEFAULT_SOURCE_ROOT)
  const outputRoot = resolveOption(options.output, DEFAULT_OUTPUT_ROOT)
  assertSafeOutputPath(outputRoot)

  const stagingRoot = `${outputRoot}.tmp-${process.pid}`
  await rm(stagingRoot, { force: true, recursive: true })
  await mkdir(stagingRoot, { recursive: true })

  try {
    const [
      electionConfig,
      partyOverrideConfig,
      partyRegistryRows,
      localityDisplayOverrideRows,
      statisticalAreaDisplayOverrideRows,
      statisticalAreaDisplayGroupRows,
      summaryRows,
      geographySummary,
      statisticalMetadataRows,
      localityMetadataRows,
      statisticalAreas,
      localities,
      statisticalAreaBackdrop,
      compositeLocalities,
      customGeographies,
    ] = await Promise.all([
      readJson(resolve(APP_ROOT, 'config', 'elections.json')),
      readJson(resolve(APP_ROOT, 'config', 'party-overrides.json')),
      readCsv(resolve(REPOSITORY_ROOT, 'data', 'manual', 'party_registry.csv')),
      readCsv(resolve(REPOSITORY_ROOT, 'data', 'manual', 'locality_display_overrides.csv')),
      readCsv(
        resolve(REPOSITORY_ROOT, 'data', 'manual', 'statistical_area_display_overrides.csv'),
      ),
      readCsv(
        resolve(REPOSITORY_ROOT, 'data', 'manual', 'statistical_area_display_groups.csv'),
      ),
      readCsv(resolve(sourceRoot, 'public', 'election_summary.csv')),
      readJson(resolve(sourceRoot, 'geographies', 'geography_build_summary.json')),
      readCsv(resolve(sourceRoot, 'geographies', 'statistical_areas_2022.metadata.csv')),
      readCsv(resolve(sourceRoot, 'geographies', 'localities_2022.metadata.csv')),
      readJson(
        resolve(sourceRoot, 'geographies', 'statistical_areas_2022.display.simplified.geojson'),
      ),
      readJson(
        resolve(sourceRoot, 'geographies', 'localities_2022_dissolved.display.simplified.geojson'),
      ),
      readJson(
        resolve(sourceRoot, 'geographies', 'statistical_area_land_backdrop.simplified.geojson'),
      ),
      readJson(resolve(sourceRoot, 'geographies', 'composite_localities.simplified.geojson')),
      readJson(resolve(sourceRoot, 'geographies', 'custom_geographies.geojson')),
    ])
    const historicalStatisticalSources = await Promise.all(
      HISTORICAL_STATISTICAL_AREA_VINTAGES.map(async (vintage) => [
        vintage,
        {
          metadataRows: await readCsv(
            resolve(sourceRoot, 'geographies', `statistical_areas_${vintage}.metadata.csv`),
          ),
          geography: await readJson(
            resolve(
              sourceRoot,
              'geographies',
              `statistical_areas_${vintage}.display.simplified.geojson`,
            ),
          ),
        },
      ]),
    )
    const statisticalSourcesByVintage = new Map([
      ...historicalStatisticalSources,
      [2022, { metadataRows: statisticalMetadataRows, geography: statisticalAreas }],
    ])

    validateConfiguration(electionConfig, partyOverrideConfig)
    const partyRegistryByElection = buildPartyRegistryIndex(partyRegistryRows)
    validatePartyRegistryElections(electionConfig, partyRegistryByElection)

    const summaryByElection = new Map(summaryRows.map((row) => [row.election, row]))
    const statisticalMetadataByVintage = new Map(
      [...statisticalSourcesByVintage].map(([vintage, source]) => [
        vintage,
        buildMetadataIndex(source.metadataRows, 'statistical-area'),
      ]),
    )
    const localityMetadata = new Map([
      ...buildMetadataIndex(localityMetadataRows, 'locality'),
      ...buildCompositeMetadataIndex(compositeLocalities),
    ])
    const localityDisplayOverrides = buildLocalityDisplayOverrideIndex(
      localityDisplayOverrideRows,
      electionConfig,
      localityMetadata,
    )
    const statisticalAreaDisplayOverrides = buildStatisticalAreaDisplayOverrideIndex(
      statisticalAreaDisplayOverrideRows,
      electionConfig,
      statisticalMetadataByVintage,
    )
    const customMetadata = buildCustomMetadataIndex(customGeographies)
    const statisticalAreaDisplayGroups = buildStatisticalAreaDisplayGroupIndex(
      statisticalAreaDisplayGroupRows,
      electionConfig,
      statisticalMetadataByVintage,
      customMetadata,
    )
    const coverageByElection = new Map(
      electionConfig.map((election) => [
        election.id,
        {
          'statistical-area': buildCoverage(summaryByElection.get(election.id), 'statistical-area'),
          locality: buildCoverage(summaryByElection.get(election.id), 'locality'),
        },
      ]),
    )

    const prunedStatisticalAreasByVintage = new Map(
      [...statisticalSourcesByVintage].map(([vintage, source]) => [
        vintage,
        pruneGeography(source.geography, 'statistical-area', customGeographies),
      ]),
    )
    const prunedLocalities = pruneGeography(
      localities,
      'locality',
      customGeographies,
      compositeLocalities,
    )
    const electionSourceDataById = new Map(
      await Promise.all(
        electionConfig.map(async (election) => {
          const electionSlug = election.id.toLowerCase()
          const [statisticalRows, localityRows, customRows, envelopeRows, fallbackRows] =
            await Promise.all([
              readCsv(
                resolve(sourceRoot, 'public', 'statistical_area_results', `${electionSlug}.csv`),
              ),
              readCsv(resolve(sourceRoot, 'public', 'locality_results', `${electionSlug}.csv`)),
              readCsv(
                resolve(sourceRoot, 'public', 'custom_geography_results', `${electionSlug}.csv`),
              ),
              readCsv(resolve(sourceRoot, 'public', 'envelope_results', `${electionSlug}.csv`)),
              readCsv(
                resolve(
                  sourceRoot,
                  'public',
                  'municipality_display_fallbacks',
                  `${electionSlug}.csv`,
                ),
              ),
            ])
          return [
            election.id,
            { statisticalRows, localityRows, customRows, envelopeRows, fallbackRows },
          ]
        }),
      ),
    )
    const fallbackFeaturesByVintage = new Map()
    for (const election of electionConfig) {
      const sourceData = electionSourceDataById.get(election.id)
      const vintage = Number(election.statisticalAreaVintage)
      const statisticalGeography = prunedStatisticalAreasByVintage.get(vintage)
      if (!sourceData || !statisticalGeography) {
        throw new Error(`${election.id} is missing municipality fallback build inputs`)
      }
      const fallbackDisplay = buildMunicipalityFallbackDisplay({
        electionId: election.id,
        vintage,
        fallbackRows: sourceData.fallbackRows,
        localityGeography: prunedLocalities,
        statisticalGeography,
      })
      electionSourceDataById.set(election.id, { ...sourceData, fallbackDisplay })

      let fallbackFeatures = fallbackFeaturesByVintage.get(vintage)
      if (!fallbackFeatures) {
        fallbackFeatures = new Map()
        fallbackFeaturesByVintage.set(vintage, fallbackFeatures)
      }
      for (const feature of fallbackDisplay.features) {
        const existing = fallbackFeatures.get(feature.id)
        if (existing && JSON.stringify(existing) !== JSON.stringify(feature)) {
          throw new Error(`Municipality fallback geometry changed across elections: ${feature.id}`)
        }
        fallbackFeatures.set(feature.id, feature)
      }
    }
    for (const [vintage, featuresById] of fallbackFeaturesByVintage) {
      prunedStatisticalAreasByVintage.get(vintage)?.features.push(...featuresById.values())
    }
    const statisticalAreaBackdropUrl = 'geographies/statistical-area-backdrop.geojson'
    const statisticalMarkersByVintage = new Map(
      [...prunedStatisticalAreasByVintage].map(([vintage, geography]) => [
        vintage,
        buildDisplayMarkers(geography),
      ]),
    )
    const localityMarkers = buildDisplayMarkers(prunedLocalities)

    const assets = []
    const writeJsonAsset = async (relativePath, payload, pretty = false) => {
      const text = `${JSON.stringify(payload, null, pretty ? 2 : undefined)}\n`
      const assetHash = createHash('sha256').update(text).digest('hex')
      const absolutePath = resolve(stagingRoot, relativePath)
      await mkdir(dirname(absolutePath), { recursive: true })
      await writeFile(absolutePath, text, 'utf8')
      assets.push({ path: relativePath.replaceAll('\\', '/'), bytes: Buffer.byteLength(text), sha256: assetHash })
    }

    const statisticalGeographyAssetsByVintage = new Map(
      [...prunedStatisticalAreasByVintage].map(([vintage, geography]) => {
        const markers = statisticalMarkersByVintage.get(vintage)
        if (!markers) {
          throw new Error(`Missing marker geography for statistical-area vintage ${vintage}`)
        }
        return [
          vintage,
          {
            vintage,
            geometryUrl: `geographies/statistical-areas-${vintage}.geojson`,
            markerGeometryUrl: `geographies/statistical-area-markers-${vintage}.geojson`,
            backdropGeometryUrl: statisticalAreaBackdropUrl,
            featureCount: geography.features.length,
            markerFeatureCount: markers.features.length,
          },
        ]
      }),
    )
    const localityGeographyAsset = {
      vintage: 2022,
      geometryUrl: 'geographies/localities.geojson',
      markerGeometryUrl: 'geographies/locality-markers.geojson',
      featureCount: prunedLocalities.features.length,
      markerFeatureCount: localityMarkers.features.length,
    }

    await Promise.all([
      ...[...prunedStatisticalAreasByVintage].flatMap(([vintage, geography]) => [
        writeJsonAsset(`geographies/statistical-areas-${vintage}.geojson`, geography),
        writeJsonAsset(
          `geographies/statistical-area-markers-${vintage}.geojson`,
          statisticalMarkersByVintage.get(vintage),
        ),
      ]),
      writeJsonAsset(localityGeographyAsset.geometryUrl, prunedLocalities),
      writeJsonAsset(localityGeographyAsset.markerGeometryUrl, localityMarkers),
      writeJsonAsset(statisticalAreaBackdropUrl, statisticalAreaBackdrop),
    ])

    const catalogElections = []
    for (const election of electionConfig) {
      const electionSlug = election.id.toLowerCase()
      const statisticalAreaVintage = Number(election.statisticalAreaVintage)
      const statisticalMetadata = statisticalMetadataByVintage.get(statisticalAreaVintage)
      const statisticalGeographyAsset = statisticalGeographyAssetsByVintage.get(
        statisticalAreaVintage,
      )
      if (!statisticalMetadata || !statisticalGeographyAsset) {
        throw new Error(
          `${election.id} references unavailable statistical-area vintage ${election.statisticalAreaVintage}`,
        )
      }
      const sourceData = electionSourceDataById.get(election.id)
      if (!sourceData) {
        throw new Error(`${election.id} is missing compiled source data`)
      }
      const {
        statisticalRows,
        localityRows,
        customRows,
        envelopeRows,
        fallbackDisplay,
      } = sourceData
      const coverageByMode = coverageByElection.get(election.id)
      const displayOverrides = localityDisplayOverrides.get(election.id) ?? new Map()
      const statisticalDisplayOverrides =
        statisticalAreaDisplayOverrides.get(election.id) ?? new Map()
      const configuredHiddenStatisticalIds = [...statisticalDisplayOverrides]
        .filter(([, override]) => override.visibility === 'hidden')
        .map(([statAreaId]) => statAreaId)
      const hiddenLocalityIds = [
        ...new Set([
          ...buildHiddenLocalityIds(prunedLocalities, election.id),
          ...[...displayOverrides]
            .filter(([, override]) => override.visibility === 'hidden')
            .map(([localityId]) => localityId),
        ]),
      ].toSorted()
      const electionLocalityMetadata = applyMetadataNameOverrides(
        localityMetadata,
        displayOverrides,
      )
      const electionStatisticalMetadata = applyMetadataNameOverrides(
        statisticalMetadata,
        statisticalDisplayOverrides,
      )
      const displayedLocalityRows = aliasJoinedCompositeResults(
        localityRows,
        prunedLocalities,
        election.id,
      )
      const statisticalCustomRows = customRows.filter(
        (row) => !row.geography_mode || row.geography_mode === 'statistical-area',
      )
      const localityCustomRows = customRows.filter(
        (row) => !row.geography_mode || row.geography_mode === 'locality',
      )
      const statisticalDisplay = applyStatisticalDisplayGroups({
        electionId: election.id,
        primaryRows: statisticalRows,
        customRows,
        groups: statisticalAreaDisplayGroups.get(election.id),
      })
      const hiddenStatisticalIds = [
        ...new Set([
          ...configuredHiddenStatisticalIds,
          ...statisticalDisplay.hiddenGeographyIds,
          ...fallbackDisplay.hiddenGeographyIds,
        ]),
      ].toSorted()
      const overrides = partyOverrideConfig.elections[election.id] ?? {}
      const partyRegistry = partyRegistryByElection.get(election.id)
      const excludedPartyColumns = Object.keys(
        partyOverrideConfig.ignoredResultColumns[election.id] ?? {},
      )
      const statisticalPayload = buildResultPayload({
        electionId: election.id,
        mode: 'statistical-area',
        primaryRows: statisticalDisplay.primaryRows,
        customRows: [
          ...statisticalCustomRows,
          ...statisticalDisplay.displayRows,
          ...fallbackDisplay.displayRows,
        ],
        envelopeRows,
        metadataById: electionStatisticalMetadata,
        customMetadataById: new Map([
          ...customMetadata,
          ...fallbackDisplay.metadataById,
        ]),
        coverage: coverageByMode['statistical-area'],
        hiddenGeographyIds: hiddenStatisticalIds,
        partyRegistry,
        partyColorsByBallotLetter: partyOverrideConfig.ballotLetterColors,
        partyOverrides: overrides,
        excludedPartyColumns,
      })
      const localityPayload = buildResultPayload({
        electionId: election.id,
        mode: 'locality',
        primaryRows: displayedLocalityRows,
        customRows: localityCustomRows,
        envelopeRows,
        metadataById: electionLocalityMetadata,
        customMetadataById: customMetadata,
        coverage: coverageByMode.locality,
        hiddenGeographyIds: hiddenLocalityIds,
        partyRegistry,
        partyColorsByBallotLetter: partyOverrideConfig.ballotLetterColors,
        partyOverrides: overrides,
        excludedPartyColumns,
        validatePartyTotals: true,
      })

      const resultUrls = {
        'statistical-area': `results/${electionSlug}/statistical-areas.json`,
        locality: `results/${electionSlug}/localities.json`,
      }
      await Promise.all([
        writeJsonAsset(resultUrls['statistical-area'], statisticalPayload),
        writeJsonAsset(resultUrls.locality, localityPayload),
      ])

      catalogElections.push({
        ...election,
        coverageByMode,
        resultUrls,
        geographiesByMode: {
          'statistical-area': statisticalGeographyAsset,
          locality: localityGeographyAsset,
        },
      })
    }

    const sortedAssets = assets.toSorted((left, right) => left.path.localeCompare(right.path))
    const buildHash = createHash('sha256')
    for (const asset of sortedAssets) {
      buildHash.update(asset.path).update('\0').update(asset.sha256)
    }
    const buildId = buildHash.digest('hex').slice(0, 16)
    const currentStatisticalGeographyAsset = statisticalGeographyAssetsByVintage.get(2022)
    if (!currentStatisticalGeographyAsset) {
      throw new Error('Missing current 2022 statistical-area geography asset')
    }
    const catalog = {
      schemaVersion: 3,
      buildId,
      generatedAt: new Date().toISOString(),
      source: {
        statisticalAreaVintages: [...statisticalGeographyAssetsByVintage.keys()].toSorted(),
        localityGeometryVintage: 2022,
        electionRange: { first: 'K17', last: 'K25' },
        assignmentStatus: 'official-crosswalk-first-locality-complete-statistical-areas-partial',
        resultColumnExclusions: Object.entries(partyOverrideConfig.ignoredResultColumns).flatMap(
          ([electionId, columns]) =>
            Object.entries(columns).map(([column, reason]) => ({ electionId, column, reason })),
        ),
      },
      bounds: [
        [geographySummary.bounds_wgs84.min_lon, geographySummary.bounds_wgs84.min_lat],
        [geographySummary.bounds_wgs84.max_lon, geographySummary.bounds_wgs84.max_lat],
      ],
      partyColorPolicy: {
        status: 'partial',
        description: 'Reviewed ballot-letter colors stay constant across elections, election-specific overrides take precedence, and unreviewed letters use deterministic placeholders.',
      },
      geographyModes: [
        {
          id: 'statistical-area',
          label: { en: 'Statistical areas', he: 'אזורים סטטיסטיים' },
          ...currentStatisticalGeographyAsset,
        },
        {
          id: 'locality',
          label: { en: 'Localities', he: 'יישובים' },
          ...localityGeographyAsset,
        },
      ],
      elections: catalogElections,
      assets: sortedAssets,
    }
    await writeJsonAsset('catalog.json', catalog, true)

    await publishDirectory(stagingRoot, outputRoot)

    const totalBytes = assets.reduce((sum, asset) => sum + asset.bytes, 0)
    console.log(`web_data_build=${buildId}`)
    console.log(`elections=${catalogElections.length}`)
    console.log(`assets=${assets.length}`)
    console.log(`bytes=${totalBytes}`)
  } catch (error) {
    await rm(stagingRoot, { force: true, recursive: true })
    throw error
  }
}

async function publishDirectory(stagingRoot, outputRoot) {
  const backupRoot = `${outputRoot}.backup-${process.pid}`
  await rm(backupRoot, { force: true, recursive: true })
  await mkdir(dirname(outputRoot), { recursive: true })

  let previousOutputMoved = false
  try {
    await rename(outputRoot, backupRoot)
    previousOutputMoved = true
  } catch (error) {
    if (error?.code !== 'ENOENT') {
      throw error
    }
  }

  try {
    await rename(stagingRoot, outputRoot)
  } catch (publishError) {
    if (previousOutputMoved) {
      try {
        await rename(backupRoot, outputRoot)
      } catch (rollbackError) {
        throw new AggregateError(
          [publishError, rollbackError],
          'Could not publish the generated data bundle or restore the previous bundle.',
        )
      }
    }
    throw publishError
  }

  if (previousOutputMoved) {
    await rm(backupRoot, { force: true, recursive: true })
  }
}

function parseArguments(args) {
  const options = {}
  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index]
    if (argument === '--source' || argument === '--output') {
      const value = args[index + 1]
      if (!value) {
        throw new Error(`${argument} requires a path`)
      }
      options[argument.slice(2)] = value
      index += 1
      continue
    }
    throw new Error(`Unknown argument: ${argument}`)
  }
  return options
}

function resolveOption(value, fallback) {
  if (!value) {
    return fallback
  }
  return isAbsolute(value) ? value : resolve(process.cwd(), value)
}

function assertSafeOutputPath(outputRoot) {
  const generatedRoot = resolve(APP_ROOT, 'public', 'data')
  const relativePath = relative(generatedRoot, outputRoot)
  if (relativePath.startsWith('..') || isAbsolute(relativePath) || relativePath === '') {
    throw new Error(`Output must be a versioned directory inside ${generatedRoot}`)
  }
}

async function readJson(path) {
  const text = await readFile(path, 'utf8')
  try {
    return JSON.parse(text.replace(/^\uFEFF/, ''))
  } catch (error) {
    throw new Error(`Invalid JSON in ${path}: ${error.message}`)
  }
}

async function readCsv(path) {
  return parseCsv(await readFile(path, 'utf8'), path)
}

function buildLocalityDisplayOverrideIndex(rows, elections, localityMetadata) {
  const configuredElections = new Set(elections.map((election) => election.id))
  const byElection = new Map(elections.map((election) => [election.id, new Map()]))

  for (const row of rows) {
    const localityId = String(row.locality_id ?? '').trim()
    const electionIds = String(row.elections ?? '')
      .split('|')
      .map((value) => value.trim())
      .filter(Boolean)
    const visibility = String(row.visibility ?? '').trim() || 'default'
    const nameHe = String(row.name_he ?? '').trim()
    const nameEn = String(row.name_en ?? '').trim()
    const note = String(row.note ?? '').trim()

    if (!localityMetadata.has(localityId)) {
      throw new Error(`Unknown locality display override: ${localityId || '(blank ID)'}`)
    }
    if (electionIds.length === 0 || electionIds.some((id) => !configuredElections.has(id))) {
      throw new Error(`${localityId} has invalid display-override elections`)
    }
    if (!['default', 'hidden'].includes(visibility)) {
      throw new Error(`${localityId} has invalid display visibility: ${visibility}`)
    }

    for (const electionId of electionIds) {
      const electionOverrides = byElection.get(electionId)
      if (electionOverrides.has(localityId)) {
        throw new Error(`Duplicate locality display override: ${electionId}.${localityId}`)
      }
      electionOverrides.set(localityId, { visibility, nameHe, nameEn, note })
    }
  }

  return byElection
}

function buildStatisticalAreaDisplayOverrideIndex(rows, elections, metadataByVintage) {
  const electionById = new Map(elections.map((election) => [election.id, election]))
  const byElection = new Map(elections.map((election) => [election.id, new Map()]))

  for (const row of rows) {
    const statAreaId = String(row.stat_area_id ?? '').trim()
    const electionIds = String(row.elections ?? '')
      .split('|')
      .map((value) => value.trim())
      .filter(Boolean)
    const visibility = String(row.visibility ?? '').trim()
    const nameHe = String(row.name_he ?? '').trim()
    const nameEn = String(row.name_en ?? '').trim()
    const note = String(row.note ?? '').trim()

    if (
      !statAreaId ||
      !['default', 'hidden'].includes(visibility) ||
      electionIds.length === 0 ||
      (visibility === 'default' && !nameHe && !nameEn)
    ) {
      throw new Error(`Invalid statistical-area display override: ${statAreaId || '(blank ID)'}`)
    }
    for (const electionId of electionIds) {
      const election = electionById.get(electionId)
      if (!election) {
        throw new Error(`${statAreaId} has an unknown display-override election: ${electionId}`)
      }
      const metadata = metadataByVintage.get(Number(election.statisticalAreaVintage))
      if (!metadata?.has(statAreaId)) {
        throw new Error(`${electionId} display override references unavailable area ${statAreaId}`)
      }
      const electionOverrides = byElection.get(electionId)
      if (electionOverrides.has(statAreaId)) {
        throw new Error(`Duplicate statistical-area display override: ${electionId}.${statAreaId}`)
      }
      electionOverrides.set(statAreaId, { visibility, nameHe, nameEn, note })
    }
  }

  return byElection
}

function buildStatisticalAreaDisplayGroupIndex(
  rows,
  elections,
  metadataByVintage,
  customMetadata,
) {
  const electionById = new Map(elections.map((election) => [election.id, election]))
  const groupsByElection = new Map(
    elections.map((election) => [election.id, new Map()]),
  )
  const componentOwnersByElection = new Map(
    elections.map((election) => [election.id, new Map()]),
  )

  for (const row of rows) {
    const displayGeographyId = String(row.display_geography_id ?? '').trim()
    const componentStatAreaId = String(row.component_stat_area_id ?? '').trim()
    const electionIds = String(row.elections ?? '')
      .split('|')
      .map((value) => value.trim())
      .filter(Boolean)
    const note = String(row.note ?? '').trim()

    if (!customMetadata.has(displayGeographyId)) {
      throw new Error(
        `Unknown statistical display-group target: ${displayGeographyId || '(blank ID)'}`,
      )
    }
    if (!componentStatAreaId || electionIds.length === 0) {
      throw new Error(`Invalid statistical display-group component: ${componentStatAreaId}`)
    }

    for (const electionId of electionIds) {
      const election = electionById.get(electionId)
      if (!election) {
        throw new Error(
          `${componentStatAreaId} has an unknown display-group election: ${electionId}`,
        )
      }
      const metadata = metadataByVintage.get(Number(election.statisticalAreaVintage))
      if (!metadata?.has(componentStatAreaId)) {
        throw new Error(
          `${electionId} display group references unavailable area ${componentStatAreaId}`,
        )
      }

      const componentOwners = componentOwnersByElection.get(electionId)
      const existingOwner = componentOwners.get(componentStatAreaId)
      if (existingOwner) {
        throw new Error(
          `${electionId} display component ${componentStatAreaId} is already assigned to ${existingOwner}`,
        )
      }
      componentOwners.set(componentStatAreaId, displayGeographyId)

      const electionGroups = groupsByElection.get(electionId)
      const group = electionGroups.get(displayGeographyId) ?? {
        displayGeographyId,
        componentIds: [],
        note,
      }
      group.componentIds.push(componentStatAreaId)
      electionGroups.set(displayGeographyId, group)
    }
  }

  return new Map(
    [...groupsByElection].map(([electionId, groups]) => [
      electionId,
      [...groups.values()]
        .map((group) => ({ ...group, componentIds: group.componentIds.toSorted() }))
        .toSorted((left, right) =>
          left.displayGeographyId.localeCompare(right.displayGeographyId),
        ),
    ]),
  )
}

function applyMetadataNameOverrides(metadataById, overrides) {
  const output = new Map(metadataById)
  for (const [id, override] of overrides) {
    if (!override.nameHe && !override.nameEn) {
      continue
    }
    const metadata = output.get(id)
    output.set(id, {
      ...metadata,
      nameHe: override.nameHe || metadata.nameHe,
      nameEn: override.nameEn || metadata.nameEn,
    })
  }
  return output
}

function validateConfiguration(elections, partyOverrides) {
  if (!Array.isArray(elections) || elections.length === 0) {
    throw new Error('Election configuration must be a non-empty array')
  }
  const ids = new Set()
  for (const election of elections) {
    if (
      !election.id ||
      !election.number ||
      !election.label?.en ||
      !election.label?.he ||
      ![1995, 2008, 2011, 2022].includes(Number(election.statisticalAreaVintage))
    ) {
      throw new Error(
        'Every election needs an ID, number, statistical-area vintage, and English/Hebrew labels',
      )
    }
    if (ids.has(election.id)) {
      throw new Error(`Duplicate election ID: ${election.id}`)
    }
    ids.add(election.id)
  }
  if (
    partyOverrides?.schemaVersion !== 2 ||
    !partyOverrides.ballotLetterColors ||
    typeof partyOverrides.ballotLetterColors !== 'object' ||
    !partyOverrides.elections ||
    typeof partyOverrides.elections !== 'object' ||
    !partyOverrides.ignoredResultColumns ||
    typeof partyOverrides.ignoredResultColumns !== 'object'
  ) {
    throw new Error(
      'party-overrides.json must use schemaVersion 2 and contain ballotLetterColors, elections, and ignoredResultColumns objects',
    )
  }

  for (const [ballotLetter, color] of Object.entries(partyOverrides.ballotLetterColors)) {
    assertHexColor(color, `ballotLetterColors.${ballotLetter}`)
  }
  for (const [electionId, overrides] of Object.entries(partyOverrides.elections)) {
    if (!ids.has(electionId) || !overrides || typeof overrides !== 'object') {
      throw new Error(`Invalid party override election: ${electionId}`)
    }
    for (const [partyId, override] of Object.entries(overrides)) {
      if (!override || typeof override !== 'object') {
        throw new Error(`${electionId}.${partyId} must be an override object`)
      }
      if (override.color) {
        assertHexColor(override.color, `elections.${electionId}.${partyId}.color`)
      }
      for (const field of ['nameHe', 'nameEn']) {
        if (override[field] !== undefined && (typeof override[field] !== 'string' || !override[field].trim())) {
          throw new Error(`elections.${electionId}.${partyId}.${field} must be a non-empty string`)
        }
      }
    }
  }
}

function assertHexColor(color, fieldName) {
  if (typeof color !== 'string' || !/^#[0-9a-f]{6}$/i.test(color)) {
    throw new Error(`${fieldName} must be a six-digit hex color`)
  }
}

function validatePartyRegistryElections(elections, partyRegistryByElection) {
  const configuredIds = new Set(elections.map((election) => election.id))
  const missing = elections
    .map((election) => election.id)
    .filter((electionId) => !partyRegistryByElection.has(electionId))
  const extra = [...partyRegistryByElection.keys()].filter(
    (electionId) => !configuredIds.has(electionId),
  )
  if (missing.length > 0 || extra.length > 0) {
    throw new Error(
      `Party registry election coverage is invalid; missing: ${missing.join(', ') || '(none)'}; ` +
        `extra: ${extra.join(', ') || '(none)'}`,
    )
  }
}

await main()

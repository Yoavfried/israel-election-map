import { createHash } from 'node:crypto'
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises'
import { dirname, isAbsolute, relative, resolve } from 'node:path'
import {
  buildCoverage,
  buildCustomMetadataIndex,
  buildDisplayMarkers,
  buildMetadataIndex,
  buildResultPayload,
  parseCsv,
  pruneGeography,
} from './lib/compiler.mjs'

const APP_ROOT = resolve(import.meta.dirname, '..')
const REPOSITORY_ROOT = resolve(APP_ROOT, '..', '..')
const DEFAULT_SOURCE_ROOT = resolve(REPOSITORY_ROOT, 'data', 'processed')
const DEFAULT_OUTPUT_ROOT = resolve(APP_ROOT, 'public', 'data', 'v1')

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
      summaryRows,
      geographySummary,
      statisticalMetadataRows,
      localityMetadataRows,
      statisticalAreas,
      localities,
      customGeographies,
    ] = await Promise.all([
      readJson(resolve(APP_ROOT, 'config', 'elections.json')),
      readJson(resolve(APP_ROOT, 'config', 'party-overrides.json')),
      readCsv(resolve(sourceRoot, 'public', 'election_summary.csv')),
      readJson(resolve(sourceRoot, 'geographies', 'geography_build_summary.json')),
      readCsv(resolve(sourceRoot, 'geographies', 'statistical_areas_2022.metadata.csv')),
      readCsv(resolve(sourceRoot, 'geographies', 'localities_2022.metadata.csv')),
      readJson(resolve(sourceRoot, 'geographies', 'statistical_areas_2022.simplified.geojson')),
      readJson(resolve(sourceRoot, 'geographies', 'localities_2022_dissolved.simplified.geojson')),
      readJson(resolve(sourceRoot, 'geographies', 'custom_geographies.geojson')),
    ])

    validateConfiguration(electionConfig, partyOverrideConfig)

    const summaryByElection = new Map(summaryRows.map((row) => [row.election, row]))
    const statisticalMetadata = buildMetadataIndex(statisticalMetadataRows, 'statistical-area')
    const localityMetadata = buildMetadataIndex(localityMetadataRows, 'locality')
    const customMetadata = buildCustomMetadataIndex(customGeographies)
    const coverageByElection = new Map(
      electionConfig.map((election) => [election.id, buildCoverage(summaryByElection.get(election.id))]),
    )

    const prunedStatisticalAreas = pruneGeography(
      statisticalAreas,
      'statistical-area',
      customGeographies,
    )
    const prunedLocalities = pruneGeography(localities, 'locality', customGeographies)
    const statisticalMarkers = buildDisplayMarkers(prunedStatisticalAreas)
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

    await Promise.all([
      writeJsonAsset('geographies/statistical-areas.geojson', prunedStatisticalAreas),
      writeJsonAsset('geographies/localities.geojson', prunedLocalities),
      writeJsonAsset('geographies/statistical-area-markers.geojson', statisticalMarkers),
      writeJsonAsset('geographies/locality-markers.geojson', localityMarkers),
    ])

    const catalogElections = []
    for (const election of electionConfig) {
      const electionSlug = election.id.toLowerCase()
      const [statisticalRows, localityRows, customRows] = await Promise.all([
        readCsv(resolve(sourceRoot, 'public', 'statistical_area_results', `${electionSlug}.csv`)),
        readCsv(resolve(sourceRoot, 'public', 'locality_results', `${electionSlug}.csv`)),
        readCsv(resolve(sourceRoot, 'public', 'custom_geography_results', `${electionSlug}.csv`)),
      ])
      const coverage = coverageByElection.get(election.id)
      const overrides = partyOverrideConfig.elections[election.id] ?? {}
      const excludedPartyColumns = Object.keys(
        partyOverrideConfig.ignoredResultColumns[election.id] ?? {},
      )
      const statisticalPayload = buildResultPayload({
        electionId: election.id,
        mode: 'statistical-area',
        primaryRows: statisticalRows,
        customRows,
        metadataById: statisticalMetadata,
        customMetadataById: customMetadata,
        coverage,
        partyOverrides: overrides,
        excludedPartyColumns,
      })
      const localityPayload = buildResultPayload({
        electionId: election.id,
        mode: 'locality',
        primaryRows: localityRows,
        customRows,
        metadataById: localityMetadata,
        customMetadataById: customMetadata,
        coverage,
        partyOverrides: overrides,
        excludedPartyColumns,
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
        coverage,
        resultUrls,
      })
    }

    const sortedAssets = assets.toSorted((left, right) => left.path.localeCompare(right.path))
    const buildHash = createHash('sha256')
    for (const asset of sortedAssets) {
      buildHash.update(asset.path).update('\0').update(asset.sha256)
    }
    const buildId = buildHash.digest('hex').slice(0, 16)
    const catalog = {
      schemaVersion: 1,
      buildId,
      generatedAt: new Date().toISOString(),
      source: {
        geographyVintage: 2022,
        electionRange: { first: 'K17', last: 'K25' },
        assignmentStatus: 'partial-until-reviewed-geocodes-are-promoted',
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
        status: 'provisional',
        description: 'Deterministic placeholder colors keyed by election and ballot letter; reviewed overrides take precedence.',
      },
      geographyModes: [
        {
          id: 'statistical-area',
          label: { en: 'Statistical areas', he: 'אזורים סטטיסטיים' },
          geometryUrl: 'geographies/statistical-areas.geojson',
          markerGeometryUrl: 'geographies/statistical-area-markers.geojson',
          featureCount: prunedStatisticalAreas.features.length,
          markerFeatureCount: statisticalMarkers.features.length,
        },
        {
          id: 'locality',
          label: { en: 'Localities', he: 'יישובים' },
          geometryUrl: 'geographies/localities.geojson',
          markerGeometryUrl: 'geographies/locality-markers.geojson',
          featureCount: prunedLocalities.features.length,
          markerFeatureCount: localityMarkers.features.length,
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

function validateConfiguration(elections, partyOverrides) {
  if (!Array.isArray(elections) || elections.length === 0) {
    throw new Error('Election configuration must be a non-empty array')
  }
  const ids = new Set()
  for (const election of elections) {
    if (!election.id || !election.number || !election.label?.en || !election.label?.he) {
      throw new Error('Every election needs an ID, number, and English/Hebrew labels')
    }
    if (ids.has(election.id)) {
      throw new Error(`Duplicate election ID: ${election.id}`)
    }
    ids.add(election.id)
  }
  if (
    partyOverrides?.schemaVersion !== 1 ||
    !partyOverrides.elections ||
    typeof partyOverrides.elections !== 'object' ||
    !partyOverrides.ignoredResultColumns ||
    typeof partyOverrides.ignoredResultColumns !== 'object'
  ) {
    throw new Error(
      'party-overrides.json must use schemaVersion 1 and contain elections and ignoredResultColumns objects',
    )
  }
}

await main()

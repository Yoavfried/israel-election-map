import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { AppCatalogSchema, ElectionResultsSchema } from './schemas'

const dataRoot = resolve(import.meta.dirname, '..', '..', 'public', 'data', 'v1')

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
    const featureIdsByMode = new Map<string, Set<string>>()

    for (const mode of catalog.geographyModes) {
      const geometry = (await readJson(resolve(dataRoot, mode.geometryUrl))) as {
        type: string
        features: Array<{ id?: string }>
      }
      expect(geometry.type).toBe('FeatureCollection')
      expect(geometry.features).toHaveLength(mode.featureCount)
      const ids = new Set(geometry.features.map((feature) => feature.id).filter(Boolean) as string[])
      expect(ids.size).toBe(geometry.features.length)
      featureIdsByMode.set(mode.id, ids)

      const markers = (await readJson(resolve(dataRoot, mode.markerGeometryUrl))) as {
        type: string
        features: Array<{
          id?: string
          properties?: { displayMode?: string }
          geometry?: { type?: string }
        }>
      }
      expect(markers.type).toBe('FeatureCollection')
      expect(markers.features).toHaveLength(mode.markerFeatureCount)
      expect(new Set(markers.features.map((feature) => feature.id)).size).toBe(markers.features.length)
      for (const marker of markers.features) {
        expect(ids.has(marker.id ?? '')).toBe(true)
        expect(marker.properties?.displayMode).toBe('marker')
        expect(marker.geometry?.type).toBe('Point')
      }
    }

    for (const election of catalog.elections) {
      for (const mode of catalog.geographyModes) {
        const payload = ElectionResultsSchema.parse(
          await readJson(resolve(dataRoot, election.resultUrls[mode.id])),
        )
        const geometryIds = featureIdsByMode.get(mode.id)
        expect(payload.electionId).toBe(election.id)
        expect(payload.geographyMode).toBe(mode.id)
        expect(new Set(payload.records.map((record) => record.id)).size).toBe(payload.records.length)
        for (const record of payload.records) {
          expect(geometryIds?.has(record.id), `${election.id}/${mode.id}/${record.id}`).toBe(true)
        }
      }
    }
  })
})

async function readJson(path: string): Promise<unknown> {
  return JSON.parse(await readFile(path, 'utf8'))
}

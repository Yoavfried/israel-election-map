const SAMPLE_URL = "./sample.json";
const APPROVED_ORIGIN = new URLSearchParams(window.location.search)
  .get("approvedOrigin")
  ?.replace(/\/$/, "") || "";

const CSV_FIELDS = [
  "geocode_key",
  "geocoding_unit_id",
  "geocoder_query",
  "sample_category",
  "geocoder",
  "geocoder_endpoint",
  "geocode_status",
  "geocode_confidence",
  "review_status",
  "longitude",
  "latitude",
  "x_2039",
  "y_2039",
  "coordinate_crs",
  "matched_text",
  "matched_type",
  "matched_score",
  "matched_id",
  "results_count",
  "raw_result_json",
  "raw_detail_json",
  "geocode_notes",
  "geocoded_at",
];

const SEARCH_ENDPOINT_LABEL = "govmap.search";
const POINT_RE = /POINT\s*\(\s*([0-9.+-]+)\s+([0-9.+-]+)\s*\)/i;

const state = {
  sample: [],
  results: [],
  running: false,
  stopRequested: false,
};

const els = {};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  for (const id of [
    "originText",
    "sampleBadge",
    "apiToken",
    "maxResults",
    "delayMs",
    "layers",
    "accurate",
    "runOne",
    "runAll",
    "stopRun",
    "downloadCsv",
    "dryRunCsv",
    "statusText",
    "progressBar",
    "summaryCounts",
    "sampleStats",
    "resultsBody",
  ]) {
    els[id] = document.getElementById(id);
  }

  renderOrigin();
  bindActions();
  await loadSample();
  renderGovMapStatus();
}

function bindActions() {
  els.runOne.addEventListener("click", () => runSample(1));
  els.runAll.addEventListener("click", () => runSample(state.sample.length));
  els.stopRun.addEventListener("click", () => {
    state.stopRequested = true;
    setStatus("Stopping after the current request returns.");
  });
  els.downloadCsv.addEventListener("click", () => downloadRows(state.results, "govmap_spike_results"));
  els.dryRunCsv.addEventListener("click", () => {
    const rows = state.sample.map((unit) => buildOutputRow(unit, "dry_run"));
    downloadRows(rows, "govmap_spike_dry_run");
  });
}

function renderOrigin() {
  const origin = window.location.origin;
  if (!APPROVED_ORIGIN) {
    els.originText.textContent = `Origin: ${origin}. Add ?approvedOrigin=https%3A%2F%2Fmaps.example.org to compare this page with a token's approved origin.`;
    return;
  }
  if (origin === APPROVED_ORIGIN) {
    els.originText.textContent = `Origin: ${origin}. This matches the GovMap domain request.`;
    return;
  }
  els.originText.textContent = `Origin: ${origin}. GovMap live calls are expected to work only from ${APPROVED_ORIGIN}.`;
}

async function loadSample() {
  try {
    const response = await fetch(SAMPLE_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    state.sample = payload.units || [];
    els.sampleBadge.textContent = `${state.sample.length} sample rows`;
    renderSampleStats(payload);
    setStatus("Sample loaded. Token is needed only for live GovMap calls.");
  } catch (error) {
    els.sampleBadge.textContent = "Sample failed";
    setStatus(`Could not load sample.json: ${error.message}`);
  }
}

function renderSampleStats(payload) {
  const stats = [
    ["Rows", payload.row_count || state.sample.length],
    ["Generated", payload.generated_at || ""],
    ["Source", payload.source || ""],
  ];
  const categories = new Map();
  for (const unit of state.sample) {
    for (const category of splitList(unit.sample_category)) {
      categories.set(category, (categories.get(category) || 0) + 1);
    }
  }
  for (const [category, count] of [...categories.entries()].sort()) {
    stats.push([category, count]);
  }

  els.sampleStats.replaceChildren(
    ...stats.map(([label, value]) => {
      const item = document.createElement("div");
      item.className = "stat";
      item.textContent = `${label}: ${value}`;
      return item;
    }),
  );
}

function renderGovMapStatus() {
  if (isGovMapReady()) {
    setStatus("GovMap script loaded. Ready for a token after approval.");
  } else {
    setStatus("Sample loaded. GovMap script has not exposed search yet; live calls may fail until it loads.");
  }
}

async function runSample(limit) {
  if (state.running) {
    return;
  }
  if (!state.sample.length) {
    setStatus("No sample rows are loaded.");
    return;
  }

  const token = els.apiToken.value.trim();
  if (!token) {
    setStatus("Paste the approved GovMap token before live calls.");
    return;
  }

  const govmapReady = await waitForGovMap();
  if (!govmapReady) {
    setStatus("GovMap search function is not available on this page.");
    return;
  }

  state.running = true;
  state.stopRequested = false;
  state.results = [];
  updateControls();
  renderResults();

  const rows = state.sample.slice(0, limit);
  els.progressBar.max = rows.length;
  els.progressBar.value = 0;

  for (let index = 0; index < rows.length; index += 1) {
    if (state.stopRequested) {
      break;
    }
    const unit = rows[index];
    setStatus(`Running ${index + 1} of ${rows.length}: ${unit.geocoder_query}`);
    const result = await runGovMapSearch(unit, token);
    state.results.push(result);
    els.progressBar.value = index + 1;
    renderResults();
    renderCounts();
    if (index < rows.length - 1) {
      await sleep(readPositiveInt(els.delayMs.value, 300));
    }
  }

  state.running = false;
  updateControls();
  setStatus(`Finished ${state.results.length} row${state.results.length === 1 ? "" : "s"}.`);
}

async function runGovMapSearch(unit, token) {
  try {
    const searchParams = {
      apiKey: token,
      searchText: unit.geocoder_query,
      language: "he",
      maxResults: readPositiveInt(els.maxResults.value, 3),
      isAccurate: els.accurate.checked,
    };
    const layers = splitList(els.layers.value);
    if (layers.length) {
      searchParams.layers = layers;
    }

    const searchResponse = await window.govmap.search(searchParams);
    const results = Array.isArray(searchResponse?.results) ? searchResponse.results : [];
    let detailResponse = {};
    if (results.length && typeof window.govmap.getSearchResultData === "function") {
      detailResponse = await window.govmap.getSearchResultData(results[0], token);
    }
    const status = results.length ? "matched" : "no_match";
    return buildOutputRow(unit, status, searchResponse, detailResponse);
  } catch (error) {
    return buildOutputRow(unit, "error", {}, {}, error?.message || String(error));
  }
}

function buildOutputRow(unit, initialStatus, searchResponse = {}, detailResponse = {}, error = "") {
  const results = Array.isArray(searchResponse?.results) ? searchResponse.results : [];
  const topResult = results[0] || {};
  const point = parsePoint(detailResponse.centroid || topResult.centroid || detailResponse.shape || topResult.shape);
  let status = initialStatus;
  if (status === "matched" && !point) {
    status = "matched_no_coordinates";
  }

  return {
    geocode_key: unit.geocoding_unit_id,
    geocoding_unit_id: unit.geocoding_unit_id,
    geocoder_query: unit.geocoder_query,
    sample_category: unit.sample_category || "",
    geocoder: "govmap_search_browser",
    geocoder_endpoint: SEARCH_ENDPOINT_LABEL,
    geocode_status: status,
    geocode_confidence: topResult.score ?? "",
    review_status: "needs_review",
    longitude: "",
    latitude: "",
    x_2039: point?.x ?? "",
    y_2039: point?.y ?? "",
    coordinate_crs: point ? "EPSG:2039" : "",
    matched_text: detailResponse.text || topResult.text || "",
    matched_type: detailResponse.type || topResult.type || "",
    matched_score: topResult.score ?? "",
    matched_id: topResult.id || "",
    results_count: searchResponse?.resultsCount ?? results.length,
    raw_result_json: stableJson(topResult),
    raw_detail_json: stableJson(detailResponse),
    geocode_notes: error,
    geocoded_at: new Date().toISOString(),
  };
}

function parsePoint(value) {
  const match = String(value || "").match(POINT_RE);
  if (!match) {
    return null;
  }
  return { x: Number(match[1]), y: Number(match[2]) };
}

function renderResults() {
  if (!state.results.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 8;
    cell.className = "empty";
    cell.textContent = "No results yet.";
    row.appendChild(cell);
    els.resultsBody.replaceChildren(row);
    return;
  }

  els.resultsBody.replaceChildren(
    ...state.results.map((result) => {
      const row = document.createElement("tr");
      for (const value of [
        result.geocoder_query,
        result.sample_category,
        result.geocode_status,
        result.matched_text,
        result.matched_score,
        result.x_2039,
        result.y_2039,
        result.geocode_notes,
      ]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        if (value === result.geocode_status) {
          cell.className = `status-${result.geocode_status}`;
        }
        row.appendChild(cell);
      }
      return row;
    }),
  );
}

function renderCounts() {
  const counts = new Map();
  for (const row of state.results) {
    counts.set(row.geocode_status, (counts.get(row.geocode_status) || 0) + 1);
  }
  els.summaryCounts.replaceChildren(
    ...[...counts.entries()].sort().map(([status, count]) => {
      const item = document.createElement("div");
      item.className = "count";
      item.textContent = `${status}: ${count}`;
      return item;
    }),
  );
}

function updateControls() {
  els.runOne.disabled = state.running;
  els.runAll.disabled = state.running;
  els.stopRun.disabled = !state.running;
  els.downloadCsv.disabled = state.running || !state.results.length;
  els.dryRunCsv.disabled = state.running || !state.sample.length;
}

function downloadRows(rows, basename) {
  if (!rows.length) {
    return;
  }
  const csv = toCsv(rows);
  const blob = new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${basename}_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  URL.revokeObjectURL(link.href);
  link.remove();
}

function toCsv(rows) {
  const lines = [CSV_FIELDS.join(",")];
  for (const row of rows) {
    lines.push(CSV_FIELDS.map((field) => csvEscape(row[field] ?? "")).join(","));
  }
  return `${lines.join("\r\n")}\r\n`;
}

function csvEscape(value) {
  const text = String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function setStatus(message) {
  els.statusText.textContent = message;
}

async function waitForGovMap(timeoutMs = 8000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (isGovMapReady()) {
      return true;
    }
    await sleep(100);
  }
  return false;
}

function isGovMapReady() {
  return typeof window.govmap === "object" && typeof window.govmap.search === "function";
}

function splitList(value) {
  return String(value || "")
    .split(/[|,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function readPositiveInt(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

function stableJson(value) {
  return JSON.stringify(value || {});
}

function sleep(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

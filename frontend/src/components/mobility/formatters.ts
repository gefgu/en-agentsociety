// Tooltip / axis-label formatters ported from skmob-vis `static/formatter_*.js`.
//
// skmob-vis keeps these formatters out of the ECharts option JSON (they are JS
// functions injected client-side, keyed by chart type). To render the option
// natively we re-attach them here before `setOption`. `meta` is the option's
// `_meta` block.

/* eslint-disable @typescript-eslint/no-explicit-any */

function formatPercent(value: any): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return "";
  return n.toFixed(2) + "%";
}

function ensure(obj: any, key: string): any {
  if (!obj[key]) obj[key] = {};
  return obj[key];
}

function heatmapAxisData(axis: any): any[] {
  if (Array.isArray(axis)) axis = axis[0] || {};
  return (axis && axis.data) || [];
}

function ecdfAt(data: any[], x: number): number {
  let lo = 0,
    hi = data.length - 1,
    last = 0;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (data[mid][0] <= x) {
      last = data[mid][1];
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return last;
}

function formatLawNumber(value: any): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  const m = Math.abs(n);
  if ((m > 0 && m < 0.001) || m >= 10000) return n.toExponential(3);
  return parseFloat(n.toPrecision(4)).toString();
}

function applyEcdf(option: any, meta: any) {
  const xUnit = meta.xUnit || "";
  ensure(option.xAxis, "axisLabel").formatter = (v: number) =>
    Number.isInteger(v) ? String(v) : parseFloat(v.toFixed(2)).toString();
  ensure(option.yAxis, "axisLabel").formatter = (v: number) =>
    v === 0 || v === 1 ? String(v) : parseFloat(v.toFixed(1)).toString();
  ensure(option, "tooltip").formatter = (params: any[]) => {
    if (!params.length) return "";
    const x = Number(params[0].axisValue);
    const xStr = Number.isInteger(x) ? String(x) : x.toFixed(2);
    const xHeader = xUnit ? "X = " + xStr + " " + xUnit.toUpperCase() : "X = " + xStr;
    let out =
      '<div style="font-family:\'JetBrains Mono\',monospace;font-size:12px;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:6px;">' +
      xHeader +
      "</div>";
    (option.series || []).forEach((s: any) => {
      const fy = ecdfAt(s.data, x);
      const ls = s.lineStyle || {};
      const borderStyle = Array.isArray(ls.type) ? "dashed" : "solid";
      const color = ls.color || "#000";
      out += '<div style="display:flex;align-items:center;gap:10px;padding:2px 0;">';
      out +=
        '<span style="display:inline-block;width:20px;border-top:2.5px ' +
        borderStyle +
        " " +
        color +
        ';flex-shrink:0;"></span>';
      out +=
        '<span style="flex:1;font-family:\'DM Sans\',sans-serif;font-size:14px;">' +
        s.name +
        "</span>";
      out +=
        '<span style="font-family:\'JetBrains Mono\',monospace;font-size:14px;font-weight:500;font-variant-numeric:tabular-nums;">' +
        fy.toFixed(3) +
        "</span>";
      out += "</div>";
    });
    return out;
  };
}

function applyMobilityLaw(option: any) {
  ensure(option.xAxis, "axisLabel").formatter = formatLawNumber;
  ensure(option.yAxis, "axisLabel").formatter = formatLawNumber;
  ensure(option, "tooltip").formatter = (params: any) => {
    const value = params.value || [];
    let out =
      '<div style="font-family:\'DM Sans\',sans-serif;font-size:14px;">' +
      params.seriesName +
      "</div>";
    out +=
      '<div style="font-family:\'JetBrains Mono\',monospace;font-size:13px;margin-top:4px;">';
    out += "x = " + formatLawNumber(value[0]) + "<br/>y = " + formatLawNumber(value[1]) + "</div>";
    const series = (option.series || [])[params.seriesIndex] || {};
    const fp = series.fitParameters;
    if (fp) {
      const text = Object.keys(fp)
        .map((k) => k + " = " + formatLawNumber(fp[k]))
        .join(", ");
      if (text)
        out +=
          '<div style="font-family:\'JetBrains Mono\',monospace;font-size:12px;margin-top:6px;">' +
          text +
          "</div>";
    }
    return out;
  };
}

function applyVisitPurpose(option: any) {
  ensure(option, "tooltip").formatter = (params: any[]) => {
    if (!Array.isArray(params) || !params.length) return "";
    let out = params[0].name;
    params.forEach((param: any) => {
      const data = param.data || {};
      out += "<br/>" + param.marker + param.seriesName + ": " + formatPercent(data.value);
      if (data.count !== undefined && data.count !== null) out += " (" + data.count + " visits)";
    });
    return out;
  };
}

function applyDifferenceHeatmap(option: any, meta: any) {
  const formatDifference = (value: any) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return "";
    return (n > 0 ? "+" : "") + n.toFixed(2) + " pp";
  };
  ensure(option, "tooltip").formatter = (params: any) => {
    params = Array.isArray(params) ? params[0] : params;
    if (!params || !params.value) return "";
    const value = params.value;
    const xLabels = heatmapAxisData(option.xAxis);
    const yLabels = heatmapAxisData(option.yAxis);
    const xLabel = xLabels[value[0]] || String(value[0]);
    const yLabel = yLabels[value[1]] || String(value[1]);
    const labels = meta.differenceLabels || ["first", "second"];
    const direction = labels[1] + " - " + labels[0];
    const difference = formatDifference(value[2]);
    if (meta.chartType === "transition_difference")
      return yLabel + " -> " + xLabel + "<br/>" + direction + ": " + difference;
    return yLabel + "<br/>" + xLabel + "<br/>" + direction + ": " + difference;
  };
  (option.series || []).forEach((series: any) => {
    if (series.label) series.label.formatter = (p: any) => formatDifference(p.value[2]);
  });
}

function applyMotif(option: any, meta: any) {
  const motifLabelKeys = meta.motifLabelKeys || {};
  ensure(option.xAxis, "axisLabel").formatter = (value: any) => {
    const styleKey = motifLabelKeys[value];
    return styleKey ? "{" + styleKey + "| }" : value;
  };
  ensure(option, "tooltip").formatter = (params: any) => {
    const value = params.value || [];
    return (
      "Literature motif: " +
      value[2] +
      "<br/>Packed motif ID: " +
      value[3] +
      "<br/>Hex ID: " +
      value[4] +
      "<br/>" +
      params.seriesName +
      ": " +
      formatPercent(value[1]) +
      "<br/>Count: " +
      value[5]
    );
  };
}

/**
 * Attach the appropriate tooltip/axis formatters to an ECharts option in place,
 * based on the chart type produced by skmob-vis.
 */
export function applyFormatters(option: any, chartType: string | undefined, meta: any): void {
  try {
    switch (chartType) {
      case "ecdf":
        applyEcdf(option, meta);
        break;
      case "mobility_law":
        applyMobilityLaw(option);
        break;
      case "visit_purpose_comparison":
        applyVisitPurpose(option);
        break;
      case "difference_heatmap":
        applyDifferenceHeatmap(option, meta);
        break;
      case "motif":
        applyMotif(option, meta);
        break;
      default:
        break;
    }
  } catch {
    // Formatting is best-effort; ECharts default tooltips remain usable.
  }
}

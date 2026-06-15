import React, { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Col,
  Row,
  Select,
  Upload,
  Spin,
  Alert,
  Segmented,
  message,
} from "antd";
import { UploadOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { fetchCustom } from "../../components/fetch";
import { Experiment } from "../../components/type";
import MetricChart from "../../components/mobility/MetricChart";
import StvdMap from "../../components/mobility/StvdMap";
import { PALETTE, FONT_SERIF, FONT_SANS, FONT_MONO } from "../../components/mobility/theme";

/* eslint-disable @typescript-eslint/no-explicit-any */

type SourceType = "experiment" | "file";
interface SourceState {
  type: SourceType;
  expId?: string;
  expName?: string;
  file?: File;
  duckdb?: File;
}

const EMPTY_SOURCE: SourceState = { type: "experiment" };

// Display order + section grouping for the chart grid.
const DISTRIBUTION_CHARTS: [string, string][] = [
  ["jump_ecdf", "Jump length ECDF"],
  ["rog_ecdf", "Radius of gyration ECDF"],
  ["visits_ecdf", "Visits per user ECDF"],
  ["dwell_ecdf", "Dwell time ECDF"],
];
const LAW_CHARTS: [string, string][] = [
  ["powerlaw_jump", "Travel-distance law"],
  ["powerlaw_rog", "Radius-of-gyration law"],
  ["lognormal", "Daily locations (log-normal)"],
  ["distance_frequency", "Distance–frequency law"],
];
const ACTIVITY_CHARTS: [string, string][] = [
  ["purpose", "Visit purpose"],
  ["transition", "Activity transitions"],
  ["daily_activity", "Daily activity profile"],
  ["motif", "Daily motifs"],
];

const sectionStyle: React.CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 11,
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: "0.1em",
  color: PALETTE.muted,
  margin: "28px 0 4px",
};

const ChartsPage: React.FC = () => {
  const { t } = useTranslation();
  const { exp_id } = useParams<{ exp_id?: string }>();

  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [clickhouse, setClickhouse] = useState<boolean>(true);
  const [sourceA, setSourceA] = useState<SourceState>({ type: "experiment", expId: exp_id });
  const [sourceB, setSourceB] = useState<SourceState>({ ...EMPTY_SOURCE });
  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState<any>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    (async () => {
      try {
        const res = await fetchCustom("/api/experiments");
        if (res.ok) {
          const list: Experiment[] = (await res.json()).data || [];
          setExperiments(list);
          // Resolve the name for the pre-filled experiment from the route param.
          if (exp_id) {
            const match = list.find((e) => e.id === exp_id);
            if (match) setSourceA((prev) => ({ ...prev, expName: match.name }));
          }
        }
      } catch {
        /* non-fatal */
      }
      try {
        const res = await fetchCustom("/api/mobility/datasource");
        if (res.ok) setClickhouse(!!(await res.json()).data?.clickhouse);
      } catch {
        /* non-fatal */
      }
    })();
  }, []);

  const expOptions = useMemo(
    () => experiments.map((e) => ({ label: `${e.name} (${e.id})`, value: e.id })),
    [experiments],
  );

  const appendSource = (fd: FormData, prefix: string, s: SourceState) => {
    fd.append(`${prefix}_type`, s.type);
    if (s.type === "experiment") {
      fd.append(`${prefix}_exp_id`, s.expId || "");
      if (s.expName) fd.append(`${prefix}_label`, s.expName);
      if (!clickhouse && s.duckdb) fd.append(`${prefix}_duckdb`, s.duckdb);
    } else if (s.file) {
      fd.append(`${prefix}_file`, s.file);
    }
  };

  const valid = (s: SourceState) =>
    s.type === "experiment" ? !!s.expId && (clickhouse || !!s.duckdb) : !!s.file;

  const onCompare = async () => {
    if (!valid(sourceA)) {
      message.warning(t("charts.select_source"));
      return;
    }
    setLoading(true);
    setError("");
    setPayload(null);
    try {
      const fd = new FormData();
      appendSource(fd, "a", sourceA);
      if (valid(sourceB)) appendSource(fd, "b", sourceB);
      const res = await fetchCustom("/api/mobility/compare", { method: "POST", body: fd });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || (await res.statusText));
      setPayload(body.data);
    } catch (err: any) {
      setError(String(err?.message || err));
      message.error(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  };

  const renderSlot = (slot: string, s: SourceState, set: (s: SourceState) => void) => (
    <Card
      size="small"
      title={t("charts.source", { slot })}
      style={{ background: PALETTE.panel, borderColor: PALETTE.border }}
    >
      <Segmented
        value={s.type}
        onChange={(v) => set({ type: v as SourceType })}
        options={[
          { label: t("charts.simulation"), value: "experiment" },
          { label: t("charts.file"), value: "file" },
        ]}
        style={{ marginBottom: 12 }}
      />
      {s.type === "experiment" ? (
        <>
          <Select
            showSearch
            allowClear
            placeholder={t("charts.select_experiment")}
            style={{ width: "100%" }}
            value={s.expId}
            options={expOptions}
            optionFilterProp="label"
            onChange={(v) => {
              const name = experiments.find((e) => e.id === v)?.name;
              set({ ...s, expId: v, expName: name });
            }}
          />
          {!clickhouse && s.expId && (
            <Upload
              maxCount={1}
              beforeUpload={(file) => {
                set({ ...s, duckdb: file });
                return false;
              }}
              onRemove={() => set({ ...s, duckdb: undefined })}
            >
              <Button size="small" icon={<UploadOutlined />} style={{ marginTop: 8 }}>
                {t("charts.upload_duckdb")}
              </Button>
            </Upload>
          )}
        </>
      ) : (
        <Upload
          maxCount={1}
          beforeUpload={(file) => {
            set({ ...s, file });
            return false;
          }}
          onRemove={() => set({ ...s, file: undefined })}
        >
          <Button icon={<UploadOutlined />}>{t("charts.upload_trajectory")}</Button>
        </Upload>
      )}
    </Card>
  );

  const metrics = payload?.metrics;
  const charts = payload?.charts || {};

  const renderChart = (key: string, title: string) => {
    const chart = charts[key];
    if (!chart) return null;
    return (
      <Col md={24} xl={12} key={key}>
        <Card
          size="small"
          title={title}
          style={{ background: PALETTE.panel, borderColor: PALETTE.border }}
          styles={{ header: { fontFamily: FONT_SANS } }}
        >
          <MetricChart option={chart.option} chartType={chart.chartType} />
          {chart.parameters && (
            <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: PALETTE.muted, padding: "6px 4px 0" }}>
              {chart.formula && <div style={{ marginBottom: 4 }}>{chart.formula}</div>}
              {chart.parameters.map((p: any) => (
                <div key={p.label}>
                  {p.label}:{" "}
                  {Object.entries(p.values)
                    .map(([k, v]) => `${k}=${v}`)
                    .join(", ")}
                </div>
              ))}
            </div>
          )}
        </Card>
      </Col>
    );
  };

  const hasAny = (entries: [string, string][]) => entries.some(([k]) => charts[k]);

  const metricTable = (title: string, rows: any[], cols: [string, string][]) =>
    rows && rows.length ? (
      <div style={{ minWidth: 240 }}>
        <h3 style={sectionStyle}>{title}</h3>
        <table style={{ borderCollapse: "collapse", fontFamily: FONT_MONO, fontSize: 13 }}>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {cols.map(([field], j) => (
                  <td key={j} style={{ padding: "3px 20px 3px 0" }}>
                    {field === "value" ? r.value : field === "resolution" ? `H3 ${r.resolution}` : r[field]}
                    {field === "value" && r.unit ? ` ${r.unit}` : ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : null;

  return (
    <div style={{ padding: 24, background: PALETTE.bg, minHeight: "100%", color: PALETTE.axis }}>
      <h2 style={{ fontFamily: FONT_SERIF, fontSize: 32, margin: 0 }}>{t("charts.title")}</h2>
      <p style={{ color: PALETTE.muted, fontFamily: FONT_SANS, marginTop: 4 }}>{t("charts.subtitle")}</p>

      <Row gutter={[16, 16]} style={{ marginTop: 8 }} align="middle">
        <Col md={24} xl={11}>{renderSlot("A", sourceA, setSourceA)}</Col>
        <Col md={24} xl={11}>{renderSlot("B", sourceB, setSourceB)}</Col>
        <Col md={24} xl={2}>
          <Button type="primary" loading={loading} onClick={onCompare} style={{ width: "100%" }}>
            {valid(sourceB) ? t("charts.compare") : t("charts.analyse")}
          </Button>
        </Col>
      </Row>

      {error && <Alert type="error" message={error} style={{ marginTop: 16 }} showIcon />}

      {loading && (
        <div style={{ textAlign: "center", padding: 64 }}>
          <Spin tip={t("charts.comparing")} />
        </div>
      )}

      {payload && (
        <div style={{ marginTop: 16 }}>
          <h2 style={{ fontFamily: FONT_SERIF, fontSize: 22 }}>
            {payload.labels?.length === 1
              ? payload.labels[0]
              : <>{payload.labels?.[0]} &nbsp;vs&nbsp; {payload.labels?.[1]}</>}
          </h2>

          {(metrics?.wasserstein?.length > 0 || metrics?.jensen_shannon?.length > 0 || metrics?.cpc?.length > 0) && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 48 }}>
              {metricTable(t("charts.metrics_wasserstein"), metrics?.wasserstein, [["name", ""], ["value", ""]])}
              {metricTable(t("charts.metrics_jsd"), metrics?.jensen_shannon, [["name", ""], ["value", ""]])}
              {metricTable(t("charts.metrics_cpc"), metrics?.cpc, [["resolution", ""], ["value", ""]])}
            </div>
          )}

          {hasAny(DISTRIBUTION_CHARTS) && <h3 style={sectionStyle}>{t("charts.distributions")}</h3>}
          <Row gutter={[16, 16]}>{DISTRIBUTION_CHARTS.map(([k, title]) => renderChart(k, title))}</Row>

          {hasAny(LAW_CHARTS) && <h3 style={sectionStyle}>{t("charts.mobility_laws")}</h3>}
          <Row gutter={[16, 16]}>{LAW_CHARTS.map(([k, title]) => renderChart(k, title))}</Row>

          {hasAny(ACTIVITY_CHARTS) && <h3 style={sectionStyle}>{t("charts.activity")}</h3>}
          <Row gutter={[16, 16]}>{ACTIVITY_CHARTS.map(([k, title]) => renderChart(k, title))}</Row>

          {charts.stvd && (
            <>
              <h3 style={sectionStyle}>{t("charts.stvd")}</h3>
              <Card size="small" style={{ background: PALETTE.panel, borderColor: PALETTE.border }}>
                <StvdMap stvd={charts.stvd} />
              </Card>
            </>
          )}

          {payload.warnings?.length > 0 && (
            <Alert
              type="warning"
              style={{ marginTop: 24 }}
              message={t("charts.warnings")}
              description={
                <ul style={{ margin: 0, fontFamily: FONT_MONO, fontSize: 12 }}>
                  {payload.warnings.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              }
            />
          )}
        </div>
      )}
    </div>
  );
};

export default ChartsPage;

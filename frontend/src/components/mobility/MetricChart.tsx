import React, { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { applyFormatters } from "./formatters";
import { PALETTE } from "./theme";

/**
 * Renders a skmob-vis ECharts option (returned as JSON by the backend) natively.
 * Re-attaches the per-chart-type tooltip/axis formatters that skmob-vis would
 * otherwise inject as client-side JS.
 */
const MetricChart: React.FC<{
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  option: any;
  chartType?: string;
  height?: string;
}> = ({ option, chartType, height = "420px" }) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !option) return;
    const chart = echarts.init(ref.current);

    // Deep clone so we can mutate/strip _meta without touching the source.
    const opt = JSON.parse(JSON.stringify(option));
    const meta = opt._meta || {};
    delete opt._meta;
    if (opt.backgroundColor === undefined) opt.backgroundColor = PALETTE.bg;
    applyFormatters(opt, chartType, meta);
    chart.setOption(opt);

    const resize = () => chart.resize();
    const ro = new ResizeObserver(resize);
    ro.observe(ref.current);
    window.addEventListener("resize", resize);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [option, chartType]);

  return <div ref={ref} style={{ width: "100%", height }} />;
};

export default MetricChart;

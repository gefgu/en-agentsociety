import React, { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { applyFormatters } from "./formatters";
import { getPalette } from "./theme";
import { useTheme } from "../../context/ThemeContext";

const MetricChart: React.FC<{
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  option: any;
  chartType?: string;
  height?: string;
}> = ({ option, chartType, height = "420px" }) => {
  const ref = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  useEffect(() => {
    if (!ref.current || !option) return;
    const chart = echarts.init(ref.current);

    const palette = getPalette(theme);
    const opt = JSON.parse(JSON.stringify(option));
    const meta = opt._meta || {};
    delete opt._meta;
    if (opt.backgroundColor === undefined) opt.backgroundColor = palette.bg;
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
  }, [option, chartType, theme]);

  return <div ref={ref} style={{ width: "100%", height }} />;
};

export default MetricChart;

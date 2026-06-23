import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { fetchCustom } from './fetch';
import message from 'antd/lib/message';
import { useTheme } from '../context/ThemeContext';

type DailyActivityResponse = {
  data: {
    time_labels: string[];
    series: Record<string, number[]>;
  }
}

const DailyActivityChart = ({
  exp_id,
  exp_name,
  width,
  height
}: {
  exp_id: string,
  exp_name: string,
  width: string,
  height: string
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartData, setChartData] = useState<DailyActivityResponse['data'] | null>(null);
  const { theme } = useTheme();

  const fetchVisitData = async (experimentId: string) => {
    try {
      const res = await fetchCustom(`/api/visits/daily-activity?exp_id=${experimentId}&step_minutes=10`);
      if (res.ok) {
        const response = await res.json();
        setChartData(response.data);
      } else {
        throw new Error(await res.text());
      }
    } catch (err) {
      console.error('Failed to fetch daily activity:', err);
      message.error('Failed to fetch daily activity: ' + err);
    }
  }

  useEffect(() => {
    if (exp_id) {
      fetchVisitData(exp_id);
    }
  }, [exp_id]);

  useEffect(() => {
    if (chartRef.current && chartData) {
      const myChart = echarts.init(chartRef.current);
      const textColor = theme === 'dark' ? '#c9d8ee' : '#333333';

      const colorMap: Record<string, string> = {
        'HOME':     '#d95f02',
        'WORK':     '#e6ab02',
        'LEISURE':  '#7570b3',
        'STUDIES':  '#66a61e',
        'PURCHASE': '#e7298a',
        'HEALTH':   '#1b9e77',
        'UNKNOWN':  '#d3d3d3'
      };

      const purposes = Object.keys(chartData.series);

      const option = {
        backgroundColor: 'transparent',
        title: {
          text: 'Daily Activity Distribution',
          left: 'center',
          textStyle: { fontWeight: 'bold', fontSize: 32, color: textColor }
        },
        toolbox: {
          show: true,
          feature: {
            saveAsImage: {
              show: true,
              title: 'Save',
              type: 'png',
              name: `${exp_name || exp_id}_daily_activity`,
              pixelRatio: 2
            }
          },
          right: 20,
          top: 20
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'line',
            label: { backgroundColor: '#6a7985' }
          },
          formatter: (params: any) => {
            let tooltip = `<b>${params[0].axisValue}</b><br/>`;
            params.forEach((item: any) => {
              if (item.value > 0) {
                tooltip += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${item.color};"></span>`;
                tooltip += `${item.seriesName}: <b>${item.value}%</b><br/>`;
              }
            });
            return tooltip;
          }
        },
        legend: {
          data: purposes,
          bottom: -5,
          icon: 'circle',
          itemGap: 24,
          textStyle: { fontSize: 16, color: textColor }
        },
        grid: {
          left: '5%',
          right: '4%',
          bottom: '10%',
          containLabel: true
        },
        xAxis: [
          {
            type: 'category',
            boundaryGap: false,
            data: chartData.time_labels,
            axisLabel: {
              interval: 17,
              fontWeight: 'bold',
              fontSize: 20,
              color: textColor
            },
            axisLine: { lineStyle: { color: textColor } }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: '% of Trips',
            nameLocation: 'middle',
            nameGap: 60,
            max: 100,
            axisLabel: { formatter: '{value}%', fontSize: 20, color: textColor },
            nameTextStyle: { fontSize: 24, color: textColor },
            splitLine: { lineStyle: { color: theme === 'dark' ? 'rgba(255,255,255,0.07)' : '#e0e0e0' } }
          }
        ],
        series: purposes.map(purpose => ({
          name: purpose,
          type: 'line',
          stack: 'Total',
          smooth: true,
          showSymbol: false,
          areaStyle: { opacity: 1 },
          lineStyle: { width: 0 },
          itemStyle: { color: colorMap[purpose] || '#999' },
          emphasis: { focus: 'series' },
          data: chartData.series[purpose]
        }))
      };

      myChart.setOption(option);

      const handleResize = () => myChart.resize();
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        myChart.dispose();
      };
    }
  }, [chartData, theme]);

  return (
    <div
      ref={chartRef}
      style={{
        width: width,
        height: height,
        background: 'transparent',
        borderRadius: '8px',
        padding: '10px',
        margin: '24px'
      }}
    />
  );
};

export default DailyActivityChart;

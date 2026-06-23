import * as echarts from 'echarts';
import React, { useState, useEffect, useRef } from 'react';
import { fetchCustom } from './fetch';
import message from 'antd/lib/message';
import { useTheme } from '../context/ThemeContext';

type VisitPurposeDistribution = {
  purpose: string;
  proportion: number;
  count: number;
}

type VisitDistributionResponse = {
  data: {
    distributions: VisitPurposeDistribution[];
    total_visits: number;
  }
}

const VisitDistributionBarChart = ({
  exp_id, exp_name, width, height,
}: {
  exp_id: string,
  exp_name: string,
  width: string,
  height: string,
}) => {
  const chartRef = useRef(null);
  const heightOffset = parseFloat(height.replace('px', '')) * 0.2;
  const { theme } = useTheme();

  const [visit_data, setVisitData] = useState<VisitDistributionResponse>();

  const fetchVisitData = async (experimentId: string) => {
    try {
      const res = await fetchCustom(`/api/visits/purpose-distributions?exp_id=${experimentId}`);
      if (res.ok) {
        const data = await res.json();
        setVisitData(data);
      } else {
        throw new Error(await res.text());
      }
    } catch (err) {
      console.error('Failed to fetch visit data:', err);
      message.error('Failed to fetch visit data: ' + err);
      return null;
    }
  }

  useEffect(() => {
    if (exp_id) {
      fetchVisitData(exp_id);
    }
  }, [exp_id]);

  useEffect(() => {
    if (chartRef.current) {
      const myChart = echarts.init(chartRef.current);
      const data = visit_data?.data.distributions || [];
      const totalTrips = visit_data?.data.total_visits || 0;
      const textColor = theme === 'dark' ? '#c9d8ee' : '#333333';
      const boxFill = theme === 'dark' ? '#0c1728' : '#ffffff';
      const boxStroke = theme === 'dark' ? 'rgba(255,255,255,0.2)' : '#333333';
      const splitLineColor = theme === 'dark' ? 'rgba(255,255,255,0.07)' : '#e0e0e0';

      const option = {
        backgroundColor: 'transparent',
        title: {
          text: `Visit Purpose Distribution`,
          left: 'center',
          textStyle: { fontSize: 32, fontWeight: 'bold', color: textColor }
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const d = params[0].data;
            return `${params[0].name}<br/>Count: <b>${d.count}</b><br/>Percentage: <b>${d.value}%</b>`;
          }
        },
        graphic: [
          {
            type: 'group',
            right: 20,
            top: heightOffset,
            children: [
              {
                type: 'rect',
                shape: { width: 100, height: 40, r: 5 },
                style: { fill: boxFill, stroke: boxStroke, lineWidth: 1 }
              },
              {
                type: 'text',
                position: [50, 20],
                style: {
                  text: `N = ${totalTrips}`,
                  textAlign: 'center',
                  textVerticalAlign: 'middle',
                  fontSize: 16,
                  fontWeight: 'bold',
                  fill: textColor
                }
              }
            ]
          }
        ],
        grid: {
          left: '5%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.map(item => item.purpose),
          axisLabel: { fontWeight: 'bold', fontSize: 14, interval: 0, color: textColor },
          axisTick: { alignWithLabel: true },
          axisLine: { lineStyle: { color: textColor } }
        },
        yAxis: {
          type: 'value',
          name: '% of Trips',
          nameLocation: 'middle',
          nameGap: 50,
          nameTextStyle: { fontSize: 32, color: textColor },
          max: 100,
          axisLabel: { fontSize: 28, color: textColor },
          splitLine: { lineStyle: { color: splitLineColor } }
        },
        toolbox: {
          show: true,
          feature: {
            saveAsImage: {
              show: true,
              title: 'Save as Image',
              type: 'png',
              name: `visit_distribution_${exp_name || exp_id}`,
              pixelRatio: 2
            }
          },
          right: 20,
          top: 20
        },
        series: [
          {
            name: 'Purpose',
            type: 'bar',
            data: data.map(item => ({
              value: parseFloat((item.proportion * 100).toFixed(2)),
              count: item.count,
              proportion: item.proportion
            })),
            barWidth: '60%',
            itemStyle: {
              color: (params) => {
                const colorList = ['#d95f02', '#e6ab02', '#e7298a', '#7570b3', '#1b9e77', '#66a61e', '#90ed7d'];
                return colorList[params.dataIndex % colorList.length];
              }
            }
          }
        ]
      };

      myChart.setOption(option);

      const handleResize = () => myChart.resize();
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }
  }, [visit_data, theme]);

  return (
    <div
      ref={chartRef}
      style={{
        width: width,
        height: height,
        background: 'transparent',
        margin: '24px',
      }}
    />
  )
}

export default VisitDistributionBarChart;

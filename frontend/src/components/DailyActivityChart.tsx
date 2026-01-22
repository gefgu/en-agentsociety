import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { fetchCustom } from './fetch';
import message from 'antd/lib/message';

// 1. Define types matching the NEW backend response
type DailyActivityResponse = {
  data: {
    time_labels: string[];            // ["00:00", "00:10", ...]
    series: Record<string, number[]>; // { "HOME": [50.5, ...], "WORK": [...] }
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

  // 2. Fetch data (simplified)
  const fetchVisitData = async (experimentId: string) => {
    try {
      // Note: Endpoint changed to match your backend route name if necessary
      // You named it '/visits/daily-activity' in Python
      const res = await fetchCustom(`/api/visits/daily-activity?exp_id=${experimentId}&step_minutes=10`);

      if (res.ok) {
        const response = await res.json();
        console.log('Fetched daily activity:', response);
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

      // --- CONFIGURATION ---
      const colorMap: Record<string, string> = {
        'HOME': '#d95f02',      // Orange
        'WORK': '#e6ab02',      // Mustard
        'LEISURE': '#7570b3',   // Purple
        'STUDIES': '#66a61e',   // Green
        'PURCHASE': '#e7298a',  // Pink
        'HEALTH': '#1b9e77',    // Teal
        'UNKNOWN': '#d3d3d3'    // Grey
      };

      // Get keys (purposes) from the dictionary
      const purposes = Object.keys(chartData.series);

      const option = {
        title: {
          text: 'Daily Activity Distribution',
          left: 'center',
          textStyle: { fontWeight: 'bold', fontSize: 32, color: '#333' }
        },
        // ADDED: Save feature with default naming
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
          textStyle: { fontSize: 16 } // Slightly smaller to fit if many categories
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
            data: chartData.time_labels, // Use backend labels directly
            axisLabel: {
              interval: 17, // Show roughly every 3 hours (18 steps * 10min = 180min)
              fontWeight: 'bold',
              fontSize: 20
            }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: '% of Trips',
            nameLocation: 'middle',
            nameGap: 60,
            max: 100,
            axisLabel: { formatter: '{value}%', fontSize: 20 },
            nameTextStyle: {
              fontSize: 24,
              color: '#333'
            },
          }
        ],
        series: purposes.map(purpose => ({
          name: purpose,
          type: 'line',
          stack: 'Total', // Enables the stacked area effect
          smooth: true,
          showSymbol: false,
          areaStyle: { opacity: 1 },
          lineStyle: { width: 0 },
          itemStyle: {
            color: colorMap[purpose] || '#999'
          },
          emphasis: { focus: 'series' },
          data: chartData.series[purpose] // Use backend data directly
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
  }, [chartData]); // Re-render when data arrives

  return (
    <div
      ref={chartRef}
      style={{
        width: width,
        height: height,
        background: '#fff',
        borderRadius: '8px',
        padding: '10px',
        margin: '24px' // Consistent margin
      }}
    />
  );
};

export default DailyActivityChart;
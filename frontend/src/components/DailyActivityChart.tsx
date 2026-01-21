import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

// Helper to format minutes into HH:mm
const formatTime = (minutes: number) => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
};

const DailyActivityChart = ({ visit_data, width, height }: { visit_data: any[], width: string, height: string }) => {
  const chartRef = useRef(null);

  useEffect(() => {
    if (chartRef.current && visit_data.length > 0) {
      const myChart = echarts.init(chartRef.current);

      // --- 1. CONFIGURATION ---
      // Time granularity: 10 minutes = 144 data points per day
      const STEP_MINUTES = 10;
      const totalSteps = (24 * 60) / STEP_MINUTES;

      // Define specific colors to match your reference image
      const colorMap: Record<string, string> = {
        'HOME': '#d95f02',      // Orange
        'WORK': '#e6ab02',      // Deep Sky Blue (Cyan-ish)
        'LEISURE': '#7570b3',   // Lawn Green
        'STUDIES': '#66a61e',   // Medium Purple
        'PURCHASE': '#e7298a',  // Deep Pink
        'HEALTH': '#1b9e77',    // Gold/Yellow
        'UNKNOWN': '#d3d3d3'    // Grey
      };

      // Get all unique purposes from data to ensure we create series for all of them
      const allPurposes = Array.from(new Set(visit_data.map(v => v.purpose || 'UNKNOWN')));

      // --- 2. DATA PROCESSING ---

      // Initialize buckets for every time step
      // timerSeries[stepIndex] = { HOME: 0, WORK: 0, ... }
      const timeSeries = Array.from({ length: totalSteps }, () => {
        const counts: Record<string, number> = {};
        allPurposes.forEach(p => counts[p] = 0);
        return counts;
      });

      // Populate buckets based on data intervals
      visit_data.forEach(trip => {
        const start = new Date(trip.start_timestamp);
        const end = new Date(trip.end_timestamp);
        const purpose = trip.purpose || 'UNKNOWN';

        // Convert timestamps to minutes-from-midnight (0 - 1439)
        const startMinutes = start.getHours() * 60 + start.getMinutes();
        const endMinutes = end.getHours() * 60 + end.getMinutes();

        // Calculate which steps this trip covers
        let startIndex = Math.floor(startMinutes / STEP_MINUTES);
        let endIndex = Math.floor(endMinutes / STEP_MINUTES);

        // Handle day wrap-around (if end < start, it means it ends next day)
        // For this visual, we treat simple time-of-day. 
        if (endIndex < startIndex) endIndex += totalSteps;

        for (let i = startIndex; i <= endIndex; i++) {
          // Use modulo to wrap around 24h (index 144 becomes 0)
          const index = i % totalSteps;
          if (timeSeries[index]) {
            timeSeries[index][purpose] += 1;
          }
        }
      });

      // --- 3. CALCULATE PERCENTAGES ---
      // We need arrays of values for ECharts series
      const seriesData: Record<string, number[]> = {};
      allPurposes.forEach(p => seriesData[p] = []);

      timeSeries.forEach((counts) => {
        const total = Object.values(counts).reduce((sum, val) => sum + val, 0);

        allPurposes.forEach(p => {
          // Avoid division by zero
          const percentage = total === 0 ? 0 : (counts[p] / total) * 100;
          seriesData[p].push(parseFloat(percentage.toFixed(1)));
        });
      });

      // --- 4. ECHARTS OPTION ---
      const categories = Array.from({ length: totalSteps }, (_, i) => formatTime(i * STEP_MINUTES));

      const option = {
        title: {
          text: 'Daily Activity Distribution',
          left: 'center',
          textStyle: { fontWeight: 'bold', fontSize: 32, color: '#333' }
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
                tooltip += `${item.seriesName}: ${item.value}%<br/>`;
              }
            });
            return tooltip;
          }
        },
        legend: {
          data: allPurposes,
          bottom: -10,
          icon: 'circle',
          itemGap: 48,
          textStyle: { fontSize: 28 }
        },
        grid: {
          left: '5%',
          right: '4%',
          bottom: '10%', // Space for dataZoom and legend
          containLabel: true
        },
        xAxis: [
          {
            type: 'category',
            boundaryGap: false,
            data: categories,
            axisLabel: { interval: 17, fontWeight: 'bold', fontSize: 24 } // Show label every ~3 hours
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: '% of Trips',
            nameLocation: 'middle',
            nameGap: 75, // Space for the axis name
            max: 100,
            axisLabel: { formatter: '{value}%', fontSize: 28 },
            nameTextStyle: {
              fontSize: 32,
              color: '#333'
            },
          }
        ],
        dataZoom: [
          {
            type: 'slider',
            show: true,
            xAxisIndex: [0],
            start: 0,
            end: 100,
            bottom: 30
          }
        ],
        series: allPurposes.map(purpose => ({
          name: purpose,
          type: 'line',
          stack: 'Total', // This creates the stacking effect
          smooth: true,   // Makes the curves rounded like the image
          showSymbol: false,
          areaStyle: { opacity: 1 }, // Solid fill
          lineStyle: { width: 0 },   // Hide the line stroke itself for cleaner look
          itemStyle: {
            color: colorMap[purpose] || '#' + Math.floor(Math.random() * 16777215).toString(16) // Fallback random color
          },
          emphasis: { focus: 'series' },
          data: seriesData[purpose]
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
  }, [visit_data]);

  return (
    <div
      ref={chartRef}
      style={{
        width: width,
        height: height,
        background: '#fff',
        borderRadius: '8px',
        padding: '10px' // Internal padding for aesthetics
      }}
    />
  );
};

export default DailyActivityChart;
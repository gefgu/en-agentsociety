import * as echarts from 'echarts'; // Import ECharts
import { count } from 'echarts/types/src/component/dataZoom/history.js';
import React, { useState, useEffect, useRef } from 'react';

const VisitDistributionBarChart = ({
  visit_data, width, height,
}: {
  visit_data: any,
  width: string,
  height: string,
}) => {
  const chartRef = useRef(null);
  const heightOffset = parseFloat(height.replace('px', '')) * 0.2; // Offset to position the graphic box lower

  useEffect(() => {
    if (chartRef.current) {
      const myChart = echarts.init(chartRef.current);
      const totalTrips = visit_data.length;

      const purposeCounts = visit_data.reduce((acc: any, visit: any) => {
        const purpose = visit.purpose || 'UNKNOWN';
        acc[purpose] = (acc[purpose] || 0) + 1;
        return acc;
      }, {});

      const chartData = Object.keys(purposeCounts).map((purpose) => ({
        name: purpose,
        value: parseFloat(((purposeCounts[purpose] / totalTrips) * 100).toFixed(1)),
        count: purposeCounts[purpose],
      })).sort((a, b) => b.value - a.value);


      const option = {
        title: {
          text: 'Visit Purpose Distribution',
          left: 'center',
          textStyle: {
            fontSize: 32,
            fontWeight: 'bold',
            color: '#333'
          }
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const data = params[0].data; // Access custom data
            return `${params[0].name}<br/>Count: <b>${data.count}</b><br/>Percentage: <b>${data.value}%</b>`;
          }
        },
        // The "N = ..." Box
        graphic: [
          {
            type: 'group',
            right: 20,
            top: heightOffset,
            children: [
              {
                type: 'rect',
                shape: { width: 100, height: 40, r: 5 },
                style: { fill: '#fff', stroke: '#333', lineWidth: 1 }
              },
              {
                type: 'text',
                position: [50, 20], // Center text in rect
                style: {
                  text: `N = ${totalTrips}`,
                  textAlign: 'center',
                  textVerticalAlign: 'middle',
                  fontSize: 16,
                  fontWeight: 'bold',
                  fill: '#333'
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
          data: chartData.map(item => item.name),
          axisLabel: {
            fontWeight: 'bold',
            fontSize: 14,
            interval: 0 // Force show all labels
          },
          axisTick: { alignWithLabel: true }
        },
        yAxis: {
          type: 'value',
          name: '% of Trips',
          nameLocation: 'middle',
          nameGap: 50, // Space for the axis name
          nameTextStyle: {
            fontSize: 32,
            color: '#333'
          },
          max: 100, // Fix scale to 100% like the image
          axisLabel: {
            fontSize: 28
          }
        },
        series: [
          {
            name: 'Purpose',
            type: 'bar',
            data: chartData, // Pass the full object so tooltip can access .count
            barWidth: '60%',
            itemStyle: {
              // Function to assign different colors per bar based on index
              color: (params) => {
                const colorList = [
                  '#d95f02', // Home (Orange/Brown)
                  '#e6ab02', // Work (Mustard)
                  '#e7298a', // Purchase (Pink)
                  '#7570b3', // Leisure (Purple)
                  '#1b9e77', // Health (Teal)
                  '#66a61e', // Studies/Other
                  '#90ed7d'
                ];
                return colorList[params.dataIndex % colorList.length];
              }
            }
          }
        ]
      };


      myChart.setOption(option);

      const handleResize = () => {
        myChart.resize();
      };

      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
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
        margin: '24px',
      }}
    />
  )
}

export default VisitDistributionBarChart;
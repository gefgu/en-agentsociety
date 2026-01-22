import * as echarts from 'echarts'; // Import ECharts
import { count } from 'echarts/types/src/component/dataZoom/history.js';
import React, { useState, useEffect, useRef } from 'react';
import { fetchCustom } from './fetch';
import message from 'antd/lib/message';


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
  const heightOffset = parseFloat(height.replace('px', '')) * 0.2; // Offset to position the graphic box lower

  const [visit_data, setVisitData] = useState<VisitDistributionResponse>();

  const fetchVisitData = async (experimentId: string) => {
    try {
      const res = await fetchCustom(`/api/visits/purpose-distributions?exp_id=${experimentId}`);
      if (res.ok) {
        const data = await res.json();
        console.log('Fetched visit data:', data);
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

      const option = {
        title: {
          text: `Visit Purpose Distribution`,
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
          data: data.map(item => item.purpose),
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
        toolbox: {
            show: true,
            feature: {
              saveAsImage: {
                show: true,
                title: 'Save as Image',
                type: 'png', // or 'jpeg'
                name: `visit_distribution_${exp_name || exp_id}`, // Default naming
                pixelRatio: 2 // This makes it High Resolution (Retina quality)
              }
            },
            right: 20,
            top: 20
          },
        series: [
          {
            name: 'Purpose',
            type: 'bar',
            // Convert proportions to 0-100 scale for the Y-Axis
            data: data.map(item => ({
              value: parseFloat((item.proportion * 100).toFixed(2)),
              // Keep the original metadata for the tooltip
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
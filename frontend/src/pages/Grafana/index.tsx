import React, { useState, useEffect } from 'react';
import { Layout, Typography, Button, Space, Row, Col } from 'antd';
import { GithubOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

const { Title, Text, Link } = Typography;



const GrafanaPage = () => {
  const { t } = useTranslation();
  const { exp_id } = useParams<{ exp_id?: string }>();

  // Build the Grafana URL with exp_id if available
  const grafanaUrl = exp_id 
    ? `http://localhost:3000/d/adt6tmn/llm-performance-dashboard?orgId=1&from=now-6h&to=now&timezone=browser&var-exp_id=${exp_id}&refresh=1m`
    : `http://localhost:3000/d/adt6tmn/llm-performance-dashboard?orgId=1&from=now-6h&to=now&timezone=browser&refresh=1m`;
  return (
    <iframe
      src={grafanaUrl}
      width="100%"
      height="100%"
      style={{ border: 'none' }}
      title="Grafana Simulation Overview"
      >
    </iframe>
  );
};

export default GrafanaPage;
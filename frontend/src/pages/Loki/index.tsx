import React from 'react';
import { Typography } from 'antd';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

const LokiPage = () => {
  const { t } = useTranslation();
  const { exp_id } = useParams<{ exp_id?: string }>();

  // 1. Base Path
  const basePath = 'http://localhost:3000/a/grafana-lokiexplore-app/explore/service_name/fastsociety/logs';

  // 2. Common parameters (Time, Data Source, Service Name Filter)
  // Note: %7C is '|' and %3D is '='
  let queryParams = [
    'from=now-24h',
    'to=now',
    'var-ds=efaqni0b8wjr4a',
    'var-filters=service_name%7C%3D%7Cfastsociety'
  ];

  // 3. Inject exp_id filter if it exists
  if (exp_id) {
    queryParams.push(`var-filters=exp_id%7C%3D%7C${exp_id}`);
  }

  // 4. Visual settings (Patterns, Fields, Sorting, Timezone)
  const viewSettings = [
    'patterns=%5B%5D',
    'var-lineFormat=',
    'var-fields=',
    'var-levels=',
    'var-metadata=',
    'var-jsonFields=',
    'var-patterns=',
    'var-lineFilterV2=',
    'var-lineFilters=',
    'displayedFields=%5B%22body%22%5D', // Shows only "body"
    'urlColumns=%5B%5D',
    'visualizationType=%22logs%22',
    'var-labelBy=$__all',
    'timezone=browser',
    'var-all-fields=',
    'prettifyLogMessage=false',
    'sortOrder=%22Descending%22',
    'wrapLogMessage=true'
  ];

  // Combine everything
  const lokiUrl = `${basePath}?${[...queryParams, ...viewSettings].join('&')}`;

  return (
    <iframe
      src={lokiUrl}
      width="100%"
      height="100%"
      style={{ border: 'none' }}
      title="Loki Explore Logs"
    />
  );
};

export default LokiPage;
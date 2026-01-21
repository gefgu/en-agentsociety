import React from 'react';
import { useRouteError } from 'react-router-dom';
import { Button, Result } from 'antd'; // Using Ant Design since you already have it

const ErrorPage = () => {
  const error: any = useRouteError();
  console.error(error);

  return (
    <div style={{ padding: '50px', display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Result
        status="500"
        title="Something went wrong"
        subTitle={error.statusText || error.message || "An unexpected error occurred."}
        extra={[
          <Button type="primary" key="home" onClick={() => window.location.href = '/'}>
            Back Home
          </Button>,
          <Button key="reload" onClick={() => window.location.reload()}>
            Reload Page
          </Button>
        ]}
      />
    </div>
  );
};

export default ErrorPage;
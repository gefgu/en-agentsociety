import { Col, Row, Button } from 'antd';
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import VisitDistributionBarChart from "../../components/VisitDistributionBarChart";
import DailyActivityChart from "../../components/DailyActivityChart";


const ChartsPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate(); // 获取导航函数
  const { exp_id, name: EncodedName } = useParams<{ exp_id?: string, name?: string }>();
  const name = EncodedName ? decodeURIComponent(EncodedName) : 'Experiment';

  if (!exp_id) {
    return (
      <div style={{ padding: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <h2 style={{ fontSize: 48 }}>{t('charts.title')}</h2>
          </Col>
          <Col span={24}>
            <p style={{ fontSize: '18px' }}>{t('charts.no_exp_id')}</p>
          </Col>
        </Row>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={22}>
          <h2 style={{ fontSize: 48 }}>{t('charts.title')}</h2>
        </Col>
        <Col span={2}>
          <Button
            type="primary"
            onClick={() => {} } 
            style={{ height: '40px', }}
          >
            {t('charts.reload')}
          </Button>
        </Col>
        <Col md={24} xl={8}>
          {/* Container for the chart */}
          <VisitDistributionBarChart exp_id={exp_id!} exp_name={name} width="100%" height="400px" />
        </Col>
        <Col md={24} xl={16}>
          <DailyActivityChart exp_id={exp_id!} exp_name={name} width="100%" height="450px" />
        </Col>
      </Row>
    </div>
  );
}

export default ChartsPage;

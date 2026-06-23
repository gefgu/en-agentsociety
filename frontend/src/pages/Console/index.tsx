import React, { useEffect, useState, useRef } from "react";
import { message, Button, Space, Popconfirm, Modal, Dropdown, Select, Table, Input } from 'antd';
import { ColumnsType } from "antd/es/table";
import { parseT } from "../../components/util";
import { Link, useNavigate } from "react-router-dom";
import { Experiment } from "../../components/type";
import { ProDescriptions } from "@ant-design/pro-components";
import { EllipsisOutlined, ReloadOutlined, PlusOutlined } from "@ant-design/icons";
import { fetchCustom, postDownloadCustom } from "../../components/fetch";
import { useTranslation } from "react-i18next";

const STATUS_COLORS: Record<number, { color: string; bg: string; border: string }> = {
  0: { color: '#9ca3af', bg: 'rgba(107,114,128,0.18)', border: 'rgba(107,114,128,0.17)' },
  1: { color: '#60a5fa', bg: 'rgba(96,165,250,0.13)',  border: 'rgba(96,165,250,0.18)' },
  2: { color: '#34d399', bg: 'rgba(52,211,153,0.13)',  border: 'rgba(52,211,153,0.18)' },
  3: { color: '#f87171', bg: 'rgba(248,113,113,0.13)', border: 'rgba(248,113,113,0.32)' },
  4: { color: '#f87171', bg: 'rgba(248,113,113,0.13)', border: 'rgba(248,113,113,0.32)' },
};

const StatusBadge = ({ status, label }: { status: number; label: string }) => {
  const s = STATUS_COLORS[status] ?? STATUS_COLORS[0];
  return (
    <span style={{
      display: 'inline-block',
      padding: '3px 8px',
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 500,
      fontFamily: 'var(--font-body)',
      letterSpacing: '0.01em',
      color: s.color,
      background: s.bg,
      border: `1px solid ${s.border}`,
    }}>
      {label}
    </span>
  );
};

const StatusChip = ({ status, label, active, onClick }: {
  status: number | null;
  label: string;
  active: boolean;
  onClick: () => void;
}) => {
  const baseColor = status === null
    ? { color: '#0fb8a4', bg: 'rgba(15,184,164,0.1)', border: 'rgba(15,184,164,0.22)' }
    : STATUS_COLORS[status] ?? STATUS_COLORS[0];

  return (
    <button
      onClick={onClick}
      style={{
        padding: '4px 14px',
        borderRadius: 20,
        fontSize: 12,
        fontFamily: 'var(--font-body)',
        fontWeight: active ? 600 : 400,
        cursor: 'pointer',
        border: `1px solid ${active ? baseColor.border : 'rgba(255,255,255,0.07)'}`,
        background: active ? baseColor.bg : 'transparent',
        color: active ? baseColor.color : 'var(--color-text-muted)',
        transition: 'all 0.15s',
      }}
    >
      {label}
    </button>
  );
};

const MonoCell = ({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) => (
  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-text-muted)', ...style }}>
    {children}
  </span>
);

const Page = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<Experiment | null>(null);
  const [logVisible, setLogVisible] = useState(false);
  const [logContent, setLogContent] = useState('');
  const [logLoading, setLogLoading] = useState(false);
  const [currentExpId, setCurrentExpId] = useState<string>('');
  const [refreshInterval, setRefreshInterval] = useState<number>(0);
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

  const [tableData, setTableData] = useState<Experiment[]>([]);
  const [tableLoading, setTableLoading] = useState(false);
  const [idFilter, setIdFilter] = useState('');
  const [nameFilter, setNameFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<number | null>(null);

  const clearRefreshTimer = () => {
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  };

  const setupRefreshTimer = (interval: number, expId: string) => {
    clearRefreshTimer();
    if (interval > 0) {
      refreshTimerRef.current = setInterval(() => {
        fetchLog(expId);
      }, interval * 1000);
    }
  };

  useEffect(() => {
    return () => clearRefreshTimer();
  }, []);

  const fetchLog = async (experimentId: string) => {
    setLogLoading(true);
    const oldContent = logContent;
    try {
      const res = await fetchCustom(`/api/run-experiments/${experimentId}/log`);
      if (res.ok) {
        const log = await res.text();
        setLogContent(log.replace(/\\n/g, '\n'));
      } else {
        throw new Error(await res.text());
      }
    } catch (err) {
      message.error('Failed to fetch log: ' + err);
      clearRefreshTimer();
      setLogContent(oldContent);
    } finally {
      setLogLoading(false);
    }
  };

  const fetchData = async (idF = idFilter, nameF = nameFilter, statusF = statusFilter) => {
    setTableLoading(true);
    try {
      const res = await fetchCustom('/api/experiments');
      let data = (await res.json()).data as Experiment[];
      if (idF) data = data.filter(d => d.id === idF);
      if (nameF) data = data.filter(d => d.name.includes(nameF));
      if (statusF !== null) data = data.filter(d => d.status == statusF);
      setTableData(data);
    } catch (err) {
      console.error('Failed to fetch experiments:', err);
      setTableData([]);
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleStatusChip = (s: number | null) => {
    setStatusFilter(s);
    fetchData(idFilter, nameFilter, s);
  };

  const handleSearch = () => fetchData();

  const handleReset = () => {
    setIdFilter('');
    setNameFilter('');
    setStatusFilter(null);
    fetchData('', '', null);
  };

  const columns: ColumnsType<Experiment> = [
    {
      title: t('console.table.id'),
      dataIndex: 'id',
      width: 140,
      render: (id: string) => (
        <MonoCell style={{ fontSize: 10.5 }}>{id ? id.slice(0, 8) + '…' : '—'}</MonoCell>
      ),
    },
    {
      title: t('console.table.name'),
      dataIndex: 'name',
      render: (name: string) => (
        <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: '#d8e4f2' }}>{name}</span>
      ),
    },
    { title: t('console.table.numDay'), dataIndex: 'num_day', width: 70 },
    {
      title: t('console.table.status'),
      dataIndex: 'status',
      width: 120,
      render: (status: number) => (
        <StatusBadge status={status} label={t(`console.statusEnum.${status}`)} />
      ),
    },
    { title: t('console.table.currentDay'), dataIndex: 'cur_day', width: 70 },
    {
      title: t('console.table.currentTime'),
      dataIndex: 'cur_t',
      width: 80,
      render: (v: number) => <MonoCell>{parseT(v)}</MonoCell>,
    },
    {
      title: t('console.table.inputTokens'),
      dataIndex: 'input_tokens',
      width: 90,
      render: (v: number) => <MonoCell>{formatTokens(v)}</MonoCell>,
    },
    {
      title: t('console.table.outputTokens'),
      dataIndex: 'output_tokens',
      width: 90,
      render: (v: number) => <MonoCell>{formatTokens(v)}</MonoCell>,
    },
    {
      title: t('console.table.createdAt'),
      dataIndex: 'created_at',
      width: 150,
      render: (v: string) => <MonoCell style={{ fontSize: 10 }}>{v ? new Date(v).toLocaleString() : '—'}</MonoCell>,
    },
    {
      title: t('console.table.updatedAt'),
      dataIndex: 'updated_at',
      width: 150,
      render: (v: string) => <MonoCell style={{ fontSize: 10 }}>{v ? new Date(v).toLocaleString() : '—'}</MonoCell>,
    },
    {
      title: t('console.table.action'),
      width: 160,
      render: (_, record) => {
        record = { ...record };
        return (
          <Space size={4}>
            <Button
              type="primary"
              size="small"
              onClick={() => navigate(`/exp/${record.id}`)}
              disabled={record.status === 0}
              style={{ fontSize: 11 }}
            >
              {t('console.buttons.goto')}
            </Button>
            {record.status === 1 && (
              <Popconfirm
                title={t('console.confirmations.stopExperiment')}
                onConfirm={async () => {
                  try {
                    const res = await fetchCustom(`/api/run-experiments/${record.id}`, { method: 'DELETE' });
                    if (res.ok) {
                      message.success(t('console.messages.stopSuccess'));
                      fetchData();
                    } else {
                      throw new Error(await res.text());
                    }
                  } catch (err) {
                    message.error(t('console.messages.stopFailed') + err);
                  }
                }}
              >
                <Button
                  danger
                  size="small"
                  style={{
                    fontSize: 11,
                    background: 'transparent',
                    border: '1px solid rgba(248,113,113,0.32)',
                    color: '#f87171',
                  }}
                >
                  {t('console.buttons.stop')}
                </Button>
              </Popconfirm>
            )}
            <Dropdown
              menu={{
                items: [
                  { key: 'detail', label: t('console.buttons.detail'), onClick: () => setDetail(record) },
                  {
                    key: 'log',
                    label: (
                      <Link to={`/loki/${record.id}`} target="_blank" rel="noopener noreferrer" style={{ display: 'block' }}>
                        {t('console.buttons.viewLog')}
                      </Link>
                    ),
                  },
                  {
                    key: 'grafana',
                    label: (
                      <Link to={`/grafana/${record.id}`} target="_blank" rel="noopener noreferrer" style={{ display: 'block' }}>
                        {t('console.buttons.grafana')}
                      </Link>
                    ),
                  },
                  {
                    key: 'charts',
                    label: (
                      <Link to={`/charts/${record.id}/${encodeURIComponent(record.name)}`} target="_blank" rel="noopener noreferrer" style={{ display: 'block' }}>
                        {t('console.buttons.charts')}
                      </Link>
                    ),
                  },
                  {
                    key: 'exportArtifacts',
                    label: t('console.buttons.exportArtifacts'),
                    onClick: () => postDownloadCustom(`/api/experiments/${record.id}/artifacts`),
                  },
                  {
                    key: 'export',
                    label: t('console.buttons.export'),
                    onClick: () => postDownloadCustom(`/api/experiments/${record.id}/export`),
                  },
                  {
                    key: 'delete',
                    label: (
                      <Popconfirm
                        title={t('console.confirmations.deleteExperiment')}
                        onConfirm={async () => {
                          try {
                            const res = await fetchCustom(`/api/experiments/${record.id}`, { method: 'DELETE' });
                            if (res.ok) {
                              message.success(t('console.messages.deleteSuccess'));
                              fetchData();
                            } else {
                              throw new Error(await res.text());
                            }
                          } catch (err) {
                            message.error(t('console.messages.deleteFailed') + err);
                          }
                        }}
                      >
                        <span style={{ color: '#f87171' }}>{t('console.buttons.delete')}</span>
                      </Popconfirm>
                    ),
                  },
                ],
              }}
            >
              <Button icon={<EllipsisOutlined />} size="small" />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  const statusChips: { status: number | null; key: string }[] = [
    { status: null, key: 'all' },
    { status: 1, key: '1' },
    { status: 2, key: '2' },
    { status: 0, key: '0' },
    { status: 3, key: '3' },
    { status: 4, key: '4' },
  ];

  return (
    <>
      <div style={{ padding: '32px 28px' }}>
        {/* Page header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
          <div>
            <h1 style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 22,
              fontWeight: 600,
              color: 'var(--color-text)',
              margin: 0,
              letterSpacing: '-0.022em',
            }}>
              {t('console.pageTitle')}
            </h1>
            <p style={{
              fontFamily: 'var(--font-body)',
              fontSize: 13,
              color: 'var(--color-text-muted)',
              margin: '4px 0 0',
            }}>
              {t('console.pageSubtitle')}
            </p>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/create-experiment')}
            style={{ fontFamily: 'var(--font-body)', fontWeight: 600 }}
          >
            {t('console.buttons.createExperiment')}
          </Button>
        </div>

        {/* Filter bar */}
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 10,
          padding: '14px 18px',
          display: 'flex',
          gap: 14,
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: 12,
        }}>
          <span style={{ fontSize: 10.5, fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'rgba(226,234,245,0.3)' }}>
            FILTER
          </span>
          <Input
            placeholder={t('console.table.id')}
            value={idFilter}
            onChange={e => setIdFilter(e.target.value)}
            style={{ width: 160, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 6 }}
            allowClear
          />
          <Input
            placeholder={t('console.table.name')}
            value={nameFilter}
            onChange={e => setNameFilter(e.target.value)}
            style={{ width: 200, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 6 }}
            allowClear
          />
          <Select
            value={statusFilter}
            onChange={v => setStatusFilter(v)}
            style={{ width: 150 }}
            allowClear
            placeholder={t('console.table.status')}
            options={[
              { value: 0, label: t('console.statusEnum.0') },
              { value: 1, label: t('console.statusEnum.1') },
              { value: 2, label: t('console.statusEnum.2') },
              { value: 3, label: t('console.statusEnum.3') },
              { value: 4, label: t('console.statusEnum.4') },
            ]}
          />
          <Button onClick={handleReset} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--color-text-muted)' }}>
            Reset
          </Button>
          <Button type="primary" onClick={handleSearch}>
            Search
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchData()}
            loading={tableLoading}
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--color-text-muted)' }}
          />
        </div>

        {/* Status chip row */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
          {statusChips.map(({ status, key }) => (
            <StatusChip
              key={key}
              status={status}
              label={status === null ? 'All' : t(`console.statusEnum.${status}`)}
              active={statusFilter === status}
              onClick={() => handleStatusChip(status)}
            />
          ))}
        </div>

        {/* Data table */}
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 10,
          overflow: 'hidden',
        }}>
          <Table<Experiment>
            dataSource={tableData}
            columns={columns}
            loading={tableLoading}
            rowKey="id"
            pagination={{ pageSize: 20, size: 'small' }}
            size="small"
            scroll={{ x: 1200 }}
            style={{ background: 'transparent' }}
          />
        </div>
      </div>

      {/* Detail modal */}
      <Modal
        title={t('console.modals.experimentDetail')}
        width="60vw"
        open={detail !== null}
        onCancel={() => setDetail(null)}
        footer={null}
      >
        <ProDescriptions<Experiment>
          column={2}
          title={detail?.name}
          request={async () => ({ success: true, data: detail })}
          columns={[
            { title: t('console.table.id'), dataIndex: 'id' },
            { title: t('console.table.name'), dataIndex: 'name' },
            { title: t('console.table.createdAt'), dataIndex: 'created_at', valueType: 'dateTime' },
            { title: t('console.table.updatedAt'), dataIndex: 'updated_at', valueType: 'dateTime' },
            { title: t('console.table.numDay'), dataIndex: 'num_day' },
            { title: t('console.table.status'), dataIndex: 'status', render: (status: number) => t(`console.statusEnum.${status}`) },
            { title: t('console.table.currentDay'), dataIndex: 'cur_day' },
            { title: t('console.table.currentTime'), dataIndex: 'cur_t', render: (v: number) => parseT(v) },
            { title: t('console.table.config'), dataIndex: 'config', span: 2, valueType: 'jsonCode' },
            { title: t('console.table.error'), dataIndex: 'error', span: 2, valueType: 'code' },
          ]}
        />
      </Modal>

      {/* Log modal */}
      <Modal
        title={t('console.modals.experimentLog')}
        width="80vw"
        open={logVisible}
        onCancel={() => {
          setLogVisible(false);
          setLogContent('');
          setRefreshInterval(0);
          clearRefreshTimer();
        }}
        footer={null}
      >
        <div style={{ marginBottom: '16px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchLog(currentExpId)}
            loading={logLoading}
          >
            {t('console.modals.refresh')}
          </Button>
          <Select
            value={refreshInterval}
            onChange={(value) => {
              setRefreshInterval(value);
              setupRefreshTimer(value, currentExpId);
            }}
            style={{ width: 200 }}
            options={[
              { value: 0, label: t('console.modals.manualRefresh') },
              { value: 1, label: t('console.modals.refreshIntervals.oneSecond') },
              { value: 5, label: t('console.modals.refreshIntervals.fiveSeconds') },
              { value: 10, label: t('console.modals.refreshIntervals.tenSeconds') },
              { value: 30, label: t('console.modals.refreshIntervals.thirtySeconds') },
            ]}
          />
          {logLoading && <span style={{ color: '#0fb8a4' }}>{t('console.modals.refreshing')}</span>}
        </div>
        <pre style={{
          maxHeight: '70vh',
          overflow: 'auto',
          padding: '12px',
          backgroundColor: 'var(--color-surface)',
          color: 'var(--color-text)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          borderRadius: 6,
          border: '1px solid var(--color-border)',
        }}>
          {logContent}
        </pre>
      </Modal>
    </>
  );
};

function formatTokens(n: number): string {
  if (!n || n === 0) return '—';
  if (n >= 1_000_000_000) return (n / 1e9).toFixed(1) + 'B';
  if (n >= 1_000_000) return (n / 1e6).toFixed(0) + 'M';
  if (n >= 1_000) return (n / 1e3).toFixed(0) + 'K';
  return String(n);
}

export default Page;

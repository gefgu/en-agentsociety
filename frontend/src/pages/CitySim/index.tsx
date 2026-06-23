import { useEffect, useState, useCallback, useRef } from "react";
import {
  Col, Row, Card, Select, Spin, Alert, Empty, Tag, Tooltip,
  Typography
} from 'antd';
import { useNavigate, useParams } from "react-router-dom";
import * as echarts from 'echarts';
import TimelineGrid from "../../components/ScheduleTimeline";
import BlocksLegend from "../../components/ScheduleBlocksLegend";
import { fetchCustom } from "../../components/fetch";
import "./CitySim.css";

const { Text } = Typography;

// CitySim block definitions — same as AgentSociety + DailyScheduleBlock
const CITYSIM_BLOCKS = [
  { emoji: '🏃', name: 'MobilityBlock',      desc: 'Movement',            lightColor: '#E3F2FD', darkColor: 'rgba(96,165,250,0.18)',   color: '#E3F2FD' },
  { emoji: '🧠', name: 'CognitionBlock',     desc: 'Emotions/Reflections', lightColor: '#F3E5F5', darkColor: 'rgba(167,139,250,0.18)',  color: '#F3E5F5' },
  { emoji: '💰', name: 'EconomyBlock',       desc: 'Income/Consumption',   lightColor: '#FFF9C4', darkColor: 'rgba(251,191,36,0.18)',   color: '#FFF9C4' },
  { emoji: '🔺', name: 'NeedsBlock',         desc: "Maslow's Needs",       lightColor: '#FFECB3', darkColor: 'rgba(252,211,77,0.18)',   color: '#FFECB3' },
  { emoji: '💤', name: 'OtherBlock',         desc: 'Handle the rest',      lightColor: '#E0E0E0', darkColor: 'rgba(148,163,184,0.18)', color: '#E0E0E0' },
  { emoji: '💬', name: 'SocialBlock',        desc: 'Social Interactions',  lightColor: '#C8E6C9', darkColor: 'rgba(74,222,128,0.18)',   color: '#C8E6C9' },
  { emoji: '📅', name: 'PlanBlock',          desc: 'Planning',             lightColor: '#FFCCBC', darkColor: 'rgba(251,146,60,0.18)',   color: '#FFCCBC' },
  { emoji: '🎯', name: 'Dispatcher',         desc: 'Select Block',         lightColor: '#FFCDD2', darkColor: 'rgba(248,113,113,0.18)', color: '#FFCDD2' },
  { emoji: '📆', name: 'DailyScheduleBlock', desc: 'Daily Planning',       lightColor: '#E8F5E9', darkColor: 'rgba(34,197,94,0.18)',   color: '#E8F5E9' },
];

const ACTIVITY_COLORS: Record<string, string> = {
  sleep:   '#94a3b8',
  work:    '#3b82f6',
  meal:    '#f97316',
  hygiene: '#14b8a6',
  social:  '#a855f7',
  leisure: '#ec4899',
  '[EMPTY]': '#fef08a',
};

const getActivityColor = (activity: string): string =>
  ACTIVITY_COLORS[activity.toLowerCase()] ?? '#6b7280';

type AgentOption = { id: number; name: string };

type ScheduleBlock = {
  start_time: string;
  duration: number;
  activity: string;
  description: string;
};

type DailySchedule = {
  day: number;
  blocks: ScheduleBlock[];
  generated_at: string;
};

type Big5 = {
  openness?: number;
  conscientiousness?: number;
  extraversion?: number;
  agreeableness?: number;
  neuroticism?: number;
};

type Preferences = {
  chronotype?: string;
  work_ethic?: number;
  social_frequency?: number;
  leisure_preference?: string;
};

type AgentProfile = {
  name?: string;
  big5?: Big5;
  life_stage?: string;
  hobbies?: string[];
  goals?: string[];
  preferences?: Preferences;
  [key: string]: any;
};

type BlockExecution = {
  block_name: string;
  prompt: string;
  response: string;
  func_name?: string;
  detail_available?: number;
};

type TimelineDataPoint = {
  simulation_step: number;
  block_executions: BlockExecution[];
};

const TOTAL_STEPS = 144;

// ── Planned Schedule Gantt ──────────────────────────────────────────────────
const PlannedSchedule = ({ schedule }: { schedule: DailySchedule | null }) => {
  if (!schedule || schedule.blocks.length === 0) {
    return <Empty description="No planned schedule available for this agent/day." />;
  }

  const timeToMinutes = (t: string): number => {
    const [h, m] = t.split(':').map(Number);
    return h * 60 + m;
  };

  return (
    <div className="cs-gantt-wrapper">
      {/* Time axis labels */}
      <div className="cs-gantt-axis">
        {[0, 3, 6, 9, 12, 15, 18, 21, 24].map(h => (
          <span key={h} style={{ left: `${(h / 24) * 100}%` }}>
            {String(h).padStart(2, '0')}:00
          </span>
        ))}
      </div>

      {/* Gantt bar */}
      <div className="cs-gantt-bar">
        {schedule.blocks.map((block, i) => {
          const startMin = timeToMinutes(block.start_time);
          const left = (startMin / 1440) * 100;
          const width = (block.duration / 1440) * 100;
          const color = getActivityColor(block.activity);
          return (
            <Tooltip
              key={i}
              title={
                <div>
                  <div><strong>{block.activity}</strong></div>
                  <div>{block.start_time} · {block.duration} min</div>
                  {block.description && <div style={{ marginTop: 4 }}>{block.description}</div>}
                </div>
              }
            >
              <div
                className="cs-gantt-block"
                style={{ left: `${left}%`, width: `${width}%`, background: color }}
              >
                {width > 4 && (
                  <span className="cs-gantt-label">
                    {block.activity !== '[EMPTY]' ? block.activity : '?'}
                  </span>
                )}
              </div>
            </Tooltip>
          );
        })}
      </div>

      {/* Legend */}
      <div className="cs-gantt-legend">
        {Object.entries(ACTIVITY_COLORS).map(([act, col]) => (
          <span key={act} className="cs-gantt-legend-item">
            <span className="cs-gantt-legend-dot" style={{ background: col }} />
            {act}
          </span>
        ))}
      </div>
    </div>
  );
};

// ── Big Five Radar (raw ECharts) ────────────────────────────────────────────
const Big5Radar = ({ big5 }: { big5: Big5 }) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);
    chart.setOption({
      radar: {
        indicator: [
          { name: 'Openness', max: 1 },
          { name: 'Conscientiousness', max: 1 },
          { name: 'Extraversion', max: 1 },
          { name: 'Agreeableness', max: 1 },
          { name: 'Neuroticism', max: 1 },
        ],
        splitNumber: 4,
        axisName: { color: '#888', fontSize: 11 },
      },
      series: [{
        type: 'radar',
        data: [{
          value: [
            big5.openness ?? 0,
            big5.conscientiousness ?? 0,
            big5.extraversion ?? 0,
            big5.agreeableness ?? 0,
            big5.neuroticism ?? 0,
          ],
          name: 'Big Five',
          areaStyle: { opacity: 0.25, color: '#0fb8a4' },
          lineStyle: { color: '#0fb8a4' },
          itemStyle: { color: '#0fb8a4' },
        }],
      }],
    });
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(chartRef.current);
    return () => { observer.disconnect(); chart.dispose(); };
  }, [big5.openness, big5.conscientiousness, big5.extraversion, big5.agreeableness, big5.neuroticism]);

  return <div ref={chartRef} style={{ height: 220, width: '100%' }} />;
};

// ── Personality Panel ───────────────────────────────────────────────────────
const PersonalityPanel = ({ profile }: { profile: AgentProfile | null }) => {
  if (!profile) return <Empty description="No profile data available." />;

  const big5 = profile.big5 ?? {};
  const prefs: Preferences = profile.preferences ?? {};
  const hobbies: string[] = profile.hobbies ?? [];
  const goals: string[] = profile.goals ?? [];
  const hasB5 = Object.values(big5).some(v => (v ?? 0) > 0);

  return (
    <div className="cs-personality">
      {profile.life_stage && (
        <div className="cs-personality-row">
          <Text strong>Life Stage: </Text>
          <Tag color="blue">{profile.life_stage}</Tag>
        </div>
      )}

      {hasB5 && (
        <div className="cs-personality-row">
          <Text strong>Big Five Personality</Text>
          <Big5Radar big5={big5} />
        </div>
      )}

      {Object.keys(prefs).length > 0 && (
        <div className="cs-personality-row">
          <Text strong>Preferences</Text>
          <div className="cs-prefs-grid">
            {prefs.chronotype && <div><Text type="secondary">Chronotype:</Text> {prefs.chronotype}</div>}
            {prefs.work_ethic !== undefined && <div><Text type="secondary">Work ethic:</Text> {prefs.work_ethic.toFixed(2)}</div>}
            {prefs.social_frequency !== undefined && <div><Text type="secondary">Social freq:</Text> {prefs.social_frequency.toFixed(2)}</div>}
            {prefs.leisure_preference && <div><Text type="secondary">Leisure:</Text> {prefs.leisure_preference}</div>}
          </div>
        </div>
      )}

      {hobbies.length > 0 && (
        <div className="cs-personality-row">
          <Text strong>Hobbies</Text>
          <div style={{ marginTop: 6 }}>
            {hobbies.map((h, i) => <Tag key={i} color="purple">{h}</Tag>)}
          </div>
        </div>
      )}

      {goals.length > 0 && (
        <div className="cs-personality-row">
          <Text strong>Goals</Text>
          <ol className="cs-goals-list">
            {goals.map((g, i) => <li key={i}>{g}</li>)}
          </ol>
        </div>
      )}
    </div>
  );
};

// ── Main Page ───────────────────────────────────────────────────────────────
const CitySim = () => {
  const navigate = useNavigate();
  const { exp_id, agent_id: agentIdParam } = useParams<{ exp_id?: string; agent_id?: string }>();

  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(
    agentIdParam ? parseInt(agentIdParam, 10) : null
  );
  const [timelineData, setTimelineData] = useState<TimelineDataPoint[]>([]);
  const [schedule, setSchedule] = useState<DailySchedule | null>(null);
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch agent list
  useEffect(() => {
    if (!exp_id) return;
    setLoadingAgents(true);
    fetchCustom(`/api/experiments/${exp_id}/agents/-/profile`)
      .then(r => r.json())
      .then(json => {
        const list: AgentOption[] = (json.data || []).map((p: any) => ({
          id: p.id,
          name: p.name || `Agent ${p.id}`,
        }));
        setAgents(list);
        if (list.length > 0 && selectedAgentId === null) {
          setSelectedAgentId(list[0].id);
        }
      })
      .catch(() => setError('Failed to load agent list'))
      .finally(() => setLoadingAgents(false));
  }, [exp_id]);

  // Fetch all data for selected agent
  const fetchAgentData = useCallback((agentId: number) => {
    if (!exp_id) return;
    setLoadingData(true);
    setError(null);

    Promise.all([
      fetchCustom(`/api/experiments/${exp_id}/agents/${agentId}/block-timeline`).then(r => r.json()),
      fetchCustom(`/api/experiments/${exp_id}/agents/${agentId}/daily-plan`).then(r => r.json()),
      fetchCustom(`/api/experiments/${exp_id}/agents/${agentId}/profile`).then(r => r.json()),
    ])
      .then(([timelineJson, scheduleJson, profileJson]) => {
        // Timeline
        const steps = timelineJson.data || [];
        const grid: TimelineDataPoint[] = Array.from({ length: TOTAL_STEPS }, (_, i) => ({
          simulation_step: i,
          block_executions: [],
        }));
        for (const step of steps) {
          const idx = step.simulation_step;
          if (idx >= 0 && idx < TOTAL_STEPS) {
            grid[idx].block_executions = step.block_executions;
          }
        }
        setTimelineData(grid);

        // Daily schedule
        setSchedule(scheduleJson.data ?? null);

        // Agent profile
        const p = profileJson.data;
        setProfile(p ? p.profile ?? p : null);
      })
      .catch(() => setError('Failed to load CitySim data'))
      .finally(() => setLoadingData(false));
  }, [exp_id]);

  useEffect(() => {
    if (selectedAgentId !== null) {
      fetchAgentData(selectedAgentId);
      if (exp_id) {
        navigate(`/citysim-schedule/${exp_id}/${selectedAgentId}`, { replace: true });
      }
    }
  }, [selectedAgentId]);

  const agentName = agents.find(a => a.id === selectedAgentId)?.name ?? '';

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <h2 style={{ fontSize: 36 }}>
            CitySim Daily Schedule{agentName ? ` — ${agentName}` : ''}
          </h2>
        </Col>

        {/* Agent selector */}
        {exp_id && (
          <Col span={24}>
            <span style={{ marginRight: 12, fontWeight: 600 }}>Agent:</span>
            <Select
              loading={loadingAgents}
              value={selectedAgentId ?? undefined}
              onChange={val => setSelectedAgentId(val)}
              style={{ width: 280 }}
              placeholder="Select an agent"
              showSearch
              filterOption={(input, opt) =>
                (opt?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={agents.map(a => ({ value: a.id, label: `${a.name} (${a.id})` }))}
            />
          </Col>
        )}

        {error && (
          <Col span={24}>
            <Alert type="error" message={error} showIcon />
          </Col>
        )}

        {loadingData ? (
          <Col span={24} style={{ textAlign: 'center', padding: 48 }}>
            <Spin size="large" />
          </Col>
        ) : (
          <>
            {/* Planned schedule Gantt */}
            <Col span={24}>
              <Card title={`Planned Daily Schedule${schedule ? ` — Day ${schedule.day}` : ''}`}>
                <PlannedSchedule schedule={schedule} />
              </Card>
            </Col>

            {/* Block execution + personality side by side */}
            <Col xs={24} lg={16}>
              <Card title="Block Execution Timeline">
                {timelineData.length === 0 ? (
                  <Empty description="No timeline data. Select an experiment and agent." />
                ) : (
                  <TimelineGrid timelineData={timelineData} blocks={CITYSIM_BLOCKS} />
                )}
              </Card>
              <div style={{ marginTop: 16 }}>
                <h3 style={{ fontSize: 20 }}>Block Types</h3>
                <BlocksLegend blocks={CITYSIM_BLOCKS} />
              </div>
            </Col>

            <Col xs={24} lg={8}>
              <Card title="Agent Personality">
                <PersonalityPanel profile={profile} />
              </Card>
            </Col>
          </>
        )}
      </Row>
    </div>
  );
};

export default CitySim;

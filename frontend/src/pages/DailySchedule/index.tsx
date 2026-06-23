import { useEffect, useState, useCallback, useRef } from "react";
import {
  Col, Row, Card, Select, Spin, Alert, Empty, Tag, Tooltip, Typography,
} from 'antd';
import { useNavigate, useParams } from "react-router-dom";
import TimelineGrid from "../../components/ScheduleTimeline";
import BlocksLegend from "../../components/ScheduleBlocksLegend";
import ScheduleAttributesLegend from "../../components/ScheduleAttributesLegend";
import { fetchCustom } from "../../components/fetch";
import * as echarts from 'echarts';

const { Text } = Typography;

// ── Block definitions ───────────────────────────────────────────────────────

const BLOCKS = [
  { emoji: '🏃', name: 'MobilityBlock',      desc: 'Movement',            lightColor: '#E3F2FD', darkColor: 'rgba(96,165,250,0.18)',   color: '#E3F2FD' },
  { emoji: '🧠', name: 'CognitionBlock',     desc: 'Emotions/Reflections', lightColor: '#F3E5F5', darkColor: 'rgba(167,139,250,0.18)',  color: '#F3E5F5' },
  { emoji: '💰', name: 'EconomyBlock',       desc: 'Income/Consumption',   lightColor: '#FFF9C4', darkColor: 'rgba(251,191,36,0.18)',   color: '#FFF9C4' },
  { emoji: '🔺', name: 'NeedsBlock',         desc: "Maslow's Needs",       lightColor: '#FFECB3', darkColor: 'rgba(252,211,77,0.18)',   color: '#FFECB3' },
  { emoji: '💤', name: 'OtherBlock',         desc: 'Handle the rest',      lightColor: '#E0E0E0', darkColor: 'rgba(148,163,184,0.18)', color: '#E0E0E0' },
  { emoji: '💬', name: 'SocialBlock',        desc: 'Social Interactions',  lightColor: '#C8E6C9', darkColor: 'rgba(74,222,128,0.18)',   color: '#C8E6C9' },
  { emoji: '📅', name: 'PlanBlock',          desc: 'Planning',             lightColor: '#FFCCBC', darkColor: 'rgba(251,146,60,0.18)',   color: '#FFCCBC' },
  { emoji: '🎯', name: 'Dispatcher',         desc: 'Select Block',         lightColor: '#FFCDD2', darkColor: 'rgba(248,113,113,0.18)', color: '#FFCDD2' },
];

const CITYSIM_BLOCKS = [
  ...BLOCKS,
  { emoji: '📆', name: 'DailyScheduleBlock', desc: 'Daily Planning', lightColor: '#E8F5E9', darkColor: 'rgba(34,197,94,0.18)', color: '#E8F5E9' },
];

// ── Attribute emoji map (used by TimelineGrid modal) ────────────────────────

const ATTRIBUTE_TO_EMOJI: Record<string, string> = {
  "location": "🗺️", "radius": "⭕", "residence": "🏠", "work": "🏢", "city": "🏙️",
  "weather": "☁️", "temperature": "🌡️", "environment_info": "🌳", "time": "⌚",
  "name": "🏷️", "gender": "⚧", "age": "🎂", "race": "🌍", "religion": "🛐",
  "marriage_status": "💍", "background_story": "📜",
  "emotion": "😶", "emotion_levels": "🎭", "thought": "💭", "memories": "🧠",
  "personality": "🧩", "topic": "💡",
  "needs": "🔋", "need": "🚨", "plan": "📝", "intention": "🎯",
  "intervention": "📢", "options": "🤔", "event": "🏁", "max_steps": "📏", "other": "ℹ️",
  "occupation": "💼", "job": "⚒️", "education": "🎓", "income": "💵", "wealth": "💰",
  "hourly_rate": "⏱️", "taxes": "📉", "interest_rate": "📈", "prices": "🏷️",
  "consumption": "🛒", "consumption_level": "📊", "family_consumption": "👨‍👩‍👧",
  "chat": "💬", "relationship_type": "🔗", "relationship_strength": "💪",
  "friend_info": "🤝", "discussion_constraint": "🤐", "blocks": "📦",
};

// ── Shared types ────────────────────────────────────────────────────────────

export type BlockExecution = {
  block_name: string;
  prompt: string;
  response: string;
  func_name?: string;
  detail_available?: number;
};

export type TimelineDataPoint = {
  simulation_step: number;
  block_executions: BlockExecution[];
};

type AgentOption = { id: number; name: string };

type ScheduleBlock = { start_time: string; duration: number; activity: string; description: string };
type DailySchedule = { day: number; blocks: ScheduleBlock[]; generated_at: string };
type Big5 = { openness?: number; conscientiousness?: number; extraversion?: number; agreeableness?: number; neuroticism?: number };
type Preferences = { chronotype?: string; work_ethic?: number; social_frequency?: number; leisure_preference?: string };
type AgentProfile = { big5?: Big5; life_stage?: string; hobbies?: string[]; goals?: string[]; preferences?: Preferences; [key: string]: any };

const TOTAL_STEPS = 144;

const ACTIVITY_COLORS: Record<string, string> = {
  sleep:    '#94a3b8',
  work:     '#3b82f6',
  meal:     '#f97316',
  hygiene:  '#14b8a6',
  social:   '#a855f7',
  leisure:  '#ec4899',
  '[EMPTY]':'#fef08a',
};
const getActivityColor = (a: string) => ACTIVITY_COLORS[a.toLowerCase()] ?? '#6b7280';

// ── CitySim sub-components ──────────────────────────────────────────────────

const PlannedSchedule = ({ schedule }: { schedule: DailySchedule | null }) => {
  if (!schedule || schedule.blocks.length === 0)
    return <Empty description="No planned schedule available for this agent/day." />;

  const toMin = (t: string) => { const [h, m] = t.split(':').map(Number); return h * 60 + m; };

  return (
    <div style={{ position: 'relative', paddingTop: 28, paddingBottom: 32 }}>
      {/* Axis */}
      <div style={{ position: 'relative', height: 20, marginBottom: 4 }}>
        {[0, 3, 6, 9, 12, 15, 18, 21, 24].map(h => (
          <span key={h} style={{ position: 'absolute', left: `${(h / 24) * 100}%`, transform: 'translateX(-50%)', fontSize: 11, color: 'var(--color-text-secondary, #888)', whiteSpace: 'nowrap' }}>
            {String(h).padStart(2, '0')}:00
          </span>
        ))}
      </div>
      {/* Bar */}
      <div style={{ position: 'relative', height: 44, background: 'rgba(0,0,0,0.06)', borderRadius: 6, overflow: 'hidden' }}>
        {schedule.blocks.map((block, i) => {
          const left = (toMin(block.start_time) / 1440) * 100;
          const width = (block.duration / 1440) * 100;
          return (
            <Tooltip key={i} title={<div><strong>{block.activity}</strong><br />{block.start_time} · {block.duration} min{block.description ? <><br />{block.description}</> : null}</div>}>
              <div style={{ position: 'absolute', top: 0, left: `${left}%`, width: `${width}%`, height: '100%', background: getActivityColor(block.activity), display: 'flex', alignItems: 'center', justifyContent: 'center', borderRight: '1px solid rgba(255,255,255,0.2)', cursor: 'default' }}>
                {width > 4 && <span style={{ fontSize: 11, fontWeight: 600, color: 'rgba(0,0,0,0.7)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', padding: '0 4px' }}>{block.activity !== '[EMPTY]' ? block.activity : '?'}</span>}
              </div>
            </Tooltip>
          );
        })}
      </div>
      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 12 }}>
        {Object.entries(ACTIVITY_COLORS).map(([act, col]) => (
          <span key={act} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
            <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: col, flexShrink: 0 }} />
            {act}
          </span>
        ))}
      </div>
    </div>
  );
};

const Big5Radar = ({ big5 }: { big5: Big5 }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);
    chart.setOption({
      radar: {
        indicator: [
          { name: 'Openness', max: 1 }, { name: 'Conscientiousness', max: 1 },
          { name: 'Extraversion', max: 1 }, { name: 'Agreeableness', max: 1 },
          { name: 'Neuroticism', max: 1 },
        ],
        splitNumber: 4,
        axisName: { color: '#888', fontSize: 11 },
      },
      series: [{ type: 'radar', data: [{ value: [big5.openness ?? 0, big5.conscientiousness ?? 0, big5.extraversion ?? 0, big5.agreeableness ?? 0, big5.neuroticism ?? 0], name: 'Big Five', areaStyle: { opacity: 0.25, color: '#0fb8a4' }, lineStyle: { color: '#0fb8a4' }, itemStyle: { color: '#0fb8a4' } }] }],
    });
    const obs = new ResizeObserver(() => chart.resize());
    obs.observe(chartRef.current);
    return () => { obs.disconnect(); chart.dispose(); };
  }, [big5.openness, big5.conscientiousness, big5.extraversion, big5.agreeableness, big5.neuroticism]);
  return <div ref={chartRef} style={{ height: 220, width: '100%' }} />;
};

const PersonalityPanel = ({ profile }: { profile: AgentProfile | null }) => {
  if (!profile) return <Empty description="No profile data." />;
  const big5 = profile.big5 ?? {};
  const prefs: Preferences = profile.preferences ?? {};
  const hobbies: string[] = profile.hobbies ?? [];
  const goals: string[] = profile.goals ?? [];
  const hasB5 = Object.values(big5).some(v => (v ?? 0) > 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {profile.life_stage && (
        <div><Text strong>Life Stage: </Text><Tag color="blue">{profile.life_stage}</Tag></div>
      )}
      {hasB5 && (
        <div><Text strong>Big Five Personality</Text><Big5Radar big5={big5} /></div>
      )}
      {Object.keys(prefs).length > 0 && (
        <div>
          <Text strong>Preferences</Text>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px', fontSize: 13, marginTop: 6 }}>
            {prefs.chronotype && <div><Text type="secondary">Chronotype:</Text> {prefs.chronotype}</div>}
            {prefs.work_ethic !== undefined && <div><Text type="secondary">Work ethic:</Text> {prefs.work_ethic.toFixed(2)}</div>}
            {prefs.social_frequency !== undefined && <div><Text type="secondary">Social freq:</Text> {prefs.social_frequency.toFixed(2)}</div>}
            {prefs.leisure_preference && <div><Text type="secondary">Leisure:</Text> {prefs.leisure_preference}</div>}
          </div>
        </div>
      )}
      {hobbies.length > 0 && (
        <div><Text strong>Hobbies</Text><div style={{ marginTop: 6 }}>{hobbies.map((h, i) => <Tag key={i} color="purple">{h}</Tag>)}</div></div>
      )}
      {goals.length > 0 && (
        <div>
          <Text strong>Goals</Text>
          <ol style={{ margin: '4px 0 0', paddingLeft: 20, fontSize: 13, lineHeight: 1.7 }}>
            {goals.map((g, i) => <li key={i}>{g}</li>)}
          </ol>
        </div>
      )}
    </div>
  );
};

// ── Main Page ───────────────────────────────────────────────────────────────

const DailySchedulePage = () => {
  const navigate = useNavigate();
  const { exp_id, agent_id: agentIdParam } = useParams<{ exp_id?: string; agent_id?: string }>();

  const [simulationMode, setSimulationMode] = useState<'citysim' | 'agentsociety' | null>(null);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(
    agentIdParam ? parseInt(agentIdParam, 10) : null
  );
  const [timelineData, setTimelineData] = useState<TimelineDataPoint[]>([]);
  const [schedule, setSchedule] = useState<DailySchedule | null>(null);
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [loadingMeta, setLoadingMeta] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch experiment metadata to determine simulation mode + agent list
  useEffect(() => {
    if (!exp_id) return;
    setLoadingMeta(true);
    Promise.all([
      fetchCustom(`/api/experiments/${exp_id}`).then(r => r.json()),
      fetchCustom(`/api/experiments/${exp_id}/agents/-/profile`).then(r => r.json()),
    ])
      .then(([expJson, profilesJson]) => {
        // Parse simulation_mode from config JSON
        try {
          const cfg = JSON.parse(expJson.data?.config ?? '{}');
          setSimulationMode(cfg.simulation_mode === 'agentsociety' ? 'agentsociety' : 'citysim');
        } catch {
          setSimulationMode('citysim');
        }
        // Build agent list
        const list: AgentOption[] = (profilesJson.data || []).map((p: any) => ({
          id: p.id,
          name: p.name || `Agent ${p.id}`,
        }));
        setAgents(list);
        if (list.length > 0 && selectedAgentId === null) {
          setSelectedAgentId(list[0].id);
        }
      })
      .catch(() => setError('Failed to load experiment metadata'))
      .finally(() => setLoadingMeta(false));
  }, [exp_id]);

  // 2. Fetch agent data whenever agent changes
  const fetchAgentData = useCallback((agentId: number, mode: 'citysim' | 'agentsociety') => {
    if (!exp_id) return;
    setLoadingData(true);
    setError(null);

    const requests: Promise<any>[] = [
      fetchCustom(`/api/experiments/${exp_id}/agents/${agentId}/block-timeline`).then(r => r.json()),
    ];
    if (mode === 'citysim') {
      requests.push(
        fetchCustom(`/api/experiments/${exp_id}/agents/${agentId}/daily-plan`).then(r => r.json()),
        fetchCustom(`/api/experiments/${exp_id}/agents/${agentId}/profile`).then(r => r.json()),
      );
    }

    Promise.all(requests)
      .then(([timelineJson, scheduleJson, profileJson]) => {
        // Map timeline steps into 144-slot grid
        const steps = timelineJson.data || [];
        const grid: TimelineDataPoint[] = Array.from({ length: TOTAL_STEPS }, (_, i) => ({
          simulation_step: i,
          block_executions: [],
        }));
        for (const step of steps) {
          const idx = step.simulation_step;
          if (idx >= 0 && idx < TOTAL_STEPS) grid[idx].block_executions = step.block_executions;
        }
        setTimelineData(grid);

        if (mode === 'citysim') {
          setSchedule(scheduleJson?.data ?? null);
          const p = profileJson?.data;
          setProfile(p ? (p.profile ?? p) : null);
        }
      })
      .catch(() => setError('Failed to load agent data'))
      .finally(() => setLoadingData(false));
  }, [exp_id]);

  useEffect(() => {
    if (selectedAgentId !== null && simulationMode !== null) {
      fetchAgentData(selectedAgentId, simulationMode);
      if (exp_id) navigate(`/daily-schedule/${exp_id}/${selectedAgentId}`, { replace: true });
    }
  }, [selectedAgentId, simulationMode]);

  const agentName = agents.find(a => a.id === selectedAgentId)?.name ?? '';
  const isCitySim = simulationMode === 'citysim';
  const blockList = isCitySim ? CITYSIM_BLOCKS : BLOCKS;
  const modeLabel = isCitySim ? 'CitySim' : 'AgentSociety';

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <h2 style={{ fontSize: 36 }}>
            Daily Schedule{agentName ? ` — ${agentName}` : ''}
            {simulationMode && (
              <Tag color={isCitySim ? 'green' : 'blue'} style={{ marginLeft: 14, fontSize: 13, verticalAlign: 'middle' }}>
                {modeLabel}
              </Tag>
            )}
          </h2>
        </Col>

        {/* Agent selector */}
        {exp_id && (
          <Col span={24}>
            <span style={{ marginRight: 12, fontWeight: 600 }}>Agent:</span>
            <Select
              loading={loadingMeta}
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

        {error && <Col span={24}><Alert type="error" message={error} showIcon /></Col>}

        {loadingData || loadingMeta ? (
          <Col span={24} style={{ textAlign: 'center', padding: 48 }}>
            <Spin size="large" />
          </Col>
        ) : (
          <>
            {/* CitySim-only: planned schedule Gantt */}
            {isCitySim && (
              <Col span={24}>
                <Card title={`Planned Daily Schedule${schedule ? ` — Day ${schedule.day}` : ''}`}>
                  <PlannedSchedule schedule={schedule} />
                </Card>
              </Col>
            )}

            {/* Block execution timeline */}
            <Col span={24} lg={isCitySim ? 16 : 24}>
              <Card title="Block Execution Timeline">
                {timelineData.length === 0 ? (
                  <Empty description="No data. Select an experiment and agent." />
                ) : (
                  <TimelineGrid timelineData={timelineData} blocks={blockList} />
                )}
              </Card>

              <h3 style={{ fontSize: 20, marginTop: 20 }}>Block Types</h3>
              <BlocksLegend blocks={blockList} />

              {!isCitySim && (
                <>
                  <h3 style={{ fontSize: 20, marginTop: 20 }}>Agent Attributes</h3>
                  <Card><ScheduleAttributesLegend /></Card>
                </>
              )}
            </Col>

            {/* CitySim-only: personality panel */}
            {isCitySim && (
              <Col span={24} lg={8}>
                <Card title="Agent Personality">
                  <PersonalityPanel profile={profile} />
                </Card>
              </Col>
            )}
          </>
        )}
      </Row>
    </div>
  );
};

export { BLOCKS, ATTRIBUTE_TO_EMOJI };
export default DailySchedulePage;

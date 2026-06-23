import { useEffect, useState, useCallback } from "react";
import { Col, Row, Card, Select, Spin, Alert, Empty } from 'antd';
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import TimelineGrid from "../../components/ScheduleTimeline";
import BlocksLegend from "../../components/ScheduleBlocksLegend";
import ScheduleAttributesLegend from "../../components/ScheduleAttributesLegend";
import { fetchCustom } from "../../components/fetch";

// Block definitions matching the Python code
const BLOCKS = [
  { emoji: '🏃', name: 'MobilityBlock',   desc: 'Movement',            lightColor: '#E3F2FD', darkColor: 'rgba(96,165,250,0.18)',   color: '#E3F2FD' },
  { emoji: '🧠', name: 'CognitionBlock',  desc: 'Emotions/Reflections', lightColor: '#F3E5F5', darkColor: 'rgba(167,139,250,0.18)',  color: '#F3E5F5' },
  { emoji: '💰', name: 'EconomyBlock',    desc: 'Income/Consumption',   lightColor: '#FFF9C4', darkColor: 'rgba(251,191,36,0.18)',   color: '#FFF9C4' },
  { emoji: '🔺', name: 'NeedsBlock',      desc: "Maslow's Needs",       lightColor: '#FFECB3', darkColor: 'rgba(252,211,77,0.18)',   color: '#FFECB3' },
  { emoji: '💤', name: 'OtherBlock',      desc: 'Handle the rest',      lightColor: '#E0E0E0', darkColor: 'rgba(148,163,184,0.18)', color: '#E0E0E0' },
  { emoji: '💬', name: 'SocialBlock',     desc: 'Social Interactions',  lightColor: '#C8E6C9', darkColor: 'rgba(74,222,128,0.18)',   color: '#C8E6C9' },
  { emoji: '📅', name: 'PlanBlock',       desc: 'Planning',             lightColor: '#FFCCBC', darkColor: 'rgba(251,146,60,0.18)',   color: '#FFCCBC' },
  { emoji: '🎯', name: 'Dispatcher',      desc: 'Select Block',         lightColor: '#FFCDD2', darkColor: 'rgba(248,113,113,0.18)', color: '#FFCDD2' },
];

// Attribute to emoji mapping
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
  "friend_info": "🤝", "discussion_constraint": "🤐",
  "blocks": "📦"
};

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

const TOTAL_STEPS = 144;

const DailySchedulePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { exp_id, agent_id: agentIdParam } = useParams<{ exp_id?: string; agent_id?: string }>();

  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(
    agentIdParam ? parseInt(agentIdParam, 10) : null
  );
  const [timelineData, setTimelineData] = useState<TimelineDataPoint[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch agent list for the experiment
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

  // Fetch block timeline whenever agent selection changes
  const fetchTimeline = useCallback((agentId: number) => {
    if (!exp_id) return;
    setLoadingTimeline(true);
    setError(null);
    fetchCustom(`/api/experiments/${exp_id}/agents/${agentId}/block-timeline`)
      .then(r => r.json())
      .then(json => {
        const steps = json.data || [];
        // Build a 144-slot array; steps not present get empty block_executions
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
      })
      .catch(() => setError('Failed to load block timeline'))
      .finally(() => setLoadingTimeline(false));
  }, [exp_id]);

  useEffect(() => {
    if (selectedAgentId !== null) {
      fetchTimeline(selectedAgentId);
      if (exp_id) {
        navigate(`/daily-schedule/${exp_id}/${selectedAgentId}`, { replace: true });
      }
    }
  }, [selectedAgentId]);

  const agentName = agents.find(a => a.id === selectedAgentId)?.name ?? '';

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <h2 style={{ fontSize: 36 }}>
            Daily Schedule Timeline{agentName ? ` — ${agentName}` : ''}
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

        {/* Timeline Grid */}
        <Col span={24}>
          <Card title="Daily Activity Timeline">
            {loadingTimeline ? (
              <div style={{ textAlign: 'center', padding: 48 }}>
                <Spin size="large" />
              </div>
            ) : timelineData.length === 0 ? (
              <Empty description="No timeline data available. Select an experiment and agent." />
            ) : (
              <TimelineGrid timelineData={timelineData} />
            )}
          </Card>
        </Col>

        {/* Block Legend */}
        <Col span={24}>
          <h3 style={{ fontSize: 24, marginTop: 24 }}>Block Types</h3>
          <BlocksLegend />
        </Col>

        {/* Attributes Grid */}
        <Col span={24}>
          <h3 style={{ fontSize: 24, marginTop: 24 }}>Agent Attributes</h3>
          <Card>
            <ScheduleAttributesLegend />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export { BLOCKS, ATTRIBUTE_TO_EMOJI };

export default DailySchedulePage;

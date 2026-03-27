import { useEffect, useState, useRef } from "react";
import {
  Col,
  Row,
  Card,
  Select,
  Button,
  InputNumber,
  Space,
  Alert,
} from "antd";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import TimelineGrid from "../../components/schedule/ScheduleTimeline";
import BlocksLegend from "../../components/schedule/ScheduleBLocksLegend";
import ScheduleAttributesLegend from "../../components/schedule/ScheduleAttributesLegend";
import { fetchCustom } from "../../components/fetch";

// Block definitions matching the Python code
const BLOCKS = [
  { emoji: "🏃", name: "MobilityBlock", desc: "Movement", color: "#E3F2FD" },
  {
    emoji: "🧠",
    name: "CognitionBlock",
    desc: "Emotions/Reflections",
    color: "#F3E5F5",
  },
  {
    emoji: "💰",
    name: "EconomyBlock",
    desc: "Income/Consumption",
    color: "#FFF9C4",
  },
  { emoji: "🔺", name: "NeedsBlock", desc: "Maslow's Needs", color: "#FFECB3" },
  {
    emoji: "💤",
    name: "OtherBlock",
    desc: "Handle the rest",
    color: "#E0E0E0",
  },
  {
    emoji: "💬",
    name: "SocialBlock",
    desc: "Social Interactions",
    color: "#C8E6C9",
  },
  { emoji: "📅", name: "PlanBlock", desc: "Planning", color: "#FFCCBC" },
  { emoji: "🎯", name: "Dispatcher", desc: "Select Block", color: "#FFCDD2" },
];

// Attribute to emoji mapping
const ATTRIBUTE_TO_EMOJI: Record<string, string> = {
  // Mobility & Location
  location: "🗺️",
  radius: "⭕",
  residence: "🏠",
  work: "🏢",
  city: "🏙️",

  // Environment & Time
  weather: "☁️",
  temperature: "🌡️",
  environment_info: "🌳",
  time: "⌚",

  // Demographics
  name: "🏷️",
  gender: "⚧",
  age: "🎂",
  race: "🌍",
  religion: "🛐",
  marriage_status: "💍",
  background_story: "📜",

  // Internal State
  emotion: "😶",
  emotion_levels: "🎭",
  thought: "💭",
  memories: "🧠",
  personality: "🧩",
  topic: "💡",

  // Needs & Planning
  needs: "🔋",
  need: "🚨",
  plan: "📝",
  intention: "🎯",
  intervention: "📢",
  options: "🤔",
  event: "🏁",
  max_steps: "📏",
  other: "ℹ️",

  // Economy & Work
  occupation: "💼",
  job: "⚒️",
  education: "🎓",
  income: "💵",
  wealth: "💰",
  hourly_rate: "⏱️",
  taxes: "📉",
  interest_rate: "📈",
  prices: "🏷️",
  consumption: "🛒",
  consumption_level: "📊",
  family_consumption: "👨‍👩‍👧",

  // Social
  chat: "💬",
  relationship_type: "🔗",
  relationship_strength: "💪",
  friend_info: "🤝",
  discussion_constraint: "🤐",

  // Blocks
  blocks: "📦",
};

// Type definition for block execution data
export type BlockExecution = {
  block_name: string;
  prompt: string;
  response: string;
};

export type TimelineDataPoint = {
  simulation_step: number;
  block_executions: BlockExecution[];
};

// Sample prompts and responses by block type
const SAMPLE_PROMPTS: Record<string, { prompt: string; response: string }> = {
  MobilityBlock: {
    prompt:
      "Given your current location and intention, determine the next destination. Consider weather conditions, time of day, and your current needs.",
    response:
      "Moving to workplace located at [coordinates: 40.7128, -74.0060]. Estimated travel time: 15 minutes. Mode: walking.",
  },
  CognitionBlock: {
    prompt:
      "Reflect on recent social interactions and evaluate your emotional state. Consider your personality traits and recent memories.",
    response:
      "Current emotional state: content (0.75). Recent interaction with colleague was positive. Memory updated with work achievement.",
  },
  EconomyBlock: {
    prompt:
      "Evaluate your current financial situation. Plan consumption based on income, savings, and current needs. Consider prices and taxes.",
    response:
      "Monthly budget: $3,500. Planned expenses: $2,800. Savings target: $700. Current consumption level: moderate.",
  },
  NeedsBlock: {
    prompt:
      "Assess your current physiological and psychological needs based on Maslow's hierarchy. Prioritize actions accordingly.",
    response:
      "Primary need: Physiological (hunger: 0.6). Secondary need: Social belonging (0.4). Action: Plan lunch break.",
  },
  OtherBlock: {
    prompt:
      "Handle routine activities that don't fall into specific categories. Consider time of day and energy levels.",
    response:
      "Entering rest state. Sleep duration planned: 7 hours. Alarm set for 6:30 AM.",
  },
  SocialBlock: {
    prompt:
      "Engage with nearby agents based on relationship strength and current context. Consider personality compatibility and discussion topics.",
    response:
      "Initiated conversation with friend. Topic: weekend plans. Relationship strength increased by 0.05. Duration: 20 minutes.",
  },
  PlanBlock: {
    prompt:
      "Create or update your daily plan based on current time, weather, needs, and obligations. Consider work schedule and personal goals.",
    response:
      "Daily plan updated: 9AM-5PM work, 6PM gym, 7PM dinner with family. Flexibility: medium. Contingency: rain backup plan.",
  },
  Dispatcher: {
    prompt:
      "Select the most appropriate block to execute next based on current context, needs, and intentions.",
    response:
      "Selected block: EconomyBlock (priority: high). Reason: work hours, income generation needed. Next: MobilityBlock.",
  },
};

// Sample data generator with prompt and response
const generateSampleData = (): TimelineDataPoint[] => {
  const data: TimelineDataPoint[] = [];

  for (let step = 0; step < 144; step++) {
    const hour = Math.floor(step / 6);
    let blockNames: string[] = [];

    // Simulate realistic patterns
    if (hour >= 0 && hour < 6) {
      blockNames = ["OtherBlock"];
    } else if (hour >= 6 && hour < 9) {
      blockNames = ["Dispatcher", "MobilityBlock", "NeedsBlock"];
    } else if (hour >= 9 && hour < 12) {
      blockNames = ["Dispatcher", "EconomyBlock", "CognitionBlock"];
    } else if (hour >= 12 && hour < 13) {
      blockNames = ["NeedsBlock", "SocialBlock"];
    } else if (hour >= 13 && hour < 18) {
      blockNames = ["Dispatcher", "EconomyBlock", "MobilityBlock"];
    } else if (hour >= 18 && hour < 22) {
      blockNames = ["SocialBlock", "NeedsBlock", "PlanBlock"];
    } else {
      blockNames = ["OtherBlock"];
    }

    // Create block executions with prompts and responses
    const block_executions: BlockExecution[] = blockNames.map((name) => ({
      block_name: name,
      prompt: SAMPLE_PROMPTS[name]?.prompt || `Execute ${name} at step ${step}`,
      response:
        SAMPLE_PROMPTS[name]?.response ||
        `Completed ${name} execution successfully`,
    }));

    data.push({
      simulation_step: step,
      block_executions,
    });
  }

  return data;
};

const DailySchedulePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { exp_id, name: EncodedName } = useParams<{
    exp_id?: string;
    name?: string;
  }>();
  const name = EncodedName ? decodeURIComponent(EncodedName) : "Experiment";

  // State for filters and data
  const [agentIds, setAgentIds] = useState<number[]>([]);
  const [totalDays, setTotalDays] = useState<number>(0);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [timelineData, setTimelineData] =
    useState<TimelineDataPoint[]>(generateSampleData());
  const [isRealData, setIsRealData] = useState(false);

  // Fetch experiment metadata (agent IDs and days)
  useEffect(() => {
    if (!exp_id) return;

    const fetchMetadata = async () => {
      try {
        setLoading(true);
        // TODO: Replace with actual API endpoint
        const res = await fetchCustom(
          `/api/experiments/${exp_id}/schedule-metadata`,
        );
        if (res.ok) {
          const data = await res.json();
          setAgentIds(data?.data?.agent_ids || []);
          setTotalDays(data?.data?.total_days || 1);
          // Set default selections
          if (data?.data?.agent_ids && data?.data?.agent_ids.length > 0) {
            setSelectedAgentId(data?.data?.agent_ids[0]);
          }
        } else {
          console.error("Failed to fetch metadata");
          // Set sample metadata for development
          setAgentIds([1, 2, 3, 4, 5]);
          setTotalDays(7);
          setSelectedAgentId(1);
        }
      } catch (error) {
        console.error("Error fetching metadata:", error);
        // Set sample metadata for development
        setAgentIds([1, 2, 3, 4, 5]);
        setTotalDays(7);
        setSelectedAgentId(1);
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();
  }, [exp_id]);

  // Fetch schedule data
  const handleFetchSchedule = async () => {
    if (!exp_id || selectedAgentId === null) return;

    try {
      setLoading(true);
      // TODO: Replace with actual API endpoint
      const res = await fetchCustom(
        `/api/experiments/${exp_id}/agent/${selectedAgentId}/schedule?day=${selectedDay}`,
      );

      if (res.ok) {
        const data = await res.json();
        setTimelineData(data?.data?.schedule || generateSampleData());
        setIsRealData(true);
      } else {
        console.error("Failed to fetch schedule data");
        setIsRealData(false);
      }
    } catch (error) {
      console.error("Error fetching schedule:", error);
      setIsRealData(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "24px" }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <h2 style={{ fontSize: 48 }}>
            Daily Schedule Timeline{name ? ` - ${name}` : ""}
          </h2>
        </Col>

        {/* Filter Controls */}
        <Col span={24}>
          <Card>
            <Space size="large" wrap>
              <div>
                <label
                  style={{
                    display: "block",
                    marginBottom: 8,
                    fontWeight: "bold",
                  }}
                >
                  Agent ID
                </label>
                <Select
                  showSearch
                  style={{ width: 200 }}
                  placeholder="Select Agent ID"
                  value={selectedAgentId}
                  onChange={(value) => setSelectedAgentId(value)}
                  options={agentIds.map((id) => ({
                    label: `Agent ${id}`,
                    value: id,
                  }))}
                  filterOption={(input, option) =>
                    (option?.label ?? "")
                      .toLowerCase()
                      .includes(input.toLowerCase())
                  }
                  disabled={loading || agentIds.length === 0}
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    marginBottom: 8,
                    fontWeight: "bold",
                  }}
                >
                  Day
                </label>
                <InputNumber
                  min={1}
                  max={totalDays}
                  value={selectedDay}
                  onChange={(value) => setSelectedDay(value || 1)}
                  style={{ width: 120 }}
                  disabled={loading}
                />
              </div>

              <div style={{ paddingTop: 28 }}>
                <Button
                  type="primary"
                  size="large"
                  onClick={handleFetchSchedule}
                  loading={loading}
                  disabled={selectedAgentId === null}
                >
                  Load Schedule
                </Button>
              </div>
            </Space>
          </Card>
        </Col>

        {/* Sample Data Warning */}
        {!isRealData && (
          <Col span={24}>
            <Alert
              message={
                <span style={{ color: "#ffffff", fontSize: "1.25rem" }}>
                  Sample Data
                </span>
              }
              description={
                <span style={{ color: "#fff", fontSize: "1rem" }}>
                  Currently showing sample/placeholder data. Select an agent and
                  day, then click 'Load Schedule' to view actual simulation
                  data.
                </span>
              }
              type="warning"
              showIcon
              closable
              style={{
                backgroundColor: "#5a5a5a",
                border: "1px solid #707070",
              }}
            />
          </Col>
        )}

        {/* Timeline Grid */}
        <Col span={24}>
          <Card
            title={
              <span>
                Daily Activity Timeline
                {isRealData && selectedAgentId !== null && (
                  <span
                    style={{
                      marginLeft: 16,
                      fontSize: 14,
                      fontWeight: "normal",
                      color: "#666",
                    }}
                  >
                    Agent {selectedAgentId} - Day {selectedDay}
                  </span>
                )}
              </span>
            }
          >
            <TimelineGrid timelineData={timelineData} />
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
};

export { BLOCKS, ATTRIBUTE_TO_EMOJI };
export default DailySchedulePage;

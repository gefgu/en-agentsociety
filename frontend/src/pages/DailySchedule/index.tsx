import { useEffect, useState, useRef } from "react";
import { Col, Row, Card } from 'antd';
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import TimelineGrid from "../../components/ScheduleTimeline";
import BlocksLegend from "../../components/ScheduleBlocksLegend";
import ScheduleAttributesLegend from "../../components/ScheduleAttributesLegend";

// Block definitions matching the Python code
const BLOCKS = [
  { emoji: '🏃', name: 'MobilityBlock', desc: 'Movement', color: '#E3F2FD' },
  { emoji: '🧠', name: 'CognitionBlock', desc: 'Emotions/Reflections', color: '#F3E5F5' },
  { emoji: '💰', name: 'EconomyBlock', desc: 'Income/Consumption', color: '#FFF9C4' },
  { emoji: '🔺', name: 'NeedsBlock', desc: "Maslow's Needs", color: '#FFECB3' },
  { emoji: '💤', name: 'OtherBlock', desc: 'Handle the rest', color: '#E0E0E0' },
  { emoji: '💬', name: 'SocialBlock', desc: 'Social Interactions', color: '#C8E6C9' },
  { emoji: '📅', name: 'PlanBlock', desc: 'Planning', color: '#FFCCBC' },
  { emoji: '🎯', name: 'Dispatcher', desc: 'Select Block', color: '#FFCDD2' },
];

// Attribute to emoji mapping
const ATTRIBUTE_TO_EMOJI: Record<string, string> = {
  // Mobility & Location
  "location": "🗺️",
  "radius": "⭕",
  "residence": "🏠",
  "work": "🏢",
  "city": "🏙️",

  // Environment & Time
  "weather": "☁️",
  "temperature": "🌡️",
  "environment_info": "🌳",
  "time": "⌚",

  // Demographics
  "name": "🏷️",
  "gender": "⚧",
  "age": "🎂",
  "race": "🌍",
  "religion": "🛐",
  "marriage_status": "💍",
  "background_story": "📜",

  // Internal State
  "emotion": "😶",
  "emotion_levels": "🎭",
  "thought": "💭",
  "memories": "🧠",
  "personality": "🧩",
  "topic": "💡",

  // Needs & Planning
  "needs": "🔋",
  "need": "🚨",
  "plan": "📝",
  "intention": "🎯",
  "intervention": "📢",
  "options": "🤔",
  "event": "🏁",
  "max_steps": "📏",
  "other": "ℹ️",

  // Economy & Work
  "occupation": "💼",
  "job": "⚒️",
  "education": "🎓",
  "income": "💵",
  "wealth": "💰",
  "hourly_rate": "⏱️",
  "taxes": "📉",
  "interest_rate": "📈",
  "prices": "🏷️",
  "consumption": "🛒",
  "consumption_level": "📊",
  "family_consumption": "👨‍👩‍👧",

  // Social
  "chat": "💬",
  "relationship_type": "🔗",
  "relationship_strength": "💪",
  "friend_info": "🤝",
  "discussion_constraint": "🤐",

  // Blocks
  "blocks": "📦"
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
    prompt: "Given your current location and intention, determine the next destination. Consider weather conditions, time of day, and your current needs.",
    response: "Moving to workplace located at [coordinates: 40.7128, -74.0060]. Estimated travel time: 15 minutes. Mode: walking."
  },
  CognitionBlock: {
    prompt: "Reflect on recent social interactions and evaluate your emotional state. Consider your personality traits and recent memories.",
    response: "Current emotional state: content (0.75). Recent interaction with colleague was positive. Memory updated with work achievement."
  },
  EconomyBlock: {
    prompt: "Evaluate your current financial situation. Plan consumption based on income, savings, and current needs. Consider prices and taxes.",
    response: "Monthly budget: $3,500. Planned expenses: $2,800. Savings target: $700. Current consumption level: moderate."
  },
  NeedsBlock: {
    prompt: "Assess your current physiological and psychological needs based on Maslow's hierarchy. Prioritize actions accordingly.",
    response: "Primary need: Physiological (hunger: 0.6). Secondary need: Social belonging (0.4). Action: Plan lunch break."
  },
  OtherBlock: {
    prompt: "Handle routine activities that don't fall into specific categories. Consider time of day and energy levels.",
    response: "Entering rest state. Sleep duration planned: 7 hours. Alarm set for 6:30 AM."
  },
  SocialBlock: {
    prompt: "Engage with nearby agents based on relationship strength and current context. Consider personality compatibility and discussion topics.",
    response: "Initiated conversation with friend. Topic: weekend plans. Relationship strength increased by 0.05. Duration: 20 minutes."
  },
  PlanBlock: {
    prompt: "Create or update your daily plan based on current time, weather, needs, and obligations. Consider work schedule and personal goals.",
    response: "Daily plan updated: 9AM-5PM work, 6PM gym, 7PM dinner with family. Flexibility: medium. Contingency: rain backup plan."
  },
  Dispatcher: {
    prompt: "Select the most appropriate block to execute next based on current context, needs, and intentions.",
    response: "Selected block: EconomyBlock (priority: high). Reason: work hours, income generation needed. Next: MobilityBlock."
  }
};

// Sample data generator with prompt and response
const generateSampleData = (): TimelineDataPoint[] => {
  const data: TimelineDataPoint[] = [];

  for (let step = 0; step < 144; step++) {
    const hour = Math.floor(step / 6);
    let blockNames: string[] = [];

    // Simulate realistic patterns
    if (hour >= 0 && hour < 6) {
      blockNames = ['OtherBlock'];
    } else if (hour >= 6 && hour < 9) {
      blockNames = ['Dispatcher', 'MobilityBlock', 'NeedsBlock'];
    } else if (hour >= 9 && hour < 12) {
      blockNames = ['Dispatcher', 'EconomyBlock', 'CognitionBlock'];
    } else if (hour >= 12 && hour < 13) {
      blockNames = ['NeedsBlock', 'SocialBlock'];
    } else if (hour >= 13 && hour < 18) {
      blockNames = ['Dispatcher', 'EconomyBlock', 'MobilityBlock'];
    } else if (hour >= 18 && hour < 22) {
      blockNames = ['SocialBlock', 'NeedsBlock', 'PlanBlock'];
    } else {
      blockNames = ['OtherBlock'];
    }

    // Create block executions with prompts and responses
    const block_executions: BlockExecution[] = blockNames.map(name => ({
      block_name: name,
      prompt: SAMPLE_PROMPTS[name]?.prompt || `Execute ${name} at step ${step}`,
      response: SAMPLE_PROMPTS[name]?.response || `Completed ${name} execution successfully`
    }));

    data.push({
      simulation_step: step,
      block_executions
    });
  }

  return data;
};

const DailySchedulePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { exp_id, name: EncodedName } = useParams<{ exp_id?: string, name?: string }>();
  const name = EncodedName ? decodeURIComponent(EncodedName) : 'Experiment';

  const [timelineData] = useState<TimelineDataPoint[]>(generateSampleData());

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <h2 style={{ fontSize: 48 }}>Daily Schedule Timeline{name ? ` - ${name}` : ''}</h2>
        </Col>
        
        {/* Timeline Grid */}
        <Col span={24}>
          <Card title="Daily Activity Timeline">
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
}

export { BLOCKS, ATTRIBUTE_TO_EMOJI };
export type { BlockExecution, TimelineDataPoint };

export default DailySchedulePage;
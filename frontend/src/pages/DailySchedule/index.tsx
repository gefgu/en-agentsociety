import { useEffect, useState, useRef } from "react";
import { Col, Row, Card } from 'antd';
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import BlocksLegend from "../../components/ScheduleBlocksLegend";
import ScheduleAttributesLegend from "../../components/ScheduleAttributesLegend";
import TimelineGrid from "../../components/ScheduleTimeline";

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




// Sample data generator (replace with API call)
const generateSampleData = () => {
  const data: Array<{ simulation_step: number; block_name: string[] }> = [];

  for (let step = 0; step < 144; step++) {
    const hour = Math.floor(step / 6);
    let blocks: string[] = [];

    // Simulate realistic patterns
    if (hour >= 0 && hour < 6) {
      // Night: mostly sleep
      blocks = ['OtherBlock'];
    } else if (hour >= 6 && hour < 9) {
      // Morning: mobility, needs, planning
      blocks = ['Dispatcher', 'MobilityBlock', 'NeedsBlock'];
    } else if (hour >= 9 && hour < 12) {
      // Work hours
      blocks = ['Dispatcher', 'EconomyBlock', 'CognitionBlock'];
    } else if (hour >= 12 && hour < 13) {
      // Lunch
      blocks = ['NeedsBlock', 'SocialBlock'];
    } else if (hour >= 13 && hour < 18) {
      // Afternoon work
      blocks = ['Dispatcher', 'EconomyBlock', 'MobilityBlock'];
    } else if (hour >= 18 && hour < 22) {
      // Evening: social, needs
      blocks = ['SocialBlock', 'NeedsBlock', 'PlanBlock'];
    } else {
      // Late evening
      blocks = ['OtherBlock'];
    }

    data.push({
      simulation_step: step,
      block_name: blocks
    });
  }

  return data;
};


const DailySchedulePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { exp_id, name: EncodedName } = useParams<{ exp_id?: string, name?: string }>();
  const name = EncodedName ? decodeURIComponent(EncodedName) : 'Experiment';

  const [timelineData] = useState(generateSampleData());

  console.log("Rendering DailySchedulePage");

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
        <Col span={10}>

          <h3 style={{ fontSize: 24, marginTop: 24 }}>Block Types</h3>
          <BlocksLegend />
        </Col>

        {/* Attribute Legend */}
        <Col span={14}>
          <h3 style={{ fontSize: 24, marginTop: 24 }}>Agent Attributes</h3>
          <Card>
            <ScheduleAttributesLegend />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export { BLOCKS, ATTRIBUTE_TO_EMOJI, }

export default DailySchedulePage;
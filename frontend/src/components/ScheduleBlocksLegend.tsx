import { Row, Col, Card } from "antd";
import { ATTRIBUTE_TO_EMOJI, BLOCKS } from "../pages/DailySchedule";

// Block to attributes mapping
const BLOCK_TO_ATTRIBUTES: Record<string, string[]> = {
  "MobilityBlock": [
    "plan", "intention", "radius", "weather", "temperature",
    "emotion", "thought", "residence", "work"
  ],
  "CognitionBlock": [
    "topic", "gender", "age", "race", "religion", "marriage_status",
    "residence", "occupation", "education", "personality", "consumption",
    "family_consumption", "income", "hourly_rate", "thought", "emotion",
    "emotion_levels", "memories"
  ],
  "EconomyBlock": [
    "plan", "intention", "emotion", "name", "age", "city", "job",
    "hourly_rate", "consumption", "wealth", "taxes", "prices", "interest_rate"
  ],
  "NeedsBlock": [
    "gender", "education", "consumption_level", "occupation", "age",
    "income", "time", "plan", "event", "needs", "need", "intervention", "intention"
  ],
  "OtherBlock": [
    "plan", "intention", "emotion"
  ],
  "PlanBlock": [
    "weather", "temperature", "need", "location", "time", "consumption",
    "job", "age", "emotion", "thought", "options", "other", "plan", "max_steps"
  ],
  "SocialBlock": [
    "name", "gender", "occupation", "education", "personality", "thought",
    "background_story", "relationship_type", "relationship_strength",
    "intention", "chat", "discussion_constraint", "environment_info",
    "friend_info", "emotion"
  ],
  "Dispatcher": [
    "intention", "blocks"
  ]
};

const BlocksLegend = () => {
  return (
    <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
      {BLOCKS.map((block) => (
        <Col key={block.name} xs={24} sm={12} md={12} lg={8} xl={6}>
          <Card
            style={{
              backgroundColor: block.color,
              border: '3px solid #333',
              borderRadius: 15,
              textAlign: 'center',
              minHeight: 200,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: 50 }}>{block.emoji}</div>
              <div style={{ fontSize: 18, fontWeight: 'bold', marginTop: 8 }}>
                {block.name}
              </div>
              <div style={{ fontSize: 14, color: '#333', marginTop: 4 }}>
                {block.desc}
              </div>
            </div>

            {/* Show attribute emojis for this block */}
            {BLOCK_TO_ATTRIBUTES[block.name] && (
              <div style={{ marginTop: 12, minHeight: 40 }}>
                {BLOCK_TO_ATTRIBUTES[block.name]
                  .filter(attr => ATTRIBUTE_TO_EMOJI[attr])
                  .map((attr, idx) => (
                    <span
                      key={idx}
                      title={attr}
                      style={{
                        fontSize: 18,
                        margin: '0 3px',
                        opacity: 1,
                        cursor: 'help'
                      }}
                    >
                      {ATTRIBUTE_TO_EMOJI[attr]}
                    </span>
                  ))}
              </div>
            )}
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export default BlocksLegend;
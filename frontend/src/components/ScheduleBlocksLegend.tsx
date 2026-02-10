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
    <div style={{ 
      padding: '25px',
      backgroundColor: 'white',
      borderRadius: '8px'
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
        gap: '16px',
        maxWidth: '100%'
      }}>
        {BLOCKS.map((block) => (
          <div
            key={block.name}
            style={{
              backgroundColor: block.color,
              border: '3px solid #333',
              borderRadius: '15px',
              padding: '24px 16px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'space-between',
              minHeight: '250px',
              transition: 'transform 0.2s, box-shadow 0.2s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '60px', lineHeight: 1 }}>
                {block.emoji}
              </div>
              <div style={{ 
                fontSize: '20px', 
                fontWeight: 'bold', 
                marginTop: '12px',
                color: '#000'
              }}>
                {block.name}
              </div>
              <div style={{ 
                fontSize: '15px', 
                color: '#333', 
                marginTop: '6px',
                lineHeight: 1.3
              }}>
                {block.desc}
              </div>
            </div>

            {/* Show attribute emojis for this block */}
            {BLOCK_TO_ATTRIBUTES[block.name] && (
              <div style={{ 
                marginTop: '16px', 
                minHeight: '50px',
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '6px'
              }}>
                {BLOCK_TO_ATTRIBUTES[block.name]
                  .filter(attr => ATTRIBUTE_TO_EMOJI[attr])
                  .map((attr, idx) => (
                    <span
                      key={idx}
                      title={attr.replace(/_/g, ' ')}
                      style={{
                        fontSize: '22px',
                        opacity: 0.85,
                        cursor: 'help',
                        transition: 'transform 0.15s, opacity 0.15s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.3)';
                        e.currentTarget.style.opacity = '1';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.opacity = '0.85';
                      }}
                    >
                      {ATTRIBUTE_TO_EMOJI[attr]}
                    </span>
                  ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default BlocksLegend;
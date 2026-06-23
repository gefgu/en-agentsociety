import { ATTRIBUTE_TO_EMOJI, BLOCKS } from "../pages/DailySchedule";
import { useTheme } from "../context/ThemeContext";
import "./ScheduleBlocksLegend.css";

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
  "OtherBlock": ["plan", "intention", "emotion"],
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
  "Dispatcher": ["intention", "blocks"]
};

const BlocksLegend = () => {
  const { theme } = useTheme();

  return (
    <div className="blocks-legend">
      <div className="blocks-grid">
        {BLOCKS.map((block) => (
          <div
            key={block.name}
            className="block-card"
            style={{ '--block-color': theme === 'dark' ? block.darkColor : block.lightColor } as React.CSSProperties}
          >
            <div className="block-card-header">
              <div className="block-emoji">{block.emoji}</div>
              <div className="block-name">{block.name}</div>
              <div className="block-desc">{block.desc}</div>
            </div>

            {BLOCK_TO_ATTRIBUTES[block.name] && (
              <div className="block-attrs">
                {BLOCK_TO_ATTRIBUTES[block.name]
                  .filter(attr => ATTRIBUTE_TO_EMOJI[attr])
                  .map((attr, i) => (
                    <span key={i} className="block-attr-emoji" title={attr.replace(/_/g, ' ')}>
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

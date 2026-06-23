import { ATTRIBUTE_TO_EMOJI } from "../pages/DailySchedule";
import "./ScheduleAttributesLegend.css";

const ScheduleAttributesLegend = () => {
  const ATTRIBUTES = Object.keys(ATTRIBUTE_TO_EMOJI).map(attr => ({
    emoji: ATTRIBUTE_TO_EMOJI[attr],
    name: attr.replace(/_/g, ' '),
    displayName: attr,
  }));

  return (
    <div className="attrs-legend">
      <div className="attrs-grid">
        {ATTRIBUTES.map((attr, i) => (
          <div key={i} className="attr-card" title={attr.displayName}>
            <div className="attr-emoji">{attr.emoji}</div>
            <div className="attr-name">
              {attr.name.split(' ').map((word, j) => (
                <div key={j}>{word}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScheduleAttributesLegend;

import { ATTRIBUTE_TO_EMOJI } from "../pages/DailySchedule";

const ScheduleAttributesLegend = () => {
  // Generate attributes list
  const ATTRIBUTES = Object.keys(ATTRIBUTE_TO_EMOJI).map(attr => ({
    emoji: ATTRIBUTE_TO_EMOJI[attr],
    name: attr.replace(/_/g, ' '),
    displayName: attr,
    color: '#D1C4E9'
  }));

  return (
    <div style={{ 
      padding: '25px',
      backgroundColor: 'white',
      borderRadius: '8px'
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(125px, 1fr))',
        gap: '10px',
        maxWidth: '100%'
      }}>
        {ATTRIBUTES.map((attr, idx) => (
          <div
            key={idx}
            style={{
              backgroundColor: attr.color,
              border: '3px solid #333333',
              borderRadius: '15px',
              padding: '16px 8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '125px',
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
            title={attr.displayName}
          >
            <div style={{
              fontSize: '42px',
              marginBottom: '8px',
              lineHeight: 1
            }}>
              {attr.emoji}
            </div>
            <div style={{
              fontSize: '16px',
              fontWeight: 'bold',
              textAlign: 'center',
              color: '#000000',
              wordBreak: 'break-word',
              lineHeight: '1.2'
            }}>
              {attr.name.split(' ').map((word, i) => (
                <div key={i}>{word}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScheduleAttributesLegend;
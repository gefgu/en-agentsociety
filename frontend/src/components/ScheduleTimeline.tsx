import { BLOCKS, BlockExecution, TimelineDataPoint, ATTRIBUTE_TO_EMOJI } from "../pages/DailySchedule";
import { useEffect, useState } from "react";
import { Modal, Typography, Tag } from "antd";

const { Title, Paragraph } = Typography;

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

const TimelineGrid = ({ timelineData }: { timelineData: TimelineDataPoint[] }) => {
  const [isBigScreen, setIsBigScreen] = useState(window.innerWidth >= 1400);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<BlockExecution | null>(null);

  useEffect(() => {
    const handleResize = () => {
      setIsBigScreen(window.innerWidth >= 1920);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Mapping for block emoji lookup
  const BLOCK_EMOJI_MAP = BLOCKS.reduce((acc, block) => {
    acc[block.name] = block.emoji;
    return acc;
  }, {} as Record<string, string>);

  // Dynamic columns based on screen size
  const columns = isBigScreen 
    ? [
        { start: 0, end: 4 },
        { start: 4, end: 8 },
        { start: 8, end: 12 },
        { start: 12, end: 16 },
        { start: 16, end: 20 },
        { start: 20, end: 24 }
      ]
    : [
        { start: 0, end: 6 },
        { start: 6, end: 12 },
        { start: 12, end: 18 },
        { start: 18, end: 24 }
      ];

  const intervalsPerColumn = isBigScreen ? 24 : 36;

  const getTimeLabel = (columnIndex: number, intervalIndex: number) => {
    const hoursPerColumn = isBigScreen ? 4 : 6;
    const startHour = columnIndex * hoursPerColumn;
    const hours = startHour + Math.floor(intervalIndex / 6);
    const minutes = (intervalIndex % 6) * 10;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  const getBlockExecutionsForInterval = (columnIndex: number, intervalIndex: number): BlockExecution[] => {
    const globalIdx = (columnIndex * intervalsPerColumn) + intervalIndex;
    if (globalIdx < timelineData.length) {
      return timelineData[globalIdx].block_executions || [];
    }
    return [];
  };

  const handleEmojiClick = (execution: BlockExecution) => {
    setSelectedExecution(execution);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedExecution(null);
  };

  return (
    <>
      <div style={{
        display: 'flex',
        gap: '40px',
        justifyContent: 'center',
        padding: '20px',
        backgroundColor: 'white',
        overflowX: 'auto',
        flexWrap: 'wrap'
      }}>
        {columns.map((column, colIndex) => (
          <div key={colIndex} style={{ display: 'flex', flexDirection: 'column', minWidth: '280px' }}>
            {/* Column Header */}
            <div style={{
              fontSize: '32px',
              fontWeight: 'bold',
              textAlign: 'center',
              marginBottom: '30px',
              color: '#000'
            }}>
              {`${column.start.toString().padStart(2, '0')}:00 - ${column.end.toString().padStart(2, '0')}:00`}
            </div>

            {/* Timeline Column */}
            <div style={{ display: 'flex', position: 'relative' }}>
              {/* Vertical Line */}
              <div style={{
                width: '5px',
                backgroundColor: '#000',
                position: 'absolute',
                left: '80px',
                top: 0,
                bottom: 0,
                zIndex: 1
              }} />

              {/* Time Labels and Emojis */}
              <div style={{ display: 'flex', flexDirection: 'column', width: '300px' }}>
                {Array.from({ length: intervalsPerColumn }).map((_, intervalIdx) => {
                  const executions = getBlockExecutionsForInterval(colIndex, intervalIdx);
                  const timeLabel = getTimeLabel(colIndex, intervalIdx);

                  return (
                    <div
                      key={intervalIdx}
                      style={{
                        height: '30px',
                        display: 'flex',
                        alignItems: 'center',
                        position: 'relative'
                      }}
                    >
                      {/* Time Label */}
                      <div style={{
                        fontSize: '22px',
                        textAlign: 'right',
                        width: '70px',
                        color: '#000',
                        fontFamily: 'system-ui, -apple-system, sans-serif'
                      }}>
                        {timeLabel}
                      </div>

                      {/* Tick Mark */}
                      <div style={{
                        width: '20px',
                        height: '2px',
                        backgroundColor: '#000',
                        marginLeft: '0px',
                        zIndex: 2,
                        position: 'relative'
                      }} />

                      {/* Emojis */}
                      <div style={{
                        display: 'flex',
                        gap: '10px',
                        marginLeft: '20px',
                        alignItems: 'center'
                      }}>
                        {executions.map((execution, stackIdx) => {
                          const emoji = BLOCK_EMOJI_MAP[execution.block_name] || '❓';
                          const block = BLOCKS.find(b => b.name === execution.block_name);
                          
                          return (
                            <span
                              key={stackIdx}
                              title={`${execution.block_name} - ${block?.desc || ''} (Click for details)`}
                              style={{
                                fontSize: '16px',
                                cursor: 'pointer',
                                transition: 'transform 0.15s',
                                display: 'inline-block'
                              }}
                              onClick={() => handleEmojiClick(execution)}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'scale(1.5)';
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'scale(1)';
                              }}
                            >
                              {emoji}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal for displaying prompt and response */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '32px' }}>
              {selectedExecution && BLOCK_EMOJI_MAP[selectedExecution.block_name]}
            </span>
            <span style={{ fontSize: '20px', fontWeight: 'bold' }}>
              {selectedExecution?.block_name}
            </span>
          </div>
        }
        open={modalOpen}
        onCancel={handleModalClose}
        footer={null}
        width={800}
        centered
      >
        {selectedExecution && (
          <div>
            {/* Required Attributes Section */}
            <div style={{ marginTop: 16, marginBottom: 24 }}>
              <Title level={4}>Required Attributes</Title>
              <div style={{
                backgroundColor: '#f9f9f9',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0'
              }}>
                {BLOCK_TO_ATTRIBUTES[selectedExecution.block_name] ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {BLOCK_TO_ATTRIBUTES[selectedExecution.block_name].map((attr, idx) => {
                      const emoji = ATTRIBUTE_TO_EMOJI[attr];
                      return (
                        <Tag
                          key={idx}
                          style={{
                            fontSize: '14px',
                            padding: '6px 12px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            border: '1px solid #d9d9d9',
                            borderRadius: '6px'
                          }}
                        >
                          {emoji && <span style={{ fontSize: '16px' }}>{emoji}</span>}
                          <span>{attr.replace(/_/g, ' ')}</span>
                        </Tag>
                      );
                    })}
                  </div>
                ) : (
                  <span style={{ color: '#999', fontStyle: 'italic' }}>No attributes defined</span>
                )}
              </div>
            </div>

            {/* Prompt Section */}
            <Title level={4}>Prompt</Title>
            <Paragraph
              style={{
                backgroundColor: '#f5f5f5',
                padding: '16px',
                borderRadius: '8px',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '14px'
              }}
            >
              {selectedExecution.prompt}
            </Paragraph>

            {/* Response Section */}
            <Title level={4} style={{ marginTop: 24 }}>Response</Title>
            <Paragraph
              style={{
                backgroundColor: '#e6f7ff',
                padding: '16px',
                borderRadius: '8px',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '14px',
                border: '1px solid #91d5ff'
              }}
            >
              {selectedExecution.response}
            </Paragraph>
          </div>
        )}
      </Modal>
    </>
  );
};

export default TimelineGrid;
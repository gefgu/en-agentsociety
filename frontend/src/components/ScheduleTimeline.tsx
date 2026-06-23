import { BLOCKS, BlockExecution, TimelineDataPoint, ATTRIBUTE_TO_EMOJI } from "../pages/DailySchedule";

type Block = typeof BLOCKS[0];
import { useEffect, useState } from "react";
import { Modal, Typography, Tag } from "antd";
import "./ScheduleTimeline.css";

const { Title } = Typography;

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

const TimelineGrid = ({ timelineData, blocks }: { timelineData: TimelineDataPoint[]; blocks?: Block[] }) => {
  const displayBlocks = blocks ?? BLOCKS;
  const [isBigScreen, setIsBigScreen] = useState(window.innerWidth >= 1400);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<BlockExecution | null>(null);

  useEffect(() => {
    const handleResize = () => setIsBigScreen(window.innerWidth >= 1920);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const BLOCK_EMOJI_MAP = displayBlocks.reduce((acc, block) => {
    acc[block.name] = block.emoji;
    return acc;
  }, {} as Record<string, string>);

  const columns = isBigScreen
    ? [{ start: 0, end: 4 }, { start: 4, end: 8 }, { start: 8, end: 12 },
       { start: 12, end: 16 }, { start: 16, end: 20 }, { start: 20, end: 24 }]
    : [{ start: 0, end: 6 }, { start: 6, end: 12 }, { start: 12, end: 18 }, { start: 18, end: 24 }];

  const intervalsPerColumn = isBigScreen ? 24 : 36;

  const getTimeLabel = (colIdx: number, intervalIdx: number) => {
    const hoursPerColumn = isBigScreen ? 4 : 6;
    const hours = colIdx * hoursPerColumn + Math.floor(intervalIdx / 6);
    const minutes = (intervalIdx % 6) * 10;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
  };

  const getExecutions = (colIdx: number, intervalIdx: number): BlockExecution[] => {
    const globalIdx = colIdx * intervalsPerColumn + intervalIdx;
    return globalIdx < timelineData.length ? timelineData[globalIdx].block_executions || [] : [];
  };

  return (
    <>
      <div className="timeline-wrapper">
        {columns.map((col, colIdx) => (
          <div key={colIdx} className="timeline-column">
            <div className="timeline-col-header">
              {`${String(col.start).padStart(2, '0')}:00 – ${String(col.end).padStart(2, '0')}:00`}
            </div>

            <div className="timeline-track">
              <div className="timeline-axis-line" />
              <div className="timeline-rows">
                {Array.from({ length: intervalsPerColumn }).map((_, intervalIdx) => {
                  const executions = getExecutions(colIdx, intervalIdx);
                  return (
                    <div key={intervalIdx} className="timeline-row">
                      <div className="timeline-time-label">{getTimeLabel(colIdx, intervalIdx)}</div>
                      <div className="timeline-tick" />
                      <div className="timeline-emojis">
                        {executions.map((exec, i) => {
                          const emoji = BLOCK_EMOJI_MAP[exec.block_name] || '❓';
                          const block = displayBlocks.find(b => b.name === exec.block_name);
                          return (
                            <span
                              key={i}
                              className="timeline-emoji"
                              title={`${exec.block_name} – ${block?.desc || ''} (click for details)`}
                              onClick={() => { setSelectedExecution(exec); setModalOpen(true); }}
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

      <Modal
        title={
          <span style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 32 }}>{selectedExecution && BLOCK_EMOJI_MAP[selectedExecution.block_name]}</span>
            <span style={{ fontSize: 20, fontWeight: 'bold' }}>{selectedExecution?.block_name}</span>
          </span>
        }
        open={modalOpen}
        onCancel={() => { setModalOpen(false); setSelectedExecution(null); }}
        footer={null}
        width={800}
        centered
      >
        {selectedExecution && (
          <div>
            <div style={{ marginTop: 16, marginBottom: 24 }}>
              <Title level={4}>Required Attributes</Title>
              <div className="modal-attrs-box">
                {BLOCK_TO_ATTRIBUTES[selectedExecution.block_name] ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {BLOCK_TO_ATTRIBUTES[selectedExecution.block_name].map((attr, i) => {
                      const emoji = ATTRIBUTE_TO_EMOJI[attr];
                      return (
                        <Tag key={i} style={{ fontSize: 14, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6, borderRadius: 6 }}>
                          {emoji && <span style={{ fontSize: 16 }}>{emoji}</span>}
                          <span>{attr.replace(/_/g, ' ')}</span>
                        </Tag>
                      );
                    })}
                  </div>
                ) : (
                  <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>No attributes defined</span>
                )}
              </div>
            </div>

            <Title level={4}>Prompt</Title>
            <p className="modal-prompt-box">{selectedExecution.prompt}</p>

            <Title level={4} style={{ marginTop: 24 }}>Response</Title>
            <p className="modal-response-box">{selectedExecution.response}</p>
          </div>
        )}
      </Modal>
    </>
  );
};

export default TimelineGrid;

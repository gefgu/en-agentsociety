import { BLOCKS, BlockExecution, TimelineDataPoint, ATTRIBUTE_TO_EMOJI, BLOCK_TO_ATTRIBUTES, BLOCK_NAME_ALIAS } from "../pages/DailySchedule";

type Block = typeof BLOCKS[0];
import { useEffect, useState } from "react";
import { Modal, Typography, Tag } from "antd";
import "./ScheduleTimeline.css";

const { Title } = Typography;

const resolveBlock = (raw: string) => BLOCK_NAME_ALIAS[raw] ?? raw;

const TimelineGrid = ({
  timelineData,
  blocks,
  stepColors,
}: {
  timelineData: TimelineDataPoint[];
  blocks?: Block[];
  stepColors?: string[];
}) => {
  const displayBlocks = blocks ?? BLOCKS;
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<BlockExecution | null>(null);

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const BLOCK_EMOJI_MAP = displayBlocks.reduce((acc, block) => {
    acc[block.name] = block.emoji;
    return acc;
  }, {} as Record<string, string>);

  // Dynamically reduce column count when rows are dense, to avoid emoji overflow.
  // Base is higher now that the timeline is full-width (not 2/3 of the page).
  const maxEmojisPerStep = timelineData.reduce(
    (mx, step) => Math.max(mx, step.block_executions?.length ?? 0),
    0,
  );
  const baseColumns = windowWidth >= 1800 ? 8 : windowWidth >= 1400 ? 6 : windowWidth >= 1000 ? 4 : 3;
  const numColumns = maxEmojisPerStep > 14 ? Math.min(baseColumns, 3)
    : maxEmojisPerStep > 8 ? Math.min(baseColumns, 4)
    : maxEmojisPerStep > 4 ? Math.min(baseColumns, 6)
    : baseColumns;

  const hoursPerCol = 24 / numColumns;
  const columns = Array.from({ length: numColumns }, (_, i) => ({
    start: i * hoursPerCol,
    end: (i + 1) * hoursPerCol,
  }));
  const intervalsPerColumn = 6 * hoursPerCol; // 6 ten-minute intervals per hour

  const getTimeLabel = (colIdx: number, intervalIdx: number) => {
    const hoursPerColumn = hoursPerCol;
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
                      <div
                        className="timeline-time-label"
                        style={{ color: stepColors?.[colIdx * intervalsPerColumn + intervalIdx] || undefined }}
                      >
                        {getTimeLabel(colIdx, intervalIdx)}
                      </div>
                      <div className="timeline-tick" />
                      <div className="timeline-emojis">
                        {executions.map((exec, i) => {
                          const resolved = resolveBlock(exec.block_name);
                          const emoji = BLOCK_EMOJI_MAP[resolved] || '❓';
                          const block = displayBlocks.find(b => b.name === resolved);
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
          selectedExecution && (() => {
            const resolved = resolveBlock(selectedExecution.block_name);
            return (
              <span style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 32 }}>{BLOCK_EMOJI_MAP[resolved]}</span>
                <span>
                  <span style={{ fontSize: 20, fontWeight: 'bold' }}>{selectedExecution.block_name}</span>
                  {resolved !== selectedExecution.block_name && (
                    <span style={{ fontSize: 13, color: 'var(--color-text-secondary, #888)', marginLeft: 8 }}>
                      ({resolved})
                    </span>
                  )}
                </span>
              </span>
            );
          })()
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
                {(() => {
                  const attrs = BLOCK_TO_ATTRIBUTES[resolveBlock(selectedExecution.block_name)];
                  return attrs ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {attrs.map((attr, i) => {
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
                  );
                })()}
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

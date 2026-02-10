import { BLOCKS, BlockExecution, TimelineDataPoint } from "../pages/DailySchedule";
import { useEffect, useState } from "react";
import { Modal, Typography } from "antd";

const { Title, Paragraph } = Typography;

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
            <Title level={4} style={{ marginTop: 16 }}>Prompt</Title>
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
import { ATTRIBUTE_TO_EMOJI, BLOCKS, BLOCK_TO_ATTRIBUTES } from "../pages/DailySchedule";
import { useTheme } from "../context/ThemeContext";
import "./ScheduleBlocksLegend.css";

type Block = typeof BLOCKS[0];

const BlocksLegend = ({ blocks }: { blocks?: Block[] }) => {
  const { theme } = useTheme();
  const displayBlocks = blocks ?? BLOCKS;

  return (
    <div className="blocks-legend">
      <div className="blocks-grid">
        {displayBlocks.map((block) => (
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

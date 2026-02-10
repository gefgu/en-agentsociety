import { useRef, useEffect } from "react";
import { BLOCKS } from "../pages/DailySchedule";

const TimelineGrid = ({ timelineData }: { timelineData: Array<{ simulation_step: number; block_name: string[] }> }) => {
  const svgRef = useRef<SVGSVGElement>(null);


  // Mapping for block emoji lookup
  const BLOCK_EMOJI_MAP = BLOCKS.reduce((acc, block) => {
    acc[block.name] = block.emoji;
    return acc;
  }, {} as Record<string, string>);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = svgRef.current;
    const intervalsPerColumn = 36; // 6 hours * 6 (10-minute intervals)
    const emojiSize = 16;
    const intervalHeight = 30;
    const marginLeft = 80;
    const marginRight = 20;
    const marginTop = 50;
    const marginBottom = 50;
    const columnSpacing = 40;
    const emojiSpacing = 10;

    const columnWidth = marginLeft + 200 + marginRight;
    const columnHeight = marginTop + (intervalsPerColumn * intervalHeight) + marginBottom;
    const totalWidth = (columnWidth * 4) + (columnSpacing * 3);
    const totalHeight = columnHeight;

    // Clear existing content
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }

    // Set SVG attributes
    svg.setAttribute('width', totalWidth.toString());
    svg.setAttribute('height', totalHeight.toString());
    svg.setAttribute('viewBox', `0 0 ${totalWidth} ${totalHeight}`);

    // Add white background
    const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    background.setAttribute('width', totalWidth.toString());
    background.setAttribute('height', totalHeight.toString());
    background.setAttribute('fill', 'white');
    svg.appendChild(background);

    // Draw each column
    for (let col = 0; col < 4; col++) {
      const colXOffset = col * (columnWidth + columnSpacing);
      const timelineX = colXOffset + marginLeft;
      const startHour = col * 6;
      const endHour = (col + 1) * 6;

      // Draw column header
      const header = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      header.setAttribute('x', (colXOffset + columnWidth / 2).toString());
      header.setAttribute('y', '25');
      header.setAttribute('font-family', 'system-ui, -apple-system, sans-serif');
      header.setAttribute('font-size', '32');
      header.setAttribute('font-weight', 'bold');
      header.setAttribute('text-anchor', 'middle');
      header.setAttribute('fill', '#000000');
      header.textContent = `${startHour.toString().padStart(2, '0')}:00 - ${endHour.toString().padStart(2, '0')}:00`;
      svg.appendChild(header);

      // Draw vertical timeline
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', timelineX.toString());
      line.setAttribute('y1', marginTop.toString());
      line.setAttribute('x2', timelineX.toString());
      line.setAttribute('y2', (columnHeight - marginBottom).toString());
      line.setAttribute('stroke', '#000000');
      line.setAttribute('stroke-width', '5');
      svg.appendChild(line);

      // Draw intervals
      for (let i = 0; i < intervalsPerColumn; i++) {
        const globalIdx = (col * intervalsPerColumn) + i;
        const yPos = marginTop + (i * intervalHeight);

        // Draw tick mark
        const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        tick.setAttribute('x1', (timelineX - 10).toString());
        tick.setAttribute('y1', yPos.toString());
        tick.setAttribute('x2', (timelineX + 10).toString());
        tick.setAttribute('y2', yPos.toString());
        tick.setAttribute('stroke', '#000000');
        tick.setAttribute('stroke-width', '2');
        svg.appendChild(tick);

        // Format time label
        const hours = startHour + Math.floor(i / 6);
        const minutes = (i % 6) * 10;
        const timeLabel = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;

        // Draw time label
        const timeText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        timeText.setAttribute('x', (timelineX - 15).toString());
        timeText.setAttribute('y', yPos.toString());
        timeText.setAttribute('font-family', 'system-ui, -apple-system, sans-serif');
        timeText.setAttribute('font-size', '22');
        timeText.setAttribute('text-anchor', 'end');
        timeText.setAttribute('dominant-baseline', 'middle');
        timeText.setAttribute('fill', '#000000');
        timeText.textContent = timeLabel;
        svg.appendChild(timeText);

        // Draw emojis for blocks
        if (globalIdx < timelineData.length) {
          const { block_name } = timelineData[globalIdx];

          if (block_name && block_name.length > 0) {
            block_name.forEach((blockName, stackIdx) => {
              const emoji = BLOCK_EMOJI_MAP[blockName] || '❓';
              const emojiX = timelineX + 30 + (stackIdx * (emojiSize + emojiSpacing));

              const emojiElem = document.createElementNS('http://www.w3.org/2000/svg', 'text');
              emojiElem.setAttribute('x', emojiX.toString());
              emojiElem.setAttribute('y', yPos.toString());
              emojiElem.setAttribute('font-family', 'system-ui, -apple-system, sans-serif');
              emojiElem.setAttribute('font-size', emojiSize.toString());
              emojiElem.setAttribute('text-anchor', 'start');
              emojiElem.setAttribute('dominant-baseline', 'middle');
              emojiElem.textContent = emoji;
              svg.appendChild(emojiElem);
            });
          }
        }
      }
    }
  }, [timelineData]);

  return <svg ref={svgRef} style={{ display: 'block', margin: '0 auto' }} />;
};


export default TimelineGrid;
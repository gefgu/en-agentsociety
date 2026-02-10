import { useRef, useEffect } from "react";
import { ATTRIBUTE_TO_EMOJI } from "../pages/DailySchedule";



  

const ScheduleAttributesLegend = () => {
  const svgRef = useRef<SVGSVGElement>(null);

  // Generate attributes list
  const ATTRIBUTES = Object.keys(ATTRIBUTE_TO_EMOJI).map(attr => ({
    emoji: ATTRIBUTE_TO_EMOJI[attr],
    name: attr.replace(/_/g, ' '),
    displayName: attr,
    color: '#D1C4E9'
  }));

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = svgRef.current;
    const boxSize = 125;
    const spacing = 10;
    const margin = 25;
    const gridCols = 10;
    const gridRows = Math.ceil(ATTRIBUTES.length / gridCols);

    const canvasWidth = margin * 2 + (boxSize * gridCols) + (spacing * (gridCols - 1));
    const canvasHeight = margin * 2 + (boxSize * gridRows) + (spacing * (gridRows - 1));

    const emojiSize = 42;
    const nameSize = 16;

    // Clear existing content
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }

    // Set SVG attributes
    svg.setAttribute('width', canvasWidth.toString());
    svg.setAttribute('height', canvasHeight.toString());
    svg.setAttribute('viewBox', `0 0 ${canvasWidth} ${canvasHeight}`);

    // Add white background
    const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    background.setAttribute('width', canvasWidth.toString());
    background.setAttribute('height', canvasHeight.toString());
    background.setAttribute('fill', 'white');
    svg.appendChild(background);

    // Draw each attribute box
    ATTRIBUTES.forEach((attr, idx) => {
      const row = Math.floor(idx / gridCols);
      const col = idx % gridCols;

      const x = margin + col * (boxSize + spacing);
      const y = margin + row * (boxSize + spacing);

      // Draw box background
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x.toString());
      rect.setAttribute('y', y.toString());
      rect.setAttribute('width', boxSize.toString());
      rect.setAttribute('height', boxSize.toString());
      rect.setAttribute('rx', '15');
      rect.setAttribute('ry', '15');
      rect.setAttribute('fill', attr.color);
      rect.setAttribute('stroke', '#333333');
      rect.setAttribute('stroke-width', '3');
      svg.appendChild(rect);

      // Draw emoji
      const emojiY = y + boxSize * 0.2;
      const emojiText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      emojiText.setAttribute('x', (x + boxSize / 2).toString());
      emojiText.setAttribute('y', (emojiY + emojiSize / 2).toString());
      emojiText.setAttribute('font-family', 'system-ui, -apple-system, sans-serif');
      emojiText.setAttribute('font-size', emojiSize.toString());
      emojiText.setAttribute('text-anchor', 'middle');
      emojiText.setAttribute('dominant-baseline', 'central');
      emojiText.setAttribute('fill', 'black');
      emojiText.textContent = attr.emoji;
      svg.appendChild(emojiText);

      // Draw name (handle multi-line)
      const nameY = y + boxSize * 0.7;
      const nameLines = attr.name.split(' ');
      nameLines.forEach((line, lineIdx) => {
        const lineOffset = (lineIdx - (nameLines.length - 1) / 2) * (nameSize + 2);
        const nameText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        nameText.setAttribute('x', (x + boxSize / 2).toString());
        nameText.setAttribute('y', (nameY + lineOffset).toString());
        nameText.setAttribute('font-family', 'system-ui, -apple-system, sans-serif');
        nameText.setAttribute('font-size', nameSize.toString());
        nameText.setAttribute('font-weight', 'bold');
        nameText.setAttribute('text-anchor', 'middle');
        nameText.setAttribute('dominant-baseline', 'middle');
        nameText.setAttribute('fill', '#000000');
        nameText.textContent = line;
        svg.appendChild(nameText);
      });
    });
  }, []);

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg ref={svgRef} style={{ display: 'block', margin: '0 auto' }} />
    </div>
  );
};


export default ScheduleAttributesLegend;
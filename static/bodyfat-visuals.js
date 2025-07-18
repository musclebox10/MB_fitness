document.addEventListener('DOMContentLoaded', function() {
  var el = document.getElementById('bodyfat-gauge');
  if (el) el.style.background = 'yellow';
});

function renderBodyFatGauge({percentage}) {
  // Responsive segmented arc gauge: 0-50 range, 10 segments, value in center
  const percent = Math.max(0, Math.min(percentage, 50));
  const minValue = 0, maxValue = 50;
  // Smaller for mobile
  const cx = 120, cy = 120, r = 95;
  const arcWidth = 22;
  const segmentCount = 10;
  const segmentColors = [
    '#43a047', '#66bb6a', '#aee571', '#ffee58', '#ffd54f',
    '#ffb300', '#ff7043', '#ef5350', '#bdbdbd', '#eeeeee'
  ];
  const svgW = 2*cx, svgH = cy+40;
  const valueFontSize = 48;

  function describeArc(cx, cy, r, startAngle, endAngle) {
    function polarToCartesian(cx, cy, r, angleDeg) {
      var angle = (angleDeg-90) * Math.PI / 180.0;
      return {
        x: cx + (r * Math.cos(angle)),
        y: cy + (r * Math.sin(angle))
      };
    }
    var start = polarToCartesian(cx, cy, r, startAngle);
    var end = polarToCartesian(cx, cy, r, endAngle);
    var arcSweep = (endAngle - startAngle) <= 180 ? "0" : "1";
    return [
      "M", start.x, start.y,
      "A", r, r, 0, arcSweep, 1, end.x, end.y
    ].join(" ");
  }

  let arcSegments = '';
  for (let i = 0; i < segmentCount; i++) {
    const segStart = 180 - (180/segmentCount)*i;
    const segEnd = 180 - (180/segmentCount)*(i+1);
    arcSegments += `<path d="${describeArc(cx, cy, r, segStart, segEnd)}" fill="none" stroke="${segmentColors[i]}" stroke-width="${arcWidth}" stroke-linecap="butt" />`;
  }

  document.getElementById('bodyfat-gauge').innerHTML = `
    <div style="display:flex;justify-content:center;align-items:center;width:100%;background:#fff;">
      <svg width="100%" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}" style="max-width:300px;background:#fff;">
        ${arcSegments}
        <text x="${cx}" y="${cy+28}" text-anchor="middle" font-size="${valueFontSize}" font-weight="bold" fill="#222" font-family="Montserrat,Inter,sans-serif">${percent.toFixed(1)}</text>
        <text x="${cx}" y="${cy+60}" text-anchor="middle" font-size="1.1em" font-weight="700" fill="#d32f2f" font-family="Montserrat,Inter,sans-serif">Body Fat %</text>
      </svg>
    </div>
  `;
}

function renderBodyFatBar({lean_mass_kg, fat_mass_kg}) {
  const total = lean_mass_kg + fat_mass_kg;
  const leanPercent = total ? (lean_mass_kg / total) * 100 : 0;
  const fatPercent = total ? (fat_mass_kg / total) * 100 : 0;
  document.getElementById('bodyfat-bar').innerHTML = `
    <div style="width:100%;max-width:300px;margin:0 auto;">
      <div style="font-size:1em;font-weight:700;margin-bottom:6px;">Lean Mass vs Fat Mass</div>
      <div style="display:flex;height:28px;border-radius:8px;overflow:hidden;border:1.5px solid #bbb;">
        <div style="width:${leanPercent}%;background:#4caf50;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;">
          ${lean_mass_kg > 0 ? lean_mass_kg.toFixed(1) + ' kg' : ''}
        </div>
        <div style="width:${fatPercent}%;background:#f44336;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;">
          ${fat_mass_kg > 0 ? fat_mass_kg.toFixed(1) + ' kg' : ''}
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:0.95em;margin-top:4px;">
        <span style="color:#4caf50;font-weight:600;">Lean Mass</span>
        <span style="color:#f44336;font-weight:600;">Fat Mass</span>
      </div>
    </div>
  `;
}

if (window.bodyFatData) {
  renderBodyFatGauge(window.bodyFatData);
  renderBodyFatBar(window.bodyFatData);
} 
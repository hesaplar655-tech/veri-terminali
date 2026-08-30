/**
 * Grafiklerin altina "tarih araligi" kaydiricisi ekler: mini bir onizleme
 * cizgisi + iki tutamacli bir secim kutusu. Secilen aralik degistikce
 * verilen Chart.js orneginin x ekseni min/max'ini gunceller (zoom).
 */
function createDateRangeSlider({ container, dates, values, chart, xScaleId = 'x' }) {
  const n = dates.length;
  if (n < 2) return;

  container.innerHTML = `
    <div class="drs-wrap">
      <canvas class="drs-sparkline"></canvas>
      <div class="drs-selection"></div>
      <input type="range" class="drs-handle drs-handle-left" min="0" max="${n - 1}" value="0" step="1">
      <input type="range" class="drs-handle drs-handle-right" min="0" max="${n - 1}" value="${n - 1}" step="1">
    </div>
    <div class="drs-labels">
      <span class="drs-label-left"></span>
      <button type="button" class="drs-reset btn-sm btn-sm-ghost">Tumunu goster</button>
      <span class="drs-label-right"></span>
    </div>
  `;

  const sparkCanvas = container.querySelector('.drs-sparkline');
  const selection = container.querySelector('.drs-selection');
  const leftHandle = container.querySelector('.drs-handle-left');
  const rightHandle = container.querySelector('.drs-handle-right');
  const labelLeft = container.querySelector('.drs-label-left');
  const labelRight = container.querySelector('.drs-label-right');
  const resetBtn = container.querySelector('.drs-reset');

  function drawSparkline() {
    const rect = sparkCanvas.getBoundingClientRect();
    if (rect.width === 0) return;
    const dpr = window.devicePixelRatio || 1;
    sparkCanvas.width = rect.width * dpr;
    sparkCanvas.height = rect.height * dpr;
    const ctx = sparkCanvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const w = rect.width, h = rect.height;
    ctx.clearRect(0, 0, w, h);
    const min = Math.min(...values), max = Math.max(...values);
    ctx.beginPath();
    values.forEach((v, i) => {
      const x = (i / (n - 1)) * w;
      const y = h - 4 - ((v - min) / (max - min || 1)) * (h - 8);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#4fd1c5';
    ctx.lineWidth = 1.25;
    ctx.stroke();
  }

  function updateSelection() {
    const l = parseInt(leftHandle.value, 10);
    const r = parseInt(rightHandle.value, 10);
    const lo = Math.min(l, r), hi = Math.max(l, r);
    const leftPct = (lo / (n - 1)) * 100;
    const rightPct = (hi / (n - 1)) * 100;
    selection.style.left = leftPct + '%';
    selection.style.width = Math.max(rightPct - leftPct, 0.5) + '%';
    labelLeft.textContent = dates[lo];
    labelRight.textContent = dates[hi];
    if (chart) {
      chart.options.scales[xScaleId].min = dates[lo];
      chart.options.scales[xScaleId].max = dates[hi];
      chart.update('none');
    }
  }

  leftHandle.addEventListener('input', () => {
    if (parseInt(leftHandle.value, 10) > parseInt(rightHandle.value, 10)) {
      leftHandle.value = rightHandle.value;
    }
    updateSelection();
  });
  rightHandle.addEventListener('input', () => {
    if (parseInt(rightHandle.value, 10) < parseInt(leftHandle.value, 10)) {
      rightHandle.value = leftHandle.value;
    }
    updateSelection();
  });
  resetBtn.addEventListener('click', () => {
    leftHandle.value = 0;
    rightHandle.value = n - 1;
    updateSelection();
  });

  window.addEventListener('resize', drawSparkline);
  requestAnimationFrame(() => {
    drawSparkline();
    updateSelection();
  });
}

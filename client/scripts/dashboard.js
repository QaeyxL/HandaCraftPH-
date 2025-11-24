// Small utilities: animate number change and update stats reactively
function animateValue(el, end, duration = 800) {
  if (!el) return;
  const start = parseInt(el.textContent.replace(/[^0-9\-]/g, '')) || 0;
  end = Number(end) || 0;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const value = Math.round(start + (end - start) * progress);
    el.textContent = String(value);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function updateStats(data = {}) {
  // Accept either { points: [...] } or { customersTotal: n, ordersCount: m }
  let totalCustomers = 0;
  let ordersCount = 0;
  if (Array.isArray(data.points)) {
    totalCustomers = data.points.reduce((s, p) => s + (p.customers || 0), 0);
    ordersCount = data.ordersCount != null ? data.ordersCount : data.points.length;
  } else {
    totalCustomers = Number(data.customersTotal) || 0;
    ordersCount = Number(data.ordersCount) || 0;
  }

  const custEl = document.querySelector('.div1 .stat-value');
  const ordersEl = document.querySelector('.div2 .stat-value');
  animateValue(custEl, totalCustomers);
  animateValue(ordersEl, ordersCount);
}

// Expose helper so future data loads can update the dashboard:
window.updateDashboardStats = updateStats;
window.fetchAndUpdateStats = async function(url) {
  try {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error('Fetch failed: ' + res.status);
    const json = await res.json();
    updateStats(json);
  } catch (e) {
    console.warn('fetchAndUpdateStats error', e);
  }
};

// --- Live charts using Chart.js ---
let monthlySalesChart = null;
let targetVsActualChart = null;

function buildMonthlySalesChart(ctx, labels = [], data = []) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not available — monthly sales chart will not render.');
    try {
      const holder = ctx && ctx.canvas ? ctx.canvas : (document.getElementById('monthly-sales-canvas'));
      if (holder) holder.parentElement.innerHTML = '<div class="text-muted">Chart library not loaded. Please ensure Chart.js is available.</div>';
    } catch (e) {}
    return null;
  }

  if (monthlySalesChart) {
    monthlySalesChart.data.labels = labels;
    monthlySalesChart.data.datasets[0].data = data;
    monthlySalesChart.update();
    return monthlySalesChart;
  }
  monthlySalesChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Sales',
        data: data,
        borderColor: '#1976d2',
        backgroundColor: 'rgba(25,118,210,0.08)',
        fill: true,
        tension: 0.3,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } }
    }
  });
  return monthlySalesChart;
}

function buildTargetVsActualChart(ctx, target = 1000, actual = 0) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not available — target chart will not render.');
    try {
      const holder = ctx && ctx.canvas ? ctx.canvas : (document.getElementById('target-vs-actual-canvas'));
      if (holder) holder.parentElement.innerHTML = '<div class="text-muted">Chart library not loaded. Please ensure Chart.js is available.</div>';
    } catch (e) {}
    return null;
  }

  if (targetVsActualChart) {
    targetVsActualChart.data.datasets[0].data = [actual, Math.max(0, target - actual)];
    targetVsActualChart.update();
    return targetVsActualChart;
  }
  targetVsActualChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Actual', 'Remaining to target'],
      datasets: [{
        data: [actual, Math.max(0, target - actual)],
        backgroundColor: ['#33a02c', '#e0e0e0']
      }]
    },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
  });
  return targetVsActualChart;
}

async function fetchDashboardStats(categoryId) {
  try {
    const base = (window.DASHBOARD_ENDPOINTS && window.DASHBOARD_ENDPOINTS.stats) || '/dashboard/stats/';
    const url = categoryId ? `${base}?category=${encodeURIComponent(categoryId)}` : base;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error('stats fetch failed ' + res.status);
    const json = await res.json();

    // update stat panels
    updateStats(json);

    // monthly sales: views return monthly_sales: [{year, month, total}, ...]
    const monthly = json.monthly_sales || [];
    const labels = monthly.map(m => `${m.year}-${String(m.month).padStart(2,'0')}`);
    const data = monthly.map(m => Number(m.total || 0));
    const msCtx = document.getElementById('monthly-sales-canvas');
    if (msCtx) buildMonthlySalesChart(msCtx.getContext('2d'), labels, data);

    // target vs actual: naive target = average of highest 3 months * 1.2 or fixed
    let target = 1000;
    if (data.length) {
      const top = data.slice().sort((a,b)=>b-a).slice(0,3);
      const avgTop = top.reduce((s,v)=>s+v,0)/Math.max(1,top.length);
      target = Math.round(avgTop * 1.2);
    }
    const actual = data.reduce((s,v)=>s+v,0);
    const tvCtx = document.getElementById('target-vs-actual-canvas');
    if (tvCtx) buildTargetVsActualChart(tvCtx.getContext('2d'), target, actual);

    // inCartTotal update (if present in payload)
    if (json.inCartTotal != null) {
      const cartEl = document.querySelector('.div-cart .stat-value');
      if (cartEl) animateValue(cartEl, Number(json.inCartTotal));
    }

  } catch (e) {
    console.warn('fetchDashboardStats error', e);
  }
}

async function fetchCartActivity() {
  try {
    const base = (window.DASHBOARD_ENDPOINTS && window.DASHBOARD_ENDPOINTS.cart_activity) || '/dashboard/cart-activity/';
    const res = await fetch(base, { cache: 'no-store' });
    if (!res.ok) throw new Error('cart activity fetch failed ' + res.status);
    const json = await res.json();
    const list = document.getElementById('recent-cart-activity');
    if (!list) return;
    const items = (json.cart_activity || []).slice(0,6);
    if (!items.length) {
      list.innerHTML = '<p class="text-muted">No recent cart activity.</p>';
      return;
    }
    const html = items.map(it=>`<div class="small mb-1"><strong>${it.buyer_username}</strong> added <em>${it.product_name}</em> x ${it.quantity}</div>`).join('');
    list.innerHTML = html;
  } catch (e) {
    console.warn('fetchCartActivity error', e);
  }
}

// Polling + initial load
function startDashboardLivePolling() {
  // initial category selection
  const catSelect = document.getElementById('dashboard-category');
  const currentCat = catSelect ? catSelect.value : '';
  fetchDashboardStats(currentCat);
  fetchCartActivity();

  // poll every 10 seconds
  setInterval(()=>{
    const cat = catSelect ? catSelect.value : '';
    fetchDashboardStats(cat);
    fetchCartActivity();
  }, 10000);

  // also refresh map points on the same interval
  setInterval(()=>{
    fetchMapPoints();
  }, 10000);

  if (catSelect) {
    catSelect.addEventListener('change', ()=>{
      fetchDashboardStats(catSelect.value);
    });
  }
}

// Start after DOM ready
document.addEventListener('DOMContentLoaded', ()=>{
  startDashboardLivePolling();
});

// --- Map points fetcher ---
async function fetchMapPoints() {
  try {
    const base = (window.DASHBOARD_ENDPOINTS && window.DASHBOARD_ENDPOINTS.map_points) || '/dashboard/map-points/';
    const res = await fetch(base, { cache: 'no-store' });
    if (!res.ok) throw new Error('map points fetch failed ' + res.status);
    const json = await res.json();
    const pts = (json.points || []).map(p => p);
    if (window.updateMapPoints) window.updateMapPoints(pts);
  } catch (e) {
    console.warn('fetchMapPoints error', e);
  }
}

am5.ready(function() {
  try {
    var root = am5.Root.new("ph-map");

    root.setThemes([
      am5themes_Animated.new(root)
    ]);

    var chart = root.container.children.push(
      am5map.MapChart.new(root, {
        panX: "none",
        panY: "none",
        projection: am5map.geoMercator()
      })
    );

    var polygonSeries = chart.series.push(
      am5map.MapPolygonSeries.new(root, {
        geoJSON: am5geodata_philippinesLow
      })
    );

    polygonSeries.mapPolygons.template.setAll({
      tooltipText: "{name}",
      interactive: true
    });

    // Define legend colors (hex) and use them for both legend and map fills
    const regionLegend = {
      "Luzon": "#FF5733",
      "Visayas": "#33FF57",
      "Mindanao": "#3357FF"
    };

    polygonSeries.mapPolygons.template.adapters.add("fill", function(fill, target) {
      const name = target.dataItem && target.dataItem.dataContext && target.dataItem.dataContext.name;
      if (name) {
        for (let region in regionLegend) {
          if (name.includes(region)) return am5.color(parseInt(regionLegend[region].slice(1), 16));
        }
      }
      return fill;
    });

    // Populate legend element (if present) using regionLegend mapping
    (function buildLegend() {
      let legendEl = document.getElementById('ph-legend');
      if (!legendEl) return;
      legendEl.innerHTML = '';
      for (const region of Object.keys(regionLegend)) {
        const item = document.createElement('div');
        item.className = 'item';
        const sw = document.createElement('span');
        sw.className = 'swatch';
        sw.style.background = regionLegend[region];
        const label = document.createElement('span');
        label.className = 'label';
        label.textContent = region;
        item.appendChild(sw);
        item.appendChild(label);
        legendEl.appendChild(item);
      }
    })();

    var pointSeries = chart.series.push(am5map.MapPointSeries.new(root, {}));
    pointSeries.bullets.push(function() {
      return am5.Bullet.new(root, {
        sprite: am5.Circle.new(root, {
          radius: 6,
          fill: am5.color(0xff0000),
          tooltipText: "{title}"
        })
      });
    });

    pointSeries.data.setAll([
      { title: "Manila", customers: 20, geometry: { type: "Point", coordinates: [120.9842, 14.5995] } }
    ]);
      // expose a reference and an updater so other code can refresh map points
      window.__am5PointSeries = pointSeries;
      window.updateMapPoints = function(points) {
        try {
          if (!window.__am5PointSeries) return;
          // points should be array of { title, customers, geometry: { type: 'Point', coordinates: [lng, lat] } }
          window.__am5PointSeries.data.setAll(points || []);
          // optionally update stat panels based on points
          try { updateStats({ points: points || [] }); } catch (e) {}
        } catch (e) { console.warn('updateMapPoints error', e); }
      };
    // Update dashboard stat panels (customers, orders) from map/sample data
    try {
      const points = [
        { title: "Manila", customers: 20, geometry: { type: "Point", coordinates: [120.9842, 14.5995] } }
      ];
      // update with animation
      updateStats({ points });
    } catch (e) {
      console.warn('Failed to update stat panels:', e);
    }
  } catch (e) {
    console.error('Map init error:', e);
    const mapEl = document.getElementById('ph-map');
    if (mapEl) {
      mapEl.innerHTML = '<div style="color:#900;padding:12px;background:#fff;border-radius:6px;">Map error: ' + (e && e.message ? e.message : e) + '</div>';
    }
  }
});

// Chat data
const chats = {
  1: [
    { type: "received", text: "What...???" },
    { type: "sent", text: "Praes gravida nibh vel velit aliquet. Aenean..." }
  ],
  2: [
    { type: "received", text: "Hey, any updates on my order?" },
    { type: "sent", text: "Yes, it’s being processed!" }
  ],
  3: [
    { type: "received", text: "Hello!" },
    { type: "sent", text: "Hi there, how can I help you?" }
  ]
};

const chatUsers = document.querySelectorAll(".chat-user");
const chatWindow = document.querySelector(".chat-window");
const messagesContainer = document.querySelector(".messages");
const usernameDisplay = document.querySelector(".chat-username");
const inputField = document.querySelector(".chat-input input");
const sendButton = document.querySelector(".chat-input button");

chatUsers.forEach(user => {
  user.addEventListener("click", () => {
    // Remove previous active state
    chatUsers.forEach(u => u.classList.remove("active"));
    user.classList.add("active");

    // Show chat window
    chatWindow.classList.remove("hidden");

    // Set username in header
    usernameDisplay.textContent = user.textContent;

    // Load messages
    const userId = user.getAttribute("data-user");
    const userMessages = chats[userId] || [];
    messagesContainer.innerHTML = "";

    userMessages.forEach(msg => {
      const div = document.createElement("div");
      div.classList.add("message", msg.type);
      div.textContent = msg.text;
      messagesContainer.appendChild(div);
    });
  });
});

// Send new message
sendButton.addEventListener("click", sendMessage);
inputField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

function sendMessage() {
  const text = inputField.value.trim();
  if (!text) return;
  
  const div = document.createElement("div");
  div.classList.add("message", "sent");
  div.textContent = text;
  messagesContainer.appendChild(div);

  inputField.value = "";
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
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
function fmtPHP(n){
  return '₱' + (Number(n)||0).toFixed(2);
}

async function fetchAdminSales(){
  const start = document.getElementById('adm-start').value;
  const end = document.getElementById('adm-end').value;
  const cat = document.getElementById('adm-category').value;
  let url = '/hc_app/admin/sales-api/';
  const params = new URLSearchParams();
  if(start) params.set('start_date', start);
  if(end) params.set('end_date', end);
  if(cat) params.set('category', cat);
  if(Array.from(params).length) url += '?' + params.toString();

  try{
    const res = await fetch(url, {cache:'no-store'});
    if(!res.ok) throw new Error('Fetch failed');
    const json = await res.json();
    document.getElementById('adm-total-sales').textContent = fmtPHP(json.total_sales);
    document.getElementById('adm-total-orders').textContent = json.total_orders;

    const bycat = document.getElementById('adm-by-category');
    bycat.innerHTML = '';
    if(Array.isArray(json.by_category) && json.by_category.length){
      const table = document.createElement('table');
      table.className = 'table table-sm';
      const tbody = document.createElement('tbody');
      json.by_category.forEach(b=>{
        const tr = document.createElement('tr');
        const td1 = document.createElement('td'); td1.textContent = b.category;
        const td2 = document.createElement('td'); td2.textContent = fmtPHP(b.total); td2.style.textAlign='right';
        tr.appendChild(td1); tr.appendChild(td2);
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      bycat.appendChild(table);
    } else {
      bycat.innerHTML = '<div class="text-muted">No category sales.</div>';
    }

    // timeseries render
    const ts = document.getElementById('adm-timeseries');
    ts.innerHTML = '';
    if(Array.isArray(json.timeseries) && json.timeseries.length){
      const max = Math.max(...json.timeseries.map(t=>Number(t.total)||0), 1);
      const wrap = document.createElement('div');
      wrap.style.display = 'flex'; wrap.style.gap='8px'; wrap.style.alignItems='end';
      json.timeseries.forEach(m=>{
        const barWrap = document.createElement('div');
        barWrap.style.width='64px'; barWrap.style.textAlign='center';
        const bar = document.createElement('div');
        const val = Number(m.total)||0; const pct = Math.round((val/max)*100);
        bar.style.height = Math.max(6,pct) + 'px'; bar.style.background = '#0d6efd'; bar.style.borderRadius='4px 4px 0 0';
        const lbl = document.createElement('div'); lbl.style.fontSize='11px'; lbl.textContent = new Date(m.year, m.month-1,1).toLocaleString(undefined,{month:'short'});
        const valL = document.createElement('div'); valL.style.fontSize='11px'; valL.textContent = fmtPHP(val);
        barWrap.appendChild(bar); barWrap.appendChild(valL); barWrap.appendChild(lbl);
        wrap.appendChild(barWrap);
      });
      ts.appendChild(wrap);
    } else {
      ts.innerHTML = '<div class="text-muted">No timeseries data.</div>';
    }

  }catch(e){
    console.warn('admin fetch error', e);
  }
}

window.addEventListener('DOMContentLoaded', ()=>{
  document.getElementById('adm-refresh').addEventListener('click', fetchAdminSales);
  // auto fetch on load
  fetchAdminSales();
});

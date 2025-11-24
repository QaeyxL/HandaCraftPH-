document.addEventListener('DOMContentLoaded', function() {
  const productIdEl = document.querySelector('[data-product-id]');
  if (!productIdEl) return;
  const productId = productIdEl.getAttribute('data-product-id');
  const attrContainer = document.getElementById('customization-panel');
  const priceEl = document.getElementById('custom-price');
  const basePriceEl = document.getElementById('base-price');

  async function fetchAttributes() {
    try {
      const res = await fetch(`/hc_app/product/${productId}/attributes/`);
      if (!res.ok) throw new Error('Network');
      const json = await res.json();
      renderAttributes(json.attributes || []);
    } catch (e) {
      console.warn('Failed to load attributes', e);
    }
  }

  function renderAttributes(attrs) {
    if (!attrContainer) return;
    attrContainer.innerHTML = '';
    attrs.forEach(attr => {
      const wrapper = document.createElement('div');
      wrapper.className = 'mb-2';
      const label = document.createElement('label');
      label.className = 'form-label';
      label.textContent = attr.name;
      wrapper.appendChild(label);

      if (attr.type === 'single') {
        const select = document.createElement('select');
        select.className = 'form-select attr-select';
        select.name = `attr_${attr.id}`;
        select.dataset.attrId = attr.id;
        const emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        emptyOpt.textContent = attr.required ? 'Select...' : 'None';
        select.appendChild(emptyOpt);
        attr.options.forEach(o => {
          const opt = document.createElement('option');
          opt.value = o.id;
          opt.textContent = o.value + (o.price_modifier && Number(o.price_modifier) ? ` (+₱${o.price_modifier})` : '');
          select.appendChild(opt);
        });
        wrapper.appendChild(select);
      } else if (attr.type === 'multi') {
        attr.options.forEach(o => {
          const div = document.createElement('div');
          div.className = 'form-check form-check-inline';
          const chk = document.createElement('input');
          chk.type = 'checkbox';
          chk.className = 'form-check-input attr-checkbox';
          chk.value = o.id;
          chk.id = `opt_${o.id}`;
          const lbl = document.createElement('label');
          lbl.className = 'form-check-label';
          lbl.setAttribute('for', chk.id);
          lbl.textContent = o.value + (o.price_modifier && Number(o.price_modifier) ? ` (+₱${o.price_modifier})` : '');
          div.appendChild(chk);
          div.appendChild(lbl);
          wrapper.appendChild(div);
        });
      } else if (attr.type === 'numeric') {
        const input = document.createElement('input');
        input.type = 'number';
        input.step = '0.01';
        input.className = 'form-control attr-numeric';
        input.name = `attr_${attr.id}`;
        wrapper.appendChild(input);
      }

      attrContainer.appendChild(wrapper);
    });

    // attach listeners
    attrContainer.querySelectorAll('.attr-select, .attr-checkbox, .attr-numeric').forEach(el => {
      el.addEventListener('change', calculatePrice);
    });
    calculatePrice();
  }

  async function calculatePrice() {
    const selected = [];
    attrContainer.querySelectorAll('.attr-select').forEach(s => { if (s.value) selected.push(s.value); });
    attrContainer.querySelectorAll('.attr-checkbox:checked').forEach(c => { selected.push(c.value); });
    // numeric values are passed as size_value if present
    let size_value = null;
    const numeric = attrContainer.querySelector('.attr-numeric');
    if (numeric && numeric.value) size_value = numeric.value;

    try {
      const body = { product_id: productId, selected_options: selected };
      if (size_value) body.size_value = size_value;
      const res = await fetch('/hc_app/product/calculate-price/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const json = await res.json();
      if (basePriceEl && json.base) basePriceEl.textContent = `₱${json.base}`;
      if (priceEl && json.final) priceEl.textContent = `₱${json.final}`;
    } catch (e) {
      console.warn('price calc error', e);
    }
  }

  fetchAttributes();
});

// Inventory Document Print System (Document Type 5 & 6)
// Uses c:\Users\User\Desktop\Baraa.html layout as print design for Type 5
// Uses c:\Users\User\Desktop\Baraa2.html layout as print design for Type 6

(function () {
    function buildBaraaHtml(data) {
        const docNo = data.documentNo || '';
        const docDate = data.documentDate || '';
        // Get organization name from globalConstants (context processor) or fallback
        const orgName = (window.globalConstants && window.globalConstants.COMPANY_NAME) || data.organizationName || 'Сити энерги ХХК';
        const orgRegister = (window.globalConstants && window.globalConstants.CONSTANT_8) || '';
        const supplierName = data.clientName || '';
        const supplierRegister = data.clientRegister || '';
        const description = data.description || '';
        const warehouseName = data.warehouseName || '';
        const items = Array.isArray(data.items) ? data.items : [];
        const isVat = data.isVat === true || data.isVat === 'Y' || data.isVat === 'y';
        const vatRate = data.vatRate || (window.globalConstants && window.globalConstants.VAT_RATE) || 0.10; // Default 10%

        // Build item rows HTML
        let itemsRowsHtml = '';
        let sumQty = 0;
        let sumTotal = 0;
        let sumVat = 0;
        let sumTotalWithVat = 0;
        
        items.forEach((it, idx) => {
            const no = it.no || String(idx + 1);
            const inventoryCode = it.inventoryCode || '';
            const name = it.name || '';
            const unit = it.unit || '';
            const qty = it.qty || '';
            const unitPrice = it.unitPrice || '';
            
            // Convert to numbers
            const toNum = v => parseFloat(String(v).replace(/,/g, '')) || 0;
            let qtyNum = toNum(qty);
            let total = toNum(it.total || '');
            
            // Format values for display
            const fmt = n => n.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const totalFormatted = fmt(total);
            
            // Sum for totals
            sumQty += qtyNum;
            sumTotal += total;
            
            itemsRowsHtml += `<tr>
        <td>${no}</td>
        <td>${inventoryCode}</td>
        <td>${name}</td>
        <td>${unit}</td>
        <td class="text-right">${qty}</td>
        <td class="text-right">${unitPrice}</td>
        <td class="text-right">${totalFormatted}</td>
      </tr>`;
        });
        
        if (!itemsRowsHtml) {
            itemsRowsHtml = '<tr><td colspan="7" style="text-align:center; padding:8px;">Мөр алга</td></tr>';
        }
        
        // Calculate VAT and totals
        if (isVat && sumTotal > 0) {
            sumVat = sumTotal * vatRate;
            sumTotalWithVat = sumTotal + sumVat;
        } else {
            sumVat = 0;
            sumTotalWithVat = sumTotal;
        }
        
        // Format function for totals
        const fmt = n => n.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        return `<!DOCTYPE html>
<html>
<head>
<title>Бараа материалын орлогын падаан</title>
<style>
  html { background-color: #f0f0f0; }
  body {
    font-family: Tahoma, sans-serif;
    color: #333;
    font-size: 11px;
    width: 210mm; padding: 15mm; margin: 20px auto; box-sizing: border-box;
    background-color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.15);
  }
  @page { size: A4; margin: 0; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; font-size: 11px; }
  .header-right { text-align: right; }
  .title { text-align: center; font-size: 13px; font-weight: bold; margin-bottom: 5px; }
  .subtitle { text-align: center; font-size: 11px; margin-bottom: 30px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; }
  .subtitle .document-no { grid-column: 2; justify-self: center; }
  .subtitle .document-date { grid-column: 3; justify-self: end; }
  .section { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 11px; }
  .section-left, .section-right { width: 48%; }
  .section-item { display: flex; margin-bottom: 5px; }
  .label { width: 150px; font-weight: normal; }
  .value { flex-grow: 1; border-bottom: 1px dotted #999; padding-left: 5px; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 11px; }
  th, td { border: 1px solid #333; padding: 8px; text-align: left; }
  th { background-color: #f2f2f2; text-align: center; }
  .text-right { text-align: right; }
  .footer { margin-top: 30px; font-size: 11px; }
  .footer-row { display: flex; margin-bottom: 15px; }
  .footer-label { width: 150px; }
  .footer-value { flex-grow: 1; border-bottom: 1px dotted #999; padding-left: 5px; }
  .signature-line { border-bottom: 1px dotted #999; flex-grow: 1; margin: 0 10px; }
  .footer-columns { display: flex; gap: 20px; align-items: flex-start; }
  .footer-left { width: 20%; }
  .footer-left .footer-label { display: block; margin-bottom: 8px; }
  .footer-right { flex: 1; }
  .button-container { text-align: center; margin-bottom: 20px; }
  .print-button, .close-button { padding: 8px 20px; margin: 0 10px; font-size: 11px; font-family: Tahoma, sans-serif; cursor: pointer; border: 1px solid #333; background-color: #f5f5f5; }
  .print-button:hover, .close-button:hover { background-color: #e0e0e0; }
  @media print { html, body { width: 100%; height: auto; min-height: auto; margin: 0; padding: 0; background-color: #fff; box-shadow: none; } .header { margin-top: 30px; } .header, .section, .footer-row, tr { page-break-inside: avoid; } .button-container { display: none; } }
</style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      Сангийн сайдын 2017 оны 12-р сарын 05-ны өдрийн <br>347 тоот тушаалын хавсралт
    </div>
    <div class="header-right">НХМаягт БМ-2</div>
  </div>

  <div class="title">Бараа материалын орлогын падаан</div>
  <div class="subtitle">
    <span class="document-no">${docNo}</span>
    <span class="document-date">${docDate}</span>
  </div>

  <div class="section">
    <div class="section-left">
      <div class="section-item"><span class="label">Байгууллагын нэр:</span><span class="value">${orgName}</span></div>
      <div class="section-item"><span class="label">Регистер :</span><span class="value">${orgRegister}</span></div>
      <div class="section-item"><span class="label">Гүйлгээний дэлгэрэнгүй:</span><span class="value">${description}</span></div>
      <div class="section-item"><span class="label">Агуулах:</span><span class="value">${warehouseName}</span></div>
    </div>
    <div class="section-right">
      <div class="section-item"><span class="label">Бэлтгэн нийлүүлэгчийн нэр :</span><span class="value">${supplierName}</span></div>
      <div class="section-item"><span class="label">Регистер :</span><span class="value">${supplierRegister}</span></div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>№</th>
        <th>Барааны код</th>
        <th>Бараа материалын нэр</th>
        <th>Нэгж</th>
        <th>Тоо ширхэг</th>
        <th>Нэгж үнэ</th>
        <th>Нийт үнэ</th>
      </tr>
    </thead>
    <tbody>
      ${itemsRowsHtml}
      <tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">Нийт дүн:</td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumQty)}</td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumTotal)}</td>
      </tr>
      ${isVat ? `<tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">НӨАТ:</td>
        <td></td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumVat)}</td>
      </tr>` : ''}
      <tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">Бүх дүн:</td>
        <td></td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumTotalWithVat)}</td>
      </tr>
    </tbody>
  </table>

  <div class="footer">
    <div class="footer-columns">
      <div class="footer-left">
        <span class="footer-label">Тэмдэг:</span>
      </div>
      <div class="footer-right">
        <div class="footer-row"><span class="footer-label">Хүлээлгэн өгсөн:</span><span class="signature-line"></span><span style="width: 150px; text-align: center;">/ ${supplierName || ''} /</span></div>
        <div class="footer-row"><span class="footer-label">Хүлээн авсан:</span><span class="signature-line"></span><span style="width: 150px; text-align: center;">/ ${data.createdBy || ''} /</span></div>
        <div class="footer-row"><span class="footer-label">Шалгасан нягтлан бодогч:</span><span class="signature-line"></span><span style="width: 150px; text-align: center;">/....................... /</span></div>
      </div>
    </div>
  </div>

  <div class="date-time" style="text-align:right; margin-top:20px; font-size:11px;">Хэвлэсэн огноо: ${new Date().toLocaleString('mn-MN')}</div>
  <div class="button-container">
    <button class="print-button" onclick="window.print()">Хэвлэх</button>
    <button class="close-button" onclick="window.close()">Хаах</button>
  </div>
</body>
</html>`;
    }

    function buildBaraa2Html(data) {
        const docNo = data.documentNo || '';
        const docDate = data.documentDate || '';
        // Get organization name from globalConstants (context processor) or fallback
        const orgName = (window.globalConstants && window.globalConstants.COMPANY_NAME) || data.organizationName || 'Сити энерги ХХК';
        const clientName = data.clientName || '';
        const clientRegister = data.clientRegister || '';
        const accountCode = data.accountCode || '';
        const accountName = data.accountName || '';
        const warehouseName = data.warehouseName || '';
        const description = data.description || '';
        const items = Array.isArray(data.items) ? data.items : [];
        const isVat = data.isVat === true || data.isVat === 'Y' || data.isVat === 'y';
        const vatRate = data.vatRate || (window.globalConstants && window.globalConstants.VAT_RATE) || 0.10; // Default 10%

        // Build item rows HTML
        let itemsRowsHtml = '';
        let sumQty = 0;
        let sumTotal = 0;
        let sumVat = 0;
        let sumTotalWithVat = 0;
        
        items.forEach((it, idx) => {
            const no = it.no || String(idx + 1);
            const inventoryCode = it.inventoryCode || '';
            const name = it.name || '';
            const unit = it.unit || '';
            const qty = it.qty || '';
            const unitPrice = it.unitPrice || '';
            
            // Convert to numbers
            const toNum = v => parseFloat(String(v).replace(/,/g, '')) || 0;
            let qtyNum = toNum(qty);
            let unitPriceNum = toNum(unitPrice);
            let total = toNum(it.total || '');
            
            // Format values for display
            const fmt = n => n.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const qtyFormatted = fmt(qtyNum);
            const unitPriceFormatted = fmt(unitPriceNum);
            const totalFormatted = fmt(total);
            
            // Sum for totals
            sumQty += qtyNum;
            sumTotal += total;
            
            itemsRowsHtml += `<tr>
        <td>${no}</td>
        <td>${inventoryCode}</td>
        <td>${name}</td>
        <td>${unit}</td>
        <td class="text-right">${qtyFormatted}</td>
        <td class="text-right">${unitPriceFormatted}</td>
        <td class="text-right">${totalFormatted}</td>
      </tr>`;
        });
        
        if (!itemsRowsHtml) {
            itemsRowsHtml = '<tr><td colspan="7" style="text-align:center; padding:8px;">Мөр алга</td></tr>';
        }
        
        // Calculate VAT and totals
        if (isVat && sumTotal > 0) {
            sumVat = sumTotal * vatRate;
            sumTotalWithVat = sumTotal + sumVat;
        } else {
            sumVat = 0;
            sumTotalWithVat = sumTotal;
        }
        
        // Format function for totals
        const fmt = n => n.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        return `<!DOCTYPE html>
<html>
<head>
<title>Бараа материалын зарлагын падаан</title>
<style>
  html { background-color: #f0f0f0; }
  body {
    font-family: Tahoma, sans-serif;
    color: #333;
    font-size: 11px;
    width: 210mm; padding: 15mm; margin: 20px auto; box-sizing: border-box;
    background-color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.15);
  }
  @page { size: A4; margin: 0; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; font-size: 11px; }
  .header-right { text-align: right; }
  .title { text-align: center; font-size: 13px; font-weight: bold; margin-bottom: 5px; margin-top: 15px; }
  .subtitle { text-align: center; font-size: 11px; margin-bottom: 30px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; }
  .subtitle .document-no { grid-column: 2; justify-self: center; }
  .subtitle .document-date { grid-column: 3; justify-self: end; }
  .section { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 11px; }
  .section-left, .section-right { width: 48%; }
  .section-item { display: flex; margin-bottom: 5px; }
  .label { width: 150px; font-weight: normal; }
  .value { flex-grow: 1; border-bottom: 1px dotted #999; padding-left: 5px; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 11px; }
  th, td { border: 1px solid #333; padding: 8px; text-align: left; }
  th { background-color: #f2f2f2; text-align: center; }
  .text-right { text-align: right; }
  .footer { margin-top: 30px; font-size: 11px; }
  .footer-columns { display: flex; gap: 20px; align-items: flex-start; }
  .footer-left { width: 15%; }
  .footer-left .footer-label { display: block; margin-bottom: 8px; }
  .footer-right { flex: 1; }
  .footer-row { display: flex; margin-bottom: 15px; white-space: nowrap; align-items: baseline; }
  .footer-label { width: 200px; white-space: nowrap; flex-shrink: 0; margin-right: 15px; }
  .signature-dots { white-space: nowrap; flex-grow: 1; min-width: 50px; margin-left: 15px; margin-right: 10px; }
  .signature-line { border-bottom: 1px dotted #999; flex-grow: 1; margin-left: 15px; margin-right: 10px; white-space: nowrap; }
  .signature-text { text-align: left; white-space: nowrap; }
  .date-time { text-align: right; margin-top: 20px; font-size: 11px; }
  .button-container { text-align: center; margin-bottom: 20px; }
  .print-button, .close-button { padding: 8px 20px; margin: 0 10px; font-size: 11px; font-family: Tahoma, sans-serif; cursor: pointer; border: 1px solid #333; background-color: #f5f5f5; }
  .print-button:hover, .close-button:hover { background-color: #e0e0e0; }
  @media print { html, body { width: 100%; height: auto; min-height: auto; margin: 0; padding: 0; background-color: #fff; box-shadow: none; } .header { margin-top: 30px; } .header, .section, .footer-row, .signature-item, tr { page-break-inside: avoid; } .button-container { display: none; } }
</style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      Сангийн сайдын 2017 оны 12-р сарын 05-ны өдрийн <br>347 тоот тушаалын хавсралт
    </div>
    <div class="header-right">НХМаягт БМ-3</div>
  </div>

  <div class="title">Бараа материалын зарлагын падаан</div>
  <div class="subtitle">
    <span class="document-no">${docNo}</span>
    <span class="document-date">${docDate}</span>
  </div>

  <div class="section">
    <div class="section-left">
      <div class="section-item"><span class="label">Байгууллагын нэр:</span><span class="value">${orgName}</span></div>
      <div class="section-item"><span class="label">Регистер :</span><span class="value">${(window.globalConstants && window.globalConstants.CONSTANT_8) || ''}</span></div>
      <div class="section-item"><span class="label">Дансны дугаар:</span><span class="value">${accountCode}</span></div>
      <div class="section-item"><span class="label">Дансны нэр:</span><span class="value">${accountName}</span></div>
      <div class="section-item"><span class="label">Агуулах:</span><span class="value">${warehouseName}</span></div>
      <div class="section-item"><span class="label">Гүйлгээний дэлгэрэнгүй:</span><span class="value">${description}</span></div>
    </div>
    <div class="section-right">
      <div class="section-item"><span class="label">Худалдaн авагчийн нэр :</span><span class="value">${clientName}</span></div>
      <div class="section-item"><span class="label">Регистер :</span><span class="value">${clientRegister}</span></div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>№</th>
        <th>Барааны код</th>
        <th>Бараа материалын нэр</th>
        <th>Хэмжих нэгж</th>
        <th>Тоо ширхэг</th>
        <th>Нэгж үнэ</th>
        <th>Нийт дүн</th>
      </tr>
    </thead>
    <tbody>
      ${itemsRowsHtml}
      <tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">Нийт дүн:</td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumQty)}</td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumTotal)}</td>
      </tr>
      ${isVat ? `<tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">НӨАТ:</td>
        <td></td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumVat)}</td>
      </tr>` : ''}
      <tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">Бүх дүн:</td>
        <td></td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumTotalWithVat)}</td>
      </tr>
    </tbody>
  </table>

  <div class="footer">
    <div class="footer-columns">
      <div class="footer-left">
        <span class="footer-label">Тэмдэг:</span>
      </div>
      <div class="footer-right">
        <div class="footer-row">
          <span class="footer-label">Хүлээлгэн өгсөн эд хариуцагч:</span>
          <span class="signature-dots">.........................</span>
          <span class="signature-text">/ /</span>
        </div>
        <div class="footer-row">
          <span class="footer-label">Хүлээн авсан:</span>
          <span class="signature-dots">.........................</span>
          <span class="signature-text">/ ${clientName || ''} /</span>
        </div>
        <div class="footer-row">
          <span class="footer-label">Шалгасан нягтлан бодогч:</span>
          <span class="signature-dots">.........................</span>
          <span class="signature-text">/ ${data.createdBy || ''} /</span>
        </div>
      </div>
    </div>
  </div>

  <div class="date-time">Хэвлэсэн огноо: ${new Date().toLocaleString('mn-MN')}</div>
  <div class="button-container">
    <button class="print-button" onclick="window.print()">Хэвлэх</button>
    <button class="close-button" onclick="window.close()">Хаах</button>
  </div>
</body>
</html>`;
    }

    function buildBaraa3Html(data) {
        const docNo = data.documentNo || '';
        const docDate = data.documentDate || '';
        // Get organization name from globalConstants (context processor) or fallback
        const orgName = (window.globalConstants && window.globalConstants.COMPANY_NAME) || data.organizationName || 'Сити энерги ХХК';
        const clientName = data.clientName || '';
        const clientRegister = data.clientRegister || '';
        const accountCode = data.accountCode || '';
        const accountName = data.accountName || '';
        const warehouseName = data.warehouseName || '';
        const description = data.description || '';
        const items = Array.isArray(data.items) ? data.items : [];

        // Build item rows HTML
        let itemsRowsHtml = '';
        let sumQty = 0;
        let sumTotal = 0;
        
        items.forEach((it, idx) => {
            const no = it.no || String(idx + 1);
            const inventoryCode = it.inventoryCode || '';
            const name = it.name || '';
            const unit = it.unit || '';
            const qty = it.qty || '';
            const unitPrice = it.unitPrice || '';
            
            // Convert to numbers
            const toNum = v => parseFloat(String(v).replace(/,/g, '')) || 0;
            let qtyNum = toNum(qty);
            let unitPriceNum = toNum(unitPrice);
            let total = toNum(it.total || '');
            
            // Format values for display
            const fmt = n => n.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const qtyFormatted = fmt(qtyNum);
            const unitPriceFormatted = fmt(unitPriceNum);
            const totalFormatted = fmt(total);
            
            // Sum for totals
            sumQty += qtyNum;
            sumTotal += total;
            
            itemsRowsHtml += `<tr>
        <td>${no}</td>
        <td>${inventoryCode}</td>
        <td>${name}</td>
        <td>${unit}</td>
        <td class="text-right">${qtyFormatted}</td>
        <td class="text-right">${unitPriceFormatted}</td>
        <td class="text-right">${totalFormatted}</td>
      </tr>`;
        });
        
        if (!itemsRowsHtml) {
            itemsRowsHtml = '<tr><td colspan="7" style="text-align:center; padding:8px;">Мөр алга</td></tr>';
        }
        
        // Format function for totals
        const fmt = n => n.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        return `<!DOCTYPE html>
<html>
<head>
<title>Бараа материалын зарлагын падаан</title>
<style>
  html { background-color: #f0f0f0; }
  body {
    font-family: Tahoma, sans-serif;
    color: #333;
    font-size: 11px;
    width: 210mm; padding: 15mm; margin: 20px auto; box-sizing: border-box;
    background-color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.15);
  }
  @page { size: A4; margin: 0; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; font-size: 11px; }
  .header-right { text-align: right; }
  .title { text-align: center; font-size: 13px; font-weight: bold; margin-bottom: 5px; margin-top: 15px; }
  .subtitle { text-align: center; font-size: 11px; margin-bottom: 30px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; }
  .subtitle .document-no { grid-column: 2; justify-self: center; }
  .subtitle .document-date { grid-column: 3; justify-self: end; }
  .section { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 11px; }
  .section-left, .section-right { width: 48%; }
  .section-item { display: flex; margin-bottom: 5px; }
  .label { width: 150px; font-weight: normal; }
  .value { flex-grow: 1; border-bottom: 1px dotted #999; padding-left: 5px; }
  table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 11px; }
  th, td { border: 1px solid #333; padding: 8px; text-align: left; }
  th { background-color: #f2f2f2; text-align: center; }
  .text-right { text-align: right; }
  .footer { margin-top: 30px; font-size: 11px; }
  .footer-columns { display: flex; gap: 20px; align-items: flex-start; }
  .footer-left { width: 15%; }
  .footer-left .footer-label { display: block; margin-bottom: 8px; }
  .footer-right { flex: 1; }
  .footer-row { display: flex; margin-bottom: 15px; white-space: nowrap; align-items: baseline; }
  .footer-label { width: 200px; white-space: nowrap; flex-shrink: 0; margin-right: 15px; }
  .signature-dots { white-space: nowrap; flex-grow: 1; min-width: 50px; margin-left: 15px; margin-right: 10px; }
  .signature-line { border-bottom: 1px dotted #999; flex-grow: 1; margin-left: 15px; margin-right: 10px; white-space: nowrap; }
  .signature-text { text-align: left; white-space: nowrap; }
  .date-time { text-align: right; margin-top: 20px; font-size: 11px; }
  .button-container { text-align: center; margin-bottom: 20px; }
  .print-button, .close-button { padding: 8px 20px; margin: 0 10px; font-size: 11px; font-family: Tahoma, sans-serif; cursor: pointer; border: 1px solid #333; background-color: #f5f5f5; }
  .print-button:hover, .close-button:hover { background-color: #e0e0e0; }
  @media print { html, body { width: 100%; height: auto; min-height: auto; margin: 0; padding: 0; background-color: #fff; box-shadow: none; } .header { margin-top: 30px; } .header, .section, .footer-row, .signature-item, tr { page-break-inside: avoid; } .button-container { display: none; } }
</style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      Сангийн сайдын 2017 оны 12-р сарын 05-ны өдрийн <br>347 тоот тушаалын хавсралт
    </div>
    <div class="header-right">НХМаягт БМ-3</div>
  </div>

  <div class="title">Бараа материалын зарлагын падаан</div>
  <div class="subtitle">
    <span class="document-no">${docNo}</span>
    <span class="document-date">${docDate}</span>
  </div>

  <div class="section">
    <div class="section-left">
      <div class="section-item"><span class="label">Байгууллагын нэр:</span><span class="value">${orgName}</span></div>
      <div class="section-item"><span class="label">Регистер :</span><span class="value">${(window.globalConstants && window.globalConstants.CONSTANT_8) || ''}</span></div>
      <div class="section-item"><span class="label">Дансны дугаар:</span><span class="value">${accountCode}</span></div>
      <div class="section-item"><span class="label">Дансны нэр:</span><span class="value">${accountName}</span></div>
      <div class="section-item"><span class="label">Агуулах:</span><span class="value">${warehouseName}</span></div>
      <div class="section-item"><span class="label">Гүйлгээний дэлгэрэнгүй:</span><span class="value">${description}</span></div>
    </div>
    <div class="section-right">
      <div class="section-item"><span class="label">Худалдaн авагчийн нэр :</span><span class="value">${clientName}</span></div>
      <div class="section-item"><span class="label">Регистер :</span><span class="value">${clientRegister}</span></div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>№</th>
        <th>Барааны код</th>
        <th>Бараа материалын нэр</th>
        <th>Хэмжих нэгж</th>
        <th>Тоо ширхэг</th>
        <th>Нэгж үнэ</th>
        <th>Нийт дүн</th>
      </tr>
    </thead>
    <tbody>
      ${itemsRowsHtml}
      <tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">Нийт дүн:</td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumQty)}</td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumTotal)}</td>
      </tr>
      <tr>
        <td colspan="4" style="text-align: right; font-weight: bold;">Бүх дүн:</td>
        <td></td>
        <td></td>
        <td class="text-right" style="font-weight: bold;">${fmt(sumTotal)}</td>
      </tr>
    </tbody>
  </table>

  <div class="footer">
    <div class="footer-columns">
      <div class="footer-left">
        <span class="footer-label">Тэмдэг:</span>
      </div>
      <div class="footer-right">
        <div class="footer-row">
          <span class="footer-label">Хүлээлгэн өгсөн эд хариуцагч:</span>
          <span class="signature-dots">.........................</span>
          <span class="signature-text">/ /</span>
        </div>
        <div class="footer-row">
          <span class="footer-label">Хүлээн авсан:</span>
          <span class="signature-dots">.........................</span>
          <span class="signature-text">/ ${clientName || ''} /</span>
        </div>
        <div class="footer-row">
          <span class="footer-label">Шалгасан нягтлан бодогч:</span>
          <span class="signature-dots">.........................</span>
          <span class="signature-text">/ ${data.createdBy || ''} /</span>
        </div>
      </div>
    </div>
  </div>

  <div class="date-time">Хэвлэсэн огноо: ${new Date().toLocaleString('mn-MN')}</div>
  <div class="button-container">
    <button class="print-button" onclick="window.print()">Хэвлэх</button>
    <button class="close-button" onclick="window.close()">Хаах</button>
  </div>
</body>
</html>`;
    }

    function printBaraaDoc(data) {
        const printWindow = window.open('', '_blank', 'width=900,height=700');
        printWindow.document.write(buildBaraaHtml(data));
        printWindow.document.close();
        printWindow.focus();
    }

    function printBaraa2Doc(data) {
        const printWindow = window.open('', '_blank', 'width=900,height=700');
        printWindow.document.write(buildBaraa2Html(data));
        printWindow.document.close();
        printWindow.focus();
    }

    function printBaraa3Doc(data) {
        const printWindow = window.open('', '_blank', 'width=900,height=700');
        printWindow.document.write(buildBaraa3Html(data));
        printWindow.document.close();
        printWindow.focus();
    }

    window.InvDocPrint = {
        print: function (documentData) {
            const dtid = parseInt(documentData.documentTypeId, 10);
            const dtcode = (documentData.documentTypeCode || '').trim();
            console.log('[InvDocPrint] payload:', documentData);
            if (dtid === 5) {
                printBaraaDoc(documentData);
                return;
            }
            if (dtid === 6) {
                printBaraa2Doc(documentData);
                return;
            }
            if (dtid === 7) {
                printBaraa3Doc(documentData);
                return;
            }
            alert(`This print design is only for Document Type 5, 6, or 7. Received: DocumentTypeId=${dtid}${dtcode ? `, DocumentTypeCode=${dtcode}` : ''}`);
        }
    };
})();


/**
 * Silicon4 Accounting - Document Print System
 * 
 * This system provides a flexible way to print different document types with unique styles.
 * 
 * Usage:
 * 1. Add new document types to DOCUMENT_PRINT_CONFIG
 * 2. Each document type can have custom title, subtitle, template, and CSS styles
 * 3. The system automatically generates print content based on document data
 * 4. Supports cash_document and ref_constant table data
 * 
 * To add a new document type:
 * - Add entry to DOCUMENT_PRINT_CONFIG with unique ID
 * - Define title, subtitle, template name, and custom CSS styles
 * - The system will automatically use the new configuration
 */

// Document Type Print Configuration
window.DOCUMENT_PRINT_CONFIG = {
    // Document Type 1: Receipt (Орлого) - Vertical Layout
    1: {
        title: 'Кассын Орлогын Ордер',
        subtitle: 'Cash Receipt Voucher',
        template: 'receipt',
        layout: 'vertical',
        style: `
            .header { background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
            .header h1 { margin: 0; font-size: 28px; font-weight: bold; }
            .header h2 { margin: 5px 0 0 0; font-size: 16px; opacity: 0.9; }
            .amount { color: #059669; font-weight: bold; font-size: 18px; }
            .section-header { background: #f0fdf4; color: #166534; padding: 10px 15px; border-left: 4px solid #10b981; margin: 20px 0 10px 0; font-weight: bold; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
            .info-item { background: #f9fafb; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; }
            .info-label { font-weight: bold; color: #374151; margin-bottom: 5px; }
            .info-value { color: #1f2937; }
        `
    },
    // Document Type 2: Payment (Зарлага) - Horizontal Layout
    2: {
        title: 'Кассын Зарлагын Ордер',
        subtitle: 'Cash Payment Voucher',
        template: 'payment',
        layout: 'horizontal',
        style: `
            .header { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
            .header h1 { margin: 0; font-size: 28px; font-weight: bold; }
            .header h2 { margin: 5px 0 0 0; font-size: 16px; opacity: 0.9; }
            .amount { color: #dc2626; font-weight: bold; font-size: 18px; }
            .section-header { background: #fef2f2; color: #991b1b; padding: 10px 15px; border-left: 4px solid #ef4444; margin: 20px 0 10px 0; font-weight: bold; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 20px 0; }
            .info-item { background: #f9fafb; padding: 12px; border-radius: 8px; border: 1px solid #e5e7eb; }
            .info-label { font-weight: bold; color: #374151; margin-bottom: 5px; font-size: 14px; }
            .info-value { color: #1f2937; font-size: 14px; }
        `
    },
    // Document Type 3: Transfer (Шилжүүлэг) - Compact Layout
    3: {
        title: 'Төлбөрийн даалгавар',
        subtitle: 'Payment Order',
        template: 'transfer',
        layout: 'compact',
        style: `
            .header { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
            .header h1 { margin: 0; font-size: 24px; font-weight: bold; }
            .header h2 { margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }
            .amount { color: #2563eb; font-weight: bold; font-size: 16px; }
            .section-header { background: #eff6ff; color: #1e40af; padding: 8px 12px; border-left: 4px solid #3b82f6; margin: 15px 0 8px 0; font-weight: bold; font-size: 14px; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
            .info-item { background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; }
            .info-label { font-weight: bold; color: #374151; margin-bottom: 3px; font-size: 12px; }
            .info-value { color: #1f2937; font-size: 13px; }
        `
    },
    // Document Type 4: Adjustment (Тохируулга) - Detailed Layout
    4: {
        title: 'Харилцахын орлого',
        subtitle: 'Account Receivable',
        template: 'adjustment',
        layout: 'detailed',
        style: `
            .header { background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; padding: 30px; border-radius: 15px; box-shadow: 0 6px 8px rgba(0,0,0,0.15); text-align: center; }
            .header h1 { margin: 0; font-size: 32px; font-weight: bold; }
            .header h2 { margin: 8px 0 0 0; font-size: 18px; opacity: 0.9; }
            .amount { color: #7c3aed; font-weight: bold; font-size: 20px; }
            .section-header { background: #faf5ff; color: #6b21a8; padding: 12px 18px; border-left: 5px solid #8b5cf6; margin: 25px 0 12px 0; font-weight: bold; font-size: 16px; }
            .info-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 25px 0; }
            .info-item { background: #f9fafb; padding: 18px; border-radius: 10px; border: 2px solid #e5e7eb; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .info-label { font-weight: bold; color: #374151; margin-bottom: 8px; font-size: 14px; }
            .info-value { color: #1f2937; font-size: 15px; }
        `
    }
};

// Generic Print Function
window.printDocument = function(documentId, documentNo, documentDate, description, createdBy, documentTypeId, documentData) {
    const config = window.DOCUMENT_PRINT_CONFIG[documentTypeId] || window.DOCUMENT_PRINT_CONFIG[1];
    const printWindow = window.open('', '_blank', 'width=800,height=600');
    
    const printContent = generatePrintContent(config, {
        documentId,
        documentNo,
        documentDate,
        description,
        createdBy,
        documentTypeId,
        ...documentData
    });
    
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
}

// Generate Print Content Based on Document Type
function generatePrintContent(config, data) {
    const baseStyles = `
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 30px; }
        .info-row { margin: 10px 0; display: flex; }
        .label { font-weight: bold; width: 150px; }
        .value { flex: 1; }
        .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #666; }
        .amount-section { background: #f9fafb; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .details-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .details-table th, .details-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .details-table th { background: #f3f4f6; }
        @media print {
            body { margin: 0; }
            .no-print { display: none; }
        }
    `;
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>${config.title} - ${data.documentNo}</title>
            <style>${baseStyles}${config.style}</style>
        </head>
        <body>
            <div class="header">
                <h1>${config.title}</h1>
                <h2>${config.subtitle}</h2>
            </div>
            
            ${generateDocumentInfoSection(config.layout, data)}
            
            ${generateAmountSection(config, data)}
            ${generateDetailsTable(data)}
            
            <div class="footer">
                <p>Silicon4 Accounting System</p>
                <p>Хэвлэсэн: ${new Date().toLocaleString('mn-MN')}</p>
            </div>
            
            <div class="no-print text-center mt-5">
                <button onclick="window.print()" class="px-5 py-2 m-1 bg-blue-600 text-white rounded hover:bg-blue-700">Хэвлэх</button>
                <button onclick="window.close()" class="px-5 py-2 m-1 bg-gray-600 text-white rounded hover:bg-gray-700">Хаах</button>
            </div>
        </body>
        </html>
    `;
}

// Generate Amount Section Based on Document Type
function generateAmountSection(config, data) {
    const currencySymbol = data.currencyName === 'MNT' ? '₮' : data.currencyName || '';
    
    return `
        <div class="amount-section">
            <h3>Дүнгийн мэдээлэл</h3>
            <div class="info-row">
                <span class="label">Валют:</span>
                <span class="value">${data.currencyName || '-'}</span>
            </div>
            <div class="info-row">
                <span class="label">Валютын дүн:</span>
                <span class="value amount">${data.currencyAmount || '0.00'} ${currencySymbol}</span>
            </div>
            <div class="info-row">
                <span class="label">Ханш:</span>
                <span class="value">${data.currencyExchange || '1.0000'}</span>
            </div>
            <div class="info-row">
                <span class="label">Монгол төгрөг:</span>
                <span class="value amount">${data.currencyMNT || '0.00'} ₮</span>
            </div>
            ${data.isVat ? `
                <div class="info-row">
                    <span class="label">НӨТ:</span>
                    <span class="value amount">${data.vatAmount || '0.00'} ₮</span>
                </div>
            ` : ''}
        </div>
    `;
}

// Get Document Details from Detail Grid
function getDocumentDetails(documentId) {
    const details = [];
    const detailRows = document.querySelectorAll('#detail-grid-container tbody tr');
    
    detailRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 10) {
            const detail = {
                accountCode: cells[0]?.textContent.trim() || '-',
                clientName: cells[1]?.textContent.trim() || '-',
                currencyName: cells[2]?.textContent.trim() || '-',
                currencyExchange: cells[3]?.textContent.trim() || '1.0000',
                currencyAmount: cells[4]?.textContent.trim() || '0.00',
                isDebit: cells[5]?.textContent.trim().includes('Дебит') || false,
                debitAmount: cells[6]?.textContent.trim() || '0.00',
                creditAmount: cells[7]?.textContent.trim() || '0.00',
                cashFlowName: cells[8]?.textContent.trim() || '-',
                contractName: cells[9]?.textContent.trim() || '-'
            };
            details.push(detail);
        }
    });
    
    return details;
}

// Generate Details Table
function generateDetailsTable(data) {
    if (!data.details || data.details.length === 0) {
        return '';
    }
    
    let tableRows = '';
    data.details.forEach(detail => {
        tableRows += `
            <tr>
                <td>${detail.accountCode || '-'}</td>
                <td>${detail.clientName || '-'}</td>
                <td>${detail.currencyName || '-'}</td>
                <td>${detail.currencyExchange || '1.0000'}</td>
                <td>${detail.currencyAmount || '0.00'}</td>
                <td>${detail.isDebit ? 'Дебит' : 'Кредит'}</td>
                <td>${detail.debitAmount || '0.00'}</td>
                <td>${detail.creditAmount || '0.00'}</td>
                <td>${detail.cashFlowName || '-'}</td>
                <td>${detail.contractName || '-'}</td>
            </tr>
        `;
    });
    
    return `
        <table class="details-table">
            <thead>
                <tr>
                    <th>Данс</th>
                    <th>Харилцагч</th>
                    <th>Валют</th>
                    <th>Ханш</th>
                    <th>Валютын дүн</th>
                    <th>БТ</th>
                    <th>Дебит</th>
                    <th>Кредит</th>
                    <th>Мөнгөн гүйлгээ</th>
                    <th>Гэрээ</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
    `;
}

// Generate Document Info Section Based on Layout
function generateDocumentInfoSection(layout, data) {
    switch(layout) {
        case 'vertical':
            return generateVerticalInfoSection(data);
        case 'horizontal':
            return generateHorizontalInfoSection(data);
        case 'compact':
            return generateCompactInfoSection(data);
        case 'detailed':
            return generateDetailedInfoSection(data);
        default:
            return generateVerticalInfoSection(data);
    }
}

// Vertical Layout - 2 column grid
function generateVerticalInfoSection(data) {
    return `
        <div class="section-header">Баримтын мэдээлэл</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Баримтын дугаар</div>
                <div class="info-value">${data.documentNo}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Огноо</div>
                <div class="info-value">${data.documentDate}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Тайлбар</div>
                <div class="info-value">${data.description}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Харилцагч</div>
                <div class="info-value">${data.clientName || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Данс</div>
                <div class="info-value">${data.accountName || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Үүсгэсэн</div>
                <div class="info-value">${data.createdBy || 'N/A'}</div>
            </div>
        </div>
    `;
}

// Horizontal Layout - 3 column grid
function generateHorizontalInfoSection(data) {
    return `
        <div class="section-header">Баримтын мэдээлэл</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Баримтын дугаар</div>
                <div class="info-value">${data.documentNo}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Огноо</div>
                <div class="info-value">${data.documentDate}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Харилцагч</div>
                <div class="info-value">${data.clientName || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Данс</div>
                <div class="info-value">${data.accountName || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Үүсгэсэн</div>
                <div class="info-value">${data.createdBy || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Тайлбар</div>
                <div class="info-value">${data.description}</div>
            </div>
        </div>
    `;
}

// Compact Layout - 2 column grid with smaller spacing
function generateCompactInfoSection(data) {
    return `
        <div class="section-header">Баримтын мэдээлэл</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Дугаар</div>
                <div class="info-value">${data.documentNo}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Огноо</div>
                <div class="info-value">${data.documentDate}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Харилцагч</div>
                <div class="info-value">${data.clientName || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Данс</div>
                <div class="info-value">${data.accountName || 'N/A'}</div>
            </div>
        </div>
        <div class="info-item mt-2">
            <div class="info-label">Тайлбар</div>
            <div class="info-value">${data.description}</div>
        </div>
    `;
}

// Detailed Layout - 3 column grid with enhanced styling
function generateDetailedInfoSection(data) {
    return `
        <div class="section-header">Баримтын дэлгэрэнгүй мэдээлэл</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Баримтын дугаар</div>
                <div class="info-value">${data.documentNo}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Огноо</div>
                <div class="info-value">${data.documentDate}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Үүсгэсэн</div>
                <div class="info-value">${data.createdBy || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Харилцагч</div>
                <div class="info-value">${data.clientName || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Данс</div>
                <div class="info-value">${data.accountName || 'N/A'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Статус</div>
                <div class="info-value">Идэвхтэй</div>
            </div>
        </div>
        <div class="info-item mt-4">
            <div class="info-label">Тайлбар</div>
            <div class="info-value">${data.description}</div>
        </div>
    `;
}

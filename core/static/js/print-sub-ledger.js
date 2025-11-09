/**
 * Subsidiary Ledger Print System
 * 
 * Handles landscape A4 printing for subsidiary ledger tables
 * 
 * Usage:
 * window.printSubLedgerTable({
 *     title: 'АВЛАГА,ӨГЛӨГИЙН ТУСЛАХ ДЭВТЭР',
 *     startDate: '2025-01-01',
 *     endDate: '2025-01-31',
 *     accountCode: '1010',
 *     accountName: 'Бэлэн мөнгө',
 *     clientName: 'Client Name (optional)',
 *     allData: subsidiaryLedgerData,
 *     columnHeaders: ['Огноо', 'Баримтын дугаар', 'Харилцагч', ...],
 *     totals: { debit: totalDebit, credit: totalCredit }
 * })
 */

(function() {
    'use strict';

    /**
     * Format number with Mongolian locale
     */
    function formatNumber(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) return '0.00';
        return parseFloat(value).toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    /**
     * Format date for display
     */
    function formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('mn-MN', { 
                year: 'numeric', 
                month: '2-digit', 
                day: '2-digit' 
            });
        } catch (e) {
            return dateString;
        }
    }

    /**
     * Get current date/time formatted
     */
    function getCurrentDateTime() {
        const now = new Date();
        return now.toLocaleString('mn-MN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Escape template literal special characters
     */
    function escapeTemplateLiteral(str) {
        if (typeof str !== 'string') return String(str || '');
        return str.replace(/`/g, '\\`').replace(/\$\{/g, '\\${');
    }

    /**
     * Map data field names to column headers for subsidiary ledger
     */
    function getDataFieldMapping() {
        return {
            'Огноо': 'DocumentDate',
            'Баримтын дугаар': 'DocumentNo',
            'Харилцагч': 'ClientName',
            'Гүйлгээний утга': 'Description',
            'Валют': 'CurrencyName',
            'Ханш': 'CurrencyExchange',
            'Валютын дүн': 'CurrencyAmount',
            'Дт дүн': 'DebitAmount',
            'Кт дүн': 'CreditAmount'
        };
    }

    /**
     * Generate HTML table rows from data
     */
    function generateTableRows(data, columnHeaders, fieldMapping) {
        let html = '';
        
        data.forEach((item, index) => {
            html += '<tr>';
            
            columnHeaders.forEach(header => {
                const fieldName = fieldMapping[header];
                if (!fieldName) {
                    html += '<td></td>';
                    return;
                }
                
                let value = item[fieldName] || '';
                
                // Format numeric values
                let isNumeric = false;
                if (fieldName === 'CurrencyAmount' || 
                    fieldName === 'CurrencyExchange' || 
                    fieldName === 'DebitAmount' || 
                    fieldName === 'CreditAmount') {
                    value = formatNumber(value, fieldName === 'CurrencyExchange' ? 4 : 2);
                    isNumeric = true;
                } else if (fieldName === 'DocumentDate') {
                    value = formatDate(value);
                }
                
                // Right-align numeric columns
                const alignClass = isNumeric ? ' class="text-right"' : '';
                html += `<td${alignClass}>${value}</td>`;
            });
            
            html += '</tr>';
        });
        
        return html;
    }

    /**
     * Generate print HTML content
     */
    function generatePrintHTML(config) {
        const fieldMapping = getDataFieldMapping();
        const tableRows = generateTableRows(config.allData, config.columnHeaders, fieldMapping);
        
        // Build metadata info
        const metaInfo = [];
        if (config.startDate || config.endDate) {
            metaInfo.push(`<span><strong>Хугацаа:</strong> ${formatDate(config.startDate)} - ${formatDate(config.endDate)}</span>`);
        }
        if (config.accountCode || config.accountName) {
            const accountInfo = [config.accountCode, config.accountName].filter(Boolean).join(' - ');
            metaInfo.push(`<span><strong>Данс:</strong> ${escapeTemplateLiteral(accountInfo)}</span>`);
        }
        if (config.clientName) {
            metaInfo.push(`<span><strong>Харилцагч:</strong> ${escapeTemplateLiteral(config.clientName)}</span>`);
        }
        metaInfo.push(`<span><strong>Хэвлэсэн огноо:</strong> ${getCurrentDateTime()}</span>`);
        
        // Build summary info
        const summaryInfo = [];
        if (config.summary) {
            if (config.summary.beginBalance !== undefined && config.summary.beginBalance !== 0) {
                summaryInfo.push(`<span><strong>Эхний үлдэгдэл:</strong> ${formatNumber(config.summary.beginBalance, 2)}</span>`);
            }
            if (config.summary.debitTotal !== undefined && config.summary.debitTotal !== 0) {
                summaryInfo.push(`<span><strong>Дебит гүйлгээ:</strong> ${formatNumber(config.summary.debitTotal, 2)}</span>`);
            }
            if (config.summary.creditTotal !== undefined && config.summary.creditTotal !== 0) {
                summaryInfo.push(`<span><strong>Кредит гүйлгээ:</strong> ${formatNumber(config.summary.creditTotal, 2)}</span>`);
            }
            if (config.summary.endBalance !== undefined && config.summary.endBalance !== 0) {
                summaryInfo.push(`<span><strong>Эцсийн үлдэгдэл:</strong> ${formatNumber(config.summary.endBalance, 2)}</span>`);
            }
        }
        
        const html = `<!DOCTYPE html>
<html lang="mn">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${escapeTemplateLiteral(config.title)}</title>
    <style>
        /* Reset all styles to prevent base.html inheritance */
        html, body, div, span, applet, object, iframe,
        h1, h2, h3, h4, h5, h6, p, blockquote, pre,
        a, abbr, acronym, address, big, cite, code,
        del, dfn, em, img, ins, kbd, q, s, samp,
        small, strike, strong, sub, sup, tt, var,
        b, u, i, center,
        dl, dt, dd, ol, ul, li,
        fieldset, form, label, legend,
        table, caption, tbody, tfoot, thead, tr, th, td,
        article, aside, canvas, details, embed,
        figure, figcaption, footer, header, hgroup,
        menu, nav, output, ruby, section, summary,
        time, mark, audio, video {
            margin: 0;
            padding: 0;
            border: 0;
            font-size: 100%;
            font: inherit;
            vertical-align: baseline;
        }
        
        /* HTML5 display-role reset for older browsers */
        article, aside, details, figcaption, figure,
        footer, header, hgroup, menu, nav, section {
            display: block;
        }
        
        body {
            line-height: 1;
        }
        
        ol, ul {
            list-style: none;
        }
        
        blockquote, q {
            quotes: none;
        }
        
        blockquote:before, blockquote:after,
        q:before, q:after {
            content: '';
            content: none;
        }
        
        table {
            border-collapse: collapse;
            border-spacing: 0;
        }
        
        /* Print buttons container */
        .print-buttons {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background-color: #f5f5f5;
            border-bottom: 2px solid #000;
        }
        
        .print-btn, .excel-btn {
            padding: 10px 30px;
            margin: 0 10px;
            font-size: 14pt;
            font-weight: bold;
            cursor: pointer;
            border: 2px solid #333;
            border-radius: 5px;
            background-color: #fff;
            color: #000;
            transition: background-color 0.3s;
        }
        
        .print-btn:hover {
            background-color: #e0e0e0;
        }
        
        .excel-btn:hover {
            background-color: #e8f5e9;
        }
        
        .print-btn:active, .excel-btn:active {
            background-color: #ccc;
        }
        
        /* Now apply our print styles - ensure no base.html styles */
        @page {
            size: A4 landscape;
            margin: 10mm;
        }
        
        /* Remove all inherited styles from parent window */
        html {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100% !important;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html, body {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100% !important;
            font-family: 'Arial', 'DejaVu Sans', sans-serif;
            font-size: 8pt;
            color: #000;
            background: #fff;
        }
        
        body {
            padding: 10mm;
        }
        
        .print-header {
            margin-bottom: 10px;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
        }
        
        .print-title {
            font-size: 14pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 8px;
        }
        
        .print-info {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            font-size: 9pt;
            margin-bottom: 5px;
        }
        
        .print-info span {
            margin-right: 20px;
        }
        
        .print-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 8pt;
        }
        
        .print-table thead {
            background-color: #f0f0f0;
        }
        
        .print-table th {
            border: 1px solid #000;
            padding: 6px 4px;
            text-align: left;
            font-weight: bold;
            background-color: #e0e0e0;
        }
        
        .print-table td {
            border: 1px solid #000;
            padding: 4px;
            text-align: left;
        }
        
        .print-table tbody tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .print-table tbody tr:nth-child(odd) {
            background-color: #fff;
        }
        
        .print-table .text-right {
            text-align: right;
        }
        
        .print-table .text-center {
            text-align: center;
        }
        
        .print-footer {
            margin-top: 15px;
            border-top: 2px solid #000;
            padding-top: 10px;
        }
        
        .print-totals {
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            font-size: 9pt;
        }
        
        .print-totals-row {
            background-color: #e0e0e0 !important;
            font-weight: bold;
        }
        
        .print-totals-row td {
            border-top: 2px solid #000;
            padding: 6px 4px;
        }
        
        @media print {
            /* Reset all margins and padding */
            * {
                margin: 0 !important;
                padding: 0 !important;
                box-sizing: border-box !important;
            }
            
            html, body {
                margin: 0 !important;
                padding: 10mm !important;
                width: 100% !important;
                height: auto !important;
                background: #fff !important;
                overflow: visible !important;
            }
            
            /* Hide ALL navigation, headers, footers, sidebars */
            nav, header, footer, .navbar, .sidebar, .no-print,
            .nav, .header, .footer, .menu, .navigation,
            .topbar, .top-bar, .bottom-bar, .sidebar-menu,
            .main-header, .main-footer, .site-header, .site-footer {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                width: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            
            /* Only show print-container and its children */
            body > *:not(.print-container) {
                display: none !important;
                visibility: hidden !important;
            }
            
            .print-container {
                display: block !important;
                visibility: visible !important;
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            
            .print-header, .print-table, .print-footer {
                display: block !important;
                visibility: visible !important;
            }
            
            .print-table {
                page-break-inside: auto;
                width: 100% !important;
            }
            
            .print-table tr {
                page-break-inside: avoid;
                page-break-after: auto;
            }
            
            .print-table thead {
                display: table-header-group !important;
            }
            
            .print-table tbody {
                display: table-row-group !important;
            }
            
            .print-table tfoot {
                display: table-footer-group !important;
            }
            
            /* Hide print buttons when printing */
            .print-buttons {
                display: none !important;
            }
        }
    </style>
</head>
<body style="margin: 0 !important; padding: 0 !important; background: #fff !important; width: 100% !important; height: 100% !important;">
    <div class="print-container" style="width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important;">
    <div class="print-buttons">
        <button class="print-btn" id="print-btn">ХЭВЛЭХ</button>
        <button class="excel-btn" id="excel-btn">EXCEL</button>
    </div>
    <div class="print-header">
        <div class="print-title">${escapeTemplateLiteral(config.title)}</div>
        <div class="print-info">
            ${metaInfo.join('')}
        </div>
        ${summaryInfo.length > 0 ? `<div class="print-info" style="margin-top: 8px; border-top: 1px solid #ccc; padding-top: 8px;">
            ${summaryInfo.join('')}
        </div>` : ''}
    </div>
    
    <table class="print-table">
        <thead>
            <tr>
                ${config.columnHeaders.map(h => `<th>${escapeTemplateLiteral(h)}</th>`).join('')}
            </tr>
        </thead>
        <tbody>
            ${tableRows}
            <tr class="print-totals-row">
                <td colspan="${config.columnHeaders.length - 2}" style="text-align: right; font-weight: bold;">НИЙТ:</td>
                <td class="text-right" style="font-weight: bold;">${formatNumber(config.totals.debit, 2)}</td>
                <td class="text-right" style="font-weight: bold;">${formatNumber(config.totals.credit, 2)}</td>
            </tr>
        </tbody>
    </table>
    
    <div class="print-footer">
        <div class="print-totals">
            <span>Нийт Дебит: <strong>${formatNumber(config.totals.debit, 2)}</strong></span>
            <span>Нийт Кредит: <strong>${formatNumber(config.totals.credit, 2)}</strong></span>
        </div>
    </div>
    </div>
    <script type="text/javascript">
        // Export to Excel function with UTF-8 BOM for proper Excel encoding
        // Define globally in window scope immediately
        function exportToExcel() {
            const table = document.querySelector('.print-table');
            if (!table) {
                alert('No data to export');
                return;
            }
            
            let csvContent = '';
            const rows = table.querySelectorAll('tr');
            
            rows.forEach(function(row) {
                const cells = row.querySelectorAll('th, td');
                const rowData = [];
                
                cells.forEach(function(cell) {
                    let cellText = cell.textContent.trim();
                    // Check if we need to quote before escaping
                    // Use indexOf to avoid escape sequence issues in template literal
                    var hasComma = cellText.indexOf(',') !== -1;
                    var newlineChar = String.fromCharCode(10);
                    var returnChar = String.fromCharCode(13);
                    var hasNewline = cellText.indexOf(newlineChar) !== -1 || cellText.indexOf(returnChar) !== -1;
                    var hasQuote = cellText.indexOf('"') !== -1;
                    var needsQuoting = hasComma || hasNewline || hasQuote;
                    
                    // Escape quotes properly (only if we're quoting)
                    if (needsQuoting) {
                        cellText = cellText.replace(/"/g, '""');
                        rowData.push('"' + cellText + '"');
                    } else {
                        rowData.push(cellText);
                    }
                });
                
                csvContent += rowData.join(',') + String.fromCharCode(13, 10);
            });
            
            // Encode content as UTF-8 with BOM for Excel compatibility (especially for Mongolian Cyrillic)
            // UTF-8 BOM is 0xEF 0xBB 0xBF
            const BOM = new Uint8Array([0xEF, 0xBB, 0xBF]);
            
            // Convert CSV content to UTF-8 bytes
            const encoder = new TextEncoder();
            const csvBytes = encoder.encode(csvContent);
            
            // Combine BOM and CSV content bytes
            const csvWithBOM = new Uint8Array(BOM.length + csvBytes.length);
            csvWithBOM.set(BOM, 0);
            csvWithBOM.set(csvBytes, BOM.length);
            
            // Create blob with UTF-8 encoding
            const blob = new Blob([csvWithBOM], { 
                type: 'text/csv;charset=utf-8;' 
            });
            
            // Create blob URL
            const url = URL.createObjectURL(blob);
            
            // Force download directly without showing source
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', 'subsidiary_ledger_' + new Date().toISOString().split('T')[0] + '.csv');
            link.style.visibility = 'hidden';
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            
            // Clean up link and blob URL after download starts
            setTimeout(function() {
                document.body.removeChild(link);
                // Clean up blob URL after a short delay to ensure download starts
                setTimeout(function() {
                    URL.revokeObjectURL(url);
                }, 100);
            }, 100);
            
            alert('Subsidiary ledger exported to Excel successfully! The file should open automatically if Excel is your default application for CSV files.');
        }
        
        // Also assign to window to ensure global availability
        window.exportToExcel = exportToExcel;
        
        // Attach event listeners when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            // Attach print button event
            const printBtn = document.getElementById('print-btn');
            if (printBtn) {
                printBtn.addEventListener('click', function() {
                    window.print();
                });
            }
            
            // Attach Excel button event
            const excelBtn = document.getElementById('excel-btn');
            if (excelBtn) {
                excelBtn.addEventListener('click', function() {
                    exportToExcel();
                });
            }
        });
        
        // Also attach immediately if DOM is already loaded
        if (document.readyState === 'loading') {
            // DOM is still loading, wait for DOMContentLoaded
        } else {
            // DOM is already loaded, attach immediately
            const printBtn = document.getElementById('print-btn');
            if (printBtn) {
                printBtn.addEventListener('click', function() {
                    window.print();
                });
            }
            
            const excelBtn = document.getElementById('excel-btn');
            if (excelBtn) {
                excelBtn.addEventListener('click', function() {
                    exportToExcel();
                });
            }
        }
    </script>
</body>
</html>`;
        
        return html;
    }

    /**
     * Main print function
     */
    window.printSubLedgerTable = function(config) {
        // Validate config
        if (!config || !config.allData || !Array.isArray(config.allData)) {
            alert('Invalid print configuration: allData must be an array');
            return;
        }
        
        if (!config.columnHeaders || !Array.isArray(config.columnHeaders)) {
            alert('Invalid print configuration: columnHeaders must be an array');
            return;
        }
        
        if (!config.totals || typeof config.totals.debit === 'undefined' || typeof config.totals.credit === 'undefined') {
            alert('Invalid print configuration: totals must have debit and credit');
            return;
        }
        
        // Default values
        config.title = config.title || 'Subsidiary Ledger Report';
        config.startDate = config.startDate || '';
        config.endDate = config.endDate || '';
        config.accountCode = config.accountCode || '';
        config.accountName = config.accountName || '';
        config.clientName = config.clientName || '';
        config.summary = config.summary || {
            beginBalance: 0,
            debitTotal: 0,
            creditTotal: 0,
            endBalance: 0
        };
        
        // Generate print HTML
        const printHTML = generatePrintHTML(config);
        
        // Create a blob URL to ensure complete isolation from parent page
        const blob = new Blob([printHTML], { type: 'text/html' });
        const blobUrl = URL.createObjectURL(blob);
        
        // Open print window using blob URL (completely isolated from parent)
        // Make it visible so user can see preview and use buttons
        const printWindow = window.open(blobUrl, '_blank', 'width=1200,height=800');
        if (!printWindow) {
            alert('Please allow popups to print the subsidiary ledger');
            URL.revokeObjectURL(blobUrl);
            return;
        }
        
        // Completely isolate the window from parent
        printWindow.opener = null;
        
        // Focus the window so user can see the preview with buttons
        printWindow.focus();
        
        // Clean up blob URL when window is closed
        printWindow.addEventListener('beforeunload', function() {
            URL.revokeObjectURL(blobUrl);
        });
    };
})();


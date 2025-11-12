/**
 * Trial Balance Print System
 * 
 * Handles landscape A4 printing for trial balance tables
 * 
 * Usage:
 * window.printTrialBalanceTable({
 *     title: 'ГҮЙЛГЭЭ БАЛАНС',
 *     startDate: '2025-01-01',
 *     endDate: '2025-01-31',
 *     allData: trialBalanceData,
 *     columnHeaders: ['Дансны код', 'Дансны нэр', 'Эхний үлдэгдэл (Дт)', ...],
 *     totals: {
 *         beginDebit: totalBeginDebit,
 *         beginCredit: totalBeginCredit,
 *         debitAmount: totalDebitAmount,
 *         creditAmount: totalCreditAmount,
 *         endDebit: totalEndDebit,
 *         endCredit: totalEndCredit
 *     }
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
     * Map data field names to column headers for trial balance
     */
    function getDataFieldMapping() {
        return {
            'Дансны код': 'AccountCode',
            'Дансны нэр': 'AccountName',
            'Эхний үлдэгдэл (Дт)': 'BeginningBalanceDebit',
            'Эхний үлдэгдэл (Кт)': 'BeginningBalanceCredit',
            'Дт гүйлгээ': 'DebitAmount',
            'Кт гүйлгээ': 'CreditAmount',
            'Эцсийн үлдэгдэл (Дт)': 'EndingBalanceDebit',
            'Эцсийн үлдэгдэл (Кт)': 'EndingBalanceCredit'
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
                if (fieldName === 'BeginningBalanceDebit' || 
                    fieldName === 'BeginningBalanceCredit' ||
                    fieldName === 'DebitAmount' || 
                    fieldName === 'CreditAmount' ||
                    fieldName === 'EndingBalanceDebit' ||
                    fieldName === 'EndingBalanceCredit') {
                    value = formatNumber(value, 2);
                    isNumeric = true;
                }
                
                // Right-align numeric columns, left-align text
                const alignClass = isNumeric ? ' class="text-right"' : '';
                html += `<td${alignClass}>${escapeTemplateLiteral(String(value))}</td>`;
            });
            
            html += '</tr>';
        });
        
        return html;
    }

    /**
     * Generate totals row
     */
    function generateTotalsRow(columnHeaders, fieldMapping, totals) {
        let html = '<tr class="totals-row" style="background-color: #f3f4f6; font-weight: bold; border-top: 2px solid #000;">';
        
        columnHeaders.forEach(header => {
            const fieldName = fieldMapping[header];
            let value = '';
            
            if (header === 'Дансны код' || header === 'Дансны нэр') {
                value = 'НИЙТ:';
            } else if (fieldName === 'BeginningBalanceDebit') {
                value = formatNumber(totals.beginDebit || 0, 2);
            } else if (fieldName === 'BeginningBalanceCredit') {
                value = formatNumber(totals.beginCredit || 0, 2);
            } else if (fieldName === 'DebitAmount') {
                value = formatNumber(totals.debitAmount || 0, 2);
            } else if (fieldName === 'CreditAmount') {
                value = formatNumber(totals.creditAmount || 0, 2);
            } else if (fieldName === 'EndingBalanceDebit') {
                value = formatNumber(totals.endDebit || 0, 2);
            } else if (fieldName === 'EndingBalanceCredit') {
                value = formatNumber(totals.endCredit || 0, 2);
            }
            
            const alignClass = (fieldName && fieldName !== 'AccountCode' && fieldName !== 'AccountName') ? ' class="text-right"' : '';
            html += `<td${alignClass}>${escapeTemplateLiteral(String(value))}</td>`;
        });
        
        html += '</tr>';
        return html;
    }

    /**
     * Generate print HTML content
     */
    function generatePrintHTML(config) {
        const fieldMapping = getDataFieldMapping();
        const tableRows = generateTableRows(config.allData, config.columnHeaders, fieldMapping);
        const totalsRow = generateTotalsRow(config.columnHeaders, fieldMapping, config.totals);
        
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
        
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #000;
            background: #fff;
            margin: 0;
            padding: 20px;
        }
        
        .print-header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
        }
        
        .print-title {
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .print-subtitle {
            font-size: 11pt;
            color: #333;
            margin-bottom: 5px;
        }
        
        .print-info {
            font-size: 9pt;
            color: #666;
            margin-top: 5px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 9pt;
        }
        
        thead {
            background-color: #f3f4f6;
        }
        
        th {
            padding: 8px 6px;
            text-align: left;
            border: 1px solid #000;
            font-weight: bold;
            font-size: 9pt;
            background-color: #e5e7eb;
        }
        
        th.text-right {
            text-align: right;
        }
        
        td {
            padding: 6px;
            border: 1px solid #000;
            font-size: 9pt;
        }
        
        td.text-right {
            text-align: right;
        }
        
        tbody tr:nth-child(even) {
            background-color: #f9fafb;
        }
        
        .totals-row {
            background-color: #f3f4f6 !important;
            font-weight: bold;
            border-top: 2px solid #000;
        }
        
        .print-footer {
            margin-top: 20px;
            text-align: center;
            font-size: 8pt;
            color: #666;
            border-top: 1px solid #ccc;
            padding-top: 10px;
        }
        
        @media print {
            @page {
                size: A4 landscape;
                margin: 1cm;
            }
            
            body {
                padding: 0;
            }
            
            .no-print {
                display: none !important;
            }
        }
        
        .print-actions {
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            background-color: #f3f4f6;
            border-radius: 4px;
        }
        
        .print-btn, .excel-btn {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 12pt;
            cursor: pointer;
            border-radius: 4px;
            margin: 0 10px;
        }
        
        .print-btn:hover {
            background-color: #1d4ed8;
        }
        
        .excel-btn {
            background-color: #16a34a;
        }
        
        .excel-btn:hover {
            background-color: #15803d;
        }
    </style>
</head>
<body>
    <div class="print-header">
        <div class="print-title">${escapeTemplateLiteral(config.title)}</div>
        ${config.startDate && config.endDate ? `
        <div class="print-subtitle">Хугацаа: ${formatDate(config.startDate)} - ${formatDate(config.endDate)}</div>
        ` : ''}
        <div class="print-info">Хэвлэсэн огноо: ${getCurrentDateTime()}</div>
    </div>
    
    <table id="print-table">
        <thead>
            <tr>
                ${config.columnHeaders.map(header => `<th class="${getDataFieldMapping()[header] && getDataFieldMapping()[header] !== 'AccountCode' && getDataFieldMapping()[header] !== 'AccountName' ? 'text-right' : ''}">${escapeTemplateLiteral(header)}</th>`).join('')}
            </tr>
        </thead>
        <tbody>
            ${tableRows}
        </tbody>
        <tfoot>
            ${totalsRow}
        </tfoot>
    </table>
    
    <div class="print-footer">
        <div>Silicon4 Accounting System</div>
    </div>
    
    <div class="print-actions no-print">
        <button class="print-btn" id="print-btn" onclick="window.print()">Хэвлэх</button>
        <button class="excel-btn" id="excel-btn">EXCEL</button>
    </div>
    
    <script>
        // Export to Excel function with UTF-8 BOM for proper Excel encoding
        function exportToExcel() {
            const table = document.querySelector('table');
            if (!table) {
                alert('No data to export');
                return;
            }
            
            // Export all data from table
            let csvContent = '';
            const rows = table.querySelectorAll('tr');
            
            rows.forEach(function(row) {
                const cells = row.querySelectorAll('th, td');
                const rowData = [];
                
                cells.forEach(function(cell) {
                    let cellText = cell.textContent.trim();
                    // Check if we need to quote before escaping
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
            link.setAttribute('download', 'trial_balance_' + new Date().toISOString().split('T')[0] + '.csv');
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
            
            alert('Trial balance exported to Excel successfully! The file should open automatically if Excel is your default application for CSV files.');
        }
        
        // Also assign to window to ensure global availability
        window.exportToExcel = exportToExcel;
        
        // Auto-focus print button for better UX
        document.addEventListener('DOMContentLoaded', function() {
            const printBtn = document.getElementById('print-btn');
            if (printBtn) {
                printBtn.focus();
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
    window.printTrialBalanceTable = function(config) {
        // Validate config
        if (!config || !config.allData || !Array.isArray(config.allData)) {
            alert('Invalid print configuration: allData must be an array');
            return;
        }
        
        if (!config.columnHeaders || !Array.isArray(config.columnHeaders)) {
            alert('Invalid print configuration: columnHeaders must be an array');
            return;
        }
        
        if (!config.totals || typeof config.totals.beginDebit === 'undefined') {
            alert('Invalid print configuration: totals must have beginDebit, beginCredit, debitAmount, creditAmount, endDebit, endCredit');
            return;
        }
        
        // Default values
        config.title = config.title || 'ГҮЙЛГЭЭ БАЛАНС';
        config.startDate = config.startDate || '';
        config.endDate = config.endDate || '';
        
        // Generate print HTML
        const printHTML = generatePrintHTML(config);
        
        // Create a blob URL to ensure complete isolation from parent page
        const blob = new Blob([printHTML], { type: 'text/html' });
        const blobUrl = URL.createObjectURL(blob);
        
        // Open print window using blob URL (completely isolated from parent)
        // Make it visible so user can see preview and use buttons
        const printWindow = window.open(blobUrl, '_blank', 'width=1200,height=800');
        if (!printWindow) {
            alert('Please allow popups to print the trial balance');
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


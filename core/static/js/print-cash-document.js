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

// Get Mongolian currency name from currency code
function getMongolianCurrencyName(currencyCode) {
    const currencyMap = {
        'MNT': { main: 'төгрөг', decimal: 'мөнгө' },
        'USD': { main: 'ам доллар', decimal: 'цент' },
        'EUR': { main: 'евро', decimal: '' },
        'CNY': { main: 'юань', decimal: '' },
        'RUB': { main: 'рубль', decimal: '' },
        'GBP': { main: 'фунт', decimal: '' },
        'JPY': { main: 'иен', decimal: '' }
    };
    
    // Default to MNT if currency not found
    return currencyMap[currencyCode] || currencyMap['MNT'];
}

// Mongolian Number to Words Converter (Based on official Mongolian Finance Department implementation)
function numberToMongolianWords(num, currencyCode) {
    const Numbers = ['', 'нэг', 'хоёр', 'гурван', 'дөрвөн', 'таван', 'зургаан', 'долоон', 'найман', 'есөн'];
    const Tenths = ['', 'арван', 'хорин', 'гучин', 'дөчин', 'тавин', 'жаран', 'далан', 'наян', 'ерэн'];
    
    // Get currency names
    const currency = getMongolianCurrencyName(currencyCode || 'MNT');
    const currencyName = currency.main;
    const decimalName = currency.decimal;
    
    // Recursive function to convert number to words
    function RecurseNumber(N) {
        if (N >= 1 && N <= 9) {
            return Numbers[N];
        } else if (N >= 10 && N <= 99) {
            const tensDigit = Math.floor(N / 10);
            const onesDigit = N % 10;
            if (onesDigit > 0) {
                return Tenths[tensDigit] + ' ' + RecurseNumber(onesDigit);
            } else {
                return Tenths[tensDigit];
            }
        } else if (N >= 100 && N <= 999) {
            const hundredsDigit = Math.floor(N / 100);
            const remainder = N % 100;
            if (remainder > 0) {
                return Numbers[hundredsDigit] + ' зуун ' + RecurseNumber(remainder);
            } else {
                return Numbers[hundredsDigit] + ' зуун';
            }
        } else if (N >= 1000 && N <= 999999) {
            const thousandsPart = Math.floor(N / 1000);
            const remainder = N % 1000;
            if (remainder !== 0) {
                return RecurseNumber(thousandsPart) + ' мянга ' + RecurseNumber(remainder);
            } else {
                return RecurseNumber(thousandsPart) + ' мянган';
            }
        } else if (N >= 1000000 && N <= 999999999) {
            const millionsPart = Math.floor(N / 1000000);
            const remainder = N % 1000000;
            if (remainder > 0) {
                return RecurseNumber(millionsPart) + ' сая ' + RecurseNumber(remainder);
            } else {
                return RecurseNumber(millionsPart) + ' сая';
            }
        } else if (N >= 1000000000 && N <= 14294967295) {
            const billionsPart = Math.floor(N / 1000000000);
            const remainder = N % 1000000000;
            if (remainder > 0) {
                return RecurseNumber(billionsPart) + ' тэрбум ' + RecurseNumber(remainder);
            } else {
                return RecurseNumber(billionsPart) + ' тэрбум';
            }
        } else {
            return '';
        }
    }
    
    // Convert the number
    const wholePart = Math.floor(num);
    
    if (num === 0) {
        return 'тэг ' + currencyName;
    }
    
    if (wholePart >= 1 && wholePart <= 14294967295) {
        let result = RecurseNumber(wholePart);
        
        // Clean up multiple spaces
        result = result.replace(/\s+/g, ' ').trim();
        
        // Add currency
        result = result + ' ' + currencyName;
        
        // Handle decimal part
        const decimal = (num - wholePart).toFixed(2);
        const decimalValue = Math.round(parseFloat(decimal) * 100);
        if (decimalValue > 0 && decimalName) {
            const decimalWords = RecurseNumber(decimalValue);
            result = result + ' ' + decimalWords + ' ' + decimalName;
        }
        
        // Fix special case: "нэг мянга" -> "нэгэн мянга" (as per Mongolian Finance Department standard)
        result = result.replace(/нэг мянга /g, 'нэгэн мянга ');
        
        // Clean up any double spaces
        result = result.replace(/\s+/g, ' ').trim();
        
        return result;
    } else {
        return '';
    }
}

// Document Type Print Configuration
window.DOCUMENT_PRINT_CONFIG = {
    // Document Type 1: Receipt (Орлого) - Mongolian Cash Receipt Format
    1: {
        title: 'Бэлэн мөнгөний орлогын баримт',
        subtitle: 'Cash Receipt Document',
        template: 'receipt_mongolian',
        layout: 'mongolian_receipt',
        style: `
            @page { size: A4; margin: 10mm; }
            body { font-family: 'Arial', 'DejaVu Sans', sans-serif; margin: 0; padding: 0; font-size: 12px; }
            .document-container { border: 1px dashed #000; padding: 10px; margin: 0 auto; max-width: 210mm; }
            .receipt-wrapper { display: flex; }
            .receipt-main { flex: 0 0 65%; padding: 15px; border-right: 1px dashed #000; box-sizing: border-box; }
            .receipt-stub { flex: 0 0 35%; padding: 15px 8px 15px 8px; overflow: hidden; box-sizing: border-box; }
            .ministerial-order { text-align: right; font-size: 9px; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 1px dashed #ccc; margin-top: 0; }
            .receipt-stub .ministerial-order { display: none; }
            .company-name { font-weight: bold; font-size: 14px; margin-bottom: 10px; word-wrap: break-word; }
            .document-title { text-align: center; font-weight: bold; font-size: 16px; margin: 15px 0; }
            .receipt-stub .document-title { font-size: 14px; margin: 10px 0; }
            .field-row { display: flex; margin: 8px 0; align-items: flex-start; width: 100%; box-sizing: border-box; }
            .field-label { font-weight: bold; min-width: 140px; flex-shrink: 0; box-sizing: border-box; }
            .field-value { flex: 1; text-align: right; border-bottom: 1px dashed #ccc; padding-left: 10px; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; box-sizing: border-box; overflow: hidden; text-overflow: ellipsis; }
            .receipt-stub .field-label { min-width: 110px; max-width: 110px; font-size: 10px; flex-shrink: 0; padding-right: 5px; box-sizing: border-box; }
            .receipt-stub .field-value { font-size: 10px; padding-left: 3px; padding-right: 2px; word-wrap: break-word; overflow-wrap: break-word; min-width: 0; max-width: 100%; box-sizing: border-box; overflow: hidden; }
            .amount-section { margin: 15px 0; padding: 10px; background: #f9f9f9; border: 1px solid #ddd; box-sizing: border-box; }
            .amount-number { font-weight: bold; font-size: 14px; text-align: right; word-wrap: break-word; overflow-wrap: break-word; }
            .amount-words { margin-top: 5px; font-style: italic; font-size: 12px; word-wrap: break-word; overflow-wrap: break-word; }
            .receipt-stub .amount-section { padding: 8px 4px; margin: 10px 0; }
            .receipt-stub .amount-number { font-size: 10px; padding-right: 2px; word-wrap: break-word; overflow-wrap: break-word; }
            .receipt-stub .amount-words { font-size: 9px; padding-right: 2px; word-wrap: break-word; overflow-wrap: break-word; }
            .signatures { margin-top: 20px; width: 100%; box-sizing: border-box; }
            .signature-row { margin: 10px 0; display: flex; align-items: center; width: 100%; }
            .signature-label { font-weight: bold; min-width: 100px; flex-shrink: 0; }
            .signature-line { flex: 1; border-bottom: 1px dashed #000; margin-left: 10px; margin-right: 10px; height: 20px; max-width: 150px; }
            .signature-name { min-width: 150px; word-wrap: break-word; }
            .receipt-stub .signature-row { margin: 8px 0; }
            .receipt-stub .signature-label { min-width: 80px; max-width: 80px; font-size: 10px; flex-shrink: 0; padding-right: 3px; }
            .receipt-stub .signature-line { max-width: 50px; margin-left: 3px; margin-right: 2px; }
            .receipt-stub .signature-name { min-width: 0; font-size: 10px; max-width: 70px; word-wrap: break-word; }
            @media print {
                body { margin: 0; }
                .no-print { display: none; }
                .document-container { border: 1px dashed #000; }
            }
        `
    },
    // Document Type 2: Payment (Зарлага) - Mongolian Cash Payment Format
    2: {
        title: 'Бэлэн мөнгөний зарлагын баримт',
        subtitle: 'Cash Payment Document',
        template: 'payment_mongolian',
        layout: 'mongolian_payment',
        style: `
            @page { size: A4; margin: 10mm; }
            body { font-family: 'Arial', 'DejaVu Sans', sans-serif; margin: 0; padding: 0; font-size: 12px; }
            .document-container { border: 1px dashed #000; padding: 10px; margin: 0 auto; max-width: 210mm; }
            .receipt-wrapper { display: flex; }
            .receipt-main { flex: 0 0 65%; padding: 15px; border-right: 1px dashed #000; box-sizing: border-box; }
            .receipt-stub { flex: 0 0 35%; padding: 15px 8px 15px 8px; overflow: hidden; box-sizing: border-box; }
            .ministerial-order { text-align: right; font-size: 9px; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 1px dashed #ccc; margin-top: 0; }
            .receipt-stub .ministerial-order { display: none; }
            .company-name { font-weight: bold; font-size: 14px; margin-bottom: 10px; word-wrap: break-word; }
            .document-title { text-align: center; font-weight: bold; font-size: 16px; margin: 15px 0; }
            .receipt-stub .document-title { font-size: 14px; margin: 10px 0; }
            .field-row { display: flex; margin: 8px 0; align-items: flex-start; width: 100%; box-sizing: border-box; }
            .field-label { font-weight: bold; min-width: 140px; flex-shrink: 0; box-sizing: border-box; }
            .field-value { flex: 1; text-align: right; border-bottom: 1px dashed #ccc; padding-left: 10px; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%; box-sizing: border-box; overflow: hidden; text-overflow: ellipsis; }
            .receipt-stub .field-label { min-width: 110px; max-width: 110px; font-size: 10px; flex-shrink: 0; padding-right: 5px; box-sizing: border-box; }
            .receipt-stub .field-value { font-size: 10px; padding-left: 3px; padding-right: 2px; word-wrap: break-word; overflow-wrap: break-word; min-width: 0; max-width: 100%; box-sizing: border-box; overflow: hidden; }
            .amount-section { margin: 15px 0; padding: 10px; background: #f9f9f9; border: 1px solid #ddd; box-sizing: border-box; }
            .amount-number { font-weight: bold; font-size: 14px; text-align: right; word-wrap: break-word; overflow-wrap: break-word; }
            .amount-words { margin-top: 5px; font-style: italic; font-size: 12px; word-wrap: break-word; overflow-wrap: break-word; }
            .receipt-stub .amount-section { padding: 8px 4px; margin: 10px 0; }
            .receipt-stub .amount-number { font-size: 10px; padding-right: 2px; word-wrap: break-word; overflow-wrap: break-word; }
            .receipt-stub .amount-words { font-size: 9px; padding-right: 2px; word-wrap: break-word; overflow-wrap: break-word; }
            .signatures { margin-top: 20px; width: 100%; box-sizing: border-box; }
            .signature-row { margin: 10px 0; display: flex; align-items: center; width: 100%; }
            .signature-label { font-weight: bold; min-width: 100px; flex-shrink: 0; }
            .signature-line { flex: 1; border-bottom: 1px dashed #000; margin-left: 10px; margin-right: 10px; height: 20px; max-width: 150px; }
            .signature-name { min-width: 150px; word-wrap: break-word; }
            .receipt-stub .signature-row { margin: 8px 0; }
            .receipt-stub .signature-label { min-width: 80px; max-width: 80px; font-size: 10px; flex-shrink: 0; padding-right: 3px; }
            .receipt-stub .signature-line { max-width: 50px; margin-left: 3px; margin-right: 2px; }
            .receipt-stub .signature-name { min-width: 0; font-size: 10px; max-width: 70px; word-wrap: break-word; }
            @media print {
                body { margin: 0; }
                .no-print { display: none; }
                .document-container { border: 1px dashed #000; }
            }
        `
    },
    // Document Type 4: Transfer (Шилжүүлэг) - Mongolian Payment Order Format (Two copies on A4)
    4: {
        title: 'ТӨЛБӨРИЙН ДААЛГАВАР',
        subtitle: 'Payment Order',
        template: 'transfer_mongolian',
        layout: 'mongolian_transfer',
        style: `
            @page { size: A4 portrait; margin: 0; }
            body { width: 210mm; min-height: 297mm; margin: 0 auto; padding: 10mm; box-sizing: border-box; font-family: 'Times New Roman', Times, serif; font-size: 10pt; color: black; line-height: 1.2; }
            .document-container { width: 100%; }
            .form-copy { padding-bottom: 25px; margin-bottom: 25px; border-bottom: 1px dashed #ccc; }
            .form-copy:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
            .document-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px; }
            .title-left { font-size: 14pt; font-weight: bold; text-align: center; width: 65%; margin-left: 5%; }
            .instruction-right { text-align: right; font-size: 8pt; line-height: 1.2; width: 35%; }
            .date-and-number { display: flex; justify-content: space-between; font-size: 9pt; font-weight: normal; margin-bottom: 3px; }
            .date-and-number > div:first-child { font-weight: bold; }
            .main-form-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 9pt; }
            .main-form-table td { border: 1px solid black; padding: 3px 5px; height: 16px; vertical-align: middle; border-top: none; }
            .main-form-table tr:first-child td { border-top: 1px solid black; }
            .label { font-weight: normal; white-space: nowrap; }
            .data-value { font-weight: normal; }
            .merged-header { text-align: center; font-weight: normal; border-bottom: 1px solid black !important; }
            .amount-cell { font-size: 11pt; font-weight: normal; text-align: right; padding-right: 10px; }
            .amount-words-td { font-size: 8pt; vertical-align: top; padding-top: 5px; height: 35px; }
            .amount-words-text { font-size: 10pt; font-weight: normal; }
            .purpose-box-label { font-weight: normal; vertical-align: top; padding-top: 5px; }
            .purpose-box-value { font-weight: normal; vertical-align: top; padding-top: 5px; height: 100%; }
            .signatures-section { margin-top: 25px; display: flex; justify-content: space-between; font-size: 9pt; padding: 0 5px; }
            .signature-group { width: 45%; text-align: left; }
            .date-signature-group { width: 45%; text-align: right; }
            .signature-line-box { display: flex; justify-content: space-between; border-bottom: 1px dotted black; padding-bottom: 1px; margin-top: 5px; margin-bottom: 5px; font-weight: bold; }
            .bank-info-line { text-align: right; margin-bottom: 10px; }
            .dotted-line { border-bottom: 1px dotted black; display: inline-block; width: 30px; margin: 0 5px; }
            .accountant-line { margin-top: 10px; font-size: 9pt; border-bottom: 1px dotted black; padding-bottom: 1px; }
            .client-info { margin-top: 10px; }
            .client-info-item { font-size: 9pt; font-weight: normal; margin-top: 5px; }
            .purpose-box-table { width: 100%; border: none !important; border-collapse: collapse; margin: 0 !important; padding: 0 !important; border-spacing: 0; display: block; }
            .purpose-box-table td { margin: 0 !important; line-height: 1; }
            .purpose-box-table-cell { margin:0; border-top: none !important; border-left: none !important; border-bottom: 1px solid black; width: 60%; font-weight: normal; padding-top: 3px; }
            .purpose-box-table-cell-value { margin:0; border-top: none !important; border-right: none !important; border-left: none !important; border-bottom: 1px solid black; width: 40%; font-weight: normal; padding-top: 3px; }
            .purpose-box-table tr:last-child td { border-bottom: none !important; }
            @media print {
                body { margin: 0; padding: 10mm; }
                .no-print { display: none; }
            }
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
    // Special handling for Mongolian receipt layout
    if (config.layout === 'mongolian_receipt') {
        return generateMongolianReceiptContent(config, data);
    }
    // Special handling for Mongolian payment layout
    if (config.layout === 'mongolian_payment') {
        return generateMongolianPaymentContent(config, data);
    }
    // Special handling for Mongolian transfer layout
    if (config.layout === 'mongolian_transfer') {
        return generateMongolianTransferContent(config, data);
    }
    
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
                <p>Silicon-AI Accounting System</p>
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

// Generate Mongolian Receipt Content (Document Type 1)
function generateMongolianReceiptContent(config, data) {
    // Get organization name from data, global constants, or use default
    let orgName = data.organizationName || data.clientName;
    if (!orgName && typeof window !== 'undefined' && window.globalConstants && window.globalConstants.COMPANY_NAME) {
        orgName = window.globalConstants.COMPANY_NAME;
    }
    orgName = orgName || 'Сити энержи ХХК';
    
    const receiptNumber = data.documentNo || '';
    const receiptDate = data.documentDate || new Date().toLocaleDateString('mn-MN');
    const payer = data.clientName || orgName;
    const description = data.description || '';
    
    // Format amount - Debug: Log what fields are available
    console.log('Amount fields available:', {
        currencyMNT: data.currencyMNT,
        currencyAmount: data.currencyAmount,
        mntAmount: data.mntAmount,
        totalAmount: data.totalAmount,
        allData: Object.keys(data)
    });
    
    // Try multiple fields for amount, prioritize currencyMNT (MNT amount)
    let amountValue = data.currencyMNT || data.mntAmount || data.currencyAmount || data.totalAmount || '0';
    
    // Clean amount - remove commas and any non-numeric characters except decimal point
    const cleanedAmount = String(amountValue).replace(/[^\d.-]/g, '').replace(/,/g, '');
    const amount = parseFloat(cleanedAmount) || 0;
    
    console.log('Amount calculation:', {
        originalValue: amountValue,
        cleanedAmount: cleanedAmount,
        parsedAmount: amount
    });
    
    const formattedAmount = amount.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const amountInWords = numberToMongolianWords(amount);
    
    // Get signatures from data, global constants, or use defaults
    let director = data.director || '';
    let accountant = data.accountant || data.chiefAccountant || '';
    let cashier = data.cashier || '';
    
    if (typeof window !== 'undefined' && window.globalConstants) {
        if (!director && window.globalConstants.DIRECTOR) {
            director = window.globalConstants.DIRECTOR;
        }
        if (!accountant && window.globalConstants.CHIEF_ACCOUNTANT) {
            accountant = window.globalConstants.CHIEF_ACCOUNTANT;
        }
        if (!cashier && window.globalConstants.CASHIER) {
            cashier = window.globalConstants.CASHIER;
        }
    }
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>${config.title} - ${receiptNumber}</title>
            <meta charset="UTF-8">
            <style>${config.style}</style>
        </head>
        <body>
            <div class="document-container">
                <div class="receipt-wrapper">
                    <!-- Main Receipt (Left Side - 65%) -->
                    <div class="receipt-main">
                        <div class="ministerial-order">
                            Сангийн сайдын 2017 оны 12 дугаар сарын 05-ны өдрийн 347 тоот тушаалын хавсралт
                        </div>
                        <div class="company-name">${orgName}</div>
                        <div class="document-title">${config.title}</div>
                        
                        <div class="field-row">
                            <span class="field-label">Орлогын тасалбарын дугаар:</span>
                            <span class="field-value">${receiptNumber}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Байгууллагын нэр:</span>
                            <span class="field-value">${orgName}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Огноо:</span>
                            <span class="field-value">${receiptDate}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Мөнгө тушаагч:</span>
                            <span class="field-value">${payer}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Гүйлгээний утга:</span>
                            <span class="field-value">${description}</span>
                        </div>
                        
                        <div class="amount-section">
                            <div class="field-row">
                                <span class="field-label">Хүлээн авсан мөнгөний дүн:</span>
                                <span class="field-value amount-number">${formattedAmount} төгрөг</span>
                            </div>
                            <div class="amount-words">${amountInWords}</div>
                        </div>
                        
                        <div class="signatures">
                            <div style="font-weight: bold; margin-bottom: 10px;">Гарын үсэг:</div>
                            <div class="signature-row">
                                <span class="signature-label">Гүйцэтгэх захирал</span>
                                <span class="signature-name">${director}</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нягтлан бодогч:</span>
                                <span class="signature-name">${accountant}</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нярав:</span>
                                <span class="signature-name">${cashier}</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Тушаагч:</span>
                                <span class="signature-name">${payer}</span>
                                <span class="signature-line"></span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Stub/Duplicate (Right Side - 35%) -->
                    <div class="receipt-stub">
                        <div class="company-name">${orgName}</div>
                        
                        <div class="field-row">
                            <span class="field-label">Орлогын тасалбарын дугаар:</span>
                            <span class="field-value">${receiptNumber}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Мөнгө тушаагч:</span>
                            <span class="field-value">${payer}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Гүйлгээний утга:</span>
                            <span class="field-value">${description}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Огноо:</span>
                            <span class="field-value">${receiptDate}</span>
                        </div>
                        
                        <div class="amount-section">
                            <div class="field-row">
                                <span class="field-label">Хүлээн авсан мөнгөний дүн:</span>
                                <span class="field-value amount-number">${formattedAmount} төгрөг</span>
                            </div>
                            <div class="amount-words">${amountInWords}</div>
                        </div>
                        
                        <div class="signatures">
                            <div style="font-weight: bold; margin-bottom: 10px; font-size: 11px;">Гарын үсэг:</div>
                            <div class="signature-row">
                                <span class="signature-label">Захирал:</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нягтлан бодогч:</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нярав:</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Мөнгө тушаагч:</span>
                                <span class="signature-line"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="no-print" style="text-align: center; margin-top: 20px;">
                <button onclick="window.print()" style="padding: 10px 20px; margin: 5px; background: #3b82f6; color: white; border: none; border-radius: 5px; cursor: pointer;">Хэвлэх</button>
                <button onclick="window.close()" style="padding: 10px 20px; margin: 5px; background: #6b7280; color: white; border: none; border-radius: 5px; cursor: pointer;">Хаах</button>
            </div>
        </body>
        </html>
    `;
}

// Generate Mongolian Payment Content (Document Type 2)
function generateMongolianPaymentContent(config, data) {
    // Get organization name from data, global constants, or use default
    let orgName = data.organizationName || data.clientName;
    if (!orgName && typeof window !== 'undefined' && window.globalConstants && window.globalConstants.COMPANY_NAME) {
        orgName = window.globalConstants.COMPANY_NAME;
    }
    orgName = orgName || 'Сити энержи ХХК';
    
    const paymentNumber = data.documentNo || '';
    const paymentDate = data.documentDate || new Date().toLocaleDateString('mn-MN');
    const recipient = data.clientName || data.recipient || '';
    const description = data.description || '';
    
    // Format amount - Debug: Log what fields are available
    console.log('Amount fields available:', {
        currencyMNT: data.currencyMNT,
        currencyAmount: data.currencyAmount,
        mntAmount: data.mntAmount,
        totalAmount: data.totalAmount,
        allData: Object.keys(data)
    });
    
    // Try multiple fields for amount, prioritize currencyMNT (MNT amount)
    let amountValue = data.currencyMNT || data.mntAmount || data.currencyAmount || data.totalAmount || '0';
    
    // Clean amount - remove commas and any non-numeric characters except decimal point
    const cleanedAmount = String(amountValue).replace(/[^\d.-]/g, '').replace(/,/g, '');
    const amount = parseFloat(cleanedAmount) || 0;
    
    console.log('Amount calculation:', {
        originalValue: amountValue,
        cleanedAmount: cleanedAmount,
        parsedAmount: amount
    });
    
    const formattedAmount = amount.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const amountInWords = numberToMongolianWords(amount);
    
    // Get signatures from data, global constants, or use defaults
    let director = data.director || '';
    let accountant = data.accountant || data.chiefAccountant || '';
    let cashier = data.cashier || '';
    let receivedBy = data.receivedBy || recipient || '';
    
    if (typeof window !== 'undefined' && window.globalConstants) {
        if (!director && window.globalConstants.DIRECTOR) {
            director = window.globalConstants.DIRECTOR;
        }
        if (!accountant && window.globalConstants.CHIEF_ACCOUNTANT) {
            accountant = window.globalConstants.CHIEF_ACCOUNTANT;
        }
        if (!cashier && window.globalConstants.CASHIER) {
            cashier = window.globalConstants.CASHIER;
        }
    }
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>${config.title} - ${paymentNumber}</title>
            <meta charset="UTF-8">
            <style>${config.style}</style>
        </head>
        <body>
            <div class="document-container">
                <div class="receipt-wrapper">
                    <!-- Main Payment (Left Side - 65%) -->
                    <div class="receipt-main">
                        <div class="ministerial-order">
                            Сангийн сайдын 2017 оны 12 дугаар сарын 05-ны өдрийн 347 тоот тушаалын хавсралт
                        </div>
                        <div class="company-name">${orgName}</div>
                        <div class="document-title">${config.title}</div>
                        
                        <div class="field-row">
                            <span class="field-label">Зарлагын тасалбарын дугаар:</span>
                            <span class="field-value">${paymentNumber}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Байгууллагын нэр:</span>
                            <span class="field-value">${orgName}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Огноо:</span>
                            <span class="field-value">${paymentDate}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Мөнгө хүлээн авагч:</span>
                            <span class="field-value">${recipient}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Гүйлгээний утга:</span>
                            <span class="field-value">${description}</span>
                        </div>
                        
                        <div class="amount-section">
                            <div class="field-row">
                                <span class="field-label">Олгосон мөнгөний дүн:</span>
                                <span class="field-value amount-number">${formattedAmount} төгрөг</span>
                            </div>
                            <div class="amount-words">${amountInWords}</div>
                        </div>
                        
                        <div class="signatures">
                            <div style="font-weight: bold; margin-bottom: 10px;">Гарын үсэг:</div>
                            <div class="signature-row">
                                <span class="signature-label">Гүйцэтгэх захирал</span>
                                <span class="signature-name">${director}</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нягтлан бодогч:</span>
                                <span class="signature-name">${accountant}</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нярав:</span>
                                <span class="signature-name">${cashier}</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Хүлээн авсан:</span>
                                <span class="signature-name">${receivedBy}</span>
                                <span class="signature-line"></span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Stub/Duplicate (Right Side - 35%) -->
                    <div class="receipt-stub">
                        <div class="company-name">${orgName}</div>
                        
                        <div class="field-row">
                            <span class="field-label">Зарлагын тасалбарын дугаар:</span>
                            <span class="field-value">${paymentNumber}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Гүйлгээний утга:</span>
                            <span class="field-value">${description}</span>
                        </div>
                        
                        <div class="field-row">
                            <span class="field-label">Огноо:</span>
                            <span class="field-value">${paymentDate}</span>
                        </div>
                        
                        <div class="amount-section">
                            <div class="field-row">
                                <span class="field-label">Олгосон мөнгөний дүн:</span>
                                <span class="field-value amount-number">${formattedAmount} төгрөг</span>
                            </div>
                            <div class="amount-words">${amountInWords}</div>
                        </div>
                        
                        <div class="signatures">
                            <div style="font-weight: bold; margin-bottom: 10px; font-size: 11px;">Гарын үсэг:</div>
                            <div class="signature-row">
                                <span class="signature-label">Захирал:</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нягтлан бодогч:</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Нярав:</span>
                                <span class="signature-line"></span>
                            </div>
                            <div class="signature-row">
                                <span class="signature-label">Хүлээн авсан:</span>
                                <span class="signature-line"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="no-print" style="text-align: center; margin-top: 20px;">
                <button onclick="window.print()" style="padding: 10px 20px; margin: 5px; background: #3b82f6; color: white; border: none; border-radius: 5px; cursor: pointer;">Хэвлэх</button>
                <button onclick="window.close()" style="padding: 10px 20px; margin: 5px; background: #6b7280; color: white; border: none; border-radius: 5px; cursor: pointer;">Хаах</button>
            </div>
        </body>
        </html>
    `;
}

// Generate Mongolian Transfer Content (Document Type 4) - Two copies on A4
function generateMongolianTransferContent(config, data) {
    // Get organization name from data, global constants, or use default
    let orgName = data.organizationName || data.clientName;
    if (!orgName && typeof window !== 'undefined' && window.globalConstants && window.globalConstants.COMPANY_NAME) {
        orgName = window.globalConstants.COMPANY_NAME;
    }
    orgName = orgName || 'Сити энержи ХХК';
    
    const documentNumber = data.documentNo || '';
    const documentDate = data.documentDate || new Date().toLocaleDateString('mn-MN');
    const payer = data.clientName || orgName;
    const recipient = data.clientName || data.recipient || data.payee || '';
    const description = data.description || '';
    
    // Get bank information - try to extract from data or use defaults
    // Extract BankName and AccountNumber from AccountName by splitting on "|"
    let payerBank = data.payerBank || data.debitBank || 'Хаан банк';
    let payerAccount = data.payerAccount || data.debitAccount || '';
    
    if (data.accountName) {
        // Split AccountName by "|" - part before "|" is BankName, part after "|" is AccountNumber
        const accountParts = data.accountName.split('|');
        if (accountParts.length > 1) {
            // Part before "|" is BankName
            if (!payerBank || payerBank === 'Хаан банк') {
                payerBank = accountParts[0].trim();
            }
            // Part after "|" is AccountNumber
            if (!payerAccount) {
                payerAccount = accountParts[1].trim();
            }
        }
    }
    
    const recipientBank = data.recipientBank || data.creditBank || 'Голомт банк';
    // Try multiple fields for recipient account: BankAccount, clientBankAccount, recipientAccount, creditAccount
    // Also try to get from details array if available
    let recipientAccount = data.BankAccount || data.bankAccount || data.clientBankAccount || data.recipientAccount || data.creditAccount || '';
    
    // If recipientAccount is still empty, try to extract from details array
    if (!recipientAccount && data.details && data.details.length > 0) {
        // Look for the first detail with a client that has BankAccount
        for (let detail of data.details) {
            if (detail.BankAccount || detail.bankAccount || detail.clientBankAccount) {
                recipientAccount = detail.BankAccount || detail.bankAccount || detail.clientBankAccount;
                break;
            }
        }
    }
    
    // Format amount - use CurrencyAmount (not currencyMNT)
    let amountValue = data.currencyAmount || data.CurrencyAmount || data.currencyMNT || data.mntAmount || data.totalAmount || '0';
    const cleanedAmount = String(amountValue).replace(/[^\d.-]/g, '').replace(/,/g, '');
    const amount = parseFloat(cleanedAmount) || 0;
    const formattedAmount = amount.toLocaleString('mn-MN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    // Get currency code from CurrencyId (e.g., "MNT", "USD", "EUR")
    const currencyName = data.currencyName || data.CurrencyName || '';
    const currencyCode = currencyName.toUpperCase(); // Convert to uppercase for currency code matching
    
    // Convert amount to words with currency-specific names
    const amountInWords = numberToMongolianWords(amount, currencyCode);
    
    // Get dates
    const goodsReceivedDate = data.goodsReceivedDate || documentDate;
    const paymentPurpose = data.paymentPurpose || description;
    
    // Get signatures from data, global constants, or use defaults
    // Priority: globalConstants > data.director/accountant
    let director = '';
    let accountant = '';
    
    if (typeof window !== 'undefined' && window.globalConstants) {
        director = window.globalConstants.DIRECTOR || data.director || '';
        accountant = window.globalConstants.CHIEF_ACCOUNTANT || data.accountant || data.chiefAccountant || '';
    } else {
        director = data.director || '';
        accountant = data.accountant || data.chiefAccountant || '';
    }
    
    // Generate single copy HTML
    function generateSingleCopy() {
        return `
            <div class="form-copy">
                <div class="document-header">
                    <div class="title-left">ТӨЛБӨРИЙН ДААЛГАВАР</div>
                    <div class="instruction-right">Сангийн сайдын 2017 оны 12 дугаар сарын 05-ны<br> өдрийн 347 тоот тушаалын хавсралт</div>
                </div>

                <div class="date-and-number">
                    <div>№: ${documentNumber}</div>
                    <div>${documentDate}</div>
                </div>
                <div class="client-info">
                    <div class="client-info-item">Төлөгчийн нэр: ${payer}</div>
                    <div class="client-info-item">Хүлээн авагч: ${recipient}</div>
                </div>   
                <table class="main-form-table">
                    <colgroup>
                        <col style="width: 20%;">
                        <col style="width: 20%;">
                        <col style="width: 20%;">
                        <col style="width: 15%;">
                        <col style="width: 25%;">
                    </colgroup>
                    <tr>
                        <td class="label" colspan="3" style="border-top: none; border-left: none; border-right: none;"></td>
                        <td class="merged-header"  style="border-top: none; border-left: none; border-right: none; text-align: center;">Данс</td>
                        <td class="merged-header" style="border-top: none; border-left: none; border-right: none;">Дүн</td>
                    </tr>        
                    <tr>
                        <td class="label">Төлөгчийн банк</td>
                        <td class="data-value" style="font-weight: normal;">${payerBank}</td>
                        <td class="label">Дебит данс</td>
                        <td class="data-value" colspan="1">${payerAccount}</td>
                        <td class="amount-cell" rowspan="2" style="border-top: 1px solid black; border-bottom: 1px solid black;">${formattedAmount} ${currencyName}</td>
                    </tr>
                    <tr>
                        <td class="label">Хүлээн авагчийн банк</td>
                        <td class="data-value" style="font-weight: normal;">${recipientBank}</td>
                        <td class="label">Кредит данс</td>
                        <td class="data-value" colspan="1">${recipientAccount}</td>
                    </tr>
                    
                    <tr>
                        <td class="amount-words-td label" style="border-right: none;">
                            Мөнгөн дүн (үсгээр)                
                        </td>
                        <td colspan="3">
                            <div class="amount-words-text">${amountInWords}</div>
                        </td>
                        <td class="data-value" style="border-left: 1px solid black; vertical-align: middle;">
                            ... хоног торгууль ... төг ... мөн
                        </td>
                    </tr>
                    
                    <tr>
                        <td class="label" colspan="4" style="border-right: none;">
                            Барааг хүлээн авсан буюу ажил үйлчилгээ гүйцэтгэсэн: ${goodsReceivedDate}
                        </td>
                        <td class="label" style="border-left: 1px solid black;">
                            Дүн (торгуультай)
                        </td>
                    </tr>
                    
                    <tr>
                        <td class="purpose-box-label" style="border-right: none; text-align: top left; vertical-align: top; padding: 0;"><div style="border-left: none; border-top: none; border-right: 1px solid black; border-bottom: 1px solid black; padding: 5px; font-weight: normal;">Төлбөрийн зориулалт:</div></td>
                        <td class="purpose-box-value" rowspan="4" colspan="3" style="border-left: none; border-bottom: 1px solid black; font-weight: normal; text-align: top left; vertical-align: top;">
                            ${paymentPurpose}
                        </td>
                        <td class="label" style="border-left: 1px solid black; border-top: 1px solid black; padding: 0;">
                            <table class="purpose-box-table">
                                <tr><td class="purpose-box-table-cell">Гүйлгээний утга</td><td class="purpose-box-table-cell-value"></td></tr>
                                <tr><td class="purpose-box-table-cell">Төлбөрийн зориулалт</td><td class="purpose-box-table-cell-value"></td></tr>
                                <tr><td class="purpose-box-table-cell">Төлөх</td><td class="purpose-box-table-cell-value"></td></tr>
                                <tr><td class="purpose-box-table-cell">Төлбөрийн ээлж</td><td class="purpose-box-table-cell-value"></td></tr>
                            </table>               
                        </td>
                    </tr>
                </table>

                <div class="signatures-section">
                    <div class="signature-group">
                        <table style="width: 100%;">
                            <tr>
                                <td style="font-weight: normal; padding-right: 30px;">Тамга</td>
                                <td>
                                    <table style="width: 100%;">
                                        <tr>
                                            <td style="font-weight: normal; white-space: nowrap; padding-bottom: 8px;">Гүйцэтгэх захирал:</td>
                                            <td style="padding-bottom: 10px;"><span style="border-bottom: 1px dotted black; display: inline-block; width: 60%; min-width: 100px; height: 1.2em; vertical-align: bottom;"></span></td>
                                            <td style="padding-bottom: 10px;">${director}</td>
                                        </tr>
                                        <tr>
                                            <td style="font-weight: normal; white-space: nowrap;">Ерөнхий нягтлан бодогч:</td>
                                            <td><span style="border-bottom: 1px dotted black; display: inline-block; width: 60%; min-width: 100px; height: 1.2em; vertical-align: bottom;"></span></td>
                                            <td>${accountant}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="date-signature-group">
                        <div style="font-weight: normal;">Банкинд гүйлгээ хийсэн огноо:</div>
                        <div class="bank-info-line">
                            ...........<span class="label"> он </span>....... сар .......</span>өдөр
                        </div>
                        <div style="text-align: right; margin-top: 15px;">
                            Гарын үсэг:.................................
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>${config.title} - ${documentNumber}</title>
            <meta charset="UTF-8">
            <style>${config.style}</style>
        </head>
        <body>
            <div class="document-container">
                ${generateSingleCopy()}
                ${generateSingleCopy()}
            </div>
            
            <div class="no-print" style="text-align: center; margin-top: 20px;">
                <button onclick="window.print()" style="padding: 10px 20px; margin: 5px; background: #3b82f6; color: white; border: none; border-radius: 5px; cursor: pointer;">Хэвлэх</button>
                <button onclick="window.close()" style="padding: 10px 20px; margin: 5px; background: #6b7280; color: white; border: none; border-radius: 5px; cursor: pointer;">Хаах</button>
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
                <div class="info-label">Баримтын төрөл</div>
                <div class="info-value">${data.documentTypeName || 'N/A'}</div>
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
                <div class="info-label">Баримтын төрөл</div>
                <div class="info-value">${data.documentTypeName || 'N/A'}</div>
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
                <div class="info-label">Баримтын төрөл</div>
                <div class="info-value">${data.documentTypeName || 'N/A'}</div>
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
                <div class="info-label">Баримтын төрөл</div>
                <div class="info-value">${data.documentTypeName || 'N/A'}</div>
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

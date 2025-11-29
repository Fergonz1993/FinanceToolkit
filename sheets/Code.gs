/**
 * FinanceToolkit Google Sheets Add-on
 * 
 * This Apps Script provides custom functions and menu items for financial analysis
 * using the FinanceToolkit API.
 * 
 * Setup:
 * 1. Deploy the FastAPI backend to Google Cloud Run (or use localhost for testing)
 * 2. Update API_BASE_URL below with your Cloud Run URL
 * 3. Deploy this script as a Sheets add-on or use it in a specific spreadsheet
 */

// Configuration - Update this with your Cloud Run URL
// For local testing: 'http://localhost:8000'
// For production: 'https://your-service-name-xxxxx-uc.a.run.app'
const API_BASE_URL = 'https://your-service-name-xxxxx-uc.a.run.app';

/**
 * Called when the spreadsheet is opened.
 * Creates the custom menu.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('FinanceToolkit')
    .addItem('Analyze Company', 'showCompanyAnalysisSidebar')
    .addItem('Analyze Portfolio', 'showPortfolioAnalysisSidebar')
    .addItem('Get Macro Snapshot', 'showMacroSnapshotSidebar')
    .addSeparator()
    .addItem('Settings', 'showSettingsSidebar')
    .addToUi();
}

/**
 * Shows sidebar for company analysis.
 */
function showCompanyAnalysisSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('FinanceToolkit - Company Analysis')
    .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Shows sidebar for portfolio analysis.
 */
function showPortfolioAnalysisSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('PortfolioSidebar')
    .setTitle('FinanceToolkit - Portfolio Analysis')
    .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Shows sidebar for macro snapshot.
 */
function showMacroSnapshotSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('MacroSidebar')
    .setTitle('FinanceToolkit - Macro Snapshot')
    .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Shows settings sidebar.
 */
function showSettingsSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('SettingsSidebar')
    .setTitle('FinanceToolkit - Settings')
    .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Custom function: Get income statement for a ticker.
 * Usage: =FT_INCOME("AAPL", "2020-01-01")
 */
function FT_INCOME(ticker, startDate) {
  try {
    const response = analyzeCompanyAPI(ticker, startDate, null, false, true, false, false);
    return formatDataFrameForSheets(response.statements.income);
  } catch (e) {
    return [['Error: ' + e.toString()]];
  }
}

/**
 * Custom function: Get balance sheet for a ticker.
 * Usage: =FT_BALANCE("AAPL", "2020-01-01")
 */
function FT_BALANCE(ticker, startDate) {
  try {
    const response = analyzeCompanyAPI(ticker, startDate, null, false, true, false, false);
    return formatDataFrameForSheets(response.statements.balance);
  } catch (e) {
    return [['Error: ' + e.toString()]];
  }
}

/**
 * Custom function: Get financial ratios for a ticker.
 * Usage: =FT_RATIOS("AAPL", "profitability", "2020-01-01")
 */
function FT_RATIOS(ticker, ratioType, startDate) {
  try {
    const response = analyzeCompanyAPI(ticker, startDate, null, false, false, true, false);
    const ratioTypeLower = ratioType.toLowerCase();
    if (!response.ratios || !response.ratios[ratioTypeLower]) {
      return [['Invalid ratio type. Use: profitability, liquidity, solvency, efficiency, valuation']];
    }
    return formatDataFrameForSheets(response.ratios[ratioTypeLower]);
  } catch (e) {
    return [['Error: ' + e.toString()]];
  }
}

/**
 * Custom function: Get specific ratio value.
 * Usage: =FT_RATIO("AAPL", "Return on Equity")
 */
function FT_RATIO(ticker, metric) {
  try {
    const response = analyzeCompanyAPI(ticker, null, null, false, false, true, false);
    // Search across all ratio types
    for (const ratioType in response.ratios) {
      const ratios = response.ratios[ratioType];
      const metricRow = findRowByMetric(ratios, metric);
      if (metricRow !== null) {
        return metricRow;
      }
    }
    return 'Metric not found: ' + metric;
  } catch (e) {
    return 'Error: ' + e.toString();
  }
}

/**
 * Custom function: Get WACC for a ticker.
 * Usage: =FT_WACC("AAPL")
 */
function FT_WACC(ticker) {
  try {
    const response = analyzeCompanyAPI(ticker, null, null, false, false, false, true);
    return formatDataFrameForSheets(response.models.wacc);
  } catch (e) {
    return [['Error: ' + e.toString()]];
  }
}

/**
 * Custom function: Get macroeconomic indicator.
 * Usage: =FT_MACRO("United States", "gdp", 2020)
 */
function FT_MACRO(country, metric, startYear) {
  try {
    const request = {
      countries: country,
      metrics: [metric.toLowerCase()],
      start_year: startYear || null,
      end_year: null
    };
    
    const response = UrlFetchApp.fetch(API_BASE_URL + '/macro/snapshot', {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(request)
    });
    
    const result = JSON.parse(response.getContentText());
    if (!result[metric.toLowerCase()]) {
      return [['Invalid metric. Use: gdp, unemployment, cpi, inflation']];
    }
    
    return formatDataFrameForSheets(result[metric.toLowerCase()]);
  } catch (e) {
    return [['Error: ' + e.toString()]];
  }
}

/**
 * Helper function to call company analysis API.
 */
function analyzeCompanyAPI(ticker, startDate, endDate, quarterly, includeStatements, includeRatios, includeModels) {
  const request = {
    tickers: ticker,
    start_date: startDate || null,
    end_date: endDate || null,
    quarterly: quarterly || false,
    include_models: includeModels || false,
    include_ratios: includeRatios || false,
    include_historical: false
  };
  
  const response = UrlFetchApp.fetch(API_BASE_URL + '/analyze/company', {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(request)
  });
  
  return JSON.parse(response.getContentText());
}

/**
 * Helper function to format DataFrame response for Google Sheets.
 */
function formatDataFrameForSheets(dataFrame) {
  if (!dataFrame || !dataFrame.data || dataFrame.data.length === 0) {
    return [['No data available']];
  }
  
  const result = [];
  
  // Add header row
  if (dataFrame.columns && dataFrame.columns.length > 0) {
    result.push([dataFrame.index ? 'Metric' : ''].concat(dataFrame.columns));
  }
  
  // Add data rows
  if (dataFrame.index && dataFrame.data) {
    for (let i = 0; i < dataFrame.data.length; i++) {
      const row = dataFrame.data[i];
      const indexValue = dataFrame.index[i] || '';
      result.push([indexValue].concat(row));
    }
  } else if (dataFrame.data) {
    // No index, just data
    result.push(...dataFrame.data);
  }
  
  return result;
}

/**
 * Helper function to find a row by metric name.
 */
function findRowByMetric(ratios, metric) {
  if (!ratios || !ratios.data || !ratios.index) {
    return null;
  }
  
  const metricIndex = ratios.index.indexOf(metric);
  if (metricIndex === -1) {
    return null;
  }
  
  const row = ratios.data[metricIndex];
  if (row.length === 1) {
    return row[0];
  }
  
  return row;
}

/**
 * Function to analyze company and write results to sheet.
 * Called from sidebar.
 */
function analyzeCompanyToSheet(ticker, startDate, endDate, quarterly) {
  try {
    const response = analyzeCompanyAPI(ticker, startDate, endDate, quarterly, true, true, true);
    const sheet = SpreadsheetApp.getActiveSheet();
    const startRow = sheet.getLastRow() + 2;
    
    // Write income statement
    sheet.getRange(startRow, 1).setValue('Income Statement - ' + ticker);
    sheet.getRange(startRow + 1, 1, formatDataFrameForSheets(response.statements.income).length, 
                   formatDataFrameForSheets(response.statements.income)[0].length)
          .setValues(formatDataFrameForSheets(response.statements.income));
    
    let currentRow = startRow + formatDataFrameForSheets(response.statements.income).length + 2;
    
    // Write profitability ratios
    if (response.ratios && response.ratios.profitability) {
      sheet.getRange(currentRow, 1).setValue('Profitability Ratios - ' + ticker);
      const profitability = formatDataFrameForSheets(response.ratios.profitability);
      sheet.getRange(currentRow + 1, 1, profitability.length, profitability[0].length)
            .setValues(profitability);
      currentRow += profitability.length + 2;
    }
    
    return 'Analysis complete! Results written to sheet.';
  } catch (e) {
    return 'Error: ' + e.toString();
  }
}

/**
 * Function to get macro snapshot and write to sheet.
 * Called from sidebar.
 */
function getMacroSnapshotToSheet(countries, metrics, startYear, endYear) {
  try {
    const request = {
      countries: countries.split(',').map(c => c.trim()),
      metrics: metrics.split(',').map(m => m.trim()),
      start_year: startYear || null,
      end_year: endYear || null
    };
    
    const response = UrlFetchApp.fetch(API_BASE_URL + '/macro/snapshot', {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(request)
    });
    
    const result = JSON.parse(response.getContentText());
    const sheet = SpreadsheetApp.getActiveSheet();
    const startRow = sheet.getLastRow() + 2;
    let currentRow = startRow;
    
    for (const metric in result) {
      sheet.getRange(currentRow, 1).setValue(metric.toUpperCase());
      const data = formatDataFrameForSheets(result[metric]);
      sheet.getRange(currentRow + 1, 1, data.length, data[0].length)
            .setValues(data);
      currentRow += data.length + 2;
    }
    
    return 'Macro snapshot complete! Results written to sheet.';
  } catch (e) {
    return 'Error: ' + e.toString();
  }
}


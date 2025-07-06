// Import necessary Angular modules and services
import { CommonModule } from '@angular/common';
import { Component, HostListener } from '@angular/core';
import { NgxChartsModule } from '@swimlane/ngx-charts';  // Module for charts
import { ApiService } from '../service/api.service'; // Service to interact with API
import { FormsModule } from '@angular/forms'; // Forms module for two-way binding
import { TranslateModule, TranslateService } from '@ngx-translate/core'; // Import TranslateModule and TranslateService
import * as XLSX from 'xlsx'; // Excel export library
import { saveAs } from 'file-saver'; // File saving utility

// Define the component metadata
@Component({
  selector: 'app-dashboard', // The component selector
  standalone: true, // Marks this component as standalone (no need for NgModule)
  imports: [CommonModule, NgxChartsModule, FormsModule, TranslateModule], // Import other modules required for this component
  templateUrl: './dashboard.component.html', // HTML template
  styleUrl: './dashboard.component.css', // CSS styles for the component
})

export class DashboardComponent {
  // Define the properties for storing transaction data and chart data
  transactions: any[] = []; // Array to hold all transactions
  transactionTypeData: any[] = []; // Data for the chart showing count of transactions by type
  transactionAmountData: any[] = []; // Data for the chart showing total amount by transaction type
  monthlyTransactionData: any[] = []; // Data for the chart showing daily totals for the selected month

  // List of months, used for selecting a month
  months = [
    { name: 'JANUARY', value: '01' },
    { name: 'FEBRUARY', value: '02' },
    { name: 'MARCH', value: '03' },
    { name: 'APRIL', value: '04' },
    { name: 'MAY', value: '05' },
    { name: 'JUNE', value: '06' },
    { name: 'JULY', value: '07' },
    { name: 'AUGUST', value: '08' },
    { name: 'SEPTEMBER', value: '09' },
    { name: 'OCTOBER', value: '10' },
    { name: 'NOVEMBER', value: '11' },
    { name: 'DECEMBER', value: '12' },
  ];

  // Array to store the years (last 10 years from current year)
  years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i); 

  // Array to store days (will be updated based on selected month/year)
  days: number[] = [];

  // Selected month, year and day for filtering data
  selectedMonth = '';
  selectedYear = '';
  selectedDay = '';

  // Export related properties
  selectedReportType = 'monthly'; // Default to monthly report
  isExporting = false; // Track export status
  
  // Preview related properties
  showPreview = false;
  showExcelPreview = false; // New Excel preview modal
  previewSummaryData: any[] = [];
  previewTransactionData: any[] = [];
  previewPerformanceData: any[] = [];
  excelPreviewData: any[] = []; // Data for Excel preview

  // Chart view dimensions, legend, and animations settings
  view: [number, number] = [700, 400];  // Chart size: width x height
  showLegend = true;  // Display chart legend
  showLabels = true;  // Display labels on chart
  animations = true;  // Enable chart animations

  // Constructor to inject ApiService for API calls
  constructor(private apiService: ApiService, private translate: TranslateService) {
    // Translate month names will be done in ngOnInit after translate service is ready
    this.updateChartSize();
    this.onResize();
  }

  // 響應式圖表尺寸調整
  updateChartSize(): void {
    const screenWidth = window.innerWidth;

    if (screenWidth <= 480) {
      // 小手機
      this.view = [screenWidth - 40, 250];
    } else if (screenWidth <= 768) {
      // 手機版
      this.view = [screenWidth - 60, 300];
    } else if (screenWidth <= 1024) {
      // 平板版
      this.view = [screenWidth - 100, 350];
    } else {
      // 桌面版
      this.view = [700, 400];
    }
  }

  // 監聽視窗大小變化
  @HostListener('window:resize', ['$event'])
  onResize(): void {
    this.updateChartSize();
  }

  // ngOnInit lifecycle hook, called when the component initializes
  ngOnInit(): void {
    // Translate month names
    this.months = this.months.map(month => ({
      ...month,
      name: this.translate.instant(month.name)
    }));
    
    // Initialize days array for current month
    this.updateDaysArray();
    
    this.loadTransactions(); // Load transactions when the component initializes
  }

  // Method to fetch all transactions from the API
  loadTransactions(): void {
    this.apiService.getAllTransactions('').subscribe((data: any[]) => {
      this.transactions = data; // Store transactions data
      this.processChartData(); // Process data to generate charts
    });
  }

  // Method to process transaction data for type-based and amount-based charts
  processChartData(): void {
    // Filter transactions based on selected filters
    let filteredTransactions = this.getFilteredTransactions();

    // Object to count the number of transactions by type
    const typeCounts: { [key: string]: number } = {};

    // Object to sum the transaction amounts by type
    const amountByType: { [key: string]: number } = {};

    // Loop through each filtered transaction to calculate totals by type
    filteredTransactions.forEach((transaction) => {
      const type = transaction.transactionType; // Get the transaction type
      typeCounts[type] = (typeCounts[type] || 0) + 1; // Count transactions by type
      amountByType[type] = (amountByType[type] || 0) + transaction.totalPrice; // Sum amounts by type
    });

    // Prepare data for chart displaying number of transactions by type
    this.transactionTypeData = Object.keys(typeCounts).map((type) => ({
      name: type,
      value: typeCounts[type],
    }));

    // Prepare data for chart displaying total transaction amount by type
    this.transactionAmountData = Object.keys(amountByType).map((type) => ({
      name: type,
      value: amountByType[type],
    }));
  }

  // Method to load transaction data based on selected filters
  loadMonthlyData(): void {
    // If specific month and year are selected, use API call
    if (this.selectedMonth && this.selectedYear) {
      this.apiService
        .getTransactionsByMonthAndYear(
          Number.parseInt(this.selectedMonth), // Convert month string to number
          Number.parseInt(this.selectedYear) // Convert year string to number
        )
        .subscribe((data: any[]) => {
          this.transactions = data; // Store transactions for the selected month
          this.processChartData(); // Process the overall data for charts
          this.processMonthlyData(data); // Process the data for the daily chart
        });
    } else {
      // If no specific filters, reload all transactions and filter client-side
      this.loadTransactions();
    }
  }

  // Get filtered transactions based on selected filters
  getFilteredTransactions(): any[] {
    let filtered = this.transactions;

    // Filter by year
    if (this.selectedYear) {
      filtered = filtered.filter(transaction => {
        const transactionDate = new Date(transaction.createdAt);
        return transactionDate.getFullYear() === parseInt(this.selectedYear);
      });
    }

    // Filter by month
    if (this.selectedMonth) {
      filtered = filtered.filter(transaction => {
        const transactionDate = new Date(transaction.createdAt);
        return transactionDate.getMonth() + 1 === parseInt(this.selectedMonth);
      });
    }

    // Filter by day
    if (this.selectedDay) {
      filtered = filtered.filter(transaction => {
        const transactionDate = new Date(transaction.createdAt);
        return transactionDate.getDate() === parseInt(this.selectedDay);
      });
    }

    return filtered;
  }

  // Method to process daily transaction data for the selected month
  processMonthlyData(transactions: any[]): void {
    // Use filtered transactions if no specific API call was made
    const dataToProcess = transactions.length > 0 ? transactions : this.getFilteredTransactions();
    
    // Object to store daily total amounts (key = day, value = total amount)
    const dailyTotals: { [key: string]: number } = {};

    // Loop through each transaction and accumulate totals for each day
    dataToProcess.forEach((transaction) => {
      const date = new Date(transaction.createdAt).getDate().toString(); // Get the day from transaction date
      dailyTotals[date] = (dailyTotals[date] || 0) + transaction.totalPrice; // Sum daily totals
    });

    // Prepare data for chart displaying daily totals for the selected month
    this.monthlyTransactionData = Object.keys(dailyTotals).map((day) => ({
      name: `Day ${day}`,
      value: dailyTotals[day],
    }));
  }

  // Update days array based on selected month and year
  updateDaysArray(): void {
    if (this.selectedMonth && this.selectedYear) {
      // Get the number of days in the selected month
      const year = parseInt(this.selectedYear);
      const month = parseInt(this.selectedMonth);
      const daysInMonth = new Date(year, month, 0).getDate();
      this.days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    } else {
      // Default to current month if no selection
      const today = new Date();
      const daysInCurrentMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
      this.days = Array.from({ length: daysInCurrentMonth }, (_, i) => i + 1);
    }
    
    // Reset selected day if it's invalid for the new month
    if (this.selectedDay && parseInt(this.selectedDay) > this.days.length) {
      this.selectedDay = '';
    }
  }

  // Called when month or year selection changes
  onMonthYearChange(): void {
    this.updateDaysArray();
  }

  // Show Excel preview before export
  exportToExcel(): void {
    if (this.isExporting) return;
    
    let dataToExport: any[] = [];
    
    // Determine data based on report type
    switch (this.selectedReportType) {
      case 'daily':
        dataToExport = this.getDailyReportData();
        break;
      case 'monthly':
        dataToExport = this.getMonthlyReportData();
        break;
      case 'quarterly':
        dataToExport = this.getQuarterlyReportData();
        break;
      case 'yearly':
        dataToExport = this.getYearlyReportData();
        break;
      default:
        dataToExport = this.transactions.filter(t => t.transactionType === 'SELL');
    }

    // Store data for Excel preview
    this.excelPreviewData = dataToExport;
    this.showExcelPreview = true;
  }

  // Confirm and actually export Excel
  confirmExcelExport(): void {
    this.isExporting = true;
    this.showExcelPreview = false;
    
    try {
      let fileName = '';
      
      // Determine filename based on report type
      switch (this.selectedReportType) {
        case 'daily':
          fileName = `Daily_Sales_Report_${new Date().toISOString().split('T')[0]}`;
          break;
        case 'monthly':
          fileName = `Monthly_Sales_Report_${this.selectedYear}_${this.selectedMonth || 'All'}`;
          break;
        case 'quarterly':
          fileName = `Quarterly_Sales_Report_${this.selectedYear || new Date().getFullYear()}`;
          break;
        case 'yearly':
          fileName = `Yearly_Sales_Report_${this.selectedYear || new Date().getFullYear()}`;
          break;
        default:
          fileName = 'Sales_Report';
      }

      this.generateExcelFile(this.excelPreviewData, fileName);
      
    } catch (error) {
      console.error('Export error:', error);
      alert(this.translate.instant('EXPORT_ERROR'));
    } finally {
      this.isExporting = false;
    }
  }

  // Cancel Excel export
  cancelExcelExport(): void {
    this.showExcelPreview = false;
    this.excelPreviewData = [];
  }

  // Get Excel preview rows with product details (first 5 rows)
  getExcelPreviewRows(): any[] {
    const previewRows: any[] = [];

    for (const transaction of this.excelPreviewData.slice(0, 5)) {
      const customerCode = transaction.customer?.customerCode || '-';
      const customerName = transaction.customer?.customerName || '-';
      const productDetails = transaction.products || [];

      if (productDetails.length > 0) {
        // Create separate rows for each product in the transaction
        for (const productAssoc of productDetails) {
          const unitPrice = productAssoc.unit_price || productAssoc.product?.price || 0;
          const lineTotal = productAssoc.line_total || (unitPrice * productAssoc.quantity);

          previewRows.push({
            date: new Date(transaction.createdAt).toLocaleDateString(),
            customerCode: customerCode,
            customerName: customerName,
            salesOrderNumber: transaction.id,
            productCode: productAssoc.product?.productCode || '-',
            productName: productAssoc.product?.productName || '-',
            quantity: productAssoc.quantity || 0,
            salespersonName: transaction.user?.name || '-',
            totalAmount: lineTotal.toFixed(2),
            note: productAssoc.notes || transaction.note || '-'
          });
        }
      } else {
        // If no product details, create single row with transaction info
        previewRows.push({
          date: new Date(transaction.createdAt).toLocaleDateString(),
          customerCode: customerCode,
          customerName: customerName,
          salesOrderNumber: transaction.id,
          productCode: '-',
          productName: '-',
          quantity: transaction.totalProducts || 0,
          salespersonName: transaction.user?.name || '-',
          totalAmount: transaction.totalPrice.toFixed(2),
          note: transaction.note || '-'
        });
      }

      // Limit to 5 rows total for preview
      if (previewRows.length >= 5) break;
    }

    return previewRows;
  }

  // Get daily report data - SALES ONLY
  getDailyReportData(): any[] {
    // If specific date is selected, use it; otherwise use today
    let targetDate: Date;
    
    if (this.selectedYear && this.selectedMonth && this.selectedDay) {
      targetDate = new Date(parseInt(this.selectedYear), parseInt(this.selectedMonth) - 1, parseInt(this.selectedDay));
    } else {
      targetDate = new Date();
    }
    
    targetDate.setHours(0, 0, 0, 0);
    
    return this.transactions.filter(transaction => {
      const transactionDate = new Date(transaction.createdAt);
      transactionDate.setHours(0, 0, 0, 0);
      const isSellTransaction = transaction.transactionType === 'SELL';
      const isTargetDate = transactionDate.getTime() === targetDate.getTime();
      
      return isTargetDate && isSellTransaction;
    });
  }

  // Get monthly report data - SALES ONLY
  getMonthlyReportData(): any[] {
    return this.transactions.filter(transaction => {
      const isSellTransaction = transaction.transactionType === 'SELL';
      
      if (!this.selectedMonth || !this.selectedYear) {
        return isSellTransaction;
      }
      
      const transactionDate = new Date(transaction.createdAt);
      const isCorrectMonth = transactionDate.getMonth() + 1 === parseInt(this.selectedMonth);
      const isCorrectYear = transactionDate.getFullYear() === parseInt(this.selectedYear);
      
      return isCorrectMonth && isCorrectYear && isSellTransaction;
    });
  }

  // Get quarterly report data - SALES ONLY
  getQuarterlyReportData(): any[] {
    const currentYear = parseInt(this.selectedYear) || new Date().getFullYear();
    
    return this.transactions.filter(transaction => {
      const transactionDate = new Date(transaction.createdAt);
      const isSellTransaction = transaction.transactionType === 'SELL';
      const isCorrectYear = transactionDate.getFullYear() === currentYear;
      
      return isCorrectYear && isSellTransaction;
    });
  }

  // Get yearly report data - SALES ONLY
  getYearlyReportData(): any[] {
    const currentYear = parseInt(this.selectedYear) || new Date().getFullYear();
    
    return this.transactions.filter(transaction => {
      const transactionDate = new Date(transaction.createdAt);
      const isSellTransaction = transaction.transactionType === 'SELL';
      const isCorrectYear = transactionDate.getFullYear() === currentYear;
      
      return isCorrectYear && isSellTransaction;
    });
  }

  // Generate Excel file with single worksheet
  generateExcelFile(transactions: any[], fileName: string): void {
    // Create a new workbook
    const workbook = XLSX.utils.book_new();

    // Generate detailed sales data
    const salesData = this.generateDetailedSalesData(transactions);
    const salesWorksheet = XLSX.utils.json_to_sheet(salesData);
    
    // Create sheet name based on report type and period
    const sheetName = this.getSheetName();
    XLSX.utils.book_append_sheet(workbook, salesWorksheet, sheetName);

    // Generate Excel file and save
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(blob, `${fileName}.xlsx`);

    alert(this.translate.instant('EXPORT_SUCCESS'));
  }

  // Generate sheet name based on report type and period
  getSheetName(): string {
    const currentYear = this.selectedYear || new Date().getFullYear().toString();
    
    switch (this.selectedReportType) {
      case 'daily':
        if (this.selectedMonth && this.selectedDay) {
          return `${currentYear}-${this.selectedMonth.padStart(2, '0')}-${this.selectedDay.padStart(2, '0')}-${this.translate.instant('DAILY_REPORT_SHORT')}`;
        }
        return `${currentYear}-${this.translate.instant('DAILY_REPORT_SHORT')}`;
      case 'monthly':
        if (this.selectedMonth) {
          return `${currentYear}-${this.selectedMonth.padStart(2, '0')}-${this.translate.instant('MONTHLY_REPORT_SHORT')}`;
        }
        return `${currentYear}-${this.translate.instant('MONTHLY_REPORT_SHORT')}`;
      case 'quarterly':
        return `${currentYear}-${this.translate.instant('QUARTERLY_REPORT_SHORT')}`;
      case 'yearly':
        return `${currentYear}-${this.translate.instant('YEARLY_REPORT_SHORT')}`;
      default:
        return `${currentYear}-${this.translate.instant('SALES_REPORT_SHORT')}`;
    }
  }

  // Generate detailed sales data for Excel export
  generateDetailedSalesData(transactions: any[]): any[] {
    return transactions.map(transaction => {
      // 現在所有銷售交易都應該有客戶資訊
      const customerCode = transaction.customer?.customerCode || 'N/A';
      const customerName = transaction.customer?.customerName || 'N/A';
      
      // Extract product details from transaction
      const productDetails = transaction.products || [];
      
      // If transaction has multiple products, create separate rows for each
      if (productDetails.length > 0) {
        return productDetails.map((productAssoc: any) => {
          // 使用正確的價格來源：優先使用unit_price，否則使用product.price
          const unitPrice = productAssoc.unit_price || productAssoc.product?.price || 0;
          const lineTotal = productAssoc.line_total || (unitPrice * productAssoc.quantity);
          
          return {
            [this.translate.instant('DATE')]: new Date(transaction.createdAt).toLocaleDateString(),
            [this.translate.instant('CUSTOMER_CODE')]: customerCode,
            [this.translate.instant('CUSTOMER_NAME')]: customerName,
            [this.translate.instant('SALES_ORDER_NUMBER')]: transaction.id,
            [this.translate.instant('SALESPERSON_ID')]: transaction.user?.id || 'N/A',
            [this.translate.instant('SALESPERSON_NAME')]: transaction.user?.name || 'N/A',
            [this.translate.instant('PRODUCT_CODE')]: productAssoc.product?.productCode || 'N/A',
            [this.translate.instant('PRODUCT_NAME')]: productAssoc.product?.productName || 'N/A',
            [this.translate.instant('QUANTITY')]: productAssoc.quantity || 0,
            [this.translate.instant('TOTAL_AMOUNT')]: lineTotal.toFixed(2),
            [this.translate.instant('NOTE')]: transaction.note || 'N/A'
          };
        });
      } else {
        // If no product details, create single row with transaction info
        return [{
          [this.translate.instant('DATE')]: new Date(transaction.createdAt).toLocaleDateString(),
          [this.translate.instant('CUSTOMER_CODE')]: customerCode,
          [this.translate.instant('CUSTOMER_NAME')]: customerName,
          [this.translate.instant('SALES_ORDER_NUMBER')]: transaction.id,
          [this.translate.instant('SALESPERSON_ID')]: transaction.user?.id || 'N/A',
          [this.translate.instant('SALESPERSON_NAME')]: transaction.user?.name || 'N/A',
          [this.translate.instant('PRODUCT_CODE')]: 'N/A',
          [this.translate.instant('PRODUCT_NAME')]: 'N/A',
          [this.translate.instant('QUANTITY')]: transaction.totalProducts || 0,
          [this.translate.instant('TOTAL_AMOUNT')]: transaction.totalPrice.toFixed(2),
          [this.translate.instant('NOTE')]: transaction.note || 'N/A'
        }];
      }
    }).flat(); // Flatten array to handle multiple products per transaction
  }

  // Preview report functionality
  previewReport(): void {
    let dataToExport: any[] = [];
    
    // Get filtered sales data based on report type
    switch (this.selectedReportType) {
      case 'daily':
        dataToExport = this.getDailyReportData();
        break;
      case 'monthly':
        dataToExport = this.getMonthlyReportData();
        break;
      case 'quarterly':
        dataToExport = this.getQuarterlyReportData();
        break;
      case 'yearly':
        dataToExport = this.getYearlyReportData();
        break;
      default:
        dataToExport = this.transactions.filter(t => t.transactionType === 'SELL');
    }

    // Generate preview data
    this.previewSummaryData = this.generatePreviewSummaryData(dataToExport);
    this.previewTransactionData = this.generatePreviewTransactionData(dataToExport);
    this.previewPerformanceData = this.generatePreviewPerformanceData(dataToExport);
    
    this.showPreview = true;
  }

  closePreview(): void {
    this.showPreview = false;
  }

  getReportTitle(): string {
    switch (this.selectedReportType) {
      case 'daily':
        return this.translate.instant('DAILY_REPORT');
      case 'monthly':
        return this.translate.instant('MONTHLY_REPORT');
      case 'quarterly':
        return this.translate.instant('QUARTERLY_REPORT');
      case 'yearly':
        return this.translate.instant('YEARLY_REPORT');
      default:
        return this.translate.instant('SALES_SUMMARY');
    }
  }

  getReportPeriodInfo(): string {
    const today = new Date();
    
    switch (this.selectedReportType) {
      case 'daily':
        if (this.selectedYear && this.selectedMonth && this.selectedDay) {
          const selectedDate = new Date(parseInt(this.selectedYear), parseInt(this.selectedMonth) - 1, parseInt(this.selectedDay));
          return `${this.translate.instant('SELECTED_DATE')}: ${selectedDate.toLocaleDateString()}`;
        } else if (this.selectedYear && this.selectedMonth) {
          const monthName = this.months.find(m => m.value === this.selectedMonth)?.name || this.selectedMonth;
          return `${this.translate.instant('SELECTED_MONTH')}: ${monthName} ${this.selectedYear}`;
        } else if (this.selectedYear) {
          return `${this.translate.instant('SELECTED_YEAR')}: ${this.selectedYear}`;
        }
        return `${this.translate.instant('TODAY')}: ${today.toLocaleDateString()}`;
      case 'monthly':
        if (this.selectedMonth && this.selectedYear) {
          const monthName = this.months.find(m => m.value === this.selectedMonth)?.name || this.selectedMonth;
          return `${this.translate.instant('SELECTED_MONTH')}: ${monthName} ${this.selectedYear}`;
        }
        return this.translate.instant('SELECTED_MONTH') + ': ' + this.translate.instant('ALL');
      case 'quarterly':
        const currentYear = this.selectedYear || today.getFullYear().toString();
        return `${this.translate.instant('SELECTED_YEAR')}: ${currentYear}`;
      case 'yearly':
        const year = this.selectedYear || today.getFullYear().toString();
        return `${this.translate.instant('SELECTED_YEAR')}: ${year}`;
      default:
        return this.translate.instant('ALL');
    }
  }

  // Generate preview summary data
  generatePreviewSummaryData(transactions: any[]): any[] {
    const totalAmount = transactions.reduce((sum, t) => sum + t.totalPrice, 0);
    const totalTransactions = transactions.length;
    const averageOrderValue = totalTransactions > 0 ? totalAmount / totalTransactions : 0;
    const reportPeriod = this.getReportPeriodInfo();

    return [
      { type: this.translate.instant('REPORT_PERIOD'), value: reportPeriod },
      { type: this.translate.instant('TOTAL_SALES_AMOUNT'), value: totalAmount.toFixed(2) },
      { type: this.translate.instant('TOTAL_SALES_COUNT'), value: totalTransactions.toString() },
      { type: this.translate.instant('AVERAGE_ORDER_VALUE'), value: averageOrderValue.toFixed(2) },
      { type: this.translate.instant('SALES_ONLY'), value: this.translate.instant('YES') }
    ];
  }

  // Generate preview transaction data (first 10 records with product details)
  generatePreviewTransactionData(transactions: any[]): any[] {
    const previewData: any[] = [];

    for (const transaction of transactions.slice(0, 10)) {
      const customerCode = transaction.customer?.customerCode || 'N/A';
      const customerName = transaction.customer?.customerName || 'N/A';
      const productDetails = transaction.products || [];

      if (productDetails.length > 0) {
        // Create separate rows for each product in the transaction
        for (const productAssoc of productDetails) {
          const unitPrice = productAssoc.unit_price || productAssoc.product?.price || 0;
          const lineTotal = productAssoc.line_total || (unitPrice * productAssoc.quantity);

          previewData.push({
            date: new Date(transaction.createdAt).toLocaleDateString(),
            id: transaction.id,
            customerCode: customerCode,
            customerName: customerName,
            productCode: productAssoc.product?.productCode || 'N/A',
            productName: productAssoc.product?.productName || 'N/A',
            quantity: productAssoc.quantity || 0,
            salesperson: transaction.user?.name || 'N/A',
            amount: lineTotal.toFixed(2),
            note: productAssoc.notes || transaction.note || 'N/A'
          });
        }
      } else {
        // If no product details, create single row with transaction info
        previewData.push({
          date: new Date(transaction.createdAt).toLocaleDateString(),
          id: transaction.id,
          customerCode: customerCode,
          customerName: customerName,
          productCode: 'N/A',
          productName: 'N/A',
          quantity: transaction.totalProducts || 0,
          salesperson: transaction.user?.name || 'N/A',
          amount: transaction.totalPrice.toFixed(2),
          note: transaction.note || 'N/A'
        });
      }

      // Limit to 10 rows total
      if (previewData.length >= 10) break;
    }

    return previewData;
  }

  // Generate preview performance data
  generatePreviewPerformanceData(transactions: any[]): any[] {
    const salespersonStats: { [key: string]: any } = {};

    transactions.forEach(transaction => {
      const salespersonName = transaction.user?.name || this.translate.instant('UNKNOWN');
      
      if (!salespersonStats[salespersonName]) {
        salespersonStats[salespersonName] = {
          name: salespersonName,
          transactionCount: 0,
          totalAmount: 0
        };
      }
      
      salespersonStats[salespersonName].transactionCount++;
      salespersonStats[salespersonName].totalAmount += transaction.totalPrice;
    });

    return Object.values(salespersonStats).map((stats: any) => ({
      name: stats.name,
      count: stats.transactionCount.toString(),
      total: stats.totalAmount.toFixed(2),
      average: (stats.totalAmount / stats.transactionCount).toFixed(2)
    }));
  }
}
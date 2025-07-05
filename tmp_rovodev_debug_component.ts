// 臨時調試組件 - 可以添加到Angular應用中進行測試
import { Component } from '@angular/core';
import { ApiService } from '../app/service/api.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-debug',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div style="padding: 20px; font-family: monospace;">
      <h2>API Data Debug</h2>
      
      <button (click)="testAPI()" style="padding: 10px; margin: 10px; background: #007bff; color: white; border: none; border-radius: 4px;">
        Test API Data
      </button>
      
      <button (click)="clearResults()" style="padding: 10px; margin: 10px; background: #dc3545; color: white; border: none; border-radius: 4px;">
        Clear Results
      </button>
      
      <div *ngIf="loading" style="color: blue;">Loading...</div>
      
      <div *ngIf="error" style="color: red; background: #ffe6e6; padding: 10px; margin: 10px;">
        <strong>Error:</strong> {{ error }}
      </div>
      
      <div *ngIf="results" style="background: #f0f0f0; padding: 15px; margin: 10px; white-space: pre-wrap; max-height: 500px; overflow-y: auto;">
        {{ results }}
      </div>
    </div>
  `
})
export class DebugComponent {
  loading = false;
  error = '';
  results = '';

  constructor(private apiService: ApiService) {}

  testAPI() {
    this.loading = true;
    this.error = '';
    this.results = '';

    this.apiService.getAllTransactions('').subscribe({
      next: (data: any[]) => {
        this.loading = false;
        this.analyzeData(data);
      },
      error: (err) => {
        this.loading = false;
        this.error = `API Error: ${err.message || err}`;
      }
    });
  }

  analyzeData(transactions: any[]) {
    let analysis = `API Data Analysis Results:\n\n`;
    analysis += `Total transactions: ${transactions.length}\n`;
    
    const sellTransactions = transactions.filter(t => t.transactionType === 'SELL');
    analysis += `SELL transactions: ${sellTransactions.length}\n`;
    
    const purchaseTransactions = transactions.filter(t => t.transactionType === 'PURCHASE');
    analysis += `PURCHASE transactions: ${purchaseTransactions.length}\n\n`;

    // Analyze customer data
    const sellWithCustomer = sellTransactions.filter(t => t.customer);
    const sellWithCustomerCode = sellTransactions.filter(t => t.customer?.customerCode);
    const sellWithCustomerName = sellTransactions.filter(t => t.customer?.customerName);
    
    analysis += `Customer Data Analysis:\n`;
    analysis += `  SELL with customer object: ${sellWithCustomer.length}/${sellTransactions.length}\n`;
    analysis += `  SELL with customer code: ${sellWithCustomerCode.length}/${sellTransactions.length}\n`;
    analysis += `  SELL with customer name: ${sellWithCustomerName.length}/${sellTransactions.length}\n\n`;

    // Analyze product data
    const sellWithProducts = sellTransactions.filter(t => t.products && t.products.length > 0);
    let productAssociationsWithDetails = 0;
    let productAssociationsWithCode = 0;
    let productAssociationsWithName = 0;
    let productAssociationsWithUnitPrice = 0;
    let productAssociationsWithLineTotal = 0;

    sellTransactions.forEach(t => {
      if (t.products && t.products.length > 0) {
        t.products.forEach((p: any) => {
          if (p.product) productAssociationsWithDetails++;
          if (p.product?.productCode) productAssociationsWithCode++;
          if (p.product?.productName) productAssociationsWithName++;
          if (p.unit_price !== undefined) productAssociationsWithUnitPrice++;
          if (p.line_total !== undefined) productAssociationsWithLineTotal++;
        });
      }
    });

    analysis += `Product Data Analysis:\n`;
    analysis += `  SELL with products array: ${sellWithProducts.length}/${sellTransactions.length}\n`;
    analysis += `  Product associations with details: ${productAssociationsWithDetails}\n`;
    analysis += `  Product associations with code: ${productAssociationsWithCode}\n`;
    analysis += `  Product associations with name: ${productAssociationsWithName}\n`;
    analysis += `  Product associations with unit_price: ${productAssociationsWithUnitPrice}\n`;
    analysis += `  Product associations with line_total: ${productAssociationsWithLineTotal}\n\n`;

    // Sample data
    if (sellTransactions.length > 0) {
      analysis += `Sample SELL transaction:\n`;
      const sample = sellTransactions[0];
      analysis += JSON.stringify({
        id: sample.id,
        transactionType: sample.transactionType,
        totalPrice: sample.totalPrice,
        customer: sample.customer,
        products: sample.products?.slice(0, 1), // First product only
        user: sample.user
      }, null, 2);
    }

    this.results = analysis;
  }

  clearResults() {
    this.results = '';
    this.error = '';
  }
}
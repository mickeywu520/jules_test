import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { Router, ActivatedRoute } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-sell',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './sell.component.html',
  styleUrl: './sell.component.css'
})
export class SellComponent implements OnInit {

  constructor(
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private loadingService: LoadingService
  ){}

  // 基本資料
  customers: any[] = []
  products: any[] = []
  salesOrders: any[] = []
  filteredSalesOrders: any[] = []  // 過濾後的銷售單列表
  
  // 表單資料
  isEditing: boolean = false
  salesOrderId: string | null = null
  
  // 銷售單主檔
  formData = {
    sales_date: new Date().toISOString().split('T')[0], // 今日日期
    customer_id: '',
    payment_term: 'CASH',
    notes: '',
    tax_type: 'INCLUSIVE',
    tax_rate: 0.05,
    discount_rate: 0.0
  }
  
  // 銷售明細
  items: any[] = []
  
  // 選中的客戶資訊
  selectedCustomer: any = null
  
  // UI 狀態
  message: string = ''
  showSalesOrderList: boolean = true  // 預設顯示銷售單列表
  searchTerm: string = ''  // 搜尋關鍵字
  
  // 選項
  paymentTerms = [
    { value: 'CASH', label: 'PAYMENT_CASH' },
    { value: 'MONTHLY', label: 'PAYMENT_MONTHLY' },
    { value: 'TRANSFER', label: 'PAYMENT_TRANSFER' },
    { value: 'CREDIT_CARD', label: 'PAYMENT_CREDIT_CARD' },
    { value: 'CHECK', label: 'PAYMENT_CHECK' }
  ]
  
  taxTypes = [
    { value: 'INCLUSIVE', label: 'TAX_INCLUSIVE' },
    { value: 'EXCLUSIVE', label: 'TAX_EXCLUSIVE' },
    { value: 'ADDITIONAL', label: 'TAX_ADDITIONAL' }
  ]
  
  salesOrderStatuses = [
    { value: 'DRAFT', label: 'STATUS_DRAFT' },
    { value: 'CONFIRMED', label: 'STATUS_CONFIRMED' },
    { value: 'SHIPPED', label: 'STATUS_SHIPPED' },
    { value: 'DELIVERED', label: 'STATUS_DELIVERED' },
    { value: 'CANCELLED', label: 'STATUS_CANCELLED' }
  ]

  ngOnInit(): void {
    // 檢查是否為編輯模式
    this.salesOrderId = this.route.snapshot.paramMap.get('id');
    if (this.salesOrderId) {
      this.isEditing = true;
      this.fetchSalesOrderById(this.salesOrderId);
    }

    // 載入基本資料
    this.loadingService.showDataLoading();
    this.fetchCustomers();
    this.fetchProducts();
    this.fetchSalesOrders();
  }

  // 載入客戶列表
  fetchCustomers(): void {
    this.apiService.getAllCustomers().subscribe({
      next: (res: any) => {
        this.customers = res;
      },
      error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch customers', 'error')
    });
  }

  // 載入產品列表（只載入有效產品，不包含已刪除的產品）
  fetchProducts(): void {
    this.apiService.getActiveProducts().subscribe({
      next: (res: any) => {
        this.products = res;
      },
      error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch products', 'error')
    });
  }

  // 載入銷售單列表
  fetchSalesOrders(): void {
    this.apiService.getAllSalesOrders().subscribe({
      next: (res: any) => {
        this.salesOrders = res;
        this.applySearchFilter(); // 套用搜尋過濾
        this.loadingService.hideLoading();
      },
      error: (err) => {
        this.showToast(err?.error?.message || err?.message || 'Unable to fetch sales orders', 'error');
        this.loadingService.hideLoading();
      }
    });
  }

  // 根據 ID 載入銷售單
  fetchSalesOrderById(id: string): void {
    this.apiService.getSalesOrderById(id).subscribe({
      next: (res: any) => {
        this.formData = {
          sales_date: res.sales_date,
          customer_id: res.customer_id.toString(),
          payment_term: res.payment_term,
          notes: res.notes || '',
          tax_type: res.tax_type,
          tax_rate: res.tax_rate,
          discount_rate: res.discount_rate
        };
        this.items = res.items.map((item: any) => ({
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
          line_total: item.line_total,
          notes: item.notes || '',
          product: item.product
        }));
        this.selectedCustomer = res.customer;
      },
      error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch sales order', 'error')
    });
  }

  // 套用搜尋過濾
  applySearchFilter(): void {
    if (!this.searchTerm.trim()) {
      this.filteredSalesOrders = [...this.salesOrders];
    } else {
      const searchLower = this.searchTerm.toLowerCase().trim();
      this.filteredSalesOrders = this.salesOrders.filter(so => 
        // 搜尋銷售單號
        so.so_number?.toLowerCase().includes(searchLower) ||
        // 搜尋客戶名稱
        so.customer?.customerName?.toLowerCase().includes(searchLower)
      );
    }
  }

  // 搜尋輸入變更時的處理
  onSearchChange(): void {
    this.applySearchFilter();
  }

  // 清除搜尋
  clearSearch(): void {
    this.searchTerm = '';
    this.applySearchFilter();
  }

  // 客戶選擇變更時的處理
  onCustomerChange(): void {
    if (this.formData.customer_id) {
      // 找到選中的客戶
      this.selectedCustomer = this.customers.find(customer => customer.id.toString() === this.formData.customer_id);
    } else {
      this.selectedCustomer = null;
    }
  }

  // 添加新的銷售明細行
  addNewItem(): void {
    this.items.push({
      product_id: '',
      quantity: 1,
      unit_price: 0,
      line_total: 0,
      notes: '',
      product: null
    });
  }

  // 刪除銷售明細行
  removeItem(index: number): void {
    this.items.splice(index, 1);
    this.calculateTotals();
  }

  // 產品選擇變更時的處理
  onProductChange(index: number): void {
    const item = this.items[index];
    if (item.product_id) {
      const product = this.products.find(p => p.id.toString() === item.product_id);
      if (product) {
        item.product = product;
        item.unit_price = 0; // 預設單價為0，需要手動輸入
        // 檢查庫存
        this.checkStock(index);
        this.calculateLineTotal(index);
      }
    } else {
      item.product = null;
      item.unit_price = 0;
      item.line_total = 0;
    }
  }

  // 計算行小計
  calculateLineTotal(index: number): void {
    const item = this.items[index];
    // 檢查庫存
    this.checkStock(index);
    item.line_total = item.quantity * item.unit_price;
    this.calculateTotals();
  }

  // 檢查庫存
  checkStock(index: number): void {
    const item = this.items[index];
    if (item.product && item.quantity > 0) {
      const availableStock = item.product.stock || 0;
      if (item.quantity > availableStock) {
        this.showToast(
          `商品「${item.product.productName}」庫存不足！目前庫存：${availableStock}，需求數量：${item.quantity}`,
          'error'
        );
        // 可選：自動調整為最大可用庫存
        // item.quantity = availableStock;
      }
    }
  }

  // 計算總金額
  calculateTotals(): void {
    // 這裡只計算前端顯示，實際計算由後端處理
    const subtotal = this.items.reduce((sum, item) => sum + item.line_total, 0);
    // 可以在這裡添加前端預覽計算邏輯
  }

  // 表單提交
  handleSubmit(): void {
    // 驗證表單
    if (!this.formData.customer_id) {
      this.showToast('請選擇客戶', 'error');
      return;
    }

    if (this.items.length === 0) {
      this.showToast('請添加銷售明細', 'error');
      return;
    }

    // 驗證所有明細都有產品和數量
    for (let item of this.items) {
      if (!item.product_id || item.quantity <= 0 || item.unit_price < 0) {
        this.showToast('請確認所有銷售明細的產品、數量和單價', 'error');
        return;
      }

      // 檢查庫存是否足夠
      if (item.product && item.quantity > item.product.stock) {
        this.showToast(
          `商品「${item.product.productName}」庫存不足！目前庫存：${item.product.stock}，需求數量：${item.quantity}`,
          'error'
        );
        return;
      }
    }

    // 準備提交資料
    const salesOrderData = {
      ...this.formData,
      customer_id: parseInt(this.formData.customer_id),
      items: this.items.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price,
        notes: item.notes || null
      }))
    };

    if (this.isEditing) {
      // 更新銷售單
      this.loadingService.showUpdating();
      this.apiService.updateSalesOrder(this.salesOrderId!, salesOrderData).subscribe({
        next: (res: any) => {
          this.showToast('銷售單更新成功！', 'success');
          this.resetForm();
          this.showSalesOrderList = true;
          this.fetchSalesOrders();
          this.loadingService.hideLoading();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '更新銷售單失敗', 'error');
          this.loadingService.hideLoading();
        }
      });
    } else {
      // 新增銷售單
      this.loadingService.showSaving();
      this.apiService.createSalesOrder(salesOrderData).subscribe({
        next: (res: any) => {
          this.showToast('銷售單建立成功！', 'success');
          this.resetForm();
          this.showSalesOrderList = true;
          this.fetchSalesOrders();
          this.loadingService.hideLoading();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '建立銷售單失敗', 'error');
          this.loadingService.hideLoading();
        }
      });
    }
  }

  // 重置表單
  resetForm(): void {
    this.isEditing = false;
    this.salesOrderId = null;
    this.formData = {
      sales_date: new Date().toISOString().split('T')[0],
      customer_id: '',
      payment_term: 'CASH',
      notes: '',
      tax_type: 'INCLUSIVE',
      tax_rate: 0.05,
      discount_rate: 0.0
    };
    this.items = [];
    this.selectedCustomer = null;
  }

  // 切換銷售單列表顯示
  toggleSalesOrderList(): void {
    this.showSalesOrderList = !this.showSalesOrderList;
    if (this.showSalesOrderList) {
      this.fetchSalesOrders();
    }
  }

  // 編輯銷售單
  editSalesOrder(id: string): void {
    this.salesOrderId = id;
    this.isEditing = true;
    this.showSalesOrderList = false;
    this.fetchSalesOrderById(id);
  }

  // 刪除銷售單
  deleteSalesOrder(id: string): void {
    if (confirm('確定要刪除此銷售單嗎？')) {
      this.apiService.deleteSalesOrder(id).subscribe({
        next: (res: any) => {
          this.showToast('銷售單刪除成功！', 'success');
          this.fetchSalesOrders();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '刪除銷售單失敗', 'error');
        }
      });
    }
  }

  // 狀態變更處理
  onStatusChange(id: string | number, newStatus: string): void {
    this.apiService.updateSalesOrderStatus(id.toString(), newStatus).subscribe({
      next: (res: any) => {
        this.showToast('狀態更新成功！', 'success');
        this.fetchSalesOrders();
      },
      error: (error) => {
        this.showToast(error?.error?.message || error?.message || '狀態更新失敗', 'error');
      }
    });
  }

  // Toast 通知
  showToast(message: string, type: 'success' | 'error' = 'success'): void {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }

  // 保留舊的 showMessage 方法以保持兼容性
  showMessage(message: string) {
    this.showToast(message);
  }
}

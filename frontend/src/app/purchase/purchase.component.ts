import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { Router, ActivatedRoute } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-purchase',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './purchase.component.html',
  styleUrl: './purchase.component.css'
})
export class PurchaseComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private loadingService: LoadingService
  ){}

  // 基本資料
  products: any[] = []
  suppliers: any[] = []
  purchaseOrders: any[] = []

  // 表單資料
  isEditing: boolean = false
  purchaseOrderId: string | null = null

  // 採購單主檔
  formData = {
    purchase_date: new Date().toISOString().split('T')[0], // 今日日期
    expected_delivery_date: '',
    supplier_id: '',
    notes: '',
    tax_type: 'INCLUSIVE',
    tax_rate: 0.05,
    payment_method: ''
  }

  // 採購明細
  items: any[] = [
    {
      product_id: '',
      quantity: 1,
      unit_price: 0,
      notes: '',
      product: null // 用於顯示產品資訊
    }
  ]

  // 計算結果
  subtotal: number = 0
  tax_amount: number = 0
  total_amount: number = 0

  // UI 狀態
  message: string = ''
  showPurchaseOrderList: boolean = true  // 預設顯示採購單列表

  // 追蹤原始狀態
  private originalStatuses: { [key: string]: string } = {}

  // 選項
  taxTypes = [
    { value: 'INCLUSIVE', label: 'TAX_INCLUSIVE' },
    { value: 'EXCLUSIVE', label: 'TAX_EXCLUSIVE' },
    { value: 'ADDITIONAL', label: 'TAX_ADDITIONAL' }
  ]

  purchaseOrderStatuses = [
    { value: 'DRAFT', label: 'STATUS_DRAFT' },
    { value: 'PENDING', label: 'STATUS_PENDING' },
    { value: 'CONFIRMED', label: 'STATUS_CONFIRMED' },
    { value: 'RECEIVED', label: 'STATUS_RECEIVED' },
    { value: 'CANCELLED', label: 'STATUS_CANCELLED' }
  ]
  

  ngOnInit(): void {
    // 檢查是否為編輯模式
    this.purchaseOrderId = this.route.snapshot.paramMap.get('id');
    if (this.purchaseOrderId) {
      this.isEditing = true;
      this.fetchPurchaseOrderById(this.purchaseOrderId);
    }

    // 載入基本資料
    this.loadingService.showDataLoading();
    this.fetchProducts();
    this.fetchSuppliers();
    this.fetchPurchaseOrders();
  }

  // 載入產品資料
  fetchProducts(): void {
    this.apiService.products$.subscribe((prods: any[]) => {
      this.products = prods;
    });

    // 只有在BehaviorSubject沒有數據時才發起請求
    const currentProducts = this.apiService.productsSource.value;
    if (!currentProducts || currentProducts.length === 0) {
      this.apiService.fetchAndBroadcastProducts().subscribe({
        next: () => { /* console.log('Products loaded'); */ },
        error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch products', 'error')
      });
    }
  }

  // 載入供應商資料
  fetchSuppliers(): void {
    this.apiService.suppliers$.subscribe((supps: any[]) => {
      this.suppliers = supps;
    });

    // 只有在BehaviorSubject沒有數據時才發起請求
    const currentSuppliers = this.apiService.suppliersSource.value;
    if (!currentSuppliers || currentSuppliers.length === 0) {
      this.apiService.fetchAndBroadcastSuppliers().subscribe({
        next: () => { /* console.log('Suppliers loaded'); */ },
        error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch suppliers', 'error')
      });
    }
  }

  // 載入採購單列表
  fetchPurchaseOrders(): void {
    this.apiService.getAllPurchaseOrders().subscribe({
      next: (res: any) => {
        this.purchaseOrders = res;
        // 初始化原始狀態追蹤
        this.originalStatuses = {};
        res.forEach((po: any) => {
          this.originalStatuses[po.id.toString()] = po.status;
        });
        this.loadingService.hideLoading();
      },
      error: (err) => {
        this.showToast(err?.error?.message || err?.message || 'Unable to fetch purchase orders', 'error');
        this.loadingService.hideLoading();
      }
    });
  }

  // 根據 ID 載入採購單
  fetchPurchaseOrderById(id: string): void {
    this.apiService.getPurchaseOrderById(id).subscribe({
      next: (res: any) => {
        this.formData = {
          purchase_date: res.purchase_date,
          expected_delivery_date: res.expected_delivery_date || '',
          supplier_id: res.supplier_id.toString(),
          notes: res.notes || '',
          tax_type: res.tax_type,
          tax_rate: res.tax_rate,
          payment_method: res.payment_method || ''
        };
        this.items = res.items.map((item: any) => ({
          product_id: item.product_id.toString(),
          quantity: item.quantity,
          unit_price: item.unit_price,
          notes: item.notes || '',
          product: item.product
        }));
        this.calculateTotals();
      },
      error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch purchase order', 'error')
    });
  }

  // 產品選擇變更時的處理
  onProductChange(index: number): void {
    const item = this.items[index];
    if (item.product_id) {
      const product = this.products.find(p => p.id.toString() === item.product_id);
      if (product) {
        item.product = product;
        // 可以在這裡設定預設單價
        // item.unit_price = product.default_price || 0;
      }
    }
    this.calculateTotals();
  }

  // 數量或單價變更時重新計算
  onQuantityOrPriceChange(): void {
    this.calculateTotals();
  }

  // 新增商品明細列
  addItem(): void {
    this.items.push({
      product_id: '',
      quantity: 1,
      unit_price: 0,
      notes: '',
      product: null
    });
  }

  // 刪除商品明細列
  removeItem(index: number): void {
    if (this.items.length > 1) {
      this.items.splice(index, 1);
      this.calculateTotals();
    }
  }

  // 計算總額
  calculateTotals(): void {
    this.subtotal = this.items.reduce((sum, item) => {
      return sum + (item.quantity * item.unit_price);
    }, 0);

    if (this.formData.tax_type === 'INCLUSIVE') {
      // 含稅：總額 = 小計，稅額 = 小計 * 稅率 / (1 + 稅率)
      this.total_amount = this.subtotal;
      this.tax_amount = this.subtotal * this.formData.tax_rate / (1 + this.formData.tax_rate);
    } else if (this.formData.tax_type === 'EXCLUSIVE') {
      // 未稅：稅額 = 0，總額 = 小計
      this.tax_amount = 0;
      this.total_amount = this.subtotal;
    } else { // ADDITIONAL
      // 外加稅：稅額 = 小計 * 稅率，總額 = 小計 + 稅額
      this.tax_amount = this.subtotal * this.formData.tax_rate;
      this.total_amount = this.subtotal + this.tax_amount;
    }
  }

  // 表單提交
  handleSubmit(): void {
    // 驗證表單
    if (!this.formData.supplier_id) {
      this.showToast('請選擇供應商', 'error');
      return;
    }

    if (this.items.length === 0 || this.items.some(item => !item.product_id || item.quantity <= 0 || item.unit_price < 0)) {
      this.showToast('請確認所有商品明細都已正確填寫', 'error');
      return;
    }

    // 準備提交資料
    const purchaseOrderData = {
      ...this.formData,
      supplier_id: parseInt(this.formData.supplier_id),
      items: this.items.map(item => ({
        product_id: parseInt(item.product_id),
        quantity: item.quantity,
        unit_price: item.unit_price,
        notes: item.notes || null
      }))
    };

    if (this.isEditing) {
      // 更新採購單
      this.loadingService.showUpdating();
      this.apiService.updatePurchaseOrder(this.purchaseOrderId!, purchaseOrderData).subscribe({
        next: (res: any) => {
          this.showToast('採購單更新成功！', 'success');
          this.resetForm();
          this.showPurchaseOrderList = true; // 跳回採購單列表
          this.fetchPurchaseOrders(); // 刷新列表
          this.loadingService.hideLoading();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '更新採購單失敗', 'error');
          this.loadingService.hideLoading();
        }
      });
    } else {
      // 新增採購單
      this.loadingService.showSaving();
      this.apiService.createPurchaseOrder(purchaseOrderData).subscribe({
        next: (res: any) => {
          this.showToast('採購單建立成功！', 'success');
          this.resetForm();
          this.showPurchaseOrderList = true; // 跳回採購單列表
          this.fetchPurchaseOrders(); // 刷新列表
          this.loadingService.hideLoading();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '建立採購單失敗', 'error');
          this.loadingService.hideLoading();
        }
      });
    }
  }

  // 重置表單
  resetForm(): void {
    this.isEditing = false;
    this.purchaseOrderId = null;
    this.formData = {
      purchase_date: new Date().toISOString().split('T')[0],
      expected_delivery_date: '',
      supplier_id: '',
      notes: '',
      tax_type: 'INCLUSIVE',
      tax_rate: 0.05,
      payment_method: ''
    };
    this.items = [{
      product_id: '',
      quantity: 1,
      unit_price: 0,
      notes: '',
      product: null
    }];
    this.calculateTotals();
  }

  // 切換採購單列表顯示
  togglePurchaseOrderList(): void {
    this.showPurchaseOrderList = !this.showPurchaseOrderList;
    if (this.showPurchaseOrderList) {
      this.fetchPurchaseOrders();
    }
  }

  // 編輯採購單
  editPurchaseOrder(id: string): void {
    this.purchaseOrderId = id;
    this.isEditing = true;
    this.showPurchaseOrderList = false;
    this.fetchPurchaseOrderById(id);
  }

  // 刪除採購單
  deletePurchaseOrder(id: string | number): void {
    const idStr = id.toString();

    // 找到對應的採購單
    const purchaseOrder = this.purchaseOrders.find(po => po.id.toString() === idStr);
    if (!purchaseOrder) {
      this.showToast('找不到採購單', 'error');
      return;
    }

    // 檢查是否為草稿狀態
    if (purchaseOrder.status !== 'DRAFT') {
      this.showToast('只有草稿狀態的採購單才能刪除', 'error');
      return;
    }

    if (confirm('確定要刪除此採購單嗎？')) {
      this.apiService.deletePurchaseOrder(idStr).subscribe({
        next: (res: any) => {
          this.showToast('採購單刪除成功！', 'success');
          this.fetchPurchaseOrders();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '刪除採購單失敗', 'error');
        }
      });
    }
  }

  // 狀態變更處理
  onStatusChange(id: string | number, newStatus: string): void {
    const idStr = id.toString();

    // 找到對應的採購單
    const purchaseOrder = this.purchaseOrders.find(po => po.id.toString() === idStr);
    if (!purchaseOrder) {
      this.showToast('找不到採購單', 'error');
      console.error('Purchase order not found:', id, 'Available orders:', this.purchaseOrders.map(po => po.id));
      return;
    }

    // 取得原始狀態
    const originalStatus = this.originalStatuses[idStr];

    // 如果狀態沒有變更，直接返回
    if (originalStatus === newStatus) {
      return;
    }

    this.updatePurchaseOrderStatus(idStr, newStatus, originalStatus, purchaseOrder);
  }

  // 更新採購單狀態
  updatePurchaseOrderStatus(id: string, status: string, originalStatus: string, purchaseOrder: any): void {
    this.apiService.updatePurchaseOrderStatus(id, status).subscribe({
      next: (res: any) => {
        this.showToast('狀態更新成功！', 'success');
        // 確保本地資料與後端同步
        if (res && purchaseOrder) {
          purchaseOrder.status = res.status;
          purchaseOrder.updated_at = res.updated_at;
          // 更新原始狀態追蹤
          this.originalStatuses[id] = res.status;
        }
      },
      error: (error) => {
        this.showToast(error?.error?.message || error?.message || '狀態更新失敗', 'error');
        // 發生錯誤時恢復原始狀態
        purchaseOrder.status = originalStatus;
      }
    });
  }

  // Toast 通知
  showToast(message: string, type: 'success' | 'error' = 'success'): void {
    this.message = message;
    // 這裡可以整合真正的 Toast 組件
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }

  // 顯示舊的 message 方法（向後兼容）
  showMessage(message: string): void {
    this.showToast(message, 'error');
  }


}

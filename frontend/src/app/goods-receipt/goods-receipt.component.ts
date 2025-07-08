import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { Router, ActivatedRoute } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-goods-receipt',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './goods-receipt.component.html',
  styleUrls: ['./goods-receipt.component.css']
})

export class GoodsReceiptComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private loadingService: LoadingService
  ){}

  // 基本資料
  purchaseOrders: any[] = []
  goodsReceipts: any[] = []
  filteredGoodsReceipts: any[] = []  // 過濾後的入庫單列表
  
  // 表單資料
  isEditing: boolean = false
  goodsReceiptId: string | null = null
  
  // 入庫單主檔
  formData = {
    receipt_date: new Date().toISOString().split('T')[0], // 今日日期
    purchase_order_id: '',
    warehouse_type: 'MAIN',
    warehouse_location: '',
    notes: ''
  }
  
  // 入庫明細
  items: any[] = []
  
  // 選中的採購單資訊
  selectedPurchaseOrder: any = null
  
  // UI 狀態
  message: string = ''
  showGoodsReceiptList: boolean = true  // 預設顯示入庫單列表
  searchTerm: string = ''  // 搜尋關鍵字
  
  // 選項
  warehouseTypes = [
    { value: 'MAIN', label: 'WAREHOUSE_MAIN' },
    { value: 'RAW_MATERIAL', label: 'WAREHOUSE_RAW_MATERIAL' },
    { value: 'FINISHED_GOODS', label: 'WAREHOUSE_FINISHED_GOODS' },
    { value: 'QUARANTINE', label: 'WAREHOUSE_QUARANTINE' },
    { value: 'DAMAGED', label: 'WAREHOUSE_DAMAGED' }
  ]
  
  goodsReceiptStatuses = [
    { value: 'DRAFT', label: 'STATUS_DRAFT' },
    { value: 'PENDING', label: 'STATUS_PENDING' },
    { value: 'COMPLETED', label: 'STATUS_COMPLETED' },
    { value: 'CANCELLED', label: 'STATUS_CANCELLED' }
  ]

  ngOnInit(): void {
    // 檢查是否為編輯模式
    this.goodsReceiptId = this.route.snapshot.paramMap.get('id');
    if (this.goodsReceiptId) {
      this.isEditing = true;
      this.fetchGoodsReceiptById(this.goodsReceiptId);
    }

    // 載入基本資料
    this.loadingService.showDataLoading();
    this.fetchAvailablePurchaseOrders();
    this.fetchGoodsReceipts();
  }

  // 載入可入庫的採購單
  fetchAvailablePurchaseOrders(): void {
    this.apiService.getAllPurchaseOrders().subscribe({
      next: (res: any) => {
        // 顯示已確認和已收貨的採購單（支援多次入庫）
        this.purchaseOrders = res.filter((po: any) =>
          po.status === 'CONFIRMED' || po.status === 'RECEIVED'
        );
      },
      error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch purchase orders', 'error')
    });
  }

  // 載入入庫單列表
  fetchGoodsReceipts(): void {
    this.apiService.getAllGoodsReceipts().subscribe({
      next: (res: any) => {
        this.goodsReceipts = res;
        this.applySearchFilter(); // 套用搜尋過濾
        this.loadingService.hideLoading();
      },
      error: (err) => {
        this.showToast(err?.error?.message || err?.message || 'Unable to fetch goods receipts', 'error');
        this.loadingService.hideLoading();
      }
    });
  }

  // 套用搜尋過濾
  applySearchFilter(): void {
    if (!this.searchTerm.trim()) {
      this.filteredGoodsReceipts = [...this.goodsReceipts];
    } else {
      const searchLower = this.searchTerm.toLowerCase().trim();
      this.filteredGoodsReceipts = this.goodsReceipts.filter(gr =>
        // 搜尋入庫單號
        gr.gr_number?.toLowerCase().includes(searchLower) ||
        // 搜尋採購單號
        gr.purchase_order?.po_number?.toLowerCase().includes(searchLower)
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

  // 根據 ID 載入入庫單
  fetchGoodsReceiptById(id: string): void {
    this.apiService.getGoodsReceiptById(id).subscribe({
      next: (res: any) => {
        this.formData = {
          receipt_date: res.receipt_date,
          purchase_order_id: res.purchase_order_id.toString(),
          warehouse_type: res.warehouse_type,
          warehouse_location: res.warehouse_location || '',
          notes: res.notes || ''
        };
        this.items = res.items.map((item: any) => ({
          purchase_order_item_id: item.purchase_order_item_id,
          product_id: item.product_id,
          ordered_quantity: item.ordered_quantity,
          received_quantity: item.received_quantity,
          storage_location: item.storage_location || '',
          notes: item.notes || '',
          product: item.product
        }));
        this.selectedPurchaseOrder = res.purchase_order;
      },
      error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch goods receipt', 'error')
    });
  }

  // 採購單選擇變更時的處理
  onPurchaseOrderChange(): void {
    if (this.formData.purchase_order_id) {
      // 找到選中的採購單
      this.selectedPurchaseOrder = this.purchaseOrders.find(po => po.id.toString() === this.formData.purchase_order_id);
      
      // 載入可入庫的明細
      this.apiService.getReceivableItemsByPurchaseOrder(this.formData.purchase_order_id).subscribe({
        next: (res: any) => {
          this.items = res.map((item: any) => ({
            purchase_order_item_id: item.id,
            product_id: item.product_id,
            ordered_quantity: item.quantity,
            received_quantity: item.quantity, // 預設實到數量等於採購數量
            storage_location: '',
            notes: '',
            product: item.product
          }));
        },
        error: (err) => this.showToast(err?.error?.message || err?.message || 'Unable to fetch purchase order items', 'error')
      });
    } else {
      this.selectedPurchaseOrder = null;
      this.items = [];
    }
  }

  // 表單提交
  handleSubmit(): void {
    // 驗證表單
    if (!this.formData.purchase_order_id) {
      this.showToast('請選擇採購單', 'error');
      return;
    }

    if (this.items.length === 0) {
      this.showToast('請確認入庫明細', 'error');
      return;
    }

    // 準備提交資料
    const goodsReceiptData = {
      ...this.formData,
      purchase_order_id: parseInt(this.formData.purchase_order_id),
      items: this.items.map(item => ({
        purchase_order_item_id: item.purchase_order_item_id,
        product_id: item.product_id,
        ordered_quantity: item.ordered_quantity,
        received_quantity: item.received_quantity,
        storage_location: item.storage_location || null,
        notes: item.notes || null
      }))
    };

    if (this.isEditing) {
      // 更新入庫單
      this.loadingService.showUpdating();
      this.apiService.updateGoodsReceipt(this.goodsReceiptId!, goodsReceiptData).subscribe({
        next: (res: any) => {
          this.showToast('入庫單更新成功！', 'success');
          this.resetForm();
          this.showGoodsReceiptList = true;
          this.fetchGoodsReceipts(); // 重新載入列表
          this.fetchAvailablePurchaseOrders(); // 重新載入採購單列表
          this.loadingService.hideLoading();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '更新入庫單失敗', 'error');
          this.loadingService.hideLoading();
        }
      });
    } else {
      // 新增入庫單
      this.loadingService.showSaving();
      this.apiService.createGoodsReceipt(goodsReceiptData).subscribe({
        next: (res: any) => {
          this.showToast('入庫單建立成功！', 'success');
          this.resetForm();
          this.showGoodsReceiptList = true;
          this.fetchGoodsReceipts(); // 重新載入列表
          this.fetchAvailablePurchaseOrders(); // 重新載入採購單列表
          this.loadingService.hideLoading();
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '建立入庫單失敗', 'error');
          this.loadingService.hideLoading();
        }
      });
    }
  }

  // 重置表單
  resetForm(): void {
    this.isEditing = false;
    this.goodsReceiptId = null;
    this.formData = {
      receipt_date: new Date().toISOString().split('T')[0],
      purchase_order_id: '',
      warehouse_type: 'MAIN',
      warehouse_location: '',
      notes: ''
    };
    this.items = [];
    this.selectedPurchaseOrder = null;
  }

  // 切換入庫單列表顯示
  toggleGoodsReceiptList(): void {
    this.showGoodsReceiptList = !this.showGoodsReceiptList;
    if (this.showGoodsReceiptList) {
      this.fetchGoodsReceipts();
    }
  }

  // 編輯入庫單
  editGoodsReceipt(id: string): void {
    this.goodsReceiptId = id;
    this.isEditing = true;
    this.showGoodsReceiptList = false;
    this.fetchGoodsReceiptById(id);
  }

  // 刪除入庫單
  deleteGoodsReceipt(id: string): void {
    if (confirm('確定要刪除此入庫單嗎？')) {
      this.apiService.deleteGoodsReceipt(id).subscribe({
        next: (res: any) => {
          this.showToast('入庫單刪除成功！', 'success');
          this.fetchGoodsReceipts(); // 重新載入列表
          this.fetchAvailablePurchaseOrders(); // 重新載入採購單列表
        },
        error: (error) => {
          this.showToast(error?.error?.message || error?.message || '刪除入庫單失敗', 'error');
        }
      });
    }
  }

  // 狀態變更處理
  onStatusChange(id: string | number, newStatus: string): void {
    this.apiService.updateGoodsReceiptStatus(id.toString(), newStatus).subscribe({
      next: (res: any) => {
        this.showToast('狀態更新成功！', 'success');
        this.fetchGoodsReceipts(); // 重新載入列表
        this.fetchAvailablePurchaseOrders(); // 重新載入採購單列表
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
}

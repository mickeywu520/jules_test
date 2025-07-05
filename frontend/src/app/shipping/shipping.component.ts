import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { ApiService } from '../service/api.service';

interface Customer {
  id: number;
  customerName: string;
  customerType: string;
  contactPerson: string;
  phone: string;
  deliveryAddress: string;
}

interface Product {
  id: number;
  productName: string;
  unit: string;
  stock: number;
}

interface SalesOrder {
  id: number;
  so_number: string;
  sales_date: string;
  customer_id: number;
  status: string;
  total_amount: number;
  customer?: Customer;
  items?: SalesOrderItem[];
}

interface SalesOrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  line_total: number;
  product?: Product;
}

interface ShippingOrderItem {
  id?: number;
  product_id: number;
  ordered_quantity: number;
  shipped_quantity: number;
  batch_number?: string;
  notes?: string;
  product?: Product;
}

interface ShippingOrder {
  id: number;
  sh_number: string;
  sales_order_id: number;
  customer_id: number;
  shipping_date: string;
  shipping_address?: string;
  shipper_name?: string;
  shipping_method: string;
  tracking_number?: string;
  status: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
  sales_order?: SalesOrder;
  customer?: Customer;
  items: ShippingOrderItem[];
}

@Component({
  selector: 'app-shipping',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './shipping.component.html',
  styleUrls: ['./shipping.component.css']
})
export class ShippingComponent implements OnInit {
  // 顯示控制
  showShippingOrderList = true;
  isEditing = false;
  message = '';

  // 資料陣列
  shippingOrders: ShippingOrder[] = [];
  filteredShippingOrders: ShippingOrder[] = [];
  salesOrders: SalesOrder[] = [];
  customers: Customer[] = [];
  products: Product[] = [];

  // 搜尋和篩選
  searchTerm = '';
  statusFilter = '';

  // 表單資料
  formData = {
    sales_order_id: '',
    shipping_date: new Date().toISOString().split('T')[0],
    shipping_address: '',
    shipper_name: '',
    shipping_method: 'SELF_DELIVERY',
    tracking_number: '',
    notes: ''
  };

  items: ShippingOrderItem[] = [];
  currentShippingOrderId: number | null = null;

  // 狀態選項
  shippingOrderStatuses = [
    { value: 'PREPARING', label: 'STATUS_PREPARING' },
    { value: 'READY', label: 'STATUS_READY' },
    { value: 'SHIPPED', label: 'STATUS_SHIPPED' },
    { value: 'DELIVERED', label: 'STATUS_DELIVERED' },
    { value: 'CANCELLED', label: 'STATUS_CANCELLED' }
  ];

  shippingMethods = [
    { value: 'SELF_DELIVERY', label: 'SHIPPING_SELF_DELIVERY' },
    { value: 'HOME_DELIVERY', label: 'SHIPPING_HOME_DELIVERY' },
    { value: 'FREIGHT', label: 'SHIPPING_FREIGHT' },
    { value: 'PICKUP', label: 'SHIPPING_PICKUP' }
  ];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadShippingOrders();
    this.loadSalesOrders();
    this.loadCustomers();
    this.loadProducts();
  }

  // 載入出貨單列表
  loadShippingOrders(): void {
    this.apiService.getShippingOrders().subscribe({
      next: (data: any) => {
        this.shippingOrders = data;
        this.applyFilters();
      },
      error: (error: any) => {
        console.error('Error loading shipping orders:', error);
        this.showToast('載入出貨單失敗', 'error');
      }
    });
  }

  // 載入銷售單列表（用於創建出貨單）
  loadSalesOrders(): void {
    this.apiService.getSalesOrders().subscribe({
      next: (data: any) => {
        // 只顯示已確認且尚未出貨的銷售單
        this.salesOrders = data.filter((so: any) => so.status === 'CONFIRMED');
      },
      error: (error: any) => {
        console.error('Error loading sales orders:', error);
      }
    });
  }

  // 載入客戶列表
  loadCustomers(): void {
    this.apiService.getAllCustomers().subscribe({
      next: (data: any) => {
        this.customers = data;
      },
      error: (error: any) => {
        console.error('Error loading customers:', error);
      }
    });
  }

  // 載入產品列表
  loadProducts(): void {
    this.apiService.getAllProducts().subscribe({
      next: (data: any) => {
        this.products = data;
      },
      error: (error: any) => {
        console.error('Error loading products:', error);
      }
    });
  }

  // 切換顯示模式
  toggleShippingOrderList(): void {
    this.showShippingOrderList = !this.showShippingOrderList;
    if (this.showShippingOrderList) {
      this.resetForm();
      this.loadShippingOrders();
    }
  }

  // 搜尋變更
  onSearchChange(): void {
    this.applyFilters();
  }

  // 狀態篩選變更
  onStatusFilterChange(): void {
    this.applyFilters();
  }

  // 應用篩選
  applyFilters(): void {
    this.filteredShippingOrders = this.shippingOrders.filter(so => {
      const matchesSearch = !this.searchTerm || 
        so.sh_number.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (so.customer?.customerName || '').toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (so.sales_order?.so_number || '').toLowerCase().includes(this.searchTerm.toLowerCase());
      
      const matchesStatus = !this.statusFilter || so.status === this.statusFilter;
      
      return matchesSearch && matchesStatus;
    });
  }

  // 清除搜尋
  clearSearch(): void {
    this.searchTerm = '';
    this.statusFilter = '';
    this.applyFilters();
  }

  // 基於銷售單創建出貨單
  createFromSalesOrder(): void {
    if (!this.formData.sales_order_id) {
      this.showToast('請選擇銷售單', 'error');
      return;
    }

    const selectedSalesOrder = this.salesOrders.find(so => so.id.toString() === this.formData.sales_order_id);
    if (!selectedSalesOrder) {
      this.showToast('找不到選擇的銷售單', 'error');
      return;
    }

    // 設定客戶地址
    if (selectedSalesOrder.customer && !this.formData.shipping_address) {
      this.formData.shipping_address = selectedSalesOrder.customer.deliveryAddress;
    }

    const shippingOrderData = {
      shipping_date: this.formData.shipping_date,
      shipping_address: this.formData.shipping_address,
      shipper_name: this.formData.shipper_name,
      shipping_method: this.formData.shipping_method,
      tracking_number: this.formData.tracking_number,
      notes: this.formData.notes
    };

    this.apiService.createShippingOrderFromSalesOrder(parseInt(this.formData.sales_order_id), shippingOrderData).subscribe({
      next: (response: any) => {
        this.showToast('出貨單建立成功', 'success');
        this.resetForm();
        this.showShippingOrderList = true;
        this.loadShippingOrders();
      },
      error: (error: any) => {
        console.error('Error creating shipping order:', error);
        this.showToast(error.error?.detail || '建立出貨單失敗', 'error');
      }
    });
  }

  // 編輯出貨單
  editShippingOrder(shippingOrderId: number): void {
    const shippingOrder = this.shippingOrders.find(so => so.id === shippingOrderId);
    if (!shippingOrder) {
      this.showToast('找不到出貨單', 'error');
      return;
    }

    this.currentShippingOrderId = shippingOrderId;
    this.isEditing = true;
    this.showShippingOrderList = false;

    // 填入表單資料
    this.formData = {
      sales_order_id: shippingOrder.sales_order_id.toString(),
      shipping_date: shippingOrder.shipping_date,
      shipping_address: shippingOrder.shipping_address || '',
      shipper_name: shippingOrder.shipper_name || '',
      shipping_method: shippingOrder.shipping_method,
      tracking_number: shippingOrder.tracking_number || '',
      notes: shippingOrder.notes || ''
    };

    // 填入明細資料
    this.items = [...shippingOrder.items];
  }

  // 更新出貨單狀態
  onStatusChange(shippingOrderId: number, newStatus: string): void {
    this.apiService.updateShippingOrderStatus(shippingOrderId, { status: newStatus }).subscribe({
      next: (response: any) => {
        this.showToast('狀態更新成功', 'success');
        this.loadShippingOrders();
      },
      error: (error: any) => {
        console.error('Error updating status:', error);
        this.showToast(error.error?.detail || '狀態更新失敗', 'error');
        this.loadShippingOrders(); // 重新載入以恢復原狀態
      }
    });
  }

  // 刪除出貨單
  deleteShippingOrder(shippingOrderId: number): void {
    if (confirm('確定要刪除這個出貨單嗎？')) {
      this.apiService.deleteShippingOrder(shippingOrderId).subscribe({
        next: (response: any) => {
          this.showToast('出貨單刪除成功', 'success');
          this.loadShippingOrders();
        },
        error: (error: any) => {
          console.error('Error deleting shipping order:', error);
          this.showToast(error.error?.detail || '刪除出貨單失敗', 'error');
        }
      });
    }
  }

  // 重置表單
  resetForm(): void {
    this.formData = {
      sales_order_id: '',
      shipping_date: new Date().toISOString().split('T')[0],
      shipping_address: '',
      shipper_name: '',
      shipping_method: 'SELF_DELIVERY',
      tracking_number: '',
      notes: ''
    };
    this.items = [];
    this.currentShippingOrderId = null;
    this.isEditing = false;
  }

  // 顯示提示訊息
  showToast(message: string, type: 'success' | 'error' = 'success'): void {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 3000);
  }

  // 銷售單選擇變更
  onSalesOrderChange(): void {
    if (this.formData.sales_order_id) {
      const selectedSalesOrder = this.salesOrders.find(so => so.id.toString() === this.formData.sales_order_id);
      if (selectedSalesOrder && selectedSalesOrder.customer) {
        this.formData.shipping_address = selectedSalesOrder.customer.deliveryAddress || '';
      }
    }
  }

  // 獲取客戶名稱
  getCustomerName(customerId: number): string {
    const customer = this.customers.find(c => c.id === customerId);
    return customer ? customer.customerName : '-';
  }

  // 獲取銷售單號
  getSalesOrderNumber(salesOrderId: number): string {
    const salesOrder = this.salesOrders.find(so => so.id === salesOrderId);
    return salesOrder ? salesOrder.so_number : '-';
  }
}

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { FormsModule } from '@angular/forms';

// 導入台灣郵遞區號數據
import taiwanPostalCodes from '../../assets/data/taiwanPostalCodes.json';

// 導入批次修改dialog組件
import { BatchUpdateDialogComponent, BatchUpdateDialogData, BatchUpdateDialogResult } from './batch-update-dialog.component';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-customer',
  standalone: true,
  imports: [CommonModule, TranslateModule, FormsModule, BatchUpdateDialogComponent],
  templateUrl: './customer.component.html',
  styleUrl: './customer.component.css'
})
export class CustomerComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private router: Router,
    private loadingService: LoadingService,
    private translate: TranslateService
  ) { }
  customers: any[] = [];
  filteredCustomers: any[] = [];
  message: string = '';
  searchTerm: string = '';
  searchCriteria: string = 'all'; // 默認搜尋條件
  countyValue: string = ''; // 縣市搜尋值
  districtValue: string = ''; // 區域搜尋值
  showDistrictDropdown: boolean = false; // 控制是否顯示區域下拉選單

  // 批次修改功能相關變量
  showBatchUpdateSection: boolean = false;
  searchValue: string = '';
  batchUpdateCustomers: any[] = [];
  selectedCustomerIds: Set<number> = new Set();
  isBatchUpdateMode: boolean = false;
  hasBatchSearched: boolean = false; // 追蹤是否已執行批次搜尋

  // 客戶類型選項
  customerTypes: any[] = [];

  // 台灣縣市和區域數據
  counties: string[] = Object.keys(taiwanPostalCodes);
  districts: string[] = [];

  // 批次修改模式下的區域數據（獨立於新增/編輯客戶）
  batchUpdateDistricts: string[] = [];

  // 批次更新對話框相關
  showBatchDialog: boolean = false;
  batchDialogRef: any = null;
  batchDialogData: BatchUpdateDialogData | null = null;

  // 自定義欄位顯示相關
  columnConfig: any[] = [
    { key: 'customerCode', label: 'CUSTOMER_CODE', visible: true, fixed: false },
    { key: 'customerName', label: 'CUSTOMER_NAME', visible: true, fixed: false },
    { key: 'customerType', label: 'CUSTOMER_TYPE', visible: true, fixed: false },
    { key: 'contactPerson', label: 'CONTACT_PERSON', visible: true, fixed: false },
    { key: 'phoneNumber', label: 'PHONE_NUMBER', visible: true, fixed: false },
    { key: 'salesPersonId', label: 'SALES_PERSON_ID', visible: true, fixed: false },
    { key: 'paymentMethod', label: 'PAYMENT_METHOD', visible: true, fixed: false },
    { key: 'creditLimit', label: 'CREDIT_LIMIT', visible: true, fixed: false },
    { key: 'actions', label: 'ACTIONS', visible: true, fixed: true }
  ];
  showColumnConfigPanel: boolean = false;

  ngOnInit(): void {
    // 初始化欄位配置
    this.initColumnConfig();

    // 訂閱BehaviorSubject以獲取數據更新
    this.apiService.customers$.subscribe((custs: any[]) => {
      // 對客戶資料按客戶編號排序
      const sortedCustomers = this.sortCustomersByCode(custs);
      this.customers = sortedCustomers;
      this.filteredCustomers = sortedCustomers;
      // 如果有數據且loading還在顯示，則隱藏loading
      if (custs.length > 0 && this.loadingService.isLoading()) {
        this.loadingService.hideLoading();
      }
    });

    // 只有在BehaviorSubject沒有數據時才顯示loading並發起請求
    const currentCustomers = this.apiService.customersSource.value;
    if (!currentCustomers || currentCustomers.length === 0) {
      this.loadingService.showDataLoading();
      this.apiService.fetchAndBroadcastCustomers().subscribe({
        next: (res: any) => {
          // console.log('Initial customers fetched by CustomerComponent');
          this.loadingService.hideLoading();
        },
        error: (error: any) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to fetch initial customers" + error);
          this.loadingService.hideLoading();
        }
      });
    }

    // 獲取客戶類型數據
    this.apiService.getAllCustomerTypes().subscribe({
      next: (res: any) => {
        this.customerTypes = res;
      },
      error: (error: any) => {
        console.error('Failed to fetch customer types:', error);
        this.showMessage('無法獲取客戶類型數據');
      }
    });
  }

  // Search customers
  onSearch(): void {
    // 如果選擇了"顯示全部"，則顯示所有客戶
    if (this.searchCriteria === 'all') {
      this.loadingService.showDataLoading();
      this.apiService.getAllCustomers().subscribe({
        next: (res: any) => {
          this.filteredCustomers = this.sortCustomersByCode(res);
          this.loadingService.hideLoading();
          this.showMessage(`顯示全部 ${res.length} 筆客戶資料`);
        },
        error: (error: any) => {
          this.showMessage(error?.error?.message || error?.message || "獲取客戶資料時發生錯誤" + error);
          this.loadingService.hideLoading();
        }
      });
      return;
    }

    // 根據搜尋條件使用相應的搜尋值
    let searchValue = this.searchTerm;
    if (this.searchCriteria === 'county' && this.showDistrictDropdown) {
      searchValue = this.districtValue;
    } else if (this.searchCriteria === 'county') {
      searchValue = this.countyValue;
    }

    if (!searchValue.trim()) {
      this.showMessage('請輸入搜尋值');
      return;
    }

    this.loadingService.showDataLoading();

    // 如果顯示了區域下拉選單，表示用戶是在選擇縣市後選擇了區域
    if (this.showDistrictDropdown && this.searchCriteria === 'county') {
      // 如果選擇了"全部區域"或沒有選擇區域，則使用縣市進行搜尋
      if (this.districtValue === 'all' || !this.districtValue) {
        this.apiService.searchCustomersByCounty(this.countyValue).subscribe({
          next: (res: any) => {
            this.filteredCustomers = this.sortCustomersByCode(res);
            this.loadingService.hideLoading();
            this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
          },
          error: (error: any) => {
            this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
            this.loadingService.hideLoading();
          }
        });
      } else {
        // 使用區域進行搜尋
        this.apiService.searchCustomersByDistrict(this.districtValue).subscribe({
          next: (res: any) => {
            this.filteredCustomers = this.sortCustomersByCode(res);
            this.loadingService.hideLoading();
            this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
          },
          error: (error: any) => {
            this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
            this.loadingService.hideLoading();
          }
        });
      }
    } else {
      // 使用原始的搜尋邏輯
      switch (this.searchCriteria) {
        case 'customerName':
          this.apiService.searchCustomers(this.searchTerm).subscribe({
            next: (res: any) => {
              this.filteredCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error: any) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;

        case 'customerCode':
          this.apiService.searchCustomersByCode(this.searchTerm).subscribe({
            next: (res: any) => {
              this.filteredCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error: any) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;

        case 'contactPerson':
          this.apiService.searchCustomersByContactPerson(this.searchTerm).subscribe({
            next: (res: any) => {
              this.filteredCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error: any) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;

        case 'phoneNumber':
          this.apiService.searchCustomersByPhoneNumber(this.searchTerm).subscribe({
            next: (res: any) => {
              this.filteredCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error: any) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;

        case 'customerType':
          if (!this.searchTerm) {
            this.showMessage('請選擇客戶類型');
            this.loadingService.hideLoading();
            return;
          }
          this.apiService.searchCustomersByType(parseInt(this.searchTerm)).subscribe({
            next: (res: any) => {
              this.filteredCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error: any) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;

        case 'county':
          this.apiService.searchCustomersByCounty(this.countyValue).subscribe({
            next: (res: any) => {
              this.filteredCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error: any) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;
      }
    }
  }

  //Navigate to add customer Page
  navigateToAddCustomerPage(): void {
    this.router.navigate([`/add-customer`]);
  }

  //Navigate to edit customer Page
  navigateToEditCustomerPage(customerId: string): void {
    this.router.navigate([`/edit-customer/${customerId}`]);
  }

  //Delete a customer
  handleDeleteCustomer(customerId: string): void {
    if (window.confirm("Are you sure you want to delete this customer?")) {
      this.apiService.deleteCustomer(customerId).subscribe({
        next: (res: any) => {
          this.showMessage("Customer deleted successfully")
          this.apiService.fetchAndBroadcastCustomers().subscribe({
            next: () => { /* console.log('Customers refreshed after delete'); */ },
            error: (err: any) => {
              console.error('Failed to refresh customers after delete:', err);
              this.showMessage('Failed to refresh customer list.');
            }
          }); //reload the customers
        },
        error: (error) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to Delete Customer" + error)
        }
      })
    }
  }

  // Get customer type display text (現在直接返回中文字串)
  getCustomerTypeText(customer: any): string {
    // 如果customer對象有customer_type_obj字段且包含type_name，則返回type_name
    if (customer.customer_type_obj && customer.customer_type_obj.type_name) {
      return customer.customer_type_obj.type_name;
    }
    // 如果customer對象有customerType字段，則直接返回
    if (customer.customerType) {
      return customer.customerType;
    }
    // 默認返回'-'
    return '-';
  }

  // 修改追蹤相關方法
  isRecentlyModified(customer: any): boolean {
    if (!customer.updatedAt) return false;

    const updatedDate = new Date(customer.updatedAt);
    const createdDate = new Date(customer.createdDate);
    const now = new Date();

    // 如果更新時間比建立時間晚，且在最近7天內修改過，則顯示指示器
    const daysDiff = (now.getTime() - updatedDate.getTime()) / (1000 * 3600 * 24);
    const isModified = updatedDate.getTime() > createdDate.getTime();

    return isModified && daysDiff <= 7;
  }

  // 檢查特定欄位是否被修改過
  isFieldModified(customer: any, fieldName: string): boolean {
    // 調試日誌
    if (customer.modified_fields) {
      console.log(`Customer ${customer.id} modified_fields:`, customer.modified_fields);
    }

    // 只有當客戶有 modified_fields 且該欄位在列表中時才返回 true
    if (customer.modified_fields && customer.modified_fields.includes(fieldName)) {
      console.log(`Field ${fieldName} is modified for customer ${customer.id}`);
      return true;
    }

    // 不使用回退機制，只有真正修改過的欄位才顯示小紅點
    return false;
  }

  // 檢查是否應該顯示氣泡（只有當前懸停的欄位才顯示）
  shouldShowHistoryPopup(customer: any, fieldName: string): boolean {
    return this.showFieldHistory &&
      this.currentFieldHistory &&
      this.currentHoveredCustomer &&
      this.currentHoveredCustomer.id === customer.id &&
      this.currentHoveredField === fieldName;
  }

  getModificationTooltip(customer: any): string {
    if (!customer.updatedAt) return '';

    const updatedDate = new Date(customer.updatedAt);
    const formattedDate = updatedDate.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });

    return `最後修改時間：${formattedDate}`;
  }

  // 獲取欄位的修改歷史並顯示在 tooltip 中
  getFieldModificationTooltip(customer: any, fieldKey: string): string {
    // 這個方法會被 HTML 中的 tooltip 調用
    // 我們需要異步獲取數據，所以先返回基本信息
    if (!this.isRecentlyModified(customer)) {
      return '';
    }

    // 觸發異步獲取詳細歷史
    this.loadFieldHistory(customer.id, fieldKey);

    // 先返回基本的修改時間信息
    return this.getModificationTooltip(customer);
  }

  // 異步載入欄位修改歷史
  private fieldHistoryCache: { [key: string]: any } = {};

  // 當前顯示的修改歷史資訊
  currentFieldHistory: any = null;
  showFieldHistory: boolean = false;

  // 當前懸停的客戶和欄位
  currentHoveredCustomer: any = null;
  currentHoveredField: string = '';

  // 滑鼠位置追蹤
  mousePosition = { x: 0, y: 0 };

  loadFieldHistory(customerId: number, fieldName: string): void {
    const cacheKey = `${customerId}_${fieldName}`;

    // 如果已經有緩存，直接顯示
    if (this.fieldHistoryCache[cacheKey]) {
      this.displayFieldHistory(this.fieldHistoryCache[cacheKey], fieldName);
      return;
    }

    this.apiService.getFieldHistory(customerId.toString(), fieldName).subscribe({
      next: (response: any) => {
        this.fieldHistoryCache[cacheKey] = response;
        this.displayFieldHistory(response, fieldName);
      },
      error: (error) => {
        console.warn('Failed to load field history:', error);
        this.hideFieldHistory();
      }
    });
  }

  // 顯示欄位修改歷史
  displayFieldHistory(history: any, fieldName: string): void {
    if (history && history.has_history) {
      this.currentFieldHistory = {
        fieldName: fieldName, // 記錄欄位名稱，用於 HTML 中的條件判斷
        oldValue: history.old_value,
        newValue: history.new_value,
        changedAt: new Date(history.changed_at).toLocaleString('zh-TW', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        })
      };
      this.showFieldHistory = true;
    } else {
      this.hideFieldHistory();
    }
  }

  // 隱藏欄位修改歷史
  hideFieldHistory(): void {
    this.showFieldHistory = false;
    this.currentFieldHistory = null;
    this.currentHoveredCustomer = null;
    this.currentHoveredField = '';
  }

  // 滑鼠懸停事件處理
  onFieldHover(customer: any, fieldKey: string, event: MouseEvent): void {
    // 記錄當前懸停的客戶和欄位
    this.currentHoveredCustomer = customer;
    this.currentHoveredField = fieldKey;
    // 更新滑鼠位置
    this.updateMousePosition(event);
    // 現在只有真正修改過的欄位才會觸發
    this.loadFieldHistory(customer.id, fieldKey);
  }

  // 滑鼠移動事件處理
  onFieldMouseMove(event: MouseEvent): void {
    if (this.showFieldHistory) {
      this.updateMousePosition(event);
    }
  }

  // 更新滑鼠位置 - 智慧邊界檢測
  updateMousePosition(event: MouseEvent): void {
    const offset = 15; // 偏移量，避免遮擋滑鼠
    let x = event.clientX + offset;
    let y = event.clientY + offset;

    // 邊界檢測
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const popupWidth = 350; // 氣泡寬度
    const popupHeight = 120; // 氣泡高度

    // 右邊界檢測
    if (x + popupWidth > windowWidth) {
      x = event.clientX - popupWidth - offset;
    }

    // 下邊界檢測
    if (y + popupHeight > windowHeight) {
      y = event.clientY - popupHeight - offset;
    }

    // 確保不會超出左上邊界
    x = Math.max(10, x);
    y = Math.max(10, y);

    this.mousePosition = { x, y };
  }

  // 滑鼠離開事件處理
  private hideTimeout: any;

  onFieldLeave(): void {
    // 延遲隱藏，避免滑鼠快速移動時閃爍
    this.hideTimeout = setTimeout(() => {
      this.hideFieldHistory();
    }, 200);
  }

  // 獲取欄位的詳細修改信息
  getFieldHistoryTooltip(customer: any, fieldKey: string): string {
    const cacheKey = `${customer.id}_${fieldKey}`;
    const history = this.fieldHistoryCache[cacheKey];

    if (!history || !history.has_history) {
      return this.getModificationTooltip(customer);
    }

    const changedDate = new Date(history.changed_at);
    const formattedDate = changedDate.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });

    return `修改前：${history.old_value || '(空值)'}\n修改後：${history.new_value || '(空值)'}\n修改時間：${formattedDate}`;
  }

  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }

  // 切換批次修改模式
  toggleBatchUpdateMode(): void {
    this.showBatchUpdateSection = !this.showBatchUpdateSection;
    if (this.showBatchUpdateSection) {
      // 切換到批次修改模式時，設置搜尋條件為'customerName'
      this.searchCriteria = 'customerName';
    } else {
      this.resetBatchUpdate();
    }
  }

  // 重置批次修改功能
  resetBatchUpdate(): void {
    this.searchCriteria = 'customerName';
    this.searchValue = '';
    this.countyValue = '';
    this.districtValue = '';
    this.batchUpdateCustomers = [];
    this.selectedCustomerIds.clear();
    this.isBatchUpdateMode = false;
    this.districts = [];
    this.batchUpdateDistricts = [];
    this.showDistrictDropdown = false;
    this.hasBatchSearched = false; // 重置批次搜尋狀態
  }

  // 當在批次修改模式下選擇"區域"搜尋條件時，預先加載所有縣市的區域數據
  onBatchUpdateDistrictSearch(): void {
    // 這個方法現在不再需要，因為區域下拉選單是在選擇縣市後直接顯示的
    // 保留這個方法以防未來需要
  }

  // 當選擇縣市時更新區域列表
  onCountyChange(): void {
    if (this.countyValue) {
      const typedTaiwanPostalCodes = taiwanPostalCodes as any;
      if (typedTaiwanPostalCodes[this.countyValue]) {
        // 在批次修改模式下更新batchUpdateDistricts，否則更新districts
        if (this.showBatchUpdateSection) {
          this.batchUpdateDistricts = Object.keys(typedTaiwanPostalCodes[this.countyValue]);
          // 顯示區域下拉選單
          this.showDistrictDropdown = true;
        } else {
          this.districts = Object.keys(typedTaiwanPostalCodes[this.countyValue]);
        }
      } else {
        if (this.showBatchUpdateSection) {
          this.batchUpdateDistricts = [];
          // 隱藏區域下拉選單
          this.showDistrictDropdown = false;
        } else {
          this.districts = [];
        }
      }
    } else {
      if (this.showBatchUpdateSection) {
        this.batchUpdateDistricts = [];
        // 隱藏區域下拉選單
        this.showDistrictDropdown = false;
      } else {
        this.districts = [];
      }
    }
  }

  // 執行搜尋以進行批次修改
  searchForBatchUpdate(): void {
    // 根據搜尋條件使用相應的搜尋值
    let searchValue = this.searchValue;
    if (this.searchCriteria === 'county' && this.showDistrictDropdown) {
      searchValue = this.districtValue;
    } else if (this.searchCriteria === 'county') {
      searchValue = this.countyValue;
    }

    if (!searchValue.trim()) {
      this.showMessage('請輸入搜尋值');
      return;
    }

    this.loadingService.showDataLoading();
    this.hasBatchSearched = true; // 設置已執行批次搜尋

    // 如果顯示了區域下拉選單，表示用戶是在選擇縣市後選擇了區域
    if (this.showDistrictDropdown && this.searchCriteria === 'county') {
      // 如果選擇了"全部區域"或沒有選擇區域，則使用縣市進行搜尋
      if (this.districtValue === 'all' || !this.districtValue) {
        this.apiService.searchCustomersByCounty(this.countyValue).subscribe({
          next: (res: any) => {
            this.batchUpdateCustomers = this.sortCustomersByCode(res);
            this.loadingService.hideLoading();
            this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
          },
          error: (error) => {
            this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
            this.loadingService.hideLoading();
          }
        });
      } else {
        // 使用區域進行搜尋
        this.apiService.searchCustomersByDistrict(this.districtValue).subscribe({
          next: (res: any) => {
            this.batchUpdateCustomers = this.sortCustomersByCode(res);
            this.loadingService.hideLoading();
            this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
          },
          error: (error) => {
            this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
            this.loadingService.hideLoading();
          }
        });
      }
    } else {
      // 使用原始的搜尋邏輯
      switch (this.searchCriteria) {
        case 'customerName':
          this.apiService.searchCustomers(this.searchValue).subscribe({
            next: (res: any) => {
              this.batchUpdateCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;

        case 'customerType':
          if (!this.searchValue) {
            this.showMessage('請選擇客戶類型');
            this.loadingService.hideLoading();
            return;
          }
          this.apiService.searchCustomersByType(parseInt(this.searchValue)).subscribe({
            next: (res: any) => {
              this.batchUpdateCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;

        case 'county':
          this.apiService.searchCustomersByCounty(this.countyValue).subscribe({
            next: (res: any) => {
              this.batchUpdateCustomers = this.sortCustomersByCode(res);
              this.loadingService.hideLoading();
              this.showMessage(`找到 ${res.length} 筆符合的客戶資料`);
            },
            error: (error) => {
              this.showMessage(error?.error?.message || error?.message || "搜尋客戶時發生錯誤" + error);
              this.loadingService.hideLoading();
            }
          });
          break;
      }
    }
  }

  // 切換批次修改模式（選擇要修改的客戶）
  toggleBatchUpdateSelectionMode(): void {
    this.isBatchUpdateMode = !this.isBatchUpdateMode;
    if (!this.isBatchUpdateMode) {
      this.selectedCustomerIds.clear();
    }
  }

  // 選擇/取消選擇單個客戶
  toggleCustomerSelection(customerId: number): void {
    if (this.selectedCustomerIds.has(customerId)) {
      this.selectedCustomerIds.delete(customerId);
    } else {
      this.selectedCustomerIds.add(customerId);
    }
  }

  // 全選/取消全選
  toggleSelectAll(): void {
    if (this.selectedCustomerIds.size === this.batchUpdateCustomers.length) {
      // 如果已經全選，則取消全選
      this.selectedCustomerIds.clear();
    } else {
      // 否則全選
      this.batchUpdateCustomers.forEach(customer => {
        this.selectedCustomerIds.add(customer.id);
      });
    }
  }



  // 獲取欄位標籤
  getFieldLabel(field: string): string {
    const labels: { [key: string]: string } = {
      'contactPerson': '聯絡人',
      'phoneNumber': '電話號碼',
      'faxNumber': '傳真號碼',
      'businessHours': '營業時間',
      'paymentMethod': '收款方式',
      'paymentCategory': '收款類別',
      'creditLimit': '信用額度'
    };
    return labels.hasOwnProperty(field) ? labels[field] : field;
  }

  // 初始化欄位配置
  initColumnConfig(): void {
    const savedConfig = localStorage.getItem('customerColumnConfig');
    if (savedConfig) {
      try {
        const parsedConfig = JSON.parse(savedConfig);
        // 合併保存的配置與默認配置，以防有新的欄位
        this.columnConfig = this.columnConfig.map(defaultCol => {
          const savedCol = parsedConfig.find((col: any) => col.key === defaultCol.key);
          return savedCol ? { ...defaultCol, ...savedCol } : defaultCol;
        });
      } catch (e) {
        console.error('Failed to parse saved column config', e);
      }
    }
  }

  // 切換設置面板顯示
  toggleColumnConfigPanel(): void {
    this.showColumnConfigPanel = !this.showColumnConfigPanel;
  }

  // 切換欄位可見性
  toggleColumnVisibility(key: string): void {
    const column = this.columnConfig.find(col => col.key === key);
    if (column && !column.fixed) {
      column.visible = !column.visible;
      this.saveColumnConfig();
    }
  }

  // 保存欄位配置到localStorage
  saveColumnConfig(): void {
    localStorage.setItem('customerColumnConfig', JSON.stringify(this.columnConfig));
  }

  // 重置為默認配置
  resetToDefaultConfig(): void {
    this.columnConfig = [
      { key: 'customerCode', label: 'CUSTOMER_CODE', visible: true, fixed: false },
      { key: 'customerName', label: 'CUSTOMER_NAME', visible: true, fixed: false },
      { key: 'customerType', label: 'CUSTOMER_TYPE', visible: true, fixed: false },
      { key: 'contactPerson', label: 'CONTACT_PERSON', visible: true, fixed: false },
      { key: 'phoneNumber', label: 'PHONE_NUMBER', visible: true, fixed: false },
      { key: 'salesPersonId', label: 'SALES_PERSON_ID', visible: true, fixed: false },
      { key: 'paymentMethod', label: 'PAYMENT_METHOD', visible: true, fixed: false },
      { key: 'creditLimit', label: 'CREDIT_LIMIT', visible: true, fixed: false },
      { key: 'actions', label: 'ACTIONS', visible: true, fixed: true }
    ];
    this.saveColumnConfig();
  }

  // 獲取可見欄位
  getVisibleColumns(): any[] {
    return this.columnConfig.filter(col => col.visible);
  }

  // 獲取客戶屬性值
  getCustomerValue(customer: any, columnKey: string): string {
    switch (columnKey) {
      case 'customerType':
        return this.getCustomerTypeText(customer);
      case 'creditLimit':
        return customer[columnKey] ? customer[columnKey].toLocaleString() : '-';
      default:
        return customer[columnKey] || '-';
    }
  }

  // 依照客戶編號排序函數 - 英文字A開始數字遞增
  sortCustomersByCode(customers: any[]): any[] {
    return customers.sort((a, b) => {
      const codeA = a.customerCode || '';
      const codeB = b.customerCode || '';

      // 使用自然排序方式，讓 A1, A2, ..., A10, A11 正確排序
      return codeA.localeCompare(codeB, undefined, {
        numeric: true,
        sensitivity: 'base'
      });
    });
  }

  // 執行批次更新
  executeBatchUpdate(): void {
    console.log('executeBatchUpdate called');
    if (this.selectedCustomerIds.size === 0) {
      this.showMessage('請至少選擇一個客戶');
      return;
    }

    console.log('Selected customer IDs:', Array.from(this.selectedCustomerIds));

    // 準備對話框數據
    this.batchDialogData = {
      customerIds: Array.from(this.selectedCustomerIds),
      customerCount: this.selectedCustomerIds.size
    };

    // 創建對話框引用
    this.batchDialogRef = {
      close: (result?: BatchUpdateDialogResult) => {
        console.log('Dialog closed with result:', result);
        this.showBatchDialog = false;
        this.batchDialogRef = null;
        this.batchDialogData = null;

        // 如果有結果，執行批次更新
        if (result) {
          this.performBatchUpdate(result.customerIds, result.updateData);
        }
      }
    };

    // 顯示對話框
    this.showBatchDialog = true;
    console.log('Dialog should be visible now, showBatchDialog:', this.showBatchDialog);
  }

  // 執行實際的批次更新
  private performBatchUpdate(customerIds: number[], updateData: any): void {
    this.loadingService.showSaving();
    this.apiService.batchUpdateCustomers(customerIds, updateData).subscribe({
      next: (res: any) => {
        this.loadingService.hideLoading();
        this.showMessage(`成功更新 ${res.length} 筆客戶資料`);

        // 重新載入客戶列表
        this.apiService.fetchAndBroadcastCustomers().subscribe({
          next: () => {
            // 重置批次修改功能
            this.resetBatchUpdate();
            this.showBatchUpdateSection = false;
          },
          error: (error: any) => {
            console.error('Failed to refresh customers after batch update:', error);
            this.showMessage('Failed to refresh customer list.');
          }
        });
      },
      error: (error: any) => {
        this.loadingService.hideLoading();
        this.showMessage(error?.error?.message || error?.message || "批次更新失敗" + error);
      }
    });
  }
}

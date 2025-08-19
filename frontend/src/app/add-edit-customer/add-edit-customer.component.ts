import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { TranslateModule } from '@ngx-translate/core';
import { BusinessHoursDialogComponent } from '../business-hours-dialog/business-hours-dialog.component';

// 導入台灣郵遞區號數據
import taiwanPostalCodes from '../../assets/data/taiwanPostalCodes.json';

@Component({
  selector: 'app-add-edit-customer',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink, TranslateModule, BusinessHoursDialogComponent],
  templateUrl: './add-edit-customer.component.html',
  styleUrl: './add-edit-customer.component.css'
})
export class AddEditCustomerComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private router: Router,
    private loadingService: LoadingService
  ) {}
  message: string = '';
  isEditing: boolean = false;
  customerId: string | null = null;

  // Customer type options (從API獲取)
  customerTypes: any[] = [];

  // Payment method options (收款方式)
  paymentMethods = [
    { value: 'MONTHLY', label: 'MONTHLY_SETTLEMENT' },
    { value: 'IMMEDIATE_PAYMENT', label: 'IMMEDIATE_PAYMENT' }
  ];

  // Payment category options (收款類別，使用中文字串值)
  paymentCategories = [
    { value: '支票', label: 'CHECK' },
    { value: '現金', label: 'CASH' },
    { value: '匯款', label: 'BANK_TRANSFER' }
  ];

  // 台灣縣市列表
  counties: string[] = Object.keys(taiwanPostalCodes);

  // 區域列表（根據選擇的縣市動態更新）
  districts: string[] = [];

  // 郵遞區號（根據選擇的區域自動帶入）
  postalCode: string = '';

  dayNames = ['週一','週二','週三','週四','週五','週六','週日'];
  showBusinessHoursDialog = false;

  businessHoursModel: any = {
    weekly: [
      { weekday: 0, is_open: false, ranges: [] },
      { weekday: 1, is_open: false, ranges: [] },
      { weekday: 2, is_open: false, ranges: [] },
      { weekday: 3, is_open: false, ranges: [] },
      { weekday: 4, is_open: false, ranges: [] },
      { weekday: 5, is_open: false, ranges: [] },
      { weekday: 6, is_open: false, ranges: [] },
    ],
    exceptions: []
  };

  formData: any = {
    customerType: '',
    salesPersonId: '',
    salesPersonName: '',
    bankAccount: '',  // 新增銀行帳戶字段
    notes: '',  // 新增備註字段
    customerCode: '',
    customerName: '',
    contactPerson: '',
    invoiceTitle: '',
    taxId: '',
    phoneNumber: '',
    faxNumber: '',
    county: '',  // 新增縣市字段
    district: '',  // 新增區域字段
    deliveryAddress: '',
    businessHours: '',
    paymentMethod: '',
    paymentCategory: '',
    creditLimit: 0,
    monthlyPaymentDays: 30  // 用於前端顯示，不會直接傳送到後端
  };

  ngOnInit(): void {
    // 若為編輯模式，載入營業時間

    this.customerId = this.router.url.split('/')[2]; //extracting customer id from url
    if (this.customerId) {
      this.isEditing = true;
      this.fetchCustomer();
    }
    
    // 從API獲取客戶類型
    this.fetchCustomerTypes();
  }
  
  fetchCustomerTypes(): void {
    this.apiService.getAllCustomerTypes().subscribe({
      next: (res: any) => {
        // 將獲取到的客戶類型轉換為下拉選單所需的格式
        this.customerTypes = res.map((type: any) => ({
          value: type.id,
          label: type.type_name
        }));
      },
      error: (error) => {
        console.error('Error fetching customer types:', error);
        // 如果獲取失敗，使用硬編碼的默認值
        this.customerTypes = [
          { value: 1, label: '區域連鎖' },
          { value: 2, label: '零售' },
          { value: 3, label: '犬貓舍' },
          { value: 4, label: '一般店家' },
          { value: 5, label: '大型連鎖' }
        ];
      }
    });
  }

  fetchCustomer(): void {
    this.apiService.getCustomerById(this.customerId!).subscribe({
      next: (res: any) => {
        // 解析 paymentMethod，如果是月結格式則提取天數
        let paymentMethod = res.paymentMethod || '';
        let monthlyPaymentDays = 30;

        if (paymentMethod && paymentMethod.startsWith('月結') && paymentMethod.endsWith('天')) {
          // 提取天數，例如 "月結30天" -> 30
          const match = paymentMethod.match(/月結(\d+)天/);
          if (match) {
            monthlyPaymentDays = parseInt(match[1]);
            paymentMethod = 'MONTHLY'; // 設定為月結選項
          }
        }

        // 同步營業時間（若後端已有資料）
        this.loadBusinessHours();

        this.formData = {
          customerType: res.customer_type_id || res.customer_type_obj?.id || '',
          salesPersonId: res.salesPersonId || '',
          salesPersonName: res.salesPersonName || '',
          bankAccount: res.bankAccount || '',  // 添加銀行帳戶字段
          notes: res.notes || '',  // 添加備註字段
          customerCode: res.customerCode,
          customerName: res.customerName,
          contactPerson: res.contactPerson || '',
          invoiceTitle: res.invoiceTitle || '',
          taxId: res.taxId || '',
          phoneNumber: res.phoneNumber || '',
          faxNumber: res.faxNumber || '',
          deliveryAddress: res.deliveryAddress || '',
          businessHours: res.businessHours || '',
          paymentMethod: paymentMethod,
          paymentCategory: res.paymentCategory || '',
          creditLimit: res.creditLimit || 0,
          monthlyPaymentDays: monthlyPaymentDays
        };

        // 解析送貨地址，提取縣市、區域和郵遞區號
        const addressInfo = this.parseDeliveryAddress(res.deliveryAddress || '');
        this.formData.county = addressInfo.county;
        this.formData.district = addressInfo.district;
        this.postalCode = addressInfo.postalCode;

        // 更新區域列表
        if (this.formData.county) {
          const typedTaiwanPostalCodes = taiwanPostalCodes as any;
          if (typedTaiwanPostalCodes[this.formData.county]) {
            this.districts = Object.keys(typedTaiwanPostalCodes[this.formData.county]);
          }
        }
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            'Unable to get customer by id' + error
        );
      },
    });
  }

  loadBusinessHours(): void {
    if (!this.customerId) return;
    this.apiService.getCustomerBusinessHours(this.customerId).subscribe({
      next: (res: any) => {
        // 資料格式：{ weekly: [{weekday,is_open,ranges:[{start,end}]}...], exceptions: [...] }
        // 確保例外日 ranges 至少有一個元素供 UI 綁定
        const ex = (res.exceptions || []).map((e: any) => ({
          ...e,
          ranges: e.is_open ? (e.ranges && e.ranges.length ? e.ranges : [{ start: '09:00', end: '18:00' }]) : []
        }));
        this.businessHoursModel = {
          weekly: res.weekly || this.businessHoursModel.weekly,
          exceptions: ex
        };
      },
      error: (err) => {
        console.warn('No business hours found or failed to load', err);
      }
    });
  }

  // 營業時間對話框相關方法
  openBusinessHoursDialog(): void {
    this.showBusinessHoursDialog = true;
  }

  onBusinessHoursSave(businessHoursData: any): void {
    this.businessHoursModel = businessHoursData;
    this.showBusinessHoursDialog = false;
  }

  onBusinessHoursCancel(): void {
    this.showBusinessHoursDialog = false;
  }

  hasBusinessHours(): boolean {
    return this.businessHoursModel.weekly.some((day: any) => day.is_open) || 
           (this.businessHoursModel.exceptions && this.businessHoursModel.exceptions.length > 0);
  }

  private buildBusinessHoursPayload() {
    const weekly = (this.businessHoursModel.weekly || []).map((d: any) => ({
      weekday: d.weekday,
      is_open: !!d.is_open,
      ranges: d.is_open ? (d.ranges || []).filter((r: any) => r.start && r.end).map((r: any) => ({ start: r.start, end: r.end })) : []
    }));

    const exceptions = (this.businessHoursModel.exceptions || []).map((e: any) => ({
      date: e.date,
      is_open: !!e.is_open,
      ranges: e.is_open && e.ranges && e.ranges.length && e.ranges[0].start && e.ranges[0].end ? [{ start: e.ranges[0].start, end: e.ranges[0].end }] : null,
      reason: e.reason || null
    }));

    return { weekly, exceptions };
  }

  private saveBusinessHoursAndNavigate(customerId: string | number): void {
    const payload = this.buildBusinessHoursPayload();
    this.apiService.updateCustomerBusinessHours(String(customerId), payload).subscribe({
      next: () => {
        this.loadingService.hideLoading();
        this.router.navigate(['/customer']);
      },
      error: (err) => {
        console.warn('Failed to save business hours:', err);
        this.loadingService.hideLoading();
        this.router.navigate(['/customer']);
      }
    });
  }

  // HANDLE FORM SUBMISSION
  handleSubmit() {
    if (!this.formData.customerType || !this.formData.customerCode || !this.formData.customerName) {
      this.showMessage('Customer type, customer code, and customer name are required');
      return;
    }

    // 處理 paymentMethod，如果是月結則組合天數
    let paymentMethodValue = this.formData.paymentMethod;
    if (paymentMethodValue === 'MONTHLY') {
      const days = parseInt(this.formData.monthlyPaymentDays) || 30;
      paymentMethodValue = `月結${days}天`;
    }

    //prepare data for submission
    const customerData = {
      customer_type_id: this.formData.customerType,
      salesPersonId: this.formData.salesPersonId || null,
      salesPersonName: this.formData.salesPersonName || null,
      bankAccount: this.formData.bankAccount || null,  // 添加銀行帳戶字段
      notes: this.formData.notes || null,  // 添加備註字段
      customerCode: this.formData.customerCode,
      customerName: this.formData.customerName,
      contactPerson: this.formData.contactPerson || null,
      invoiceTitle: this.formData.invoiceTitle || null,
      taxId: this.formData.taxId || null,
      phoneNumber: this.formData.phoneNumber || null,
      faxNumber: this.formData.faxNumber || null,
      deliveryAddress: this.formData.deliveryAddress || null,
      businessHours: this.formData.businessHours || null,
      paymentMethod: paymentMethodValue || null,
      paymentCategory: this.formData.paymentCategory || null,
      creditLimit: parseFloat(this.formData.creditLimit) || 0
    };

    if (this.isEditing) {
      this.loadingService.showUpdating();
      this.apiService.updateCustomer(this.customerId!, customerData).subscribe({
        next: (res: any) => {
          // 更新客戶成功後，保存營業時間
          this.saveBusinessHoursAndNavigate(this.customerId!);
        },
        error: (error) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to edit customer" + error)
          this.loadingService.hideLoading();
        }
      })
    } else {
      this.loadingService.showSaving();
      this.apiService.addCustomer(customerData).subscribe({
        next: (res: any) => {
          // 新增客戶成功後，保存營業時間
          this.saveBusinessHoursAndNavigate(res.id);
        },
        error: (error) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to add customer" + error)
          this.loadingService.hideLoading();
        }
      })
    }
  }

  // 當客戶類型改變時調用
  onCustomerTypeChange(): void {
    // 如果正在編輯客戶，則不自動生成客戶編號
    if (this.isEditing) {
      return;
    }
    
    // 如果沒有選擇客戶類型，則清空客戶編號
    if (!this.formData.customerType) {
      this.formData.customerCode = '';
      return;
    }
    
    // 調用API獲取下一個客戶編號
    console.log('Fetching next customer code for customer type ID:', this.formData.customerType);
    this.apiService.getNextCustomerCode(this.formData.customerType).subscribe({
      next: (res: any) => {
        console.log('Received next customer code:', res);
        this.formData.customerCode = res.next_code;
      },
      error: (error) => {
        console.error('Error fetching next customer code:', error);
        this.formData.customerCode = '';
      }
    });
  }

  // 當業務員編號輸入框失去焦點時調用
  onSalesPersonIdBlur(): void {
    // 檢查業務員編號是否已填寫
    if (this.formData.salesPersonId) {
      // 調用API獲取業務員信息
      this.apiService.getUserById(parseInt(this.formData.salesPersonId)).subscribe({
        next: (res: any) => {
          // 將獲取到的業務員名稱填入業務員名稱輸入框
          this.formData.salesPersonName = res.name;
        },
        error: (error) => {
          console.error('Error fetching sales person name:', error);
          // 如果獲取失敗，清空業務員名稱
          this.formData.salesPersonName = '';
        }
      });
    } else {
      // 如果業務員編號為空，清空業務員名稱
      this.formData.salesPersonName = '';
    }
  }

  // 當選擇縣市時調用
  onCountyChange(): void {
    // 清空區域和郵遞區號
    this.formData.district = '';
    this.postalCode = '';
    this.districts = [];
    
    // 如果選擇了縣市，更新區域列表
    if (this.formData.county) {
      const county = this.formData.county as string;
      const typedTaiwanPostalCodes = taiwanPostalCodes as any;
      if (typedTaiwanPostalCodes[county]) {
        this.districts = Object.keys(typedTaiwanPostalCodes[county]);
      }
    }
  }

  // 當選擇區域時調用
  onDistrictChange(): void {
    // 如果選擇了區域，自動帶入郵遞區號
    if (this.formData.district && this.formData.county) {
      const county = this.formData.county as string;
      const district = this.formData.district as string;
      const typedTaiwanPostalCodes = taiwanPostalCodes as any;
      if (typedTaiwanPostalCodes[county] && typedTaiwanPostalCodes[county][district]) {
        this.postalCode = typedTaiwanPostalCodes[county][district];
      } else {
        this.postalCode = '';
      }
    } else {
      this.postalCode = '';
    }
  }

  // 當點擊送貨地址輸入框時調用
  onDeliveryAddressFocus(): void {
    // 如果縣市、區域和郵遞區號都已選擇，則將它們填入送貨地址欄位
    if (this.formData.county && this.formData.district && this.postalCode) {
      // 檢查送貨地址是否已包含縣市、區域和郵遞區號
      const addressPattern = new RegExp(`${this.postalCode}\\s*${this.formData.county}\\s*${this.formData.district}`);
      if (!addressPattern.test(this.formData.deliveryAddress)) {
        // 如果送貨地址不包含縣市、區域和郵遞區號，則添加它們
        this.formData.deliveryAddress = `${this.postalCode}${this.formData.county}${this.formData.district} ${this.formData.deliveryAddress || ''}`.trim();
      }
    }
  }

  // 當發票抬頭輸入框獲得焦點時調用
  onInvoiceTitleFocus(): void {
    // 如果發票抬頭為空，則自動填入客戶名稱加連字符
    if (!this.formData.invoiceTitle && this.formData.customerName) {
      this.formData.invoiceTitle = this.formData.customerName;
    }
  }

  // 解析送貨地址，提取縣市、區域和郵遞區號
  parseDeliveryAddress(address: string): { county: string; district: string; postalCode: string } {
    // 創建一個對象來存儲縣市、區域和郵遞區號
    const result = { county: '', district: '', postalCode: '' };
    
    // 如果地址為空，直接返回空結果
    if (!address) {
      return result;
    }
    
    // 遍歷所有縣市
    for (const county of this.counties) {
      // 檢查地址是否包含縣市名稱
      if (address.includes(county)) {
        result.county = county;
        
        // 獲取該縣市的所有區域
        const typedTaiwanPostalCodes = taiwanPostalCodes as any;
        const districts = Object.keys(typedTaiwanPostalCodes[county]);
        
        // 遍歷所有區域
        for (const district of districts) {
          // 檢查地址是否包含區域名稱
          if (address.includes(district)) {
            result.district = district;
            
            // 獲取該區域的郵遞區號
            result.postalCode = typedTaiwanPostalCodes[county][district];
            
            // 找到匹配的縣市、區域和郵遞區號後，跳出循環
            break;
          }
        }
        
        // 找到匹配的縣市後，跳出循環
        break;
      }
    }
    
    return result;
  }

  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}

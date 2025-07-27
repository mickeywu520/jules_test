import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-add-edit-customer',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink, TranslateModule],
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

  formData: any = {
    customerType: '',
    salesPersonId: '',
    salesPersonName: '',
    customerCode: '',
    customerName: '',
    contactPerson: '',
    invoiceTitle: '',
    taxId: '',
    phoneNumber: '',
    faxNumber: '',
    deliveryAddress: '',
    businessHours: '',
    paymentMethod: '',
    paymentCategory: '',
    creditLimit: 0,
    monthlyPaymentDays: 30  // 用於前端顯示，不會直接傳送到後端
  };

  ngOnInit(): void {
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

        this.formData = {
          customerType: res.customer_type_id || res.customer_type_obj?.id || '',
          salesPersonId: res.salesPersonId || '',
          salesPersonName: res.salesPersonName || '',
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
          this.showMessage("Customer updated successfully");
          this.loadingService.hideLoading();
          this.router.navigate(['/customer'])
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
          this.showMessage("Customer added successfully");
          this.loadingService.hideLoading();
          this.router.navigate(['/customer'])
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

  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../service/api.service';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-add-edit-customer',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink, TranslateModule],
  templateUrl: './add-edit-customer.component.html',
  styleUrl: './add-edit-customer.component.css'
})
export class AddEditCustomerComponent implements OnInit {
  constructor(private apiService: ApiService, private router: Router) {}
  message: string = '';
  isEditing: boolean = false;
  customerId: string | null = null;

  // Customer type options (使用中文字串值)
  customerTypes = [
    { value: '區域連鎖', label: 'REGIONAL_CHAIN' },
    { value: '零售', label: 'RETAIL' },
    { value: '犬貓舍', label: 'PET_KENNEL' },
    { value: '一般店家', label: 'GENERAL_STORE' },
    { value: '大型連鎖', label: 'LARGE_CHAIN' }
  ];

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
    customerType: '零售',
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
          customerType: res.customerType,
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
      customerType: this.formData.customerType,
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
      this.apiService.updateCustomer(this.customerId!, customerData).subscribe({
        next: (res: any) => {
          this.showMessage("Customer updated successfully");
          this.router.navigate(['/customer'])
        },
        error: (error) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to edit customer" + error)
        }
      })
    } else {
      this.apiService.addCustomer(customerData).subscribe({
        next: (res: any) => {
          this.showMessage("Customer added successfully");
          this.router.navigate(['/customer'])
        },
        error: (error) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to add customer" + error)
        }
      })
    }
  }

  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}
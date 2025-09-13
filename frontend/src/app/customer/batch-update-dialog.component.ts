import { Component, OnInit, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { BusinessHoursDialogComponent } from '../business-hours-dialog/business-hours-dialog.component';

export interface BatchUpdateDialogData {
  customerIds: number[];
  customerCount: number;
}

export interface BatchUpdateDialogResult {
  customerIds: number[];
  updateData: any;
}

@Component({
  selector: 'app-batch-update-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule, BusinessHoursDialogComponent],
  template: `
    <div class="dialog-overlay" (click)="onCancel()">
      <div class="dialog-container" (click)="$event.stopPropagation()">
        <div class="dialog-header">
          <h2>{{ 'BATCH_UPDATE_CUSTOMERS' | translate }}</h2>
        </div>
        <div class="dialog-content">
          <p>{{ 'BATCH_UPDATE_CONFIRM_MESSAGE' | translate: { count: data?.customerCount || 0 } }}</p>
          
          <div class="error-message" *ngIf="errorMessage">
            {{ errorMessage }}
          </div>
          
          <div class="field-selection">
            <h3>{{ 'SELECT_FIELDS_TO_UPDATE' | translate }}</h3>
            <div class="checkbox-group">
              <label *ngFor="let field of updatableFields" class="checkbox-label">
                <input 
                  type="checkbox" 
                  [(ngModel)]="field.selected"
                  (change)="onFieldSelectionChange()">
                {{ field.label | translate }}
              </label>
            </div>
          </div>

          <div class="field-inputs" *ngIf="selectedFields.length > 0">
            <h3>{{ 'ENTER_NEW_VALUES' | translate }}</h3>
            <div class="form-group" *ngFor="let field of selectedFields">
              <label>{{ field.label | translate }}:</label>
              
              <!-- Text input for text fields -->
              <input 
                *ngIf="field.type === 'text'"
                type="text" 
                [(ngModel)]="field.newValue"
                (input)="onInputChange()"
                [class]="'form-control' + (isFieldEmpty(field) && errorMessage ? ' error-input' : '')"
                [placeholder]="'請輸入' + (field.label | translate)">
              
              <!-- Number input for credit limit -->
              <input 
                *ngIf="field.type === 'number'"
                type="number" 
                [(ngModel)]="field.newValue"
                (input)="onInputChange()"
                [class]="'form-control' + (isFieldEmpty(field) && errorMessage ? ' error-input' : '')"
                [placeholder]="'請輸入' + (field.label | translate)"
                min="0"
                step="10000">
              
              <!-- Select dropdown for payment method -->
              <select 
                *ngIf="field.type === 'select' && field.key === 'paymentMethod'"
                [(ngModel)]="field.newValue"
                (change)="onInputChange()"
                [class]="'form-control' + (isFieldEmpty(field) && errorMessage ? ' error-input' : '')">
                <option value="">{{ 'SELECT_PAYMENT_METHOD' | translate }}</option>
                <option *ngFor="let method of paymentMethods" [value]="method.value">
                  {{ method.label | translate }}
                </option>
              </select>
              
              <!-- Select dropdown for payment category -->
              <select 
                *ngIf="field.type === 'select' && field.key === 'paymentCategory'"
                [(ngModel)]="field.newValue"
                (change)="onInputChange()"
                [class]="'form-control' + (isFieldEmpty(field) && errorMessage ? ' error-input' : '')">
                <option value="">{{ 'SELECT_PAYMENT_CATEGORY' | translate }}</option>
                <option *ngFor="let category of paymentCategories" [value]="category.value">
                  {{ category.label | translate }}
                </option>
              </select>
              
              <!-- Business Hours special handling -->
              <div *ngIf="field.type === 'business-hours'" class="business-hours-section">
                <div class="business-hours-container">
                  <button type="button" class="business-hours-btn" (click)="openBusinessHoursDialog()">
                    <span class="btn-icon">🕒</span>
                    {{ 'SET_BUSINESS_HOURS' | translate }}
                  </button>
                  
                  <div class="business-hours-summary" *ngIf="hasBusinessHours()">
                    <div class="summary-title">{{ 'CURRENT_BUSINESS_HOURS' | translate }}:</div>
                    <div class="summary-content">
                      <div class="day-summary" *ngFor="let day of getBusinessHoursSummary()" 
                           [class.closed]="day.hours === ('CLOSED' | translate)">
                        <span class="day-name">{{ day.name }}:</span>
                        <span class="day-hours">{{ day.hours }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="dialog-actions">
          <button class="btn btn-secondary" (click)="onCancel()">{{ 'CANCEL' | translate }}</button>
          <button 
            class="btn btn-primary" 
            [disabled]="selectedFields.length === 0"
            (click)="onConfirm()">
            {{ 'CONFIRM' | translate }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Business Hours Dialog -->
    <app-business-hours-dialog 
      [isOpen]="showBusinessHoursDialog" 
      [businessHoursData]="businessHoursModel"
      (onSave)="onBusinessHoursSave($event)" 
      (onCancel)="onBusinessHoursCancel()">
    </app-business-hours-dialog>
  `,
  styles: [`
    .dialog-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }

    .dialog-container {
      background: white;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      max-width: 500px;
      width: 90%;
      max-height: 90vh;
      overflow-y: auto;
    }

    .dialog-header {
      padding: 20px 20px 0 20px;
    }

    .dialog-header h2 {
      margin: 0;
      font-size: 1.5rem;
    }

    .dialog-content {
      padding: 20px;
    }

    .field-selection {
      margin-bottom: 20px;
    }
    
    .checkbox-group {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }
    
    .field-inputs {
      margin-top: 20px;
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: bold;
    }
    
    .form-control {
      width: 100%;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-sizing: border-box;
      font-size: 14px;
    }
    
    .form-control:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
    }
    
    select.form-control {
      background-color: white;
      cursor: pointer;
    }
    
    input[type="number"].form-control {
      -moz-appearance: textfield;
    }
    
    input[type="number"].form-control::-webkit-outer-spin-button,
    input[type="number"].form-control::-webkit-inner-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }
    
    .dialog-actions {
      padding: 0 20px 20px 20px;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
    
    .btn {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    }
    
    .btn-secondary {
      background-color: #6c757d;
      color: white;
    }
    
    .btn-primary {
      background-color: #007bff;
      color: white;
    }
    
    .btn:disabled {
      background-color: #ccc;
      cursor: not-allowed;
    }
    
    .error-message {
      color: #dc3545;
      background-color: #f8d7da;
      border: 1px solid #f5c6cb;
      padding: 10px;
      border-radius: 4px;
      margin-bottom: 15px;
    }
    
    .error-input {
      border-color: #dc3545 !important;
      box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
    }
    
    /* Business Hours Styles */
    .business-hours-section {
      margin-top: 10px;
    }
    
    .business-hours-container {
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 10px;
      background-color: #f9f9f9;
    }
    
    .business-hours-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background-color: #007bff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      width: 100%;
      justify-content: center;
    }
    
    .business-hours-btn:hover {
      background-color: #0056b3;
    }
    
    .btn-icon {
      font-size: 16px;
    }
    
    .business-hours-summary {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid #ddd;
    }
    
    .summary-title {
      font-weight: bold;
      margin-bottom: 10px;
      color: #495057;
    }
    
    .summary-content {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    
    .day-summary {
      display: flex;
      justify-content: space-between;
      padding: 3px 0;
      font-size: 13px;
    }
    
    .day-summary.closed {
      color: #6c757d;
    }
    
    .day-name {
      font-weight: 500;
      min-width: 40px;
    }
    
    .day-hours {
      text-align: right;
      flex: 1;
    }
  `]
})
export class BatchUpdateDialogComponent implements OnInit {
  @Input() dialogRef: any;
  @Input() dialogData: BatchUpdateDialogData | null = null;

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

  updatableFields = [
    { key: 'contactPerson', label: 'CONTACT_PERSON', selected: false, newValue: '', type: 'text' },
    { key: 'phoneNumber', label: 'PHONE_NUMBER', selected: false, newValue: '', type: 'text' },
    { key: 'faxNumber', label: 'FAX_NUMBER', selected: false, newValue: '', type: 'text' },
    { key: 'businessHours', label: 'BUSINESS_HOURS', selected: false, newValue: '', type: 'business-hours' },
    { key: 'paymentMethod', label: 'PAYMENT_METHOD', selected: false, newValue: '', type: 'select' },
    { key: 'paymentCategory', label: 'PAYMENT_CATEGORY', selected: false, newValue: '', type: 'select' },
    { key: 'creditLimit', label: 'CREDIT_LIMIT', selected: false, newValue: '', type: 'number' }
  ];

  selectedFields: any[] = [];
  errorMessage: string = '';

  // Business Hours related properties
  showBusinessHoursDialog: boolean = false;
  dayNames = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];
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

  constructor(private translate: TranslateService) {}

  ngOnInit(): void {
    console.log('BatchUpdateDialogComponent initialized');
    console.log('Dialog data:', this.dialogData);
    console.log('Dialog ref:', this.dialogRef);
  }

  // 獲取數據，優先使用 Input 屬性
  get data(): BatchUpdateDialogData {
    return this.dialogData || { customerIds: [], customerCount: 0 };
  }

  onFieldSelectionChange(): void {
    this.selectedFields = this.updatableFields.filter(field => field.selected);
    // 清除錯誤訊息當選擇改變時
    this.errorMessage = '';
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  getFieldLabel(fieldKey: string): string {
    const field = this.updatableFields.find(f => f.key === fieldKey);
    return field ? field.label : fieldKey;
  }

  isFieldEmpty(field: any): boolean {
    if (field.type === 'business-hours') {
      return !this.hasBusinessHours();
    }
    return !field.newValue || field.newValue.toString().trim() === '';
  }

  onInputChange(): void {
    // 當用戶開始輸入時，清除錯誤訊息
    if (this.errorMessage) {
      this.errorMessage = '';
    }
  }

  // Business Hours related methods
  openBusinessHoursDialog(): void {
    this.showBusinessHoursDialog = true;
  }

  onBusinessHoursSave(businessHoursData: any): void {
    this.businessHoursModel = businessHoursData;
    
    // 找到 businessHours 欄位並更新其值
    const businessHoursField = this.selectedFields.find(field => field.key === 'businessHours');
    if (businessHoursField) {
      businessHoursField.newValue = JSON.stringify(businessHoursData);
    }
    
    this.showBusinessHoursDialog = false;
    this.onInputChange(); // 清除錯誤訊息
  }

  onBusinessHoursCancel(): void {
    this.showBusinessHoursDialog = false;
  }

  hasBusinessHours(): boolean {
    const businessHoursField = this.selectedFields.find(field => field.key === 'businessHours');
    if (!businessHoursField || !businessHoursField.newValue) return false;
    
    try {
      const data = JSON.parse(businessHoursField.newValue);
      return data.weekly && data.weekly.some((day: any) => day.is_open);
    } catch {
      return false;
    }
  }

  getBusinessHoursSummary(): any[] {
    const businessHoursField = this.selectedFields.find(field => field.key === 'businessHours');
    if (!businessHoursField || !businessHoursField.newValue) return [];
    
    try {
      const data = JSON.parse(businessHoursField.newValue);
      return data.weekly.map((day: any, index: number) => ({
        name: this.dayNames[index],
        hours: day.is_open 
          ? day.ranges.map((range: any) => `${range.start}-${range.end}`).join(', ')
          : this.translate.instant('CLOSED')
      }));
    } catch {
      return [];
    }
  }

  onConfirm(): void {
    console.log('BatchUpdateDialog onConfirm called');
    console.log('Selected fields:', this.selectedFields);
    
    // 重置錯誤消息
    this.errorMessage = '';
    
    // 檢查是否有未輸入值的欄位
    const emptyFields = this.selectedFields.filter(field => {
      let isEmpty: boolean;
      if (field.type === 'business-hours') {
        isEmpty = !this.hasBusinessHours();
      } else {
        isEmpty = !field.newValue || field.newValue.toString().trim() === '';
      }
      console.log(`Field ${field.key}: value="${field.newValue}", isEmpty=${isEmpty}`);
      return isEmpty;
    });
    
    console.log('Empty fields:', emptyFields);
    
    if (emptyFields.length > 0) {
      // 構建錯誤消息，列出所有未輸入值的欄位
      const fieldLabels = emptyFields.map(field => 
        this.translate.instant(field.label)
      ).join('、');
      
      this.errorMessage = this.translate.instant('BATCH_UPDATE_EMPTY_FIELDS_ERROR', { 
        fields: fieldLabels 
      });
      
      console.log('Validation failed, error message:', this.errorMessage);
      return; // 阻止提交
    }
    
    const updateData: any = {};
    this.selectedFields.forEach(field => {
      // 確保值不為空才加入更新資料
      if (field.type === 'business-hours') {
        // 營業時間特殊處理
        if (this.hasBusinessHours()) {
          updateData[field.key] = field.newValue;
        }
      } else if (field.newValue && field.newValue.toString().trim() !== '') {
        let value = field.newValue.toString().trim();
        
        // 對於數字類型的欄位，轉換為數字
        if (field.type === 'number') {
          const numValue = parseFloat(value);
          if (!isNaN(numValue)) {
            updateData[field.key] = numValue;
          }
        } else {
          updateData[field.key] = value;
        }
      }
    });
    
    console.log('Validation passed, closing dialog with data:', updateData);
    
    this.dialogRef.close({
      customerIds: this.data?.customerIds || [],
      updateData: updateData
    });
  }
}

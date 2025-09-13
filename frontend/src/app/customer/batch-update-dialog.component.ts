import { Component, OnInit, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

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
  imports: [CommonModule, FormsModule, TranslateModule],
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
              <input 
                type="text" 
                [(ngModel)]="field.newValue"
                (input)="onInputChange()"
                [class]="'form-control' + (isFieldEmpty(field) && errorMessage ? ' error-input' : '')"
                [placeholder]="'請輸入' + (field.label | translate)">
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
  `]
})
export class BatchUpdateDialogComponent implements OnInit {
  @Input() dialogRef: any;
  @Input() dialogData: BatchUpdateDialogData | null = null;

  updatableFields = [
    { key: 'contactPerson', label: 'CONTACT_PERSON', selected: false, newValue: '' },
    { key: 'phoneNumber', label: 'PHONE_NUMBER', selected: false, newValue: '' },
    { key: 'faxNumber', label: 'FAX_NUMBER', selected: false, newValue: '' },
    { key: 'businessHours', label: 'BUSINESS_HOURS', selected: false, newValue: '' },
    { key: 'paymentMethod', label: 'PAYMENT_METHOD', selected: false, newValue: '' },
    { key: 'paymentCategory', label: 'PAYMENT_CATEGORY', selected: false, newValue: '' },
    { key: 'creditLimit', label: 'CREDIT_LIMIT', selected: false, newValue: '' }
  ];

  selectedFields: any[] = [];
  errorMessage: string = '';

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
    return !field.newValue || field.newValue.toString().trim() === '';
  }

  onInputChange(): void {
    // 當用戶開始輸入時，清除錯誤訊息
    if (this.errorMessage) {
      this.errorMessage = '';
    }
  }

  onConfirm(): void {
    console.log('BatchUpdateDialog onConfirm called');
    console.log('Selected fields:', this.selectedFields);
    
    // 重置錯誤消息
    this.errorMessage = '';
    
    // 檢查是否有未輸入值的欄位
    const emptyFields = this.selectedFields.filter(field => {
      const isEmpty = !field.newValue || field.newValue.toString().trim() === '';
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
      if (field.newValue && field.newValue.toString().trim() !== '') {
        updateData[field.key] = field.newValue.toString().trim();
      }
    });
    
    console.log('Validation passed, closing dialog with data:', updateData);
    
    this.dialogRef.close({
      customerIds: this.data?.customerIds || [],
      updateData: updateData
    });
  }
}

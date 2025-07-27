import { Component, Inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';

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
          <p>{{ 'BATCH_UPDATE_CONFIRM_MESSAGE' | translate: { count: data.customerCount } }}</p>
          
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
                class="form-control">
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
  `]
})
export class BatchUpdateDialogComponent {
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

  constructor(
    @Inject('dialogRef') public dialogRef: any,
    @Inject('dialogData') public data: BatchUpdateDialogData
  ) {}

  onFieldSelectionChange(): void {
    this.selectedFields = this.updatableFields.filter(field => field.selected);
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onConfirm(): void {
    const updateData: any = {};
    this.selectedFields.forEach(field => {
      updateData[field.key] = field.newValue;
    });
    
    this.dialogRef.close({
      customerIds: this.data.customerIds,
      updateData: updateData
    });
  }
}

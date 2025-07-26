import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-customer-type-management',
  standalone: true,
  imports: [FormsModule, CommonModule, TranslateModule],
  templateUrl: './customer-type-management.component.html',
  styleUrl: './customer-type-management.component.css'
})
export class CustomerTypeManagementComponent implements OnInit {
  message: string = '';
  messageType: string = 'success'; // 'success' or 'error'
  loading: boolean = false;
  isEditing: boolean = false;
  editingTypeId: number | null = null;
  deletingTypeId: number | null = null;
  
  customerTypes: any[] = [];
  
  formData: any = {
    typeName: ''
  };
  
  editingTypeData: any = {
    type_name: ''
  };

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadCustomerTypes();
  }
  
  loadCustomerTypes(): void {
    this.loading = true;
    this.apiService.getAllCustomerTypes().subscribe({
      next: (res: any) => {
        this.customerTypes = res;
        this.loading = false;
      },
      error: (error) => {
        this.showMessage('Error loading customer types: ' + (error?.error?.message || error?.message || 'Unknown error'), 'error');
        this.loading = false;
      }
    });
  }
  
  handleSubmit(): void {
    if (!this.formData.typeName) {
      this.showMessage('Type name is required', 'error');
      return;
    }
    
    if (this.isEditing && this.editingTypeId) {
      // Update existing type
      this.apiService.updateCustomerType(this.editingTypeId.toString(), { type_name: this.formData.typeName }).subscribe({
        next: (res: any) => {
          this.showMessage('Customer type updated successfully', 'success');
          this.resetForm();
          this.loadCustomerTypes(); // Reload the list
        },
        error: (error) => {
          this.showMessage('Error updating customer type: ' + (error?.error?.message || error?.message || 'Unknown error'), 'error');
        }
      });
    } else {
      // Add new type
      this.apiService.addCustomerType({ type_name: this.formData.typeName }).subscribe({
        next: (res: any) => {
          this.showMessage('Customer type added successfully', 'success');
          this.resetForm();
          this.loadCustomerTypes(); // Reload the list
        },
        error: (error) => {
          this.showMessage('Error adding customer type: ' + (error?.error?.message || error?.message || 'Unknown error'), 'error');
        }
      });
    }
  }
  
  startEditing(type: any): void {
    this.isEditing = true;
    this.editingTypeId = type.id;
    this.formData.typeName = type.type_name;
    this.editingTypeData.type_name = type.type_name;
  }
  
  saveEditing(id: number): void {
    if (!this.editingTypeData.type_name) {
      this.showMessage('Type name is required', 'error');
      return;
    }
    
    this.apiService.updateCustomerType(id.toString(), { type_name: this.editingTypeData.type_name }).subscribe({
      next: (res: any) => {
        this.showMessage('Customer type updated successfully', 'success');
        this.cancelEditing();
        this.loadCustomerTypes(); // Reload the list
      },
      error: (error) => {
        this.showMessage('Error updating customer type: ' + (error?.error?.message || error?.message || 'Unknown error'), 'error');
      }
    });
  }
  
  cancelEditing(): void {
    this.isEditing = false;
    this.editingTypeId = null;
    this.resetForm();
  }
  
  deleteCustomerType(id: number): void {
    if (!confirm('Are you sure you want to delete this customer type?')) {
      return;
    }
    
    this.deletingTypeId = id;
    this.apiService.deleteCustomerType(id.toString()).subscribe({
      next: (res: any) => {
        this.showMessage('Customer type deleted successfully', 'success');
        this.deletingTypeId = null;
        this.loadCustomerTypes(); // Reload the list
      },
      error: (error) => {
        this.showMessage('Error deleting customer type: ' + (error?.error?.message || error?.message || 'Unknown error'), 'error');
        this.deletingTypeId = null;
      }
    });
  }
  
  resetForm(): void {
    this.formData = {
      typeName: ''
    };
    this.isEditing = false;
    this.editingTypeId = null;
  }
  
  showMessage(message: string, type: string): void {
    this.message = message;
    this.messageType = type;
    setTimeout(() => {
      this.message = '';
    }, 5000);
  }
}

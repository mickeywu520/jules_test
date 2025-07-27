import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-customer',
  standalone: true,
  imports: [CommonModule, TranslateModule, FormsModule],
  templateUrl: './customer.component.html',
  styleUrl: './customer.component.css'
})
export class CustomerComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private router: Router,
    private loadingService: LoadingService
  ) {}
  customers: any[] = [];
  filteredCustomers: any[] = [];
  message: string = '';
  searchTerm: string = '';

  ngOnInit(): void {
    // 訂閱BehaviorSubject以獲取數據更新
    this.apiService.customers$.subscribe((custs: any[]) => {
      this.customers = custs;
      this.filteredCustomers = custs;
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
  }

  // Search customers
  onSearch(): void {
    if (this.searchTerm.trim() === '') {
      this.filteredCustomers = this.customers;
    } else {
      this.filteredCustomers = this.customers.filter(customer =>
        customer.customerName.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        customer.customerCode.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        (customer.contactPerson && customer.contactPerson.toLowerCase().includes(this.searchTerm.toLowerCase()))
      );
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

  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}

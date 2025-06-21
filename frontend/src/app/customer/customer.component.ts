import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../service/api.service';
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
  constructor(private apiService: ApiService, private router: Router) {}
  customers: any[] = [];
  filteredCustomers: any[] = [];
  message: string = '';
  searchTerm: string = '';

  ngOnInit(): void {
    this.apiService.customers$.subscribe((custs: any[]) => {
      this.customers = custs;
      this.filteredCustomers = custs;
    });
    // Fetch initial customers and populate/update the BehaviorSubject
    this.apiService.fetchAndBroadcastCustomers().subscribe({
      next: (res: any) => {
        // console.log('Initial customers fetched by CustomerComponent');
      },
      error: (error: any) => {
        this.showMessage(error?.error?.message || error?.message || "Unable to fetch initial customers" + error);
      }
    });
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
  getCustomerTypeText(type: string): string {
    return type || '-';
  }

  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}

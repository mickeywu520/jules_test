import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../service/api.service';
import { Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-supplier',
  standalone: true,
  imports: [CommonModule, TranslateModule],
  templateUrl: './supplier.component.html',
  styleUrl: './supplier.component.css',
})
export class SupplierComponent implements OnInit {
  constructor(private apiService: ApiService, private router: Router) {}
  suppliers: any[] = [];
  message: string = '';

  ngOnInit(): void {
    this.apiService.suppliers$.subscribe((supps: any[]) => {
      this.suppliers = supps;
    });
    // Fetch initial suppliers and populate/update the BehaviorSubject
    this.apiService.fetchAndBroadcastSuppliers().subscribe({
      next: (res: any) => {
        // console.log('Initial suppliers fetched by SupplierComponent');
      },
      error: (error: any) => {
        this.showMessage(error?.error?.message || error?.message || "Unable to fetch initial suppliers" + error);
      }
    });
  }

  //Navigate to ass supplier Page
  navigateToAddSupplierPage(): void {
    this.router.navigate([`/add-supplier`]);
  }

  //Navigate to edit supplier Page
  navigateToEditSupplierPage(supplierId: string): void {
    this.router.navigate([`/edit-supplier/${supplierId}`]);
  }

  //Delete a caetgory
  handleDeleteSupplier(supplierId: string):void{
    if (window.confirm("Are you sure you want to delete this supplier?")) {
      this.apiService.deleteSupplier(supplierId).subscribe({
        next:(res:any) =>{
          this.showMessage("Supplier deleted successfully")
          this.apiService.fetchAndBroadcastSuppliers().subscribe({
            next: () => { /* console.log('Suppliers refreshed after delete'); */ },
            error: (err: any) => {
              console.error('Failed to refresh suppliers after delete:', err);
              this.showMessage('Failed to refresh supplier list.');
            }
          }); //reload the category
        },
        error:(error) =>{
          this.showMessage(error?.error?.message || error?.message || "Unable to Delete Supplier" + error)
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

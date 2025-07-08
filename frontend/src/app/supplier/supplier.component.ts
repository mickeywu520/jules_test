import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
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
  constructor(
    private apiService: ApiService,
    private router: Router,
    private loadingService: LoadingService
  ) {}
  suppliers: any[] = [];
  message: string = '';

  ngOnInit(): void {
    // 訂閱BehaviorSubject以獲取數據更新
    this.apiService.suppliers$.subscribe((supps: any[]) => {
      this.suppliers = supps;
      // 如果有數據且loading還在顯示，則隱藏loading
      if (supps.length > 0 && this.loadingService.isLoading()) {
        this.loadingService.hideLoading();
      }
    });

    // 只有在BehaviorSubject沒有數據時才顯示loading並發起請求
    const currentSuppliers = this.apiService.suppliersSource.value;
    if (!currentSuppliers || currentSuppliers.length === 0) {
      this.loadingService.showDataLoading();
      this.apiService.fetchAndBroadcastSuppliers().subscribe({
        next: (res: any) => {
          // console.log('Initial suppliers fetched by SupplierComponent');
          this.loadingService.hideLoading();
        },
        error: (error: any) => {
          this.showMessage(error?.error?.message || error?.message || "Unable to fetch initial suppliers" + error);
          this.loadingService.hideLoading();
        }
      });
    }
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

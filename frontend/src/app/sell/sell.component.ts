import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';

@Component({
  selector: 'app-sell',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sell.component.html',
  styleUrl: './sell.component.css'
})
export class SellComponent implements OnInit {

  constructor(private apiService: ApiService){}


  products: any[] = []
  productId:string = ''
  description:string = ''
  quantity:string = ''
  message:string = ''



  ngOnInit(): void {
    // Subscribe to products from ApiService
    this.apiService.products$.subscribe((prods: any[]) => {
      this.products = prods;
    });
    this.apiService.fetchAndBroadcastProducts().subscribe({
      next: () => { /* console.log('Initial products fetched for SellComponent'); */ },
      error: (err) => this.showMessage(err?.error?.message || err?.message || 'Unable to fetch initial products')
    });
  }

  //Handle form submission
  handleSubmit():void{
    if (!this.productId || !this.quantity) {
      this.showMessage("Please fill all fields")
      return;
    }
    const body = {
      productId: this.productId,
      quantity:  parseInt(this.quantity, 10),
      description: this.description
    }

    this.apiService.sellProduct(body).subscribe({
      next: (res: any) => {
        if (res.status === 200) {
          this.showMessage(res.message)
          // Refresh product list in ApiService to reflect stock changes
          this.apiService.fetchAndBroadcastProducts().subscribe({
            next: () => { /* console.log('Product list refreshed after sell'); */ },
            error: (err: any) => { console.error('Failed to refresh product list after sell:', err); }
          });
          this.resetForm();
        }
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            'Unable to sell a product' + error
        );
      },
    })

  }

  
  resetForm():void{
    this.productId = '';
    this.description = '';
    this.quantity = '';
  }


  



  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}


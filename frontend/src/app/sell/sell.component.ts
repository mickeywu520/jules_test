import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../service/api.service';
import { Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-sell',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './sell.component.html',
  styleUrl: './sell.component.css'
})
export class SellComponent implements OnInit {

  constructor(private apiService: ApiService, private router: Router){}


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
    const quantityInt = parseInt(this.quantity, 10);
    const productIdInt = parseInt(this.productId, 10);

    // Find the product to get its price
    const product = this.products.find(p => p.id === productIdInt);
    const totalPrice = product ? product.price * quantityInt : 0;

    const body = {
      products_involved: [{
        product_id: productIdInt,
        quantity: quantityInt
      }],
      totalProducts: quantityInt, // Assuming totalProducts is just the quantity for a single product transaction
      totalPrice: totalPrice,
      transactionType: 'SELL',
      description: this.description
    }

    this.apiService.sellProduct(body).subscribe({
      next: (res: any) => {
        this.showMessage("Sell successful!") // Use a generic success message as res.message might not exist
        // Refresh product list in ApiService to reflect stock changes
        this.apiService.fetchAndBroadcastProducts().subscribe({
          next: () => { /* console.log('Product list refreshed after sell'); */ },
          error: (err: any) => { console.error('Failed to refresh product list after sell:', err); }
        });
        this.resetForm();
        this.router.navigate(['/transaction']); // Navigate to transactions page
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

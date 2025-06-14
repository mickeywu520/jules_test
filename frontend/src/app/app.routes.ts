import { Routes } from '@angular/router';
import { GuardService } from './service/guard.service';
import { LoginComponent } from './login/login.component';
import { RegisterComponent } from './register/register.component';
import { CategoryComponent } from './category/category.component';
import { SupplierComponent } from './supplier/supplier.component';
import { AddEditSupplierComponent } from './add-edit-supplier/add-edit-supplier.component';
import { ProductComponent } from './product/product.component';
import { AddEditProductComponent } from './add-edit-product/add-edit-product.component';
import { PurchaseComponent } from './purchase/purchase.component';
import { SellComponent } from './sell/sell.component';
import { TransactionComponent } from './transaction/transaction.component';
import { TransactionDetailsComponent } from './transaction-details/transaction-details.component';
import { ProfileComponent } from './profile/profile.component';
import { DashboardComponent } from './dashboard/dashboard.component';

export const routes: Routes = [

  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },

  { path: 'category', component: CategoryComponent, canActivate:[GuardService], data: {requiresAdmin: true} },

  { path: 'supplier', component: SupplierComponent, canActivate:[GuardService], data: {requiresAdmin: true} },
  { path: 'edit-supplier/:supplierId', component: AddEditSupplierComponent, canActivate:[GuardService], data: {requiresAdmin: true} },
  { path: 'add-supplier', component: AddEditSupplierComponent, canActivate:[GuardService], data: {requiresAdmin: true} },

  { path: 'product', component: ProductComponent, canActivate:[GuardService], data: {requiresAdmin: true} },
  { path: 'edit-product/:productId', component: AddEditProductComponent, canActivate:[GuardService], data: {requiresAdmin: true} },
  { path: 'add-product', component: AddEditProductComponent, canActivate:[GuardService], data: {requiresAdmin: true} },


  { path: 'purchase', component: PurchaseComponent, canActivate:[GuardService] },
  { path: 'sell', component: SellComponent, canActivate:[GuardService] },

  { path: 'transaction', component: TransactionComponent, canActivate:[GuardService] },
  { path: 'transaction/:transactionId', component: TransactionDetailsComponent, canActivate:[GuardService] },


  { path: 'profile', component: ProfileComponent, canActivate:[GuardService] },
  { path: 'dashboard', component: DashboardComponent, canActivate:[GuardService] },

//   WIDE CARD
    {path: "", redirectTo: "/login", pathMatch: 'full'},
    // {path: "**", redirectTo: "/dashboard"}

];

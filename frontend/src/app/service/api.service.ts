import { EventEmitter, Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import CryptoJS from "crypto-js";
import { environment } from '../../environments/environment';



@Injectable({
  providedIn: 'root',
})


export class ApiService {

  // BehaviorSubject for reactive categories
  public categoriesSource = new BehaviorSubject<any[]>([]);
  public categories$ = this.categoriesSource.asObservable();

  // BehaviorSubject for reactive products
  public productsSource = new BehaviorSubject<any[]>([]);
  public products$ = this.productsSource.asObservable();

  // BehaviorSubject for reactive suppliers
  public suppliersSource = new BehaviorSubject<any[]>([]);
  public suppliers$ = this.suppliersSource.asObservable();

  // BehaviorSubject for reactive customers
  public customersSource = new BehaviorSubject<any[]>([]);
  public customers$ = this.customersSource.asObservable();

  authStatuschanged = new EventEmitter<void>();
  private static BASE_URL = environment.apiUrl;
  private static ENCRYPTION_KEY = "phegon-dev-inventory";


  constructor(private http: HttpClient) {}

    // Encrypt data and save to localStorage
    encryptAndSaveToStorage(key: string, value: string): void {
      const encryptedValue = CryptoJS.AES.encrypt(value, ApiService.ENCRYPTION_KEY).toString();
      localStorage.setItem(key, encryptedValue);
    }
  
    // Retreive from localStorage and Decrypt
    private getFromStorageAndDecrypt(key: string): any {
      try {
        const encryptedValue = localStorage.getItem(key);
        if (!encryptedValue) return null;
        return CryptoJS.AES.decrypt(encryptedValue, ApiService.ENCRYPTION_KEY).toString(CryptoJS.enc.Utf8);
      } catch (error) {
        return null;
      }
    }

    
  private clearAuth() {
      localStorage.removeItem("token");
      localStorage.removeItem("role");
  }


  public fetchAndBroadcastCategories(): Observable<any[]> {
    const httpOptions = { headers: this.getHeader() };
    // Assuming the backend /api/categories/all returns an array of categories directly
    const request = this.http.get<any[]>(`${ApiService.BASE_URL}/categories/all`, httpOptions);

    request.subscribe({
      next: (categoriesArray: any[]) => {
        if (Array.isArray(categoriesArray)) {
          this.categoriesSource.next(categoriesArray);
        } else {
          console.warn("fetchAndBroadcastCategories: Response was not an array.", categoriesArray);
          this.categoriesSource.next([]); // Broadcast empty if structure is off
        }
      },
      error: (err: any) => {
        console.error("Error fetching categories for BehaviorSubject:", err);
        this.categoriesSource.next([]); // Broadcast empty on error to clear stale data
      }
    });
    return request; // Return the original observable for the caller
  }


  public fetchAndBroadcastProducts(): Observable<any[]> {
    // 使用 getActiveProducts 只獲取有效產品（用於採購單等業務邏輯）
    const request = this.getActiveProducts();

    request.subscribe({
      next: (productsArray: any[]) => {
        if (Array.isArray(productsArray)) {
          this.productsSource.next(productsArray);
        } else {
          console.warn("fetchAndBroadcastProducts: Response was not an array.", productsArray);
          this.productsSource.next([]);
        }
      },
      error: (err: any) => {
        console.error("Error fetching products for BehaviorSubject:", err);
        this.productsSource.next([]);
      }
    });
    return request;
  }


  public fetchAndBroadcastSuppliers(): Observable<any[]> {
    const httpOptions = { headers: this.getHeader() };
    const request = this.http.get<any[]>(`${ApiService.BASE_URL}/suppliers/all`, httpOptions);

    request.subscribe({
      next: (suppliersArray: any[]) => {
        if (Array.isArray(suppliersArray)) {
          this.suppliersSource.next(suppliersArray);
        } else {
          console.warn("fetchAndBroadcastSuppliers: Response was not an array.", suppliersArray);
          this.suppliersSource.next([]);
        }
      },
      error: (err: any) => {
        console.error("Error fetching suppliers for BehaviorSubject:", err);
        this.suppliersSource.next([]);
      }
    });
    return request;
  }

  public fetchAndBroadcastCustomers(): Observable<any[]> {
    const httpOptions = { headers: this.getHeader() };
    const request = this.http.get<any[]>(`${ApiService.BASE_URL}/customers/all`, httpOptions);

    request.subscribe({
      next: (customersArray: any[]) => {
        if (Array.isArray(customersArray)) {
          this.customersSource.next(customersArray);
        } else {
          console.warn("fetchAndBroadcastCustomers: Response was not an array.", customersArray);
          this.customersSource.next([]);
        }
      },
      error: (err: any) => {
        console.error("Error fetching customers for BehaviorSubject:", err);
        this.customersSource.next([]);
      }
    });
    return request;
  }


  // Method to get data from the new FastAPI backend
  getFastApiData(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/data`);
  }



  private getHeader(): HttpHeaders {
    const token = this.getFromStorageAndDecrypt("token");
    return new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });
  }







  /***AUTH & USERS API METHODS */

  registerUser(body: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/auth/register`, body);
  }

  loginUser(body: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/auth/login`, body);
  }

  getLoggedInUserInfo(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/users/current`, {
      headers: this.getHeader(),
    });
  }

  getAllUsers(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/users/all`, {
      headers: this.getHeader(),
    });
  }

  updateUser(userId: number, userData: any): Observable<any> {
    return this.http.put(`${ApiService.BASE_URL}/users/${userId}`, userData, {
      headers: this.getHeader(),
    });
  }

  getUserById(userId: number): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/users/${userId}`, {
      headers: this.getHeader(),
    });
  }









  /**CATEGOTY ENDPOINTS */
  createCategory(body: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/categories/add`, body, {
      headers: this.getHeader(),
    });
  }

  getAllCategory(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/categories/all`, {
      headers: this.getHeader(),
    });
  }

  getCategoryById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/categories/${id}`, {
      headers: this.getHeader(),
    });
  }

  updateCategory(id: string, body: any): Observable<any> {
    return this.http.put(
      `${ApiService.BASE_URL}/categories/update/${id}`,
      body,
      {
        headers: this.getHeader(),
      }
    );
  }

  deleteCategory(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/categories/delete/${id}`, {
      headers: this.getHeader(),
    });
  }






  /** SUPPLIER API */
  addSupplier(body: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/suppliers/add`, body, {
      headers: this.getHeader(),
    });
  }

  getAllSuppliers(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/suppliers/all`, {
      headers: this.getHeader(),
    });
  }

  getSupplierById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/suppliers/${id}`, {
      headers: this.getHeader(),
    });
  }

  updateSupplier(id: string, body: any): Observable<any> {
    return this.http.put(
      `${ApiService.BASE_URL}/suppliers/update/${id}`,
      body,
      {
        headers: this.getHeader(),
      }
    );
  }

  deleteSupplier(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/suppliers/delete/${id}`, {
      headers: this.getHeader(),
    });
  }

  /** CUSTOMER API */
  addCustomer(body: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/customers/add`, body, {
      headers: this.getHeader(),
    });
  }

  getAllCustomers(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/customers/all`, {
      headers: this.getHeader(),
    });
  }

  getCustomerById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/customers/${id}`, {
      headers: this.getHeader(),
    });
  }

  getCustomerByCode(customerCode: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/customers/code/${customerCode}`, {
      headers: this.getHeader(),
    });
  }

  updateCustomer(id: string, body: any): Observable<any> {
    return this.http.put(
      `${ApiService.BASE_URL}/customers/update/${id}`,
      body,
      {
        headers: this.getHeader(),
      }
    );
  }

  deleteCustomer(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/customers/delete/${id}`, {
      headers: this.getHeader(),
    });
  }

  searchCustomers(searchTerm: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/customers/search/${searchTerm}`, {
      headers: this.getHeader(),
    });
  }

  getNextCustomerCode(customerTypeId: number): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/customers/next-code/${customerTypeId}`, {
      headers: this.getHeader(),
    });
  }

  /** CUSTOMER TYPE API */
  addCustomerType(body: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/customer-types/`, body, {
      headers: this.getHeader(),
    });
  }

  getAllCustomerTypes(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/customer-types/`, {
      headers: this.getHeader(),
    });
  }

  getCustomerTypeById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/customer-types/${id}`, {
      headers: this.getHeader(),
    });
  }

  updateCustomerType(id: string, body: any): Observable<any> {
    return this.http.put(`${ApiService.BASE_URL}/customer-types/${id}`, body, {
      headers: this.getHeader(),
    });
  }

  deleteCustomerType(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/customer-types/${id}`, {
      headers: this.getHeader(),
    });
  }







  /**PRODUCTS ENDPOINTS */
  addProduct(productData: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/products/add`, productData, {
      headers: this.getHeader(),
    });
  }

  updateProduct(id: string, productData: any): Observable<any> {
    return this.http.put(`${ApiService.BASE_URL}/products/update/${id}`, productData, {
      headers: this.getHeader(),
    });
  }

  // 獲取所有產品（可選擇是否包含已刪除）
  getAllProducts(includeDeleted: boolean = false): Observable<any> {
    const params = includeDeleted ? '?include_deleted=true' : '';
    return this.http.get(`${ApiService.BASE_URL}/products/all${params}`, {
      headers: this.getHeader(),
    });
  }

  // 獲取有效產品（只用於銷售單等業務邏輯）
  getActiveProducts(): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/products/active`, {
      headers: this.getHeader(),
    });
  }

  getProductById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/products/${id}`, {
      headers: this.getHeader(),
    });
  }

  deleteProduct(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/products/delete/${id}`, {
      headers: this.getHeader(),
    });
  }

  // 恢復已刪除的產品
  restoreProduct(id: string): Observable<any> {
    return this.http.patch(`${ApiService.BASE_URL}/products/restore/${id}`, {}, {
      headers: this.getHeader(),
    });
  }








  /**Transactions Endpoints */

  purchaseProduct(body: any): Observable<any> {
    return this.http.post(
      `${ApiService.BASE_URL}/transactions/purchase`,
      body,
      {
        headers: this.getHeader(),
      }
    );
  }

  sellProduct(body: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/transactions/sell`, body, {
      headers: this.getHeader(),
    });
  }

  getAllTransactions(searchText: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/transactions/all`, {
      params: { searchText: searchText },
      headers: this.getHeader(),
    });
  }

  getTransactionById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/transactions/${id}`, {
      headers: this.getHeader(),
    });
  }

  
  updateTransactionStatus(id: string, status: string): Observable<any> {
    // The backend expects a JSON object like {"status": "NEW_STATUS"}
    const body = { status: status };
    return this.http.put(`${ApiService.BASE_URL}/transactions/update/${id}`, body, {
      headers: this.getHeader()
    });
  }


  getTransactionsByMonthAndYear(month: number, year: number): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/transactions/by-month-year`, {
      headers: this.getHeader(),
      params: {
        month: month,
        year: year,
      },
    });
  }












/**AUTHENTICATION CHECKER */
    
  logout():void{
    this.clearAuth()
  }

  isAuthenticated():boolean{
    const token = this.getFromStorageAndDecrypt("token");
    return !!token;
  }

  isAdmin():boolean {
    const role = this.getFromStorageAndDecrypt("role");
    return role === "ADMIN";
  }

  /**PURCHASE ORDER ENDPOINTS */
  // 新增採購單
  createPurchaseOrder(purchaseOrderData: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/purchase-orders/`, purchaseOrderData, {
      headers: this.getHeader(),
    });
  }

  // 獲取所有採購單
  getAllPurchaseOrders(skip: number = 0, limit: number = 100): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/purchase-orders/?skip=${skip}&limit=${limit}`, {
      headers: this.getHeader(),
    });
  }

  // 根據 ID 獲取採購單
  getPurchaseOrderById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/purchase-orders/${id}`, {
      headers: this.getHeader(),
    });
  }

  // 更新採購單
  updatePurchaseOrder(id: string, purchaseOrderData: any): Observable<any> {
    return this.http.put(`${ApiService.BASE_URL}/purchase-orders/${id}`, purchaseOrderData, {
      headers: this.getHeader(),
    });
  }

  // 刪除採購單
  deletePurchaseOrder(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/purchase-orders/${id}`, {
      headers: this.getHeader(),
    });
  }

  // 更新採購單狀態
  updatePurchaseOrderStatus(id: string, status: string): Observable<any> {
    return this.http.patch(`${ApiService.BASE_URL}/purchase-orders/${id}/status`, { status: status }, {
      headers: this.getHeader(),
    });
  }

  /**GOODS RECEIPT ENDPOINTS */
  // 新增入庫單
  createGoodsReceipt(goodsReceiptData: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/goods-receipts/`, goodsReceiptData, {
      headers: this.getHeader(),
    });
  }

  // 獲取所有入庫單
  getAllGoodsReceipts(skip: number = 0, limit: number = 100): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/goods-receipts/?skip=${skip}&limit=${limit}`, {
      headers: this.getHeader(),
    });
  }

  // 根據 ID 獲取入庫單
  getGoodsReceiptById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/goods-receipts/${id}`, {
      headers: this.getHeader(),
    });
  }

  // 根據採購單 ID 獲取可入庫明細
  getReceivableItemsByPurchaseOrder(poId: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/goods-receipts/purchase-order/${poId}/items`, {
      headers: this.getHeader(),
    });
  }

  // 根據採購單查詢入庫記錄
  getGoodsReceiptsByPurchaseOrder(poId: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/goods-receipts/by-purchase-order/${poId}`, {
      headers: this.getHeader(),
    });
  }

  // 更新入庫單
  updateGoodsReceipt(id: string, goodsReceiptData: any): Observable<any> {
    return this.http.put(`${ApiService.BASE_URL}/goods-receipts/${id}`, goodsReceiptData, {
      headers: this.getHeader(),
    });
  }

  // 刪除入庫單
  deleteGoodsReceipt(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/goods-receipts/${id}`, {
      headers: this.getHeader(),
    });
  }

  // 更新入庫單狀態
  updateGoodsReceiptStatus(id: string, status: string): Observable<any> {
    return this.http.patch(`${ApiService.BASE_URL}/goods-receipts/${id}/status`, { status: status }, {
      headers: this.getHeader(),
    });
  }

  /**SALES ORDER ENDPOINTS */
  // 新增銷售單
  createSalesOrder(salesOrderData: any): Observable<any> {
    return this.http.post(`${ApiService.BASE_URL}/sales-orders/`, salesOrderData, {
      headers: this.getHeader(),
    });
  }

  // 獲取所有銷售單
  getAllSalesOrders(skip: number = 0, limit: number = 100): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/sales-orders/?skip=${skip}&limit=${limit}`, {
      headers: this.getHeader(),
    });
  }

  // 根據 ID 獲取銷售單
  getSalesOrderById(id: string): Observable<any> {
    return this.http.get(`${ApiService.BASE_URL}/sales-orders/${id}`, {
      headers: this.getHeader(),
    });
  }

  // 更新銷售單
  updateSalesOrder(id: string, salesOrderData: any): Observable<any> {
    return this.http.put(`${ApiService.BASE_URL}/sales-orders/${id}`, salesOrderData, {
      headers: this.getHeader(),
    });
  }

  // 刪除銷售單
  deleteSalesOrder(id: string): Observable<any> {
    return this.http.delete(`${ApiService.BASE_URL}/sales-orders/${id}`, {
      headers: this.getHeader(),
    });
  }

  // 更新銷售單狀態
  updateSalesOrderStatus(id: string, status: string): Observable<any> {
    return this.http.patch(`${ApiService.BASE_URL}/sales-orders/${id}/status`, { status: status }, {
      headers: this.getHeader(),
    });
  }

}

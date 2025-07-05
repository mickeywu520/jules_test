import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TranslateModule } from '@ngx-translate/core';
import { FormsModule } from '@angular/forms';

import { ShippingComponent } from './shipping.component';

describe('ShippingComponent', () => {
  let component: ShippingComponent;
  let fixture: ComponentFixture<ShippingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ShippingComponent,
        HttpClientTestingModule,
        TranslateModule.forRoot(),
        FormsModule
      ]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ShippingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.showShippingOrderList).toBe(true);
    expect(component.isEditing).toBe(false);
    expect(component.shippingOrders).toEqual([]);
    expect(component.formData.shipping_method).toBe('SELF_DELIVERY');
  });

  it('should toggle shipping order list', () => {
    const initialState = component.showShippingOrderList;
    component.toggleShippingOrderList();
    expect(component.showShippingOrderList).toBe(!initialState);
  });

  it('should reset form', () => {
    component.formData.sales_order_id = '123';
    component.formData.shipper_name = 'Test Shipper';
    component.resetForm();
    
    expect(component.formData.sales_order_id).toBe('');
    expect(component.formData.shipper_name).toBe('');
    expect(component.isEditing).toBe(false);
  });

  it('should apply filters correctly', () => {
    component.shippingOrders = [
      {
        id: 1,
        sh_number: 'SH-20240101-001',
        status: 'PREPARING',
        customer: { customerName: 'Test Customer' }
      } as any,
      {
        id: 2,
        sh_number: 'SH-20240101-002',
        status: 'SHIPPED',
        customer: { customerName: 'Another Customer' }
      } as any
    ];

    component.searchTerm = 'Test';
    component.applyFilters();
    expect(component.filteredShippingOrders.length).toBe(1);

    component.searchTerm = '';
    component.statusFilter = 'SHIPPED';
    component.applyFilters();
    expect(component.filteredShippingOrders.length).toBe(1);
    expect(component.filteredShippingOrders[0].status).toBe('SHIPPED');
  });
});

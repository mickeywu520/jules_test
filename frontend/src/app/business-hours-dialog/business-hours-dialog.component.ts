import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-business-hours-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './business-hours-dialog.component.html',
  styleUrl: './business-hours-dialog.component.css'
})
export class BusinessHoursDialogComponent {
  @Input() isOpen: boolean = false;
  @Input() businessHoursData: any = null;
  @Output() onSave = new EventEmitter<any>();
  @Output() onCancel = new EventEmitter<void>();

  dayNames = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];

  businessHoursModel: any = {
    weekly: [
      { weekday: 0, is_open: false, ranges: [] },
      { weekday: 1, is_open: false, ranges: [] },
      { weekday: 2, is_open: false, ranges: [] },
      { weekday: 3, is_open: false, ranges: [] },
      { weekday: 4, is_open: false, ranges: [] },
      { weekday: 5, is_open: false, ranges: [] },
      { weekday: 6, is_open: false, ranges: [] },
    ],
    exceptions: []
  };

  ngOnInit() {
    if (this.businessHoursData) {
      this.businessHoursModel = JSON.parse(JSON.stringify(this.businessHoursData));
    }
    
    // 確保每天至少有一個時間段供編輯
    this.businessHoursModel.weekly.forEach((day: any) => {
      if (day.is_open && (!day.ranges || day.ranges.length === 0)) {
        day.ranges = [{ start: '09:00', end: '18:00' }];
      }
    });
  }

  onDayToggle(dayIndex: number) {
    const day = this.businessHoursModel.weekly[dayIndex];
    if (day.is_open && (!day.ranges || day.ranges.length === 0)) {
      day.ranges = [{ start: '09:00', end: '18:00' }];
    } else if (!day.is_open) {
      day.ranges = [];
    }
  }

  addRange(dayIndex: number) {
    const day = this.businessHoursModel.weekly[dayIndex];
    if (!day.ranges) day.ranges = [];
    day.ranges.push({ start: '09:00', end: '18:00' });
  }

  removeRange(dayIndex: number, rangeIndex: number) {
    const day = this.businessHoursModel.weekly[dayIndex];
    if (day && day.ranges) {
      day.ranges.splice(rangeIndex, 1);
    }
  }

  addException() {
    if (!this.businessHoursModel.exceptions) this.businessHoursModel.exceptions = [];
    this.businessHoursModel.exceptions.push({
      date: '',
      is_open: false,
      ranges: [],
      reason: ''
    });
  }

  removeException(index: number) {
    if (!this.businessHoursModel.exceptions) return;
    this.businessHoursModel.exceptions.splice(index, 1);
  }

  onExceptionToggle(exceptionIndex: number) {
    const exception = this.businessHoursModel.exceptions[exceptionIndex];
    if (exception.is_open && (!exception.ranges || exception.ranges.length === 0)) {
      exception.ranges = [{ start: '09:00', end: '18:00' }];
    } else if (!exception.is_open) {
      exception.ranges = [];
    }
  }

  save() {
    this.onSave.emit(this.businessHoursModel);
  }

  cancel() {
    this.onCancel.emit();
  }

  // 快速設定常用營業時間
  setCommonHours(type: string) {
    switch (type) {
      case 'weekdays':
        // 週一到週五 9:00-18:00
        for (let i = 0; i < 5; i++) {
          this.businessHoursModel.weekly[i].is_open = true;
          this.businessHoursModel.weekly[i].ranges = [{ start: '09:00', end: '18:00' }];
        }
        break;
      case 'everyday':
        // 每天 9:00-18:00
        this.businessHoursModel.weekly.forEach((day: any) => {
          day.is_open = true;
          day.ranges = [{ start: '09:00', end: '18:00' }];
        });
        break;
      case 'retail':
        // 零售店常見時間：週一到週日 10:00-22:00
        this.businessHoursModel.weekly.forEach((day: any) => {
          day.is_open = true;
          day.ranges = [{ start: '10:00', end: '22:00' }];
        });
        break;
    }
  }

  clearAll() {
    this.businessHoursModel.weekly.forEach((day: any) => {
      day.is_open = false;
      day.ranges = [];
    });
    this.businessHoursModel.exceptions = [];
  }
}
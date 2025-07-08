import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../service/api.service';
import { LoadingService } from '../service/loading.service';
import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, TranslateModule],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css'
})
export class ProfileComponent implements OnInit {
  constructor(
    private apiService: ApiService,
    private loadingService: LoadingService
  ){}
  user: any = null
  message: string = "";

  ngOnInit(): void {
    this.fetchUserInfo();
  }

  fetchUserInfo():void{
    this.loadingService.showDataLoading();
    this.apiService.getLoggedInUserInfo().subscribe({
      next:(res)=>{
        this.user = res;
        this.loadingService.hideLoading();
      },
      error: (error) => {
        this.showMessage(
          error?.error?.message ||
            error?.message ||
            'Unable to Get Profile Info' + error
        );
        this.loadingService.hideLoading();
      }
    })
  }



  //SHOW ERROR
  showMessage(message: string) {
    this.message = message;
    setTimeout(() => {
      this.message = '';
    }, 4000);
  }
}

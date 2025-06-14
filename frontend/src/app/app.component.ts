import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { ApiService } from './service/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})


export class AppComponent implements OnInit {
  title = 'ims';
  constructor(
    private apiService: ApiService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}


isAuth():boolean{
  return this.apiService.isAuthenticated();
}

isAdmin():boolean{
  return this.apiService.isAdmin();
}

logOut():void{
  this.apiService.logout();
  this.router.navigate(["/login"])
  this.cdr.detectChanges();
}

  ngOnInit(): void {
    this.apiService.getFastApiData().subscribe({
      next: (data) => console.log('Data from FastAPI backend:', data),
      error: (err) => console.error('Error fetching from FastAPI:', err)
    });
  }





}

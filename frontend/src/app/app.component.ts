import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { Router, RouterLink, RouterOutlet, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { ApiService } from './service/api.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, CommonModule, TranslateModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})


export class AppComponent implements OnInit, AfterViewInit {
  title = 'ims';
  @ViewChild('navLinks', { static: false }) navLinks!: ElementRef;
  private scrollInterval: any;
  sidebarOpen = false;

  constructor(
    private apiService: ApiService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private translate: TranslateService
  ) {
    this.translate.addLangs(['en', 'zh-TW']);
    this.translate.setDefaultLang('zh-TW');
  }


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

    // 監聽路由變化，自動關閉側邊欄
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.closeSidebar();
      });
  }

  ngAfterViewInit(): void {
    // 初始化滾動功能
  }

  // 滑鼠進入導航區域下半部時開始向下滾動
  onMouseEnterBottom(): void {
    this.startAutoScroll('down');
  }

  // 滑鼠進入導航區域上半部時開始向上滾動
  onMouseEnterTop(): void {
    this.startAutoScroll('up');
  }

  // 滑鼠離開時停止滾動
  onMouseLeave(): void {
    this.stopAutoScroll();
  }

  // 開始自動滾動
  private startAutoScroll(direction: 'up' | 'down'): void {
    this.stopAutoScroll(); // 先停止之前的滾動

    if (this.navLinks) {
      const scrollSpeed = 2; // 滾動速度
      this.scrollInterval = setInterval(() => {
        const element = this.navLinks.nativeElement;
        if (direction === 'down') {
          element.scrollTop += scrollSpeed;
        } else {
          element.scrollTop -= scrollSpeed;
        }
      }, 16); // 約60fps
    }
  }

  // 停止自動滾動
  private stopAutoScroll(): void {
    if (this.scrollInterval) {
      clearInterval(this.scrollInterval);
      this.scrollInterval = null;
    }
  }

  // 切換側邊欄顯示/隱藏
  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }

  // 關閉側邊欄
  closeSidebar(): void {
    this.sidebarOpen = false;
  }

  // 導航項目點擊處理
  onNavItemClick(): void {
    this.closeSidebar();
  }





}

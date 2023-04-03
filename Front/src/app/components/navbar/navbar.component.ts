import { Component, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit {
  api_assets: string = environment.api_assets;

  constructor() {
  }

  ngOnInit() {
  }

  ngOnChanges() {
  }
}

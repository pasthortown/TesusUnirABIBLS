import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ExporterService {

  options = {};

  constructor(private http: HttpClient) { }

  build_headers() {
    let headers: HttpHeaders = new HttpHeaders().set('token', environment.token as string)
    this.options = {headers: headers};
  }

  get() {
    return this.http.get(environment.api_exporter).toPromise();
  }
}

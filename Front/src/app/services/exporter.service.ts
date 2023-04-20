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

  build_qr(content: string): Promise<any> {
    this.build_headers();
    const data = { toEncode: content };
    return this.http.post(environment.api_exporter + 'qr', JSON.stringify(data), this.options).toPromise();
  }

  build_pdf(params: any, template_name: string): Promise<any> {
    this.build_headers();
    const data = {params: params, template_name: template_name};
    return this.http.post(environment.api_exporter + 'pdf', JSON.stringify(data), this.options).toPromise();
  }
}

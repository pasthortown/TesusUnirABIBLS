import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class IawsService {

  options = {};

  constructor(private http: HttpClient) { }

  build_headers() {
    let headers: HttpHeaders = new HttpHeaders().set('token', environment.token as string)
    this.options = {headers: headers};
  }

  tweets() {
    this.build_headers();
    const data = {};
    return this.http.post(environment.api_ia + 'tweets', JSON.stringify(data), this.options ).toPromise();
  }

  hashtags() {
    this.build_headers();
    const data = {};
    return this.http.post(environment.api_ia + 'hashtags', JSON.stringify(data), this.options ).toPromise();
  }
}

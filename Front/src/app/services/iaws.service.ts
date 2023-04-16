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

  search_tweets_and_store_on_db(hashtags: string[], since_date: string, until_date: string) {
    this.build_headers();
    const data = {
      hashtags: hashtags,
      since_date: since_date,
      until_date: until_date
    };
    return this.http.post(environment.api_ia + 'search_tweets_and_store_on_db', JSON.stringify(data), this.options ).toPromise();
  }

  hashtags() {
    this.build_headers();
    const data = {};
    return this.http.post(environment.api_ia + 'hashtags', JSON.stringify(data), this.options ).toPromise();
  }
}

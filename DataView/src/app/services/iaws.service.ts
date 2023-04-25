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

  hashtags() {
    this.build_headers();
    const data = {};
    return this.http.post(environment.api_ia + 'hashtags', JSON.stringify(data), this.options ).toPromise();
  }

  get_all_tweets() {
    this.build_headers();
    const data = {};
    return this.http.post(environment.api_ia + 'get_all_tweets', JSON.stringify(data), this.options ).toPromise();
  }

  upload_tweets_backup(tweets: any[]) {
    this.build_headers();
    const data = {tweets: tweets};
    return this.http.post(environment.api_ia + 'upload_tweets_backup', JSON.stringify(data), this.options ).toPromise();
  }

  get_tweets_to_process() {
    this.build_headers();
    const data = {};
    return this.http.post(environment.api_ia + 'get_tweets_to_process', JSON.stringify(data), this.options ).toPromise();
  }

  update_tweet(tweet_id: Number, clasificado: string) {
    this.build_headers();
    const data = {
      tweet_id: tweet_id,
      clasificado: clasificado
    };
    return this.http.post(environment.api_ia + 'update_tweet', JSON.stringify(data), this.options ).toPromise();
  }
}

import { Component } from '@angular/core';
import { NgxSpinnerService } from 'ngx-spinner';
import { ToastrService } from 'ngx-toastr';
import { IawsService } from 'src/app/services/iaws.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'DataView';
  tweets: any[] = [];

  constructor(
    private iaService: IawsService,
    private toastr: ToastrService,
    private spinner: NgxSpinnerService) { }

  ngOnInit(): void {
    this.get_tweets();
  }

  get_tweets() {
    this.spinner.show();
    this.iaService.get_tweets_to_process().then((r: any) => {
      this.spinner.hide();
      this.tweets = r.response;
    }).catch(e => { console.log(e); });
  }

  classify_tweet(tweet_id: Number, classification: string) {
    this.iaService.update_tweet(tweet_id, classification).then((r: any) => {
      this.get_tweets();
    }).catch(e => { console.log(e); });
  }
}
